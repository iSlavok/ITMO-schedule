from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Enum, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base
from bot.enums import UserRole

if TYPE_CHECKING:
    from . import Group, Rating, Log


class User(Base):
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", create_constraint=True, native_enum=False),
        nullable=False,
        default=UserRole.USER
    )
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)

    group: Mapped[Optional["Group"]] = relationship("Group", back_populates="users")
    ratings: Mapped[list["Rating"]] = relationship("Rating", back_populates="user")
    logs: Mapped[list["Log"]] = relationship("Log", back_populates="user")
