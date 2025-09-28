from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.enums import DateType, Week, Weekday
from app.repositories import ScheduleRepository
from app.schemas import Lesson, Schedule
from app.services.exceptions import ScheduleNotLoadedError

MSK_ZONE = ZoneInfo("Europe/Moscow")
SCHEDULE_TIMES = [
    (time(8, 10), time(9, 40)),
    (time(9, 50), time(11, 20)),
    (time(11, 30), time(13, 0)),
    (time(13, 30), time(15, 0)),
    (time(15, 30), time(17, 0)),
    (time(17, 10), time(18, 40)),
    (time(18, 50), time(20, 20)),
]
WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class ScheduleService:
    def __init__(self) -> None:
        self._schedule_repository = ScheduleRepository()
        self._schedule: Schedule | None = None
        self._dated_schedule = self._schedule_repository.dated_schedule

    @property
    def schedule(self) -> Schedule:
        return self._schedule

    @schedule.setter
    def schedule(self, schedule: Schedule) -> None:
        self._schedule = schedule
        self._schedule_repository.schedule = schedule

    def get_schedule(self, target_date: date, group: str) -> list[Lesson]:
        if self._schedule is None:
            raise ScheduleNotLoadedError

        lessons = []
        for course in self._schedule.courses:
            if group in self._schedule.courses[course].groups:
                weekday = self._get_weekday(target_date)
                is_even_week = self.is_even_week(target_date)

                group_schedule = self._schedule.courses[course].groups[group]
                week = group_schedule.even_week if is_even_week else group_schedule.odd_week
                lessons = week.days[weekday].lessons.copy()
                break

        lessons += self._get_dated_schedule(target_date, group)
        return sorted(lessons, key=lambda x: x.number)

    def _get_dated_schedule(self, target_date: date, group: str) -> list[Lesson]:
        lessons = []

        if group in self._dated_schedule.groups:
            is_even_week = self.is_even_week(target_date)
            weekday = self._get_weekday(target_date)

            for lesson in self._dated_schedule.groups[group]:
                is_date_match = lesson.date == target_date
                is_relative_match = (
                    (lesson.date_type == DateType.AFTER and target_date > lesson.date)
                    or (lesson.date_type == DateType.BEFORE and target_date < lesson.date)
                )
                is_week_match = (
                    lesson.week == Week.ALL
                    or (lesson.week == Week.EVEN and is_even_week)
                    or (lesson.week == Week.ODD and not is_even_week)
                )
                is_weekday_match = lesson.weekday == weekday

                if is_date_match or (is_relative_match and is_week_match and is_weekday_match):
                    lessons.append(lesson.lesson)

        return lessons

    def get_today_past_lecturers(self, group: str) -> list[str]:
        try:
            # schedule = self.get_schedule(datetime.now(tz=MSK_ZONE).date(), group)
            # +1 day for testing purposes
            schedule = self.get_schedule((datetime.now(tz=MSK_ZONE) + timedelta(days=1)).date(), group)
        except ScheduleNotLoadedError:
            return []

        if not schedule:
            return []

        last_lesson_num = self._get_last_lesson_num()
        lecturers = []

        for lesson in schedule:
            if lesson.number < last_lesson_num and lesson.lecturer:
                lecturers.append(lesson.lecturer)
            elif lesson.number >= last_lesson_num:
                break

        return lecturers

    @staticmethod
    def get_current_lesson() -> tuple[int, bool]:
        msk_time = datetime.now(tz=MSK_ZONE).time()
        current = len(SCHEDULE_TIMES)
        is_waiting = False

        for i, (_start, end) in enumerate(SCHEDULE_TIMES, start=1):
            if msk_time < end:
                current = i
                break

        if current - 1 < len(SCHEDULE_TIMES) and msk_time < SCHEDULE_TIMES[current - 1][0]:
            is_waiting = True

        return current, is_waiting

    @staticmethod
    def _get_last_lesson_num() -> int:
        msk_time = datetime.now(tz=MSK_ZONE).time()
        current = 0

        for i, (start, _end) in enumerate(SCHEDULE_TIMES, start=1):
            if msk_time > start:
                current = i

        return current

    @staticmethod
    def _get_weekday(target_date: date) -> Weekday:
        weekday = WEEKDAYS[target_date.weekday()]
        return Weekday(weekday)

    @staticmethod
    def is_even_week(target_date: date) -> bool:
        return target_date.isocalendar()[1] % 2 == 1
