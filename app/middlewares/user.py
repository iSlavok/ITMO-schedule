from aiogram import BaseMiddleware
from aiogram.types import User

from app.database.enums import Role
from app.services.user import UserService


class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        tg_user = get_user(event)
        if tg_user:
            service: UserService = data.get("user_service")
            user = service.get_user(tg_user.id)
            if not user:
                user = service.register_user(
                    user_id=tg_user.id,
                    username=tg_user.username,
                    name=tg_user.full_name,
                    role=Role.GUEST,
                )
            data["user"] = user
        return await handler(event, data)


def get_user(event) -> User | None:
    if hasattr(event, "from_user"):
        return event.from_user
    if hasattr(event, "message") and hasattr(event.message, "from_user"):
        return event.message.from_user
    return None
