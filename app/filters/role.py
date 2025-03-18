from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.database import User
from app.database.enums import Role


class RoleFilter(BaseFilter):
    def __init__(self, role: Role):
        self.role = role

    async def __call__(self, message: Message,  **kwargs) -> bool:
        user: User | None = kwargs.get('user')
        if user is None:
            return False
        return user.role == self.role
