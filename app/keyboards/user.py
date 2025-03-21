from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text="Сегодня"),
            KeyboardButton(text="Завтра"),
            KeyboardButton(text="Оценить"),
            KeyboardButton(text="Рейтинг")
        ],
    ])

ranking_order_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Лучшие", callback_data="rating_best_1"),
            InlineKeyboardButton(text="Худшие", callback_data="rating_worst_1")
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data="main_menu")
        ]
    ]
)


def get_pagination_rating_keyboard(page: int, total_pages: int, is_best: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"rating_{'best' if is_best else 'worst'}_{page - 1}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"rating_{'best' if is_best else 'worst'}_{page + 1}"))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            buttons,
            [
                InlineKeyboardButton(text="Назад", callback_data="rating_menu"),
            ]
        ]
    )


def get_rating_keyboard(lecturer_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐️1", callback_data=f"add_rating_{lecturer_id}_1"),
                InlineKeyboardButton(text="⭐2️", callback_data=f"add_rating_{lecturer_id}_2"),
                InlineKeyboardButton(text="⭐3️", callback_data=f"add_rating_{lecturer_id}_3"),
                InlineKeyboardButton(text="⭐4", callback_data=f"add_rating_{lecturer_id}_4"),
                InlineKeyboardButton(text="⭐5", callback_data=f"add_rating_{lecturer_id}_5"),
            ],
            [
                InlineKeyboardButton(text="Назад", callback_data="main_menu")
            ]
        ]
    )