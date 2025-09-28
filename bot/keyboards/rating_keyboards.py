from collections.abc import Iterable

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models import Lecturer
from bot.callback_data import AddRatingCD, SelectLecturerCD


def get_to_rating_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="rating")
    return builder.as_markup()


def get_rating_kb(lecturers: Iterable[Lecturer]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lecturer in lecturers:
        builder.button(text=lecturer.name, callback_data=SelectLecturerCD(lecturer_id=lecturer.id))
    builder.button(text="Назад", callback_data="main")
    return builder.adjust(1).as_markup()


def get_add_rating_kb(lecturer_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.button(text=f"⭐{i}", callback_data=AddRatingCD(lecturer_id=lecturer_id, rating=i))
    builder.button(text="Назад", callback_data="rating")
    return builder.adjust(5, 5, 1).as_markup()
