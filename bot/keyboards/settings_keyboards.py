from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.schemas import UserSettings
from bot.config import messages


def get_user_setting_kb(user_settings: UserSettings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    emoji = "✅" if user_settings.rating_notifications else "❌"
    builder.button(
        text=f"{emoji} {messages.buttons.rating_notifications}",
        callback_data="settings_rating_notifications"
    )
    return builder.as_markup()
