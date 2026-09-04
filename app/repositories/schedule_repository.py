import json
from pathlib import Path
from typing import TypeVar

from loguru import logger
from pydantic import BaseModel, ValidationError

from app.enums import FacultyCode
from app.schemas import AiNoteResponse, DatedSchedule, Schedule

DATA_DIR = Path("data")
SCHEDULE_PATHS = {
    FacultyCode.PHYSICS: DATA_DIR / "schedule.json",
    FacultyCode.CT: DATA_DIR / "schedule_ct.json",
}
DATED_SCHEDULE_PATHS = {
    FacultyCode.PHYSICS: DATA_DIR / "dated_schedule.json",
    FacultyCode.CT: DATA_DIR / "dated_schedule_ct.json",
}
DATED_OVERRIDES_PATHS = {
    FacultyCode.PHYSICS: DATA_DIR / "dated_overrides.json",
    FacultyCode.CT: DATA_DIR / "dated_overrides_ct.json",
}
NOTE_CACHE_PATH = DATA_DIR / "ai_notes_cache.json"

ModelT = TypeVar("ModelT", bound=BaseModel)


class ScheduleRepository:
    def get_schedule(self, faculty: FacultyCode) -> Schedule:
        return self._read(SCHEDULE_PATHS[faculty], Schedule)

    def set_schedule(self, faculty: FacultyCode, schedule: Schedule) -> None:
        self._write(SCHEDULE_PATHS[faculty], schedule)

    def get_dated_schedule(self, faculty: FacultyCode) -> DatedSchedule:
        return self._read(DATED_SCHEDULE_PATHS[faculty], DatedSchedule)

    def set_dated_schedule(self, faculty: FacultyCode, schedule: DatedSchedule) -> None:
        self._write(DATED_SCHEDULE_PATHS[faculty], schedule)

    def get_dated_overrides(self, faculty: FacultyCode) -> DatedSchedule:
        """Hand-written entries applied on top of the generated dated schedule."""
        return self._read(DATED_OVERRIDES_PATHS[faculty], DatedSchedule)

    @property
    def note_cache(self) -> dict[str, AiNoteResponse]:
        raw = self._read_json(NOTE_CACHE_PATH)
        cache = {}
        for key, value in raw.items():
            try:
                cache[key] = AiNoteResponse.model_validate(value)
            except ValidationError:
                logger.warning(f"Dropping unreadable note cache entry {key}")
        return cache

    @note_cache.setter
    def note_cache(self, cache: dict[str, AiNoteResponse]) -> None:
        payload = {key: value.model_dump() for key, value in cache.items()}
        self._write_json(NOTE_CACHE_PATH, payload)

    @staticmethod
    def _read_json(path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            with path.open(encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to read {path}: {e}")
            return {}

    @staticmethod
    def _write_json(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2, default=str)

    @classmethod
    def _read(cls, path: Path, model: type[ModelT]) -> ModelT:
        """Read a model, falling back to an empty one: a missing or broken file
        must not take the bot down on startup.
        """
        data = cls._read_json(path)
        if not data:
            return model()
        try:
            return model.model_validate(data)
        except ValidationError as e:
            logger.warning(f"Failed to validate {path}, using an empty one: {e}")
            return model()

    @classmethod
    def _write(cls, path: Path, model: BaseModel) -> None:
        cls._write_json(path, model.model_dump())
