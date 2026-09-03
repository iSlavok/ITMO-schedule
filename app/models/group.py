from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from . import Course, Faculty, User


class Group(Base):
    __table_args__ = (UniqueConstraint("name", "faculty_id", name="uq_group_name_faculty"),)

    name: Mapped[str] = mapped_column(index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"), index=True)
    # false once the group leaves the sheet: it keeps its users but is no longer offered
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    course: Mapped["Course"] = relationship("Course", back_populates="groups")
    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="groups")
    users: Mapped[list["User"]] = relationship("User", back_populates="group")
