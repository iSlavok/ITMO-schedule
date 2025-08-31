from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.models import User
from app.repositories import UserRepository


class UserService:
    def __init__(self, session: AsyncSession, user_repo: UserRepository):
        self._session = session
        self._user_repo = user_repo

    async def get_or_create(self, user_id: int, username: str | None, full_name: str) -> User:
        user = await self._user_repo.get_by_user_id_with_group_and_course(user_id)
        if not user:
            user = User(
                user_id=user_id,
                username=username,
                name=full_name,
            )
            self._user_repo.add(user)
            await self._session.commit()
            await self._session.refresh(user)
        elif user.username != username or user.name != full_name:
            if user.username != username:
                user.username = username
            if user.name != full_name:
                user.name = full_name
            await self._session.commit()
            await self._session.refresh(user)
        return user

    async def register_user(self, user: User, group_id: int) -> User:
        user.group_id = group_id
        user.role = UserRole.USER
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def get_users_with_group_and_course(self, page: int = 1, per_page: int = 10) -> Sequence[User]:
        if page < 1:
            page = 1
        skip = (page - 1) * per_page
        users = await self._user_repo.list_all_with_group_and_course(skip=skip, limit=per_page)
        return users

    async def get_users_count(self) -> int:
        return await self._user_repo.get_users_count()
