from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from . import Rating


class Lecturer(Base):
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    ratings: Mapped[list["Rating"]] = relationship("Rating", back_populates="lecturer")
