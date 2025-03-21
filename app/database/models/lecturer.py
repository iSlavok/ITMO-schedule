from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import BaseModel

if TYPE_CHECKING:
    from . import Rating


class Lecturer(BaseModel):
    name: Mapped[str] = mapped_column()

    ratings: Mapped[list["Rating"]] = relationship("Rating", back_populates="lecturer")

    def __repr__(self) -> str:
        return f"<Lecturer {self.name}>"
