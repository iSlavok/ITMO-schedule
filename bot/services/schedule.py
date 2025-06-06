from datetime import datetime, timedelta, date, UTC

from bot.repositories import ScheduleRepository
from bot.schedule import Schedule, Week, Weekday, DateType, Lesson


class ScheduleService:
    schedule_times = [
        (datetime.strptime("8:10", "%H:%M").time(), datetime.strptime("9:40", "%H:%M").time()),
        (datetime.strptime("9:50", "%H:%M").time(), datetime.strptime("11:20", "%H:%M").time()),
        (datetime.strptime("11:30", "%H:%M").time(), datetime.strptime("13:00", "%H:%M").time()),
        (datetime.strptime("13:30", "%H:%M").time(), datetime.strptime("15:00", "%H:%M").time()),
        (datetime.strptime("15:30", "%H:%M").time(), datetime.strptime("17:00", "%H:%M").time()),
        (datetime.strptime("17:10", "%H:%M").time(), datetime.strptime("18:40", "%H:%M").time()),
        (datetime.strptime("18:40", "%H:%M").time(), datetime.strptime("20:10", "%H:%M").time()),
    ]

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
            lessons += self._get_dated_schedule(target_date, group, weekday, _is_even_week)
            lessons.sort(key=lambda x: x.number)
            return lessons
        except KeyError:
            return []

    def get_last_lecturer(self, group: str) -> str | None:
        schedule = self.get_schedule(date.today(), group)
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

    def _get_dated_schedule(self, target_date: date, group: str, weekday: Weekday, is_even_week: bool) -> list[Lesson]:
        lessons = []
        if group in self._dated_schedule.groups:
            for lesson in self._dated_schedule.groups[group]:
                if lesson.date == target_date:
                    lessons.append(lesson.lesson)
                elif lesson.date_type == DateType.AFTER and target_date < lesson.date:
                    if lesson.week == Week.ALL or (lesson.week == Week.EVEN and is_even_week) or (
                            lesson.week == Week.ODD and not is_even_week):
                        if lesson.weekday == weekday:
                            lessons.append(lesson.lesson)
                elif lesson.date_type == DateType.BEFORE and target_date > lesson.date:
                    if lesson.week == Week.ALL or (lesson.week == Week.EVEN and is_even_week) or (
                            lesson.week == Week.ODD and not is_even_week):
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
            "sunday",
        ]
        weekday = weekdays[target_date.weekday()]
        return Weekday(weekday)

    def get_current_lesson(self) -> tuple[int, bool]:
        msk_time = self._get_msk_time()
        current_time = msk_time.time()
        current = 0
        is_waiting = False
        for i, (start, end) in enumerate(self.schedule_times):
            if current_time > end:
                current = i + 1
        if current < len(self.schedule_times) and current_time < self.schedule_times[current][0]:
            is_waiting = True
        return current + 1, is_waiting

    def get_last_lesson_num(self) -> int:
        msk_time = self._get_msk_time()
        current_time = msk_time.time()
        current = 0
        for i, (start, end) in enumerate(self.schedule_times):
            if current_time > start:
                current = i + 1
        return current

    @staticmethod
    def _get_msk_time():
        utc_time = datetime.now(UTC)
        msk_time = utc_time + timedelta(hours=3)
        return msk_time


def is_even_week(target_date: date) -> bool:
    return target_date.isocalendar()[1] % 2 == 1
