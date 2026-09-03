from collections.abc import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course, Group
from app.repositories import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Course)

    async def get_by_faculty_id(self, faculty_id: int) -> Sequence[Course]:
        """Only the courses this faculty currently has active groups on."""
        statement = (
            select(Course)
            .where(Course.id.in_(
                select(Group.course_id).where(
                    Group.faculty_id == faculty_id,
                    Group.is_active.is_(True),
                ),
            ))
            .order_by(Course.name)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_ids_by_name(self) -> dict[str, int]:
        result = await self.session.execute(select(Course.name, Course.id))
        return dict(result.all())

    def add_many(self, names: Iterable[str]) -> list[Course]:
        courses = [Course(name=name) for name in names]
        self.session.add_all(courses)
        return courses
