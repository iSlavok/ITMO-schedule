from bot.repositories import LogRepository


class LogService:
    def __init__(self, log_repository: LogRepository):
        self._log_repository = log_repository

    async def log_action(self, user_id: int, action: str):
        return await self._log_repository.create(user_id, action)

    async def get_recent_logs(self, user_id: int, limit: int = 10):
        return await self._log_repository.get_logs_by_user(user_id, limit)
