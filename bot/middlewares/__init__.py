from aiogram import Dispatcher, Bot

from app.services.ai import AiService
from app.services.schedule import ScheduleService
from .user_middleware import UserMiddleware
from .services_middleware import ServicesMiddleware
from .message_manager_middleware import MessageManagerMiddleware


def register_middlewares(dp: Dispatcher, schedule_service: ScheduleService, ai_service: AiService, bot: Bot):
    dp.update.outer_middleware(UserMiddleware())
    dp.message.middleware(ServicesMiddleware(schedule_service, ai_service))
    dp.message.middleware(MessageManagerMiddleware(bot=bot))
    dp.callback_query.middleware(MessageManagerMiddleware(bot=bot))
    dp.callback_query.middleware(ServicesMiddleware(schedule_service, ai_service))
