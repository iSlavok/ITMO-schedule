from app.models import Lecturer, Rating
from app.repositories import LecturerRepository, RatingRepository


class RatingService:
    def __init__(self, lecturer_repository: LecturerRepository, rating_repository: RatingRepository):
        self.lecturer_repository = lecturer_repository
        self.rating_repository = rating_repository

    def create_lecturer(self, name: str) -> Lecturer:
        return self.lecturer_repository.create(name)

    def get_lecturer(self, name: str) -> Lecturer | None:
        return self.lecturer_repository.get_lecturer(name)

    def get_lecturer_rating(self, name: str) -> float:
        rating = self.lecturer_repository.get_average_rating(name)
        return round(rating, 1) if rating is not None else None

    def get_top_lecturers_with_rank(self, page: int, per_page: int = 10, ascending: bool = False) -> list[
        tuple[str, int, float, int]]:
        lecturers = self.lecturer_repository.get_top_lecturers_with_rank(page, per_page, ascending)
        return [(name, rank, round(rating, 2), reviews_count) for name, rank, rating, reviews_count in lecturers]

    def create_rating(self, rating: int, lecturer_id: int, user_id: int) -> Rating | bool:
        if not self.can_user_rate_lecturer(user_id, lecturer_id):
            return False
        return self.rating_repository.create(rating, lecturer_id, user_id)

    def get_lecturers_page_count(self, per_page: int = 10) -> int:
        return self.lecturer_repository.get_lecturers_page_count(per_page)

    def can_user_rate_lecturer(self, user_id: int, lecturer_id: int) -> bool:
        return self.rating_repository.can_user_rate_lecturer(user_id, lecturer_id)
