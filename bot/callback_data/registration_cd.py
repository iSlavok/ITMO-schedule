from aiogram.filters.callback_data import CallbackData

from app.enums import FacultyCode


class FacultyCD(CallbackData, prefix="faculty"):
    id: int
    code: FacultyCode
    name: str


class CourseCD(CallbackData, prefix="course"):
    id: int
    name: str
    faculty_id: int
    faculty_code: FacultyCode


class GroupCD(CallbackData, prefix="group"):
    id: int
    name: str
    faculty_id: int
    faculty_code: FacultyCode


class FacultyListCD(CallbackData, prefix="faculty_list"):
    """Go back to the faculty list."""


class CourseListCD(CallbackData, prefix="course_list"):
    """Go back to the course list of a faculty."""

    faculty_id: int
    faculty_code: FacultyCode
