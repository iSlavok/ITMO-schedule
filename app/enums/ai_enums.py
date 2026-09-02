from enum import Enum


class AiNoteAction(str, Enum):
    """How a footnote changes the recurring schedule of its lesson."""

    CANCEL = "cancel"
    ONLY_ON = "only_on"
    FROM_DATE = "from_date"
    UNTIL_DATE = "until_date"
    OVERRIDE = "override"
