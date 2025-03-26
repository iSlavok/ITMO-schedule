from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.database.base import BaseModel

if TYPE_CHECKING:
    from . import Lecturer, User


class Rating(BaseModel):
    rating: Mapped[int] = mapped_column(nullable=False)
    lecturer_id: Mapped[int] = mapped_column(ForeignKey("lecturers.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    lecturer: Mapped["Lecturer"] = relationship("Lecturer", back_populates="ratings")
    user: Mapped["User"] = relationship("User", back_populates="ratings")

    def __repr__(self) -> str:
        return f"<Rating {self.rating} for {self.lecturer_id} by {self.user_id}>"
