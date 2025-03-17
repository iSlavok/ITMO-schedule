from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import BaseModel
from typing import TYPE_CHECKING

from ..enums import Role

if TYPE_CHECKING:
    from . import Group


class User(BaseModel):
    user_id: Mapped[int] = mapped_column(unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column()
    name: Mapped[str | None] = mapped_column()
    role: Mapped[Role] = mapped_column(default=Role.USER)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    group: Mapped["Group"] = relationship("Group", back_populates="users")

    def __repr__(self) -> str:
        return f"<User {self.username}, {self.name}, {self.user_id}, from {repr(self.group)}>"
