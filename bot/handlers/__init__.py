from aiogram import Dispatcher

from .admin import router as admin_router
from .registration_handler import router as registration_router
from .schedule_handler import router as schedule_router
from .user import router as user_router


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(registration_router)
    dp.include_router(schedule_router)
