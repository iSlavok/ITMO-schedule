from contextlib import suppress
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.enums import UserRole
from bot.filters import RoleFilter
from bot.handlers.user import delete_last_message
from bot.keyboards.user import get_main_kb
from bot.services import AdminService

router = Router()
router.message.filter(RoleFilter(UserRole.ADMIN))
router.callback_query.filter(RoleFilter(UserRole.ADMIN))


@router.message(
    Command("users"),
    flags={"services": ["admin"]}
)
async def users_command(message: Message, state: FSMContext, admin_service: AdminService):
    with suppress(Exception):
        await message.delete()
    users = await admin_service.get_users()
    text = f"{len(users)} пользователей:\n"
    for user in users:
        text += f"@{user.username} ({user.group.name})\n"
    new_message = await message.answer(text, reply_markup=get_main_kb())
    await delete_last_message(message, state, new_message.message_id)
