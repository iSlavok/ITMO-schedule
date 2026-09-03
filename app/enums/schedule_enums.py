from enum import StrEnum


class Weekday(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class Week(StrEnum):
    ODD = "odd_week"
    EVEN = "even_week"
    ALL = "all_weeks"


class DatedAction(StrEnum):
    """What a dated entry does to the recurring schedule of its slot."""

    ADD = "add"
    CANCEL = "cancel"
    OVERRIDE = "override"
