from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories import UserRepository
from app.schemas import UserDTO, UserWithGroupDTO


class UserService:
    def __init__(self, session: AsyncSession, user_repo: UserRepository) -> None:
        self._session = session
        self._user_repo = user_repo

    async def get_or_create(self, telegram_id: int, username: str | None, full_name: str) -> User:
        user = await self._user_repo.get_by_telegram_id_with_group_and_course(telegram_id=telegram_id)
        if not user:
            user = User(
                telegram_id=telegram_id,
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

    async def get_users_with_group_and_course(self, page: int, per_page: int) -> list[UserWithGroupDTO]:
        skip = (page - 1) * per_page
        users = await self._user_repo.list_all_with_group_and_course(skip=skip, limit=per_page)
        return [
            UserWithGroupDTO.model_validate(user)
            for user in users
        ]

    async def get_users_count(self) -> int:
        return await self._user_repo.get_users_count()

    async def get_users_with_rating_notifications_by_group(self) -> dict[str, list[UserDTO]]:
        rows = await self._user_repo.get_users_with_rating_notifications_with_groups()
        grouped: dict[str, list[UserDTO]] = defaultdict(list)

        for group_name, user in rows:
            grouped[group_name].append(UserDTO.model_validate(user))

        return dict(grouped)

    async def change_settings(
        self,
        user: User,
        rating_notifications: bool | None = None,
    ) -> User:
        has_changes = False

        if rating_notifications is not None:
            user.rating_notifications = rating_notifications
            has_changes = True

        if has_changes:
            await self._session.commit()
            await self._session.refresh(user)
        return user
