from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel

if TYPE_CHECKING:
    from . import Course, User


class Group(BaseModel):
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))

    course: Mapped["Course"] = relationship("Course", back_populates="groups")
    users: Mapped[list["User"]] = relationship("User", back_populates="group")
