import math
from collections.abc import Iterable

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.enums import UserRole
from app.schemas import UserWithGroupDTO
from app.services.user_service import UserService
from bot.callback_data import UsersListPageCD
from bot.config import messages
from bot.filters import RoleFilter
from bot.keyboards import get_users_list_kb
from bot.services import MessageManager

router = Router(name="admin_router")
router.message.filter(RoleFilter(UserRole.ADMIN))
router.callback_query.filter(RoleFilter(UserRole.ADMIN))

USERS_PER_PAGE = 10


@router.message(Command(commands=["users_list", "users"]))
async def users_list_open(
        _: Message,
        user_service: UserService,
        message_manager: MessageManager,
) -> None:
    await send_users_list_message(
        message_manager=message_manager,
        user_service=user_service,
        page=1,
    )


@router.callback_query(UsersListPageCD.filter())
async def users_list_page(
        callback: CallbackQuery,
        callback_data: UsersListPageCD,
        user_service: UserService,
        message_manager: MessageManager,
) -> None:
    await send_users_list_message(
        message_manager=message_manager,
        user_service=user_service,
        page=callback_data.page,
        send_new_message=False,
    )
    await callback.answer()


async def send_users_list_message(
        message_manager: MessageManager,
        user_service: UserService,
        page: int,
        *, send_new_message: bool = True,
) -> None:
    users = await user_service.get_users_with_group_and_course(page=page, per_page=USERS_PER_PAGE)
    total_count = await user_service.get_users_count()
    total_pages = math.ceil(total_count / USERS_PER_PAGE)
    text = get_users_list_text(
        users=users,
        total_count=total_count,
        skip_count=(page - 1) * USERS_PER_PAGE,
    )
    keyboard = get_users_list_kb(
        page=page,
        has_next_page=page < total_pages,
    )
    if send_new_message:
        await message_manager.send_message(text, reply_markup=keyboard)
    else:
        await message_manager.edit_message(text, reply_markup=keyboard)


def get_users_list_text(users: Iterable[UserWithGroupDTO], total_count: int, skip_count: int = 0) -> str:
    text = MessageManager.format_text(messages.admin.users_list.header, total_count=total_count)
    for i, user in enumerate(users, start=1):
        group_name = user.group.name if user.group else "Не выбрана"
        course_name = user.group.course.name if user.group else ""
        text += "\n" + MessageManager.format_text(
            messages.admin.users_list.user,
            number=i + skip_count,
            user_id=user.id,
            group_name=group_name,
            course_name=course_name,
            full_name=user.name,
            username=user.username,
        )
    return text
