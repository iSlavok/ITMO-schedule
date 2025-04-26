from typing import Iterable

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.models import Course, Group


def get_course_keyboard(courses: Iterable[Course]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for course in courses:
        builder.button(text=course.name, callback_data=f"course_{course.id}")
    return builder.as_markup()


def get_group_keyboard(groups: Iterable[Group]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(text=group.name, callback_data=f"group_{group.id}")
    return builder.as_markup()
