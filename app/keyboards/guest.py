from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.database import Course, Group


def get_course_keyboard(courses: list[Course]):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=course.name,
                callback_data=f"course_{course.id}"
            )
            for course in courses
        ]
    ])


def get_group_keyboard(groups: list[Group]):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=group.name,
                callback_data=f"group_{group.id}"
            )
            for group in groups
        ]
    ])