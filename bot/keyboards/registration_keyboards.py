from collections.abc import Iterable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.enums import FacultyCode
from app.models import Course, Faculty, Group
from bot.callback_data import CourseCD, CourseListCD, FacultyCD, FacultyListCD, GroupCD
from bot.config import messages


def get_faculty_keyboard(
        faculties: Iterable[Faculty],
        *,
        back_callback_data: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for faculty in faculties:
        builder.button(
            text=faculty.name,
            callback_data=FacultyCD(id=faculty.id, code=faculty.code, name=faculty.name),
        )
    if back_callback_data is not None:
        builder.row(InlineKeyboardButton(text=messages.buttons.back, callback_data=back_callback_data))
    return builder.as_markup()


def get_course_keyboard(
        courses: Iterable[Course],
        *,
        faculty_id: int,
        faculty_code: FacultyCode,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for course in courses:
        builder.button(
            text=course.name,
            callback_data=CourseCD(
                id=course.id,
                name=course.name,
                faculty_id=faculty_id,
                faculty_code=faculty_code,
            ),
        )
    builder.row(InlineKeyboardButton(text=messages.buttons.back, callback_data=FacultyListCD().pack()))
    return builder.as_markup()


def get_group_keyboard(
        groups: Iterable[Group],
        *,
        faculty_id: int,
        faculty_code: FacultyCode,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(
            text=group.name,
            callback_data=GroupCD(
                id=group.id,
                name=group.name,
                faculty_id=faculty_id,
                faculty_code=faculty_code,
            ),
        )
    builder.adjust(3)
    builder.row(InlineKeyboardButton(
        text=messages.buttons.back,
        callback_data=CourseListCD(faculty_id=faculty_id, faculty_code=faculty_code).pack(),
    ))
    return builder.as_markup()
