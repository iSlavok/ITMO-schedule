from enum import Enum


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
