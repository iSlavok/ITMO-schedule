from typing import Sequence, cast

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.callback_data import UsersListPageCD
from bot.config import messages
from bot.enums import UserRole
from bot.filters import RoleFilter
from bot.keyboards import get_users_list_kb
from bot.models import User
from bot.services import UserService, MessageManager

router = Router(name="admin_router")
router.message.filter(RoleFilter(UserRole.ADMIN))
router.callback_query.filter(RoleFilter(UserRole.ADMIN))


@router.callback_query(F.data == "users_list")
@router.message(Command(commands=["users_list", "users"]))
async def users_list_open(event: Message | CallbackQuery, user_service: UserService, message_manager: MessageManager):
    users = await user_service.get_users_with_group_and_course(page=1, per_page=10)
    total_count = await user_service.get_users_count()
    total_pages = (total_count // 10) + (1 if total_count % 10 > 0 else 0)
    await message_manager.send_message(
        get_users_list_text(users, total_count),
        reply_markup=get_users_list_kb(1, total_pages),
    )
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(UsersListPageCD.filter())
async def users_list_page(callback: CallbackQuery, callback_data: UsersListPageCD, user_service: UserService,
                          message_manager: MessageManager):
    users = await user_service.get_users_with_group_and_course(page=callback_data.page, per_page=10)
    total_count = await user_service.get_users_count()
    total_pages = (total_count // 10) + (1 if total_count % 10 > 0 else 0)
    await message_manager.edit_message(
        get_users_list_text(users, total_count, skip_count=(callback_data.page - 1) * 10),
        reply_markup=get_users_list_kb(callback_data.page, total_pages),
    )
    await callback.answer()


def get_users_list_text(users: Sequence[User], total_count: int, skip_count: int = 0) -> str:
    text = MessageManager.format_text(messages.admin.users_list.header, total_count=total_count)
    for i, user in enumerate(users, start=1):
        group_name = user.group.name if user.group else "Не выбрана"
        course_name = user.group.course.name if user.group else ""
        text += "\n" + MessageManager.format_text(
            messages.admin.users_list.user,
            number=i + skip_count,
            user_id=user.user_id,
            group_name=group_name,
            course_name=course_name,
            full_name=user.name,
            username=user.username,
        )
    return text
