from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

from app.database import get_session
from app.repositories.user import UserRepository
from app.services.user import UserService


class UserServiceMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        session = next(get_session())
        data["session"] = session
        user_repo = UserRepository(session)
        data["user_repo"] = user_repo
        data["user_service"] = UserService(user_repo)
        return await handler(event, data)
