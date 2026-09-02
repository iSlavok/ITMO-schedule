from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from . import Faculty, Rating


class Lecturer(Base):
    __table_args__ = (UniqueConstraint("name", "faculty_id", name="uq_lecturer_name_faculty"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"), index=True)

    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="lecturers")
    ratings: Mapped[list["Rating"]] = relationship("Rating", back_populates="lecturer")
