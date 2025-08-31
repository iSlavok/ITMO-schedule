from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course
from app.repositories import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Course)
