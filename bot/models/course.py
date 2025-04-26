from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base

if TYPE_CHECKING:
    from . import Group


class Course(Base):
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    groups: Mapped[list["Group"]] = relationship("Group", back_populates="course")
