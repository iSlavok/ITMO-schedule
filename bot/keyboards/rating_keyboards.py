from collections.abc import Iterable

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models import Lecturer
from bot.callback_data import AddRatingCD, SelectLecturerCD
from bot.config import messages


def get_to_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=messages.buttons.back, callback_data="main")
    return builder.as_markup()


def get_rating_kb(lecturers: Iterable[Lecturer]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lecturer in lecturers:
        builder.button(text=lecturer.name, callback_data=SelectLecturerCD(lecturer_id=lecturer.id))
    builder.button(text=messages.buttons.back, callback_data="main")
    return builder.adjust(1).as_markup()


def get_add_rating_kb(lecturer_id: int, back_callback_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.button(text=f"⭐{i}", callback_data=AddRatingCD(lecturer_id=lecturer_id, rating=i))
    builder.button(text=messages.buttons.back, callback_data=back_callback_data)
    return builder.adjust(5, 5, 1).as_markup()
