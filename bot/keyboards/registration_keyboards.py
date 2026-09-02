from collections.abc import Iterable

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models import Course, Faculty, Group
from bot.callback_data import CourseCD, FacultyCD, GroupCD


def get_faculty_keyboard(faculties: Iterable[Faculty]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for faculty in faculties:
        builder.button(
            text=faculty.name,
            callback_data=FacultyCD(id=faculty.id, code=faculty.code, name=faculty.name),
        )
    return builder.as_markup()


def get_course_keyboard(courses: Iterable[Course], faculty: FacultyCD) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for course in courses:
        builder.button(
            text=course.name,
            callback_data=CourseCD(
                id=course.id,
                name=course.name,
                faculty_id=faculty.id,
                faculty_code=faculty.code,
            ),
        )
    return builder.as_markup()


def get_group_keyboard(groups: Iterable[Group], course: CourseCD) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(
            text=group.name,
            callback_data=GroupCD(
                id=group.id,
                name=group.name,
                faculty_id=course.faculty_id,
                faculty_code=course.faculty_code,
            ),
        )
    return builder.adjust(3).as_markup()
