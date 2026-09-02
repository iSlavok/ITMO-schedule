from collections import defaultdict
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.enums import DatedAction, Week, Weekday

LessonType = Literal["лекция", "практика", "теория", "лабораторная", "факультатив"]


class Lesson(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    name: str | None = None
    room: str | None = None
    lecturer: str | None = None
    type: LessonType | None = None
    number: int
    subgroup: str | None = None
    note: str | None = None


class LessonPatch(BaseModel):
    """Partial lesson used by a dated override: only the set fields are applied."""

    name: str | None = None
    room: str | None = None
    lecturer: str | None = None
    type: LessonType | None = None
    note: str | None = None

    def apply_to(self, lesson: Lesson) -> Lesson:
        changes = self.model_dump(exclude_none=True)
        return lesson.model_copy(update=changes) if changes else lesson


class ScheduleDay(BaseModel):
    lessons: list[Lesson] = Field(default_factory=list)


class ScheduleWeek(BaseModel):
    days: dict[Weekday, ScheduleDay] = Field(
        default_factory=lambda: defaultdict(ScheduleDay),
    )


class ScheduleGroup(BaseModel):
    odd_week: ScheduleWeek = Field(default_factory=ScheduleWeek)
    even_week: ScheduleWeek = Field(default_factory=ScheduleWeek)


class ScheduleCourse(BaseModel):
    groups: dict[str, ScheduleGroup] = Field(
        default_factory=lambda: defaultdict(ScheduleGroup),
    )


class Schedule(BaseModel):
    courses: dict[str, ScheduleCourse] = Field(
        default_factory=lambda: defaultdict(ScheduleCourse),
    )

    def add_lesson(
        self,
        course: str,
        group: str,
        week_type: Literal["odd_week", "even_week"],
        weekday: Weekday,
        lesson: Lesson,
    ) -> None:
        target_week = (
            self.courses[course].groups[group].odd_week
            if week_type == "odd_week"
            else self.courses[course].groups[group].even_week
        )
        target_week.days[weekday].lessons.append(lesson)

    def get_lessons(self, course: str, group: str, week: Week, weekday: Weekday, number: int) -> list[Lesson]:
        schedule_course = self.courses.get(course)
        if schedule_course is None or group not in schedule_course.groups:
            return []

        schedule_group = schedule_course.groups[group]
        target_week = schedule_group.even_week if week == Week.EVEN else schedule_group.odd_week
        day = target_week.days.get(weekday)
        if day is None:
            return []

        return [lesson for lesson in day.lessons if lesson.number == number]


class ScheduleNote(BaseModel):
    """A footnote found next to a lesson, waiting to be turned into dated entries.

    `text` is the raw sheet text: it is the cache key of the AI answer, so it must
    not go through any normalization.
    """

    course: str
    group: str
    week: Week
    weekday: Weekday
    number: int
    text: str


class ParseResult(BaseModel):
    schedule: Schedule = Field(default_factory=Schedule)
    notes: list[ScheduleNote] = Field(default_factory=list)


class DatedLesson(BaseModel):
    """One change applied on top of the recurring schedule of a single slot.

    Slot is (weekday, week, number). Matching: a non-empty `dates` wins outright
    and ignores weekday/week; otherwise the entry matches every occurrence of the
    slot inside the [date_from, date_to] window.
    """

    action: DatedAction
    number: int
    weekday: Weekday
    week: Week = Week.ALL
    dates: list[date] = Field(default_factory=list)
    date_from: date | None = None
    date_to: date | None = None
    lesson: Lesson | None = None
    patch: LessonPatch | None = None
    source_note: str | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "DatedLesson":
        if self.action == DatedAction.ADD and self.lesson is None:
            msg = "lesson must be set for an add entry"
            raise ValueError(msg)
        if self.action == DatedAction.OVERRIDE and self.patch is None:
            msg = "patch must be set for an override entry"
            raise ValueError(msg)
        return self

    def matches(self, target_date: date, weekday: Weekday, *, is_even_week: bool) -> bool:
        if self.dates:
            return target_date in self.dates

        if self.weekday != weekday:
            return False
        if self.week not in (Week.ALL, Week.EVEN if is_even_week else Week.ODD):
            return False
        if self.date_from is not None and target_date < self.date_from:
            return False
        return not (self.date_to is not None and target_date > self.date_to)


class DatedSchedule(BaseModel):
    groups: dict[str, list[DatedLesson]] = Field(default_factory=dict)

    def add(self, group: str, entry: DatedLesson) -> None:
        self.groups.setdefault(group, []).append(entry)

    def merge(self, other: "DatedSchedule") -> "DatedSchedule":
        merged = self.model_copy(deep=True)
        for group, entries in other.groups.items():
            merged.groups.setdefault(group, []).extend(entry.model_copy(deep=True) for entry in entries)
        return merged
