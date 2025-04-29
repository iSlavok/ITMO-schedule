from aiogram import Dispatcher, Bot

from .user_middleware import UserMiddleware
from .services_middleware import ServicesMiddleware
from .message_manager_middleware import MessageManagerMiddleware
from bot.services import ScheduleService, AiService


def register_middlewares(dp: Dispatcher, schedule_service: ScheduleService, ai_service: AiService, bot: Bot):
    dp.update.outer_middleware(UserMiddleware())
    dp.message.middleware(ServicesMiddleware(schedule_service, ai_service))
    dp.message.middleware(MessageManagerMiddleware(bot=bot))
    dp.callback_query.middleware(MessageManagerMiddleware(bot=bot))
    dp.callback_query.middleware(ServicesMiddleware(schedule_service, ai_service))
