from bot.models import Lecturer, Rating
from bot.repositories import LecturerRepository, RatingRepository


class RatingService:
    def __init__(self, lecturer_repository: LecturerRepository, rating_repository: RatingRepository):
        self.lecturer_repository = lecturer_repository
        self.rating_repository = rating_repository

    async def create_lecturer(self, name: str) -> Lecturer:
        return await self.lecturer_repository.create(name)

    async def get_lecturer(self, name: str) -> Lecturer | None:
        return await self.lecturer_repository.get_lecturer(name)

    async def get_lecturer_rating(self, name: str) -> float:
        rating = await self.lecturer_repository.get_average_rating(name)
        return round(rating, 1) if rating is not None else None

    async def get_top_lecturers_with_rank(self, page: int, per_page: int = 10, ascending: bool = False) -> list[
        tuple[str, int, float, int]]:
        lecturers = await self.lecturer_repository.get_top_lecturers_with_rank(page, per_page, ascending)
        return [(name, rank, round(rating, 2), reviews_count) for name, rank, rating, reviews_count in lecturers]

    async def create_rating(self, rating: int, lecturer_id: int, user_id: int) -> Rating | bool:
        if not await self.can_user_rate_lecturer(user_id, lecturer_id):
            return False
        return await self.rating_repository.create(rating, lecturer_id, user_id)

    async def get_lecturers_page_count(self, per_page: int = 10) -> int:
        return await self.lecturer_repository.get_lecturers_page_count(per_page)

    async def can_user_rate_lecturer(self, user_id: int, lecturer_id: int) -> bool:
        return await self.rating_repository.can_user_rate_lecturer(user_id, lecturer_id)
