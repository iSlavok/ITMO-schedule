from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models import Course


class CourseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str) -> Course:
        course = Course(name=name)
        self.session.add(course)
        await self.session.commit()
        await self.session.refresh(course)
        return course

    async def get_by_name(self, name: str) -> Course | None:
        query = select(Course).where(Course.name == name)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_id(self, course_id: int) -> Course | None:
        query = select(Course).where(Course.id == course_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_with_groups(self, name: str) -> Course | None:
        query = select(Course).options(selectinload(Course.groups)).where(Course.name == name)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all(self) -> list[Course]:
        query = select(Course)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, course: Course) -> Course:
        await self.session.commit()
        await self.session.refresh(course)
        return course

    async def delete(self, course: Course) -> None:
        await self.session.delete(course)
        await self.session.commit()
