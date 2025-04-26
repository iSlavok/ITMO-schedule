from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.enums import UserRole
from bot.models import User


class RoleFilter(BaseFilter):
    def __init__(self, role: UserRole):
        self.role = role

    async def __call__(self, message: Message, user: User) -> bool:
        return user.role == self.role
