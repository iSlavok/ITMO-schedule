from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from bot.models import User, Group
from bot.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_user_id_with_group(self, user_id: int) -> User | None:
        statement = (
            select(User)
            .options(selectinload(User.group))
            .where(User.user_id == user_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_user_id_with_group_and_course(self, user_id: int) -> User | None:
        statement = (
            select(User)
            .where(User.user_id == user_id)
            .options(
                joinedload(User.group).options(
                    joinedload(Group.course)
                )
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_all_with_group_and_course(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        statement = (
            select(self.model)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at)
            .options(
                joinedload(User.group).options(
                    joinedload(Group.course)
                )
            )
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_users_count(self) -> int:
        statement = (
            select(func.count(self.model.id))
        )
        return await self.session.scalar(statement) or 0
