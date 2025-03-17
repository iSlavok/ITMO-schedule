from aiogram import Dispatcher
from .user import router as user_router
from .guest import router as guest_router


def register_handlers(dp: Dispatcher):
    dp.include_router(user_router)
    dp.include_router(guest_router)
