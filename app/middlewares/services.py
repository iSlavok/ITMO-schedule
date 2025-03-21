from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message

from app.repositories import GroupRepository, CourseRepository, LecturerRepository, RatingRepository
from app.services import GuestService, ScheduleService, AiService, RatingService, AdminService


class ServicesMiddleware(BaseMiddleware):
    def __init__(self, schedule_service: ScheduleService, ai_service: AiService):
        self._schedule_service = schedule_service
        self._ai_service = ai_service
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        required = get_flag(data, "services", default=[])
        services = {}
        session = data["session"]
        for service in required:
            if service == "schedule":
                services["schedule_service"] = self._schedule_service
            elif service == "ai":
                services["ai_service"] = self._ai_service
            elif service == "guest":
                course_repo = CourseRepository(session)
                group_repo = GroupRepository(session)
                services["guest_service"] = GuestService(course_repo, group_repo)
            elif service == "rating":
                lecturer_repo = LecturerRepository(session)
                rating_repo = RatingRepository(session)
                services["rating_service"] = RatingService(lecturer_repo, rating_repo)
            elif service == "admin":
                data["admin_service"] = AdminService(data["user_repo"])
        data.update(services)
        return await handler(event, data)
