from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.enums import RatingType
from bot.callback_data import RatingListCD


def get_main_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Сегодня")
    builder.button(text="Завтра")
    builder.button(text="Оценить")
    builder.button(text="Рейтинг")
    return builder.as_markup(resize_keyboard=True)


def get_rating_list_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Лучшие", callback_data=RatingListCD(type=RatingType.BEST, page=1))
    builder.button(text="Худшие", callback_data=RatingListCD(type=RatingType.WORST, page=1))
    builder.button(text="Назад", callback_data="main")
    return builder.adjust(2).as_markup()


def get_pagination_rating_list_kb(page: int, total_pages: int, rating_type: RatingType) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text="⬅️", callback_data=RatingListCD(type=rating_type, page=page - 1))
    if page < total_pages:
        builder.button(text="➡️", callback_data=RatingListCD(type=rating_type, page=page + 1))
    builder.button(text="Назад", callback_data="rating_list")
    return builder.adjust(2).as_markup()
