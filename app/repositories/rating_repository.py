from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lecturer, Rating
from app.repositories import BaseRepository

MSK_ZONE = ZoneInfo("Europe/Moscow")


class RatingRepository(BaseRepository[Rating]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Rating)

    async def can_user_rate_lecturer(self, user_id: int, lecturer_id: int) -> bool:
        query = (
            select(Rating)
            .where(
                Rating.user_id == user_id,
                Rating.lecturer_id == lecturer_id,
                datetime.now(tz=MSK_ZONE).date() == func.date(Rating.created_at),
            )
        )
        result = await self.session.execute(query)
        return result.first() is None

    async def get_rateable_lecturers(self, lecturer_names: list[str], user_id: int) -> Sequence[Lecturer]:
        today = datetime.now(tz=MSK_ZONE).date()

        subquery = (
            select(Rating.lecturer_id)
            .where(
                Rating.user_id == user_id,
                today == func.date(Rating.created_at),
            )
            .scalar_subquery()
        )

        statement = (
            select(Lecturer)
            .where(
                Lecturer.name.in_(lecturer_names),
                ~Lecturer.id.in_(subquery),
            )
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_all_today(self) -> Sequence[Rating]:
        today = datetime.now(tz=MSK_ZONE).date()
        statement = (
            select(Rating)
            .where(
                today == func.date(Rating.created_at),
            )
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
