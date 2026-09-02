from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Faculty
from app.repositories import BaseRepository


class FacultyRepository(BaseRepository[Faculty]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Faculty)

    async def get_by_code(self, code: str) -> Faculty | None:
        statement = select(Faculty).where(Faculty.code == code)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
