from sqlalchemy import select
from sqlalchemy.orm import selectinload, Session
from app.database.models import Course


class CourseRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str) -> Course:
        course = Course(name=name)
        self.session.add(course)
        self.session.commit()
        self.session.refresh(course)
        return course

    def get_by_name(self, name: str) -> Course | None:
        query = select(Course).where(Course.name == name)
        result = self.session.execute(query)
        return result.scalars().first()

    def get_by_id(self, course_id: int) -> Course | None:
        query = select(Course).where(Course.id == course_id)
        result = self.session.execute(query)
        return result.scalars().first()

    def get_with_groups(self, name: str) -> Course | None:
        query = select(Course).options(selectinload(Course.groups)).where(Course.name == name)
        result = self.session.execute(query)
        return result.scalars().first()

    def get_all(self) -> list[Course]:
        query = select(Course)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def update(self, course: Course) -> Course:
        self.session.commit()
        self.session.refresh(course)
        return course

    def delete(self, course: Course) -> None:
        self.session.delete(course)
        self.session.commit()
