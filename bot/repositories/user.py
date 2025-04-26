from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.enums import UserRole
from bot.models import User, Group


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, username: str = None, name: str = None, role: UserRole = UserRole.USER,
                     group_id: int = None) -> User:
        user = User(user_id=user_id, username=username, name=name,
                    role=role, group_id=group_id)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_user_id(self, user_id: int) -> User | None:
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_with_group(self, user_id: int) -> User | None:
        query = select(User).options(selectinload(User.group)).where(User.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all(self) -> list[User]:
        query = select(User).options(selectinload(User.group))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_group(self, group_name: str) -> list[User]:
        query = select(User).join(User.group).where(Group.name == group_name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_role(self, role: UserRole) -> list[User]:
        query = select(User).where(User.role == role)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, user: User) -> User:
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()
