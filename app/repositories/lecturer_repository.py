from collections.abc import Iterable, Sequence

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lecturer, Rating
from app.repositories import BaseRepository


class LecturerRepository(BaseRepository[Lecturer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Lecturer)

    async def get_top_lecturers_with_rank(
            self,
            faculty_id: int,
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
            .where(
                Lecturer.faculty_id == faculty_id,
                Lecturer.is_hidden.is_(False),
            )
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

    async def get_lecturers_count(self, faculty_id: int) -> int:
        statement = (
            select(func.count(Lecturer.id))
            .where(
                Lecturer.faculty_id == faculty_id,
                Lecturer.is_hidden.is_(False),
                Lecturer.id.in_(
                    select(Rating.lecturer_id)
                    .distinct(),
                ),
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def get_average_ratings(self, names: list[str], faculty_id: int) -> dict[str, float]:
        statement = (
            select(
                Lecturer.name,
                func.avg(Rating.rating).label("avg_rating"),
            )
            .join(Rating)
            .where(
                Lecturer.name.in_(names),
                Lecturer.faculty_id == faculty_id,
                Lecturer.is_hidden.is_(False),
            )
            .group_by(Lecturer.name)
        )
        result = await self.session.execute(statement)
        return {row.name: row.avg_rating for row in result.all()}

    async def list_visible(self) -> Sequence[Lecturer]:
        statement = select(Lecturer).where(Lecturer.is_hidden.is_(False))
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_names_by_faculty(self, faculty_id: int) -> set[str]:
        statement = select(Lecturer.name).where(Lecturer.faculty_id == faculty_id)
        result = await self.session.execute(statement)
        return set(result.scalars().all())

    def add_many(self, names: Iterable[str], faculty_id: int) -> list[Lecturer]:
        lecturers = [Lecturer(name=name, faculty_id=faculty_id) for name in names]
        self.session.add_all(lecturers)
        return lecturers
