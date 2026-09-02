import json
from pathlib import Path
from typing import TypeVar

from loguru import logger
from pydantic import BaseModel, ValidationError

from app.schemas import AiNoteResponse, DatedSchedule, Schedule

DATA_DIR = Path("data")
SCHEDULE_PATH = DATA_DIR / "schedule.json"
DATED_SCHEDULE_PATH = DATA_DIR / "dated_schedule.json"
DATED_OVERRIDES_PATH = DATA_DIR / "dated_overrides.json"
NOTE_CACHE_PATH = DATA_DIR / "ai_notes_cache.json"

ModelT = TypeVar("ModelT", bound=BaseModel)


class ScheduleRepository:
    @property
    def schedule(self) -> Schedule:
        return self._read(SCHEDULE_PATH, Schedule)

    @schedule.setter
    def schedule(self, schedule: Schedule) -> None:
        self._write(SCHEDULE_PATH, schedule)

    @property
    def dated_schedule(self) -> DatedSchedule:
        return self._read(DATED_SCHEDULE_PATH, DatedSchedule)

    @dated_schedule.setter
    def dated_schedule(self, schedule: DatedSchedule) -> None:
        self._write(DATED_SCHEDULE_PATH, schedule)

    @property
    def dated_overrides(self) -> DatedSchedule:
        """Hand-written entries applied on top of the generated dated schedule."""
        return self._read(DATED_OVERRIDES_PATH, DatedSchedule)

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
