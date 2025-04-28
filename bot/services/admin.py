from typing import Sequence

from bot.models import User
from bot.repositories import UserRepository


class AdminService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def get_users(self) -> Sequence[User]:  # TODO: add pagination
        return await self._user_repo.list_all()
