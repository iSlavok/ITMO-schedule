from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lecturer, Rating
from app.repositories import LecturerRepository, RatingRepository
from app.schemas import LecturerDTO


class RatingService:
    def __init__(self, session: AsyncSession,
                 lecturer_repository: LecturerRepository,
                 rating_repository: RatingRepository) -> None:
        self._session = session
        self._lecturer_repository = lecturer_repository
        self._rating_repository = rating_repository

    async def get_lecturer_by_name(self, name: str) -> Lecturer | None:
        return await self._lecturer_repository.get_by_name(name)

    async def get_lecturer_rating(self, name: str) -> float | None:
        rating = await self._lecturer_repository.get_average_rating(name)
        return round(rating, 1) if rating is not None else None

    async def get_lecturers_rating(self, names: list[str]) -> dict[str, float]:
        return await self._lecturer_repository.get_average_ratings(names)

    async def get_top_lecturers_with_rank(
            self,
            page: int,
            per_page: int = 10,
            *, ascending: bool = False,
    ) -> list[LecturerDTO]:
        lecturers = await self._lecturer_repository.get_top_lecturers_with_rank(
            limit=per_page,
            skip=(page - 1) * per_page,
            ascending=ascending,
        )
        lecturer_tuples = [
            lecturer.tuple()
            for lecturer in lecturers
        ]
        return [
            LecturerDTO(
                name=lecturer[0],
                avg_rating=lecturer[1],
                reviews_count=lecturer[2],
                rank=lecturer[3],
            ) for lecturer in lecturer_tuples
        ]

    async def create_rating(self, rating: int, lecturer_id: int, user_id: int) -> Rating | bool:
        if not await self.can_user_rate_lecturer(user_id, lecturer_id):
            return False  # TODO(iSlavok): create custom exception
        rating = Rating(
            rating=rating,
            lecturer_id=lecturer_id,
            user_id=user_id,
        )
        self._session.add(rating)
        await self._session.commit()
        return rating

    async def get_lecturers_page_count(self, per_page: int = 10) -> int:
        count = await self._lecturer_repository.get_lecturers_count()
        return count // per_page + (1 if count % per_page > 0 else 0)

    async def can_user_rate_lecturer(self, user_id: int, lecturer_id: int) -> bool:
        return await self._rating_repository.can_user_rate_lecturer(user_id, lecturer_id)
