from aiogram import Dispatcher
from .user import UserMiddleware
from .user_service import UserServiceMiddleware
from .services import ServicesMiddleware
from ..services import ScheduleService, AiService


def register_middlewares(dp: Dispatcher, schedule_service: ScheduleService, ai_service: AiService):
    dp.message.outer_middleware(UserServiceMiddleware())
    dp.message.outer_middleware(UserMiddleware())
    dp.message.middleware(ServicesMiddleware(schedule_service, ai_service))
    dp.callback_query.outer_middleware(UserServiceMiddleware())
    dp.callback_query.outer_middleware(UserMiddleware())
    dp.callback_query.middleware(ServicesMiddleware(schedule_service, ai_service))
