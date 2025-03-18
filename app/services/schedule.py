from datetime import date

from app.repositories import ScheduleRepository
from app.schedule import Schedule, Week, Weekday, DateType, Lesson


class ScheduleService:
    def __init__(self):
        self._schedule_repository = ScheduleRepository()
        self._schedule: Schedule | None = None
        self._dated_schedule = self._schedule_repository.dated_schedule

    @property
    def schedule(self) -> Schedule:
        return self._schedule

    @schedule.setter
    def schedule(self, value: dict) -> None:
        self._schedule = Schedule.model_validate(value)
        self._schedule_repository.schedule = self._schedule

    def get_schedule(self, target_date: date, group: str, user: int) -> list[Lesson]:
        weekday = self._get_weekday(target_date)
        is_even_week = self.is_even_week(target_date)
        lessons = []
        for course in self._schedule.courses:
            if group in self._schedule.courses[course].groups:
                group_schedule = self._schedule.courses[course].groups[group]
                if is_even_week and group_schedule.even_week:
                    lessons = group_schedule.even_week.days[weekday].lessons
                elif not is_even_week and group_schedule.odd_week:
                    lessons = group_schedule.odd_week.days[weekday].lessons
        lessons += self._get_dated_schedule(target_date, group, weekday, is_even_week)
        lessons.sort(key=lambda x: x.number)
        return lessons

    def _get_dated_schedule(self, target_date: date, group: str, weekday: Weekday, is_even_week: bool) -> list[Lesson]:
        lessons = []
        if group in self._dated_schedule.groups:
            for lesson in self._dated_schedule.groups[group]:
                if lesson.date == target_date:
                    lessons.append(lesson.lesson)
                elif lesson.date_type == DateType.AFTER and target_date < lesson.date:
                    if lesson.week == Week.ALL or (lesson.week == Week.EVEN and is_even_week) or (lesson.week == Week.ODD and not is_even_week):
                        if lesson.weekday == weekday:
                            lessons.append(lesson.lesson)
                elif lesson.date_type == DateType.BEFORE and target_date > lesson.date:
                    if lesson.week == Week.ALL or (lesson.week == Week.EVEN and is_even_week) or (lesson.week == Week.ODD and not is_even_week):
                        if lesson.weekday == weekday:
                            lessons.append(lesson.lesson)
        return lessons

    @staticmethod
    def _get_weekday(target_date: date) -> Weekday:
        weekdays = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "saturday",
        ]
        weekday = weekdays[target_date.weekday()]
        return Weekday(weekday)

    @staticmethod
    def is_even_week(target_date: date) -> bool:
        return target_date.isocalendar()[1] % 2 == 1
