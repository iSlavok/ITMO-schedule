from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.enums import DatedAction, FacultyCode, Weekday
from app.repositories import ScheduleRepository
from app.schemas import DatedSchedule, Lesson, Schedule, ScheduleGroup
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
    """Holds one recurring schedule per faculty plus the shared dated overlay.

    Group names carry a faculty prefix and never collide, so a lookup without a
    faculty still resolves; passing one turns a faculty whose parse has not
    succeeded yet into an error instead of an empty day.
    """

    def __init__(self) -> None:
        self._schedule_repository = ScheduleRepository()
        self._schedules: dict[FacultyCode, Schedule] = {}
        self._dated_schedule = self._schedule_repository.dated_schedule

    def get_faculty_schedule(self, faculty: FacultyCode) -> Schedule | None:
        return self._schedules.get(faculty)

    def set_faculty_schedule(self, faculty: FacultyCode, schedule: Schedule) -> None:
        self._schedules[faculty] = schedule
        self._schedule_repository.set_schedule(faculty, schedule)

    @property
    def dated_schedule(self) -> DatedSchedule:
        return self._dated_schedule

    @dated_schedule.setter
    def dated_schedule(self, dated_schedule: DatedSchedule) -> None:
        self._dated_schedule = dated_schedule
        self._schedule_repository.dated_schedule = dated_schedule

    def get_schedule(
        self,
        group: str,
        target_date: date | None = None,
        faculty: FacultyCode | None = None,
    ) -> list[Lesson]:
        schedules = self._schedules_to_search(faculty)
        if not schedules:
            raise ScheduleNotLoadedError

        if target_date is None:
            target_date = datetime.now(tz=MSK_ZONE).date()

        weekday = self._get_weekday(target_date)
        is_even_week = self.is_even_week(target_date)

        lessons = []
        for schedule in schedules:
            group_schedule = self._find_group(schedule, group)
            if group_schedule is None:
                continue
            week = group_schedule.even_week if is_even_week else group_schedule.odd_week
            # deep copy: dated overrides patch lessons in place
            lessons = [lesson.model_copy(deep=True) for lesson in week.days[weekday].lessons]
            break

        lessons = self._apply_dated_schedule(lessons, target_date, group, weekday, is_even_week=is_even_week)
        return sorted(lessons, key=lambda x: x.number)

    def _apply_dated_schedule(
        self,
        lessons: list[Lesson],
        target_date: date,
        group: str,
        weekday: Weekday,
        *,
        is_even_week: bool,
    ) -> list[Lesson]:
        """Apply the dated entries of a group: cancellations, then overrides, then additions."""
        entries = [
            entry for entry in self._dated_schedule.groups.get(group, [])
            if entry.matches(target_date, weekday, is_even_week=is_even_week)
        ]
        if not entries:
            return lessons

        cancelled = {entry.number for entry in entries if entry.action == DatedAction.CANCEL}
        lessons = [lesson for lesson in lessons if lesson.number not in cancelled]

        for entry in entries:
            if entry.action != DatedAction.OVERRIDE:
                continue
            lessons = [
                entry.patch.apply_to(lesson) if lesson.number == entry.number else lesson
                for lesson in lessons
            ]

        lessons += [
            entry.lesson.model_copy(deep=True)
            for entry in entries
            if entry.action == DatedAction.ADD
        ]
        return lessons

    def _schedules_to_search(self, faculty: FacultyCode | None) -> list[Schedule]:
        if faculty is not None:
            schedule = self._schedules.get(faculty)
            return [schedule] if schedule is not None else []
        return list(self._schedules.values())

    @staticmethod
    def _find_group(schedule: Schedule, group: str) -> ScheduleGroup | None:
        for course in schedule.courses.values():
            if group in course.groups:
                return course.groups[group]
        return None

    def get_today_past_lecturers(self, group: str, faculty: FacultyCode | None = None) -> list[str]:
        try:
            schedule = self.get_schedule(group, faculty=faculty)
        except ScheduleNotLoadedError:
            return []

        if not schedule:
            return []

        last_lesson_num = self._get_last_lesson_num()
        lecturers = []

        for lesson in schedule:
            if lesson.number <= last_lesson_num and lesson.lecturer:
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
