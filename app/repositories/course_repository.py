from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course, Group
from app.repositories import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Course)

    async def get_by_faculty_id(self, faculty_id: int) -> Sequence[Course]:
        statement = (
            select(Course)
            .where(Course.id.in_(
                select(Group.course_id).where(Group.faculty_id == faculty_id),
            ))
            .order_by(Course.name)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
