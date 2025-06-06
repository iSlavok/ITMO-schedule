import json

from bot.schedule import DatedSchedule, Schedule


class ScheduleRepository:
    @property
    def schedule(self) -> Schedule:
        with open("data/schedule.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return Schedule.model_validate(data)

    @schedule.setter
    def schedule(self, schedule: Schedule):
        with open("data/schedule.json", "w", encoding="utf-8") as file:
            json.dump(schedule.model_dump(), file, ensure_ascii=False, indent=2)

    @property
    def dated_schedule(self) -> DatedSchedule:
        with open("data/dated_schedule.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return DatedSchedule.model_validate(data)

    @dated_schedule.setter
    def dated_schedule(self, schedule: DatedSchedule):
        with open("data/dated_schedule.json", "w", encoding="utf-8") as file:
            json.dump(schedule.model_dump(), file, ensure_ascii=False, indent=2)
