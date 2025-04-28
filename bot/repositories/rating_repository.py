from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Rating, User
from bot.repositories import BaseRepository


class RatingRepository(BaseRepository[Rating]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Rating)

    async def can_user_rate_lecturer(self, user: User, lecturer_id: int) -> bool:
        today = date.today()
        query = select(Rating).where(
            Rating.user == user,
            Rating.lecturer_id == lecturer_id,
            today == func.date(Rating.created_at)
        )
        result = await self.session.execute(query)
        return result.first() is None
