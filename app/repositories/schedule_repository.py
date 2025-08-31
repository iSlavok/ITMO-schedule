import json
from pathlib import Path

from app.schedule import DatedSchedule, Schedule


class ScheduleRepository:
    @property
    def schedule(self) -> Schedule:
        path = Path("data/schedule.json")
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
            return Schedule.model_validate(data)

    @schedule.setter
    def schedule(self, schedule: Schedule) -> None:
        path = Path("data/schedule.json")
        with path.open("w", encoding="utf-8") as file:
            json.dump(schedule.model_dump(), file, ensure_ascii=False, indent=2)

    @property
    def dated_schedule(self) -> DatedSchedule:
        path = Path("data/dated_schedule.json")
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
            return DatedSchedule.model_validate(data)

    @dated_schedule.setter
    def dated_schedule(self, schedule: DatedSchedule) -> None:
        path = Path("data/dated_schedule.json")
        with path.open("w", encoding="utf-8") as file:
            json.dump(schedule.model_dump(), file, ensure_ascii=False, indent=2)
