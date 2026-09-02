import hashlib
from datetime import date, timedelta

from loguru import logger

from app.config import env_config
from app.enums import AiNoteAction, DatedAction
from app.repositories import ScheduleRepository
from app.schemas import (
    AiNoteOperation,
    AiNoteResponse,
    DatedLesson,
    DatedSchedule,
    LessonPatch,
    ParseResult,
    Schedule,
    ScheduleNote,
)
from app.services.ai_service import AiService

CACHE_VERSION = 2


class DatedScheduleBuilder:
    """Turns sheet footnotes into a generated dated schedule.

    The model is asked about the footnote text alone, never about the slot it
    belongs to: the same wording repeats across groups and weeks, so one answer
    serves many slots and the cache key is just the text.
    """

    def __init__(self, ai_service: AiService, repository: ScheduleRepository | None = None) -> None:
        self._ai_service = ai_service
        self._repository = repository or ScheduleRepository()

    async def build(self, result: ParseResult) -> DatedSchedule:
        answers = await self._resolve_notes(result.notes)

        dated = DatedSchedule()
        for note in result.notes:
            answer = answers.get(note.text)
            if answer is None or not answer.understood:
                continue
            for operation in answer.operations:
                for entry in self._materialize(note, operation, result.schedule):
                    dated.add(note.group, entry)

        overrides = self._repository.dated_overrides
        if overrides.groups:
            logger.info(f"Applying {sum(len(v) for v in overrides.groups.values())} manual dated overrides")
        return dated.merge(overrides)

    async def _resolve_notes(self, notes: list[ScheduleNote]) -> dict[str, AiNoteResponse]:
        cache = self._repository.note_cache
        texts = sorted({note.text for note in notes})

        answers: dict[str, AiNoteResponse] = {}
        asked = 0
        for text in texts:
            key = self._cache_key(text)
            if key in cache:
                answers[text] = cache[key]
                continue

            answer = await self._ai_service.note_parsing(text)
            asked += 1
            if answer is None:
                continue
            cache[key] = answer
            answers[text] = answer

        if asked:
            self._repository.note_cache = cache
        logger.info(f"Notes: {len(texts)} unique, {asked} asked, {len(texts) - asked} from cache")
        return answers

    @staticmethod
    def _cache_key(text: str) -> str:
        raw = f"{CACHE_VERSION}|{env_config.SEMESTER_START_YEAR}|{text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _semester_bounds() -> tuple[date, date]:
        start_year = env_config.SEMESTER_START_YEAR
        return date(start_year, 9, 1), date(start_year + 1, 8, 31)

    @classmethod
    def _operation_dates(cls, operation: AiNoteOperation) -> list[date]:
        """Dates the model returned, minus anything outside the academic year."""
        start, end = cls._semester_bounds()
        dates = []
        for ai_date in operation.dates:
            value = ai_date.to_date()
            if value is None:
                continue
            if not (start <= value <= end):
                logger.warning(f"Discarding out-of-semester date {value} from an AI answer")
                continue
            dates.append(value)
        return sorted(set(dates))

    @classmethod
    def _materialize(
        cls,
        note: ScheduleNote,
        operation: AiNoteOperation,
        schedule: Schedule,
    ) -> list[DatedLesson]:
        dates = cls._operation_dates(operation)
        slot = {
            "number": note.number,
            "weekday": note.weekday,
            "week": note.week,
            "source_note": note.text,
        }
        action = operation.action
        if action == AiNoteAction.ONLY_ON and (operation.room or operation.lecturer or operation.name):
            action = AiNoteAction.OVERRIDE

        entries: list[DatedLesson] = []

        if action == AiNoteAction.CANCEL and dates:
            entries = [DatedLesson(action=DatedAction.CANCEL, dates=dates, **slot)]

        elif action == AiNoteAction.FROM_DATE and dates:
            entries = [DatedLesson(
                action=DatedAction.CANCEL,
                date_to=min(dates) - timedelta(days=1),
                **slot,
            )]

        elif action == AiNoteAction.UNTIL_DATE and dates:
            entries = [DatedLesson(
                action=DatedAction.CANCEL,
                date_from=max(dates) + timedelta(days=1),
                **slot,
            )]

        elif action == AiNoteAction.OVERRIDE:
            patch = LessonPatch(
                name=operation.name or None,
                room=operation.room or None,
                lecturer=operation.lecturer or None,
                note=operation.note or None,
            )
            if patch.model_dump(exclude_none=True):
                entries = [DatedLesson(action=DatedAction.OVERRIDE, dates=dates, patch=patch, **slot)]

        elif action == AiNoteAction.ONLY_ON and dates:
            lessons = schedule.get_lessons(
                course=note.course,
                group=note.group,
                week=note.week,
                weekday=note.weekday,
                number=note.number,
            )
            entries = [DatedLesson(action=DatedAction.CANCEL, **slot)]
            entries += [
                DatedLesson(action=DatedAction.ADD, dates=dates, lesson=lesson, **slot)
                for lesson in lessons
            ]

        return entries
