from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag

from app.repositories import GroupRepository
from app.repositories.course import CourseRepository
from app.services.guest import GuestService


class ServicesMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        required = get_flag(data, "required_data", default=[])
        services = {}
        session = data["session"]
        for service in required:
            if service == "guest_service":
                course_repo = CourseRepository(session)
                group_repo = GroupRepository(session)
                services["guest_service"] = GuestService(course_repo, group_repo)
        data.update(services)
        return await handler(event, data)
