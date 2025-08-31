from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Group
from app.repositories import BaseRepository


class GroupRepository(BaseRepository[Group]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Group)

    async def get_by_course_id(self, course_id: int) -> Sequence[Group]:
        statement = (
            select(Group)
            .where(Group.course_id == course_id)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
