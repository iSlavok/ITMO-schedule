from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import TelegramObject

from app.repositories import CourseRepository, GroupRepository, LecturerRepository, LogRepository, RatingRepository
from app.services.guest_service import GuestService
from app.services.log import LogService
from app.services.rating_service import RatingService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ServicesMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> dict[str, Any]:
        required = get_flag(data, "services", default=[])
        services = {}
        session: AsyncSession = data["session"]
        log_repo = LogRepository(session)
        services["log_service"] = LogService(session, log_repo)
        for service in required:
            if service == "guest":
                course_repo = CourseRepository(session)
                group_repo = GroupRepository(session)
                services["guest_service"] = GuestService(
                    session=session,
                    course_repo=course_repo,
                    group_repo=group_repo,
                )
            elif service == "rating":
                lecturer_repo = LecturerRepository(session)
                rating_repo = RatingRepository(session)
                services["rating_service"] = RatingService(session, lecturer_repo, rating_repo)
        data.update(services)
        return await handler(event, data)
