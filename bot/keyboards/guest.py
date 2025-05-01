from typing import Iterable

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callback_data import CourseCD, GroupCD
from bot.models import Course, Group


def get_course_keyboard(courses: Iterable[Course]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for course in courses:
        builder.button(text=course.name, callback_data=CourseCD(id=course.id, name=course.name))
    return builder.as_markup()


def get_group_keyboard(groups: Iterable[Group]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(text=group.name, callback_data=GroupCD(id=group.id, name=group.name))
    return builder.as_markup()
