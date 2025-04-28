from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models import User
from bot.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_user_id_with_group(self, user_id: int) -> User | None:
        query = select(User).options(selectinload(User.group)).where(User.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().first()
