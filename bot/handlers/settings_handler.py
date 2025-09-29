from aiogram import F, Router
from aiogram.filters import or_f, Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from app.enums import UserRole
from app.models import User
from app.schemas import UserSettings
from app.services.user_service import UserService
from bot.config import messages
from bot.filters import RoleFilter
from bot.keyboards import get_user_setting_kb
from bot.services import MessageManager

router = Router(name="settings_router")
router.message.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))
router.callback_query.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))


@router.message(Command("settings"))
async def get_settings_menu(_: Message, message_manager: MessageManager, user: User) -> None:
    logger.info(f"User {user.id} opened settings menu")
    user_settings = UserSettings(
        rating_notifications=user.rating_notifications,
    )
    text = MessageManager.format_text(
        messages.settings.main,
        rating_notifications_status="✅ Включены" if user_settings.rating_notifications else "❌ Выключены",
    )
    await message_manager.send_message(
        text,
        reply_markup=get_user_setting_kb(user_settings),
    )


@router.callback_query(F.data == "settings_rating_notifications")
async def toggle_rating_notifications(
    query: CallbackQuery,
    message_manager: MessageManager,
    user_service: UserService,
    user: User,
) -> None:
    user = await user_service.change_settings(user=user, rating_notifications=not user.rating_notifications)
    user_settings = UserSettings(
        rating_notifications=user.rating_notifications,
    )

    logger.info(f"User {user.id} changed rating notifications to {user.rating_notifications}")

    text = MessageManager.format_text(
        messages.settings.main,
        rating_notifications_status="✅ Включены" if user_settings.rating_notifications else "❌ Выключены",
    )
    await message_manager.edit_message(
        text,
        reply_markup=get_user_setting_kb(user_settings),
    )
    await query.answer()
