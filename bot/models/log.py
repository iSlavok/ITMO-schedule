from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base

if TYPE_CHECKING:
    from . import User


class Log(Base):
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    action: Mapped[str] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="logs")
