from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Log


class LogRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user_id: int, action: str) -> Log:
        log = Log(user_id=user_id, action=action)
        self._session.add(log)
        await self._session.commit()
        return log

    async def get_logs_by_user(self, user_id: int, limit: int = 10):
        query = select(Log).where(Log.user_id == user_id).order_by(Log.id.desc()).limit(limit)
        return (await self._session.execute(query)).scalars().all()
