from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models import Group, Course


class GroupRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, course_id: int) -> Group:
        group = Group(name=name, course_id=course_id)
        self.session.add(group)
        await self.session.commit()
        await self.session.refresh(group)
        return group

    async def get_by_name(self, name: str) -> Group | None:
        query = select(Group).where(Group.name == name)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_id(self, group_id):
        query = select(Group).where(Group.id == group_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_with_users(self, name: str) -> Group | None:
        query = select(Group).options(selectinload(Group.users)).where(Group.name == name)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_with_course(self, name: str) -> Group | None:
        query = select(Group).options(selectinload(Group.course)).where(Group.name == name)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all(self) -> list[Group]:
        query = select(Group)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_course_name(self, course_name: str) -> list[Group]:
        query = select(Group).join(Group.course).where(Course.name == course_name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_course_id(self, course_id: int) -> list[Group]:
        query = select(Group).where(Group.course_id == course_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, group: Group) -> Group:
        await self.session.commit()
        await self.session.refresh(group)
        return group

    async def delete(self, group: Group) -> None:
        await self.session.delete(group)
        await self.session.commit()
