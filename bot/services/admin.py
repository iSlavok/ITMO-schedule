from bot.models import User
from bot.repositories import UserRepository


class AdminService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def get_users(self) -> list[User]:
        return await self._user_repo.get_all()
