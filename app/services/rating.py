from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lecturer, Rating, User
from app.repositories import LecturerRepository, RatingRepository


class RatingService:
    def __init__(self, session: AsyncSession,
                 lecturer_repository: LecturerRepository,
                 rating_repository: RatingRepository):
        self._session = session
        self._lecturer_repository = lecturer_repository
        self._rating_repository = rating_repository

    async def create_lecturer(self, name: str) -> Lecturer:
        lecturer = Lecturer(name=name)
        self._session.add(lecturer)
        await self._session.commit()
        return lecturer

    async def get_lecturer(self, name: str) -> Lecturer | None:
        return await self._lecturer_repository.get_by_name(name)

    async def get_lecturer_rating(self, name: str) -> float:
        rating = await self._lecturer_repository.get_average_rating(name)
        return round(rating, 1) if rating is not None else None

    async def get_top_lecturers_with_rank(self, page: int, per_page: int = 10, ascending: bool = False) -> list[
        tuple[str, int, float, int]]:
        lecturers = await self._lecturer_repository.get_top_lecturers_with_rank(limit=per_page,
                                                                                skip=(page - 1) * per_page,
                                                                                ascending=ascending)
        return [(lecturer.name, lecturer.rank, round(lecturer.avg_rating, 2), lecturer.reviews_count) for lecturer in lecturers]

    async def create_rating(self, rating: int, lecturer_id: int, user: User) -> Rating | bool:
        if not await self.can_user_rate_lecturer(user, lecturer_id):
            return False
        rating = Rating(
            rating=rating,
            lecturer_id=lecturer_id,
            user=user,
        )
        self._session.add(rating)
        await self._session.commit()
        return rating

    async def get_lecturers_page_count(self, per_page: int = 10) -> int:
        count = await self._lecturer_repository.get_lecturers_count()
        return count // per_page + (1 if count % per_page > 0 else 0)

    async def can_user_rate_lecturer(self, user: User, lecturer_id: int) -> bool:
        return await self._rating_repository.can_user_rate_lecturer(user, lecturer_id)
