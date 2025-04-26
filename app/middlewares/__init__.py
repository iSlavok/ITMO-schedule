from aiogram import Dispatcher

from .user_middleware import UserMiddleware
from .services_middleware import ServicesMiddleware
from app.services import ScheduleService, AiService


def register_middlewares(dp: Dispatcher, schedule_service: ScheduleService, ai_service: AiService):
    dp.update.outer_middleware(UserMiddleware())
    dp.message.middleware(ServicesMiddleware(schedule_service, ai_service))
    dp.callback_query.middleware(ServicesMiddleware(schedule_service, ai_service))
