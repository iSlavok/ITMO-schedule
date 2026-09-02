from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from . import Group, Lecturer


class Faculty(Base):
    __tablename__ = "faculties"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    groups: Mapped[list["Group"]] = relationship("Group", back_populates="faculty")
    lecturers: Mapped[list["Lecturer"]] = relationship("Lecturer", back_populates="faculty")
