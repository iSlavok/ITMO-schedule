from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callback_data import UsersListPageCD


def get_users_list_kb(page: int, *, has_next_page: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    page_buttons = 0
    if page > 1:
        builder.button(text="◀️", callback_data=UsersListPageCD(page=page - 1))
        page_buttons += 1
    if has_next_page:
        builder.button(text="▶️", callback_data=UsersListPageCD(page=page + 1))
        page_buttons += 1
    return builder.as_markup()
