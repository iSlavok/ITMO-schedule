from collections.abc import Sequence

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lecturer, Rating
from app.repositories import BaseRepository


class LecturerRepository(BaseRepository[Lecturer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Lecturer)

    async def get_by_name(self, name: str) -> Lecturer | None:
        statement = (
            select(Lecturer)
            .where(Lecturer.name == name)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_average_rating(self, name: str) -> float | None:
        statement = (
            select(func.avg(Rating.rating))
            .join(Rating.lecturer)
            .where(Lecturer.name == name)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_top_lecturers_with_rank(
            self,
            limit: int = 10,
            skip: int = 0,
            *, ascending: bool = False,
    ) -> Sequence[Row[tuple[str, float, int, int]]]:
        avg_rating_subquery = (
            select(
                Lecturer.id,
                Lecturer.name,
                func.avg(Rating.rating).label("avg_rating"),
                func.count(Rating.id).label("reviews_count"),
            )
            .join(Rating)
            .group_by(
                Lecturer.id,
                Lecturer.name,
            )
            .subquery()
        )

        rank_subquery = (
            select(
                avg_rating_subquery.c.name,
                avg_rating_subquery.c.avg_rating,
                avg_rating_subquery.c.reviews_count,
                func.row_number()
                .over(
                    order_by=avg_rating_subquery.c.avg_rating.asc() if ascending else
                    avg_rating_subquery.c.avg_rating.desc(),
                )
                .label("rank"),
            )
            .subquery()
        )

        statement = (
            select(rank_subquery)
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(statement)
        return result.all()

    async def get_lecturers_count(self) -> int:
        statement = (
            select(func.count(Lecturer.id))
            .where(
                Lecturer.id.in_(
                    select(Rating.lecturer_id)
                    .distinct(),
                ),
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def get_average_ratings(self, names: list[str]) -> dict[str, float]:
        statement = (
            select(
                Lecturer.name,
                func.avg(Rating.rating).label("avg_rating"),
            )
            .join(Rating)
            .where(Lecturer.name.in_(names))
            .group_by(Lecturer.name)
        )
        result = await self.session.execute(statement)
        return {row.name: row.avg_rating for row in result.all()}

