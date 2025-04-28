from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Group
from bot.repositories import BaseRepository


class GroupRepository(BaseRepository[Group]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Group)

    async def get_by_course_id(self, course_id: int) -> Sequence[Group]:
        query = select(Group).where(Group.course_id == course_id)
        result = await self.session.execute(query)
        return result.scalars().all()
