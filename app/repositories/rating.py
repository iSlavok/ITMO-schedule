from datetime import date
from sqlalchemy import select, func

from app.database import Rating
from app.database.connection import Session


class RatingRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, rating: int, lecturer_id: int, user_id: int):
        rating = Rating(rating=rating, lecturer_id=lecturer_id, user_id=user_id)
        self.session.add(rating)
        self.session.commit()
        return rating

    def can_user_rate_lecturer(self, user_id: int, lecturer_id: int) -> bool:
        today = date.today()
        query = select(Rating).where(
            Rating.user_id == user_id,
            Rating.lecturer_id == lecturer_id,
            today == func.date(Rating.created_at)
        )
        result = self.session.execute(query).first()
        return result is None
