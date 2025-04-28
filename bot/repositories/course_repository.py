from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models import Course
from bot.repositories import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Course)

    async def get_with_groups(self, name: str) -> Course | None:
        query = select(Course).options(selectinload(Course.groups)).where(Course.name == name)
        result = await self.session.execute(query)
        return result.scalars().first()
