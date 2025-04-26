from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database import get_session
from app.enums import UserRole
from app.repositories import UserRepository
from app.services import UserService


class UserMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: dict[str, Any]) -> Any:
        event_from_user = data["event_from_user"]
        if event_from_user:
            session = next(get_session())
            data["session"] = session
            user_service = UserService(
                user_repo=UserRepository(session),
            )
            data["user_service"] = user_service
            user = user_service.create_user(
                user_id=event_from_user.id,
                name=event_from_user.full_name,
                username=event_from_user.username,
                role=UserRole.GUEST,
            )
            data["user"] = user
            result = await handler(event, data)
            return result
        return await handler(event, data)