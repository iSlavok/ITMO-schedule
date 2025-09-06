from datetime import UTC, date, datetime, time, timedelta

import pytz

from app.repositories import ScheduleRepository
from app.schedule import DateType, Lesson, Schedule, Week, Weekday

MSK_TZ = pytz.timezone("Europe/Moscow")
schedule_times = [
    (time(8, 10), time(9, 40)),
    (time(9, 50), time(11, 20)),
    (time(11, 30), time(13, 0)),
    (time(13, 30), time(15, 0)),
    (time(15, 30), time(17, 0)),
    (time(17, 10), time(18, 40)),
    (time(18, 50), time(20, 20)),
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
    def schedule(self, value: dict) -> None:
        self._schedule = Schedule.model_validate(value)
        self._schedule_repository.schedule = self._schedule

    def get_schedule(self, target_date: date, group: str) -> list[Lesson] | None:
        if self._schedule is None:
            return None
        try:
            weekday = self._get_weekday(target_date)
            _is_even_week = is_even_week(target_date)
            lessons = []
            for course in self._schedule.courses:
                if group in self._schedule.courses[course].groups:
                    group_schedule = self._schedule.courses[course].groups[group]
                    if _is_even_week and group_schedule.even_week:
                        lessons = group_schedule.even_week.days[weekday].lessons.copy()
                    elif not _is_even_week and group_schedule.odd_week:
                        lessons = group_schedule.odd_week.days[weekday].lessons.copy()
                    break
            lessons += self._get_dated_schedule(target_date, group, weekday, is_even_week_=_is_even_week)
            lessons.sort(key=lambda x: x.number)
        except KeyError:
            return []
        else:
            return lessons

    def get_last_lecturer(self, group: str) -> str | None:
        schedule = self.get_schedule(datetime.now(tz=MSK_TZ).date(), group)
        if not schedule:
            return None
        last_lesson_num = self.get_last_lesson_num()
        last_lesson = None
        for lesson in schedule:
            if lesson.number <= last_lesson_num:
                last_lesson = lesson
            else:
                break
        if last_lesson:
            return last_lesson.lecturer
        return None

    def _get_dated_schedule(self, target_date: date, group: str, weekday: Weekday, *,
                            is_even_week_: bool) -> list[Lesson]:
        lessons = []
        if group in self._dated_schedule.groups:
            lessons.extend(
                lesson.lesson
                for lesson in self._dated_schedule.groups[group]
                if lesson.date == target_date
                or (((lesson.date_type == DateType.AFTER and target_date < lesson.date)
                     or (lesson.date_type == DateType.BEFORE and target_date > lesson.date))
                    and (lesson.week == Week.ALL
                         or (lesson.week == Week.EVEN and is_even_week_)
                         or (lesson.week == Week.ODD and not is_even_week_))
                    and lesson.weekday == weekday)
            )

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
            "sunday",
        ]
        weekday = weekdays[target_date.weekday()]
        return Weekday(weekday)

    def get_current_lesson(self) -> tuple[int, bool]:
        msk_time = self._get_msk_time()
        current_time = msk_time.time()
        current = 0
        is_waiting = False
        for i, (_start, end) in enumerate(schedule_times):
            if current_time > end:
                current = i + 1
        if current < len(schedule_times) and current_time < schedule_times[current][0]:
            is_waiting = True
        return current + 1, is_waiting

    def get_last_lesson_num(self) -> int:
        msk_time = self._get_msk_time()
        current_time = msk_time.time()
        current = 0
        for i, (start, _end) in enumerate(schedule_times):
            if current_time > start:
                current = i + 1
        return current

    @staticmethod
    def _get_msk_time() -> datetime:
        utc_time = datetime.now(UTC)
        return utc_time + timedelta(hours=3)


def is_even_week(target_date: date) -> bool:
    return target_date.isocalendar()[1] % 2 == 1
