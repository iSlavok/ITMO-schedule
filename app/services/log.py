from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Log
from app.repositories import LogRepository


class LogService:
    def __init__(self, session: AsyncSession, log_repository: LogRepository):
        self._session = session
        self._log_repository = log_repository

    async def log_action(self, user_id: int, action: str) -> Log:
        log = Log(
            user_id=user_id,
            action=action
        )
        self._session.add(log)
        await self._session.commit()
        await self._session.refresh(log)
        return log
