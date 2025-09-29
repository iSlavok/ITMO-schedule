from collections.abc import Sequence

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Group, User
from app.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_telegram_id_with_group_and_course(self, telegram_id: int) -> User | None:
        statement = (
            select(User)
            .where(User.telegram_id == telegram_id)
            .options(
                joinedload(User.group).options(
                    joinedload(Group.course),
                ),
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
                    joinedload(Group.course),
                ),
            )
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_users_count(self) -> int:
        statement = (
            select(
                func.count(self.model.id),
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def get_users_with_groups(self) -> Sequence[Row[tuple[str, User]]]:
        statement = (
            select(Group.name, User)
            .join(User.group)
            .where(
                User.group_id.isnot(None),
            )
        )
        result = await self.session.execute(statement)
        return result.all()
