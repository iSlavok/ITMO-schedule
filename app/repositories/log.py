from sqlalchemy import select

from app.database.connection import Session
from app.models import Log


class LogRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, user_id: int, action: str) -> Log:
        log = Log(user_id=user_id, action=action)
        self._session.add(log)
        self._session.commit()
        return log

    def get_logs_by_user(self, user_id: int, limit: int = 10):
        query = select(Log).where(Log.user_id == user_id).order_by(Log.id.desc()).limit(limit)
        return self._session.execute(query).scalars().all()
