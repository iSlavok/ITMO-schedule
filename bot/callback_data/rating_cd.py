from aiogram.filters.callback_data import CallbackData

from bot.enums import RatingType


class RatingCD(CallbackData, prefix="rating"):
    type: RatingType
    page: int


class AddRatingCD(CallbackData, prefix="add_rating"):
    lecturer_id: int
    rating: int
