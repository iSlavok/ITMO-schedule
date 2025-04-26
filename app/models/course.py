from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel

if TYPE_CHECKING:
    from . import Group


class Course(BaseModel):
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    groups: Mapped[list["Group"]] = relationship("Group", back_populates="course")
