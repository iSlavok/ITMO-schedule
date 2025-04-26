from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel

if TYPE_CHECKING:
    from . import User


class Log(BaseModel):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="logs")
