from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.enums import RatingType
from bot.callback_data import AddRatingCD, RatingCD


def get_main_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Сегодня")
    builder.button(text="Завтра")
    builder.button(text="Оценить")
    builder.button(text="Рейтинг")
    return builder.as_markup(resize_keyboard=True)


def get_rating_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Лучшие", callback_data=RatingCD(type=RatingType.BEST, page=1))
    builder.button(text="Худшие", callback_data=RatingCD(type=RatingType.WORST, page=1))
    builder.button(text="Назад", callback_data="main")
    return builder.adjust(2).as_markup()


def get_pagination_rating_kb(page: int, total_pages: int, rating_type: RatingType) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text="⬅️", callback_data=RatingCD(type=rating_type, page=page - 1))
    if page < total_pages:
        builder.button(text="➡️", callback_data=RatingCD(type=rating_type, page=page + 1))
    builder.button(text="Назад", callback_data="rating")
    return builder.adjust(2).as_markup()


def get_add_rating_kb(lecturer_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.button(text=f"⭐{i}", callback_data=AddRatingCD(lecturer_id=lecturer_id, rating=i))
    builder.button(text="Назад", callback_data="main")
    return builder.adjust(5, 5, 1).as_markup()
