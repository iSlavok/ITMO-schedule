from aiogram import Dispatcher
from .user import UserMiddleware
from .user_service import UserServiceMiddleware
from .services import ServicesMiddleware


def register_middlewares(dp: Dispatcher):
    dp.message.outer_middleware(UserServiceMiddleware())
    dp.message.outer_middleware(UserMiddleware())
    dp.message.middleware(ServicesMiddleware())
    dp.callback_query.outer_middleware(UserServiceMiddleware())
    dp.callback_query.outer_middleware(UserMiddleware())
    dp.callback_query.middleware(ServicesMiddleware())
    # dp.message.middleware(ServiceMiddleware())
    # dp.message.middleware(UserMiddleware())
