from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lecturer, Rating
from app.repositories import BaseRepository
from app.schemas import LecturerDTO


class LecturerRepository(BaseRepository[Lecturer]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Lecturer)

    async def get_by_name(self, name: str) -> Lecturer | None:
        query = select(Lecturer).where(Lecturer.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_average_rating(self, name: str) -> float:
        query = select(func.avg(Rating.rating)).join(
            Lecturer, Rating.lecturer_id == Lecturer.id
        ).where(Lecturer.name == name)
        result = await self.session.execute(query)
        return result.scalar()

    async def get_top_lecturers_with_rank(self, limit: int = 10, skip: int = 0,
                                          ascending: bool = False) -> list[LecturerDTO]:
        avg_rating_subq = select(
            Lecturer.id,
            Lecturer.name,
            func.avg(Rating.rating).label("avg_rating"),
            func.count(Rating.id).label("reviews_count")
        ).join(Rating).group_by(Lecturer.id, Lecturer.name).subquery()

        rank_subq = select(
            avg_rating_subq.c.name,
            avg_rating_subq.c.avg_rating,
            avg_rating_subq.c.reviews_count,
            func.row_number().over(
                order_by=avg_rating_subq.c.avg_rating.asc() if ascending else avg_rating_subq.c.avg_rating.desc()
            ).label("rank")
        ).subquery()

        query = select(rank_subq).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return [LecturerDTO(rank=rank, name=name, avg_rating=avg_rating, reviews_count=reviews_count)
                for name, avg_rating, reviews_count, rank in result]

    async def get_lecturers_count(self) -> int:
        query = select(func.count(Lecturer.id)).where(
            Lecturer.id.in_(select(Rating.lecturer_id).distinct())
        )
        result = await self.session.execute(query)
        return result.scalar()
