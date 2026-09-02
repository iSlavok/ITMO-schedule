from aiogram.filters.callback_data import CallbackData


class FacultyCD(CallbackData, prefix="faculty"):
    id: int
    code: str
    name: str


class CourseCD(CallbackData, prefix="course"):
    id: int
    name: str
    faculty_id: int
    faculty_code: str


class GroupCD(CallbackData, prefix="group"):
    id: int
    name: str
    faculty_id: int
    faculty_code: str
