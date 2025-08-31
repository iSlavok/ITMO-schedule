from datetime import date

from pydantic import BaseModel, Field, computed_field


class AiDateResponse(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)

    @computed_field
    @property
    def date(self) -> date:
        return date(year=self.year, month=self.month, day=self.day)
