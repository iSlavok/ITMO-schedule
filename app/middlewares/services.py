from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message

from app.repositories import GroupRepository, CourseRepository
from app.services import GuestService, ScheduleService


class ServicesMiddleware(BaseMiddleware):
    def __init__(self, schedule_service: ScheduleService):
        self._schedule_service = schedule_service
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
        if "schedule" in required:
            services["schedule_service"] = self._schedule_service
        for service in required:
            if service == "guest":
                course_repo = CourseRepository(session)
                group_repo = GroupRepository(session)
                services["guest_service"] = GuestService(course_repo, group_repo)
        data.update(services)
        return await handler(event, data)
