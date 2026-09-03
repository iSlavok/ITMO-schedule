from enum import StrEnum


class FacultyCode(StrEnum):
    """Stable key of a faculty: names its schedule file, parser and group prefix."""

    PHYSICS = "physics"
    CT = "ct"
