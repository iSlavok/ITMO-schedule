import time

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from app.database.enums import Role
from app.filters.role import RoleFilter
from app.services.user import UserService

router = Router()
router.message.filter(RoleFilter(Role.USER))


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот.",
    )


@router.message(F.text == "Помощь")
async def help_button(message: Message):
    await message.answer("Вот что я умею...")
