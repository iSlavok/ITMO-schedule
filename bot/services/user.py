from bot.enums import UserRole
from bot.models import User
from bot.repositories import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def create_user(self, user_id: int, username: str, name: str, role: UserRole, group_id: int = 0) -> User:
        user = await self.get_user(user_id)
        if not user:
            return await self._user_repo.create(user_id, username, name, role, group_id)
        return user

    async def register_user(self, user: User, group_id: int) -> User:
        user.group_id = group_id
        user.role = UserRole.USER
        return await self._user_repo.update(user)

    async def get_user(self, user_id):
        return await self._user_repo.get_with_group(user_id)
