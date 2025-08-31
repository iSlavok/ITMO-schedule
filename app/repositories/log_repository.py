from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Log
from app.repositories import BaseRepository


class LogRepository(BaseRepository[Log]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Log)
