from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.dispatcher.flags import get_flag
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import GroupRepository, CourseRepository, LecturerRepository, RatingRepository, LogRepository
from app.services.ai import AiService
from app.services.guest import GuestService
from app.services.log import LogService
from app.services.rating import RatingService
from app.services.schedule import ScheduleService


class ServicesMiddleware(BaseMiddleware):
    def __init__(self, schedule_service: ScheduleService, ai_service: AiService):
        self._schedule_service = schedule_service
        self._ai_service = ai_service
        super().__init__()

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: dict[str, Any]) -> dict[str, Any]:
        required = get_flag(data, "services", default=[])
        services = {}
        session: AsyncSession = data["session"]
        log_repo = LogRepository(session)
        services["log_service"] = LogService(session, log_repo)
        for service in required:
            if service == "schedule":
                services["schedule_service"] = self._schedule_service
            elif service == "ai":
                services["ai_service"] = self._ai_service
            elif service == "guest":
                course_repo = CourseRepository(session)
                group_repo = GroupRepository(session)
                services["guest_service"] = GuestService(
                    session=session,
                    course_repo=course_repo,
                    group_repo=group_repo
                )
            elif service == "rating":
                lecturer_repo = LecturerRepository(session)
                rating_repo = RatingRepository(session)
                services["rating_service"] = RatingService(session, lecturer_repo, rating_repo)
        data.update(services)
        return await handler(event, data)
