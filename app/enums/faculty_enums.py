from enum import StrEnum


class FacultyCode(StrEnum):
    """Stable key of a faculty: names its schedule file, parser and group prefix."""

    PHYSICS = "physics"
    CT = "ct"

    @property
    def group_prefix(self) -> str:
        """The letter in front of a group number of this faculty.

        Group numbers repeat across faculties, so the letter is what keeps names
        apart wherever they are compared without a faculty beside them.
        """
        return _GROUP_PREFIXES[self]


_GROUP_PREFIXES = {
    FacultyCode.PHYSICS: "Z",
    FacultyCode.CT: "M",
}
