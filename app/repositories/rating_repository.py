from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Rating
from app.repositories import BaseRepository


class RatingRepository(BaseRepository[Rating]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Rating)

    async def can_user_rate_lecturer(self, user_id: int, lecturer_id: int) -> bool:
        query = (
            select(Rating)
            .where(
                Rating.user_id == user_id,
                Rating.lecturer_id == lecturer_id,
                date.today() == func.date(Rating.created_at)
            )
        )
        result = await self.session.execute(query)
        return result.first() is None
