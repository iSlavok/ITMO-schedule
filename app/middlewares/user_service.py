from aiogram import BaseMiddleware

from app.database import get_session
from app.repositories import UserRepository
from app.services import UserService


class UserServiceMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        session = next(get_session())
        data["session"] = session
        user_repo = UserRepository(session)
        data["user_service"] = UserService(user_repo)
        return await handler(event, data)
