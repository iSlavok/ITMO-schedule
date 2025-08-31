from aiogram.filters.callback_data import CallbackData

from app.enums import RatingType


class CourseCD(CallbackData, prefix="course"):
    id: int
    name: str


class GroupCD(CallbackData, prefix="group"):
    id: int
    name: str
