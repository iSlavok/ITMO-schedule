import json

from app.schedule import DatedSchedule, Schedule, UsersSchedule


class ScheduleRepository:
    @property
    def schedule(self) -> Schedule:
        with open("app/schedule/schedule.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return Schedule.model_validate(data)

    @schedule.setter
    def schedule(self, schedule: Schedule):
        with open("app/schedule/schedule.json", "w", encoding="utf-8") as file:
            json.dump(schedule.model_dump(), file, ensure_ascii=False, indent=4)

    @property
    def dated_schedule(self) -> DatedSchedule:
        with open("app/schedule/dated_schedule.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return DatedSchedule.model_validate(data)

    @dated_schedule.setter
    def dated_schedule(self, schedule: DatedSchedule):
        with open("app/schedule/dated_schedule.json", "w", encoding="utf-8") as file:
            json.dump(schedule.model_dump(), file, ensure_ascii=False, indent=4)

    @property
    def user_schedule(self) -> UsersSchedule:
        with open("app/schedule/user_schedule.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return UsersSchedule.model_validate(data)

    @user_schedule.setter
    def user_schedule(self, schedule: UsersSchedule):
        with open("app/schedule/user_schedule.json", "w", encoding="utf-8") as file:
            json.dump(schedule.model_dump(), file, ensure_ascii=False, indent=4)


# rep = ScheduleRepository()
# sc = rep.user_schedule
# sc.users[313].lessons.append(UserLesson(
#     lesson=Lesson(
#         name="Тест",
#         room=52,
#         number=1
#     ),
#     week=Week.ALL,
#     weekday=Weekday.MONDAY
# ))
# with open("../schedule/user_schedule.json", "w", encoding="utf-8") as file:
#     json.dump(sc.model_dump(), file, ensure_ascii=False, indent=4)
# print(sc)
