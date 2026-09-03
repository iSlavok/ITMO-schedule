from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import FacultyCode

if TYPE_CHECKING:
    from . import Group, Lecturer


class Faculty(Base):
    code: Mapped[FacultyCode] = mapped_column(
        Enum(FacultyCode, name="faculty_code_enum", create_constraint=True, native_enum=False),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    groups: Mapped[list["Group"]] = relationship("Group", back_populates="faculty")
    lecturers: Mapped[list["Lecturer"]] = relationship("Lecturer", back_populates="faculty")
