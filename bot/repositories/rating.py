from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Rating


class RatingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, rating: int, lecturer_id: int, user_id: int):
        rating = Rating(rating=rating, lecturer_id=lecturer_id, user_id=user_id)
        self.session.add(rating)
        await self.session.commit()
        return rating

    async def can_user_rate_lecturer(self, user_id: int, lecturer_id: int) -> bool:
        today = date.today()
        query = select(Rating).where(
            Rating.user_id == user_id,
            Rating.lecturer_id == lecturer_id,
            today == func.date(Rating.created_at)
        )
        result = (await self.session.execute(query)).first()
        return result is None
