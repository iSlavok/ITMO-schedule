from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.enums import RatingType
from bot.callback_data import RatingListCD
from bot.config import messages


def get_main_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=messages.buttons.today_schedule)
    builder.button(text=messages.buttons.tomorrow_schedule)
    builder.button(text=messages.buttons.lecturer_rating)
    builder.button(text=messages.buttons.lecturer_rating_list)
    return builder.as_markup(resize_keyboard=True)


def get_rating_list_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=messages.buttons.best_lecturers, callback_data=RatingListCD(type=RatingType.BEST, page=1))
    builder.button(text=messages.buttons.worst_lecturers, callback_data=RatingListCD(type=RatingType.WORST, page=1))
    builder.button(text=messages.buttons.back, callback_data="main")
    return builder.adjust(2).as_markup()


def get_pagination_rating_list_kb(page: int, total_pages: int, rating_type: RatingType) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(
            text=messages.buttons.pagination_prev,
            callback_data=RatingListCD(type=rating_type, page=page - 1),
        )
    if page < total_pages:
        builder.button(
            text=messages.buttons.pagination_next,
            callback_data=RatingListCD(type=rating_type, page=page + 1),
        )
    builder.button(text=messages.buttons.back, callback_data="rating_list")
    return builder.adjust(2).as_markup()
