from aiogram.filters.callback_data import CallbackData

from app.enums import RatingType


class RatingListCD(CallbackData, prefix="rating"):
    type: RatingType
    page: int


class SelectLecturerCD(CallbackData, prefix="select_lecturer"):
    lecturer_id: int


class AddRatingCD(CallbackData, prefix="add_rating"):
    lecturer_id: int
    rating: int
