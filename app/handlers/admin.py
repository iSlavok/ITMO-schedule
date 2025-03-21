from contextlib import suppress
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database import Role
from app.filters import RoleFilter
from app.handlers.user import delete_last_message
from app.keyboards.user import main_keyboard
from app.services import AdminService

router = Router()
router.message.filter(RoleFilter(Role.ADMIN))
router.callback_query.filter(RoleFilter(Role.ADMIN))


@router.message(
    Command("users"),
    flags={"services": ["admin"]}
)
async def users_command(message: Message, state: FSMContext, admin_service: AdminService):
    with suppress(Exception):
        await message.delete()
    users = admin_service.get_users()
    text = f"{len(users)} пользователей:\n"
    for user in users:
        text += f"@{user.username} ({user.group.name})\n"
    new_message = await message.answer(text, reply_markup=main_keyboard)
    await delete_last_message(message, state, new_message.message_id)
