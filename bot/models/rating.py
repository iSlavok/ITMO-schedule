from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base

if TYPE_CHECKING:
    from . import Lecturer, User


class Rating(Base):
    rating: Mapped[int] = mapped_column(nullable=False)
    lecturer_id: Mapped[int] = mapped_column(ForeignKey("lecturers.id"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))

    lecturer: Mapped["Lecturer"] = relationship("Lecturer", back_populates="ratings")
    user: Mapped["User"] = relationship("User", back_populates="ratings")
