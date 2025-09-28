from collections import defaultdict
from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Weekday(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class Week(str, Enum):
    ODD = "odd_week"
    EVEN = "even_week"
    ALL = "all_weeks"


class DateType(str, Enum):
    EXACT = "exact"
    AFTER = "after"
    BEFORE = "before"


class Lesson(BaseModel):
    name: str | None = None
    room: int | None = None
    lecturer: str | None = None
    type: Literal["лекция", "практика", "теория", "лабораторная", "факультатив"] | None = None
    number: int


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


class DatedLesson(BaseModel):
    date: date
    date_type: DateType
    week: Week | None = None
    weekday: Weekday | None = None
    lesson: Lesson

    @model_validator(mode="after")
    def validate(self) -> "DatedLesson":
        if self.date_type != DateType.EXACT and (self.week is None or self.weekday is None):
            msg = "week and weekday must be set if date_type is not exact"
            raise ValueError(msg)
        return self


class DatedSchedule(BaseModel):
    groups: dict[str, list[DatedLesson]] = Field(default_factory=dict)
