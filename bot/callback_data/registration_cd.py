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
