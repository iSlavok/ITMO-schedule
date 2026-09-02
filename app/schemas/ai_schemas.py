from datetime import date

from pydantic import BaseModel, Field, computed_field

from app.enums import AiNoteAction


class AiDateResponse(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)

    @computed_field
    @property
    def date(self) -> date:
        return date(year=self.year, month=self.month, day=self.day)


class AiDate(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)

    def to_date(self) -> date | None:
        try:
            return date(year=self.year, month=self.month, day=self.day)
        except ValueError:
            return None


class AiNoteOperation(BaseModel):
    """One instruction extracted from a footnote next to a lesson.

    Text fields are plain strings rather than optionals on purpose: Gemini's
    structured output is unreliable with nullable unions, so "not set" is "".
    """

    action: AiNoteAction
    dates: list[AiDate] = Field(default_factory=list)
    room: str = ""
    lecturer: str = ""
    name: str = ""
    note: str = ""


class AiNoteResponse(BaseModel):
    understood: bool
    operations: list[AiNoteOperation] = Field(default_factory=list)
