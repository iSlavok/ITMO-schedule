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
    days: dict[Weekday, ScheduleDay] = Field(default_factory=dict)


class ScheduleGroup(BaseModel):
    odd_week: ScheduleWeek | None = None
    even_week: ScheduleWeek | None = None


class ScheduleCourse(BaseModel):
    groups: dict[str, ScheduleGroup] = Field(default_factory=dict)


class Schedule(BaseModel):
    courses: dict[str, ScheduleCourse] = Field(default_factory=dict)


class DatedLesson(BaseModel):
    date: date
    date_type: DateType
    week: Week | None = None
    weekday: Weekday | None = None
    lesson: Lesson

    @model_validator(mode="after")
    def validate(self) -> "DatedLesson":
        if self.date_type != DateType.EXACT:
            if self.week is None or self.weekday is None:
                raise ValueError("week and weekday must be set if date_type is not exact")
        return self


class DatedSchedule(BaseModel):
    groups: dict[str, list[DatedLesson]] = Field(default_factory=dict)
