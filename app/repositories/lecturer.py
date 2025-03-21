from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import Lecturer, Rating


class LecturerRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str) -> Lecturer:
        lecturer = Lecturer(name=name)
        self.session.add(lecturer)
        self.session.commit()
        return lecturer

    def get_lecturer(self, name: str) -> Lecturer | None:
        query = select(Lecturer).where(Lecturer.name == name)
        result = self.session.execute(query)
        return result.scalar_one_or_none()

    def get_average_rating(self, name: str) -> float:
        query = select(func.avg(Rating.rating)).join(
            Lecturer, Rating.lecturer_id == Lecturer.id
        ).where(Lecturer.name == name)
        result = self.session.execute(query)
        return result.scalar()

    def get_top_lecturers_with_rank(self, page: int, per_page: int = 10, ascending: bool = False) -> list[
        tuple[str, int, float, int]]:
        avg_rating_subq = select(
            Lecturer.id,
            Lecturer.name,
            func.avg(Rating.rating).label("avg_rating"),
            func.count(Rating.id).label("reviews_count")
        ).join(Rating).group_by(Lecturer.id, Lecturer.name).subquery()

        rank_subq = select(
            avg_rating_subq.c.id,
            avg_rating_subq.c.name,
            avg_rating_subq.c.avg_rating,
            avg_rating_subq.c.reviews_count,
            func.row_number().over(
                order_by=avg_rating_subq.c.avg_rating.asc() if ascending else avg_rating_subq.c.avg_rating.desc()
            ).label("rank")
        ).subquery()

        query = select(rank_subq).offset((page - 1) * per_page).limit(per_page)

        result = self.session.execute(query)
        return [(name, int(rank), float(avg_rating), int(reviews_count)) for id, name, avg_rating, reviews_count, rank
                in result]

    def get_lecturers_page_count(self, per_page: int = 10) -> int:
        query = select(func.count(Lecturer.id)).where(
            Lecturer.id.in_(select(Rating.lecturer_id).distinct())
        )
        result = self.session.execute(query)
        total_count = result.scalar()
        return (total_count + per_page - 1) // per_page