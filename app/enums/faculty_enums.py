from enum import Enum


class FacultyCode(str, Enum):
    """Stable key of a faculty: names its schedule file, parser and group prefix."""

    PHYSICS = "physics"
    CT = "ct"
