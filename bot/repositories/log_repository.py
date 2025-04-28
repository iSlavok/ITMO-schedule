from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Log
from bot.repositories import BaseRepository


class LogRepository(BaseRepository[Log]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Log)
