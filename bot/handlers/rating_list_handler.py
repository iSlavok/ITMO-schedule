from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.types import CallbackQuery, Message

from app.enums import RatingType, UserRole
from app.services.rating_service import RatingService
from bot.callback_data import RatingCD
from bot.filters import RoleFilter
from bot.keyboards import get_pagination_rating_kb, get_rating_kb
from bot.services import MessageManager

router = Router(name="rating_list_router")
router.message.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))
router.callback_query.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))


@router.message(F.text == "Рейтинг")
@router.callback_query(F.data == "rating")
async def get_rating_menu(event: Message | CallbackQuery, message_manager: MessageManager) -> None:
    text = "Выберите, какой рейтинг вы хотите посмотреть:"
    keyboard = get_rating_kb()
    if isinstance(event, CallbackQuery):
        await message_manager.edit_message(text, reply_markup=keyboard)
        await event.answer()
    else:
        await message_manager.send_message(text, reply_markup=keyboard)


@router.callback_query(
    RatingCD.filter(),
    flags={"services": ["rating"]},
)
async def show_rating(
        callback: CallbackQuery,
        callback_data: RatingCD,
        rating_service: RatingService,
        message_manager: MessageManager,
) -> None:
    rating_type = callback_data.type
    page = callback_data.page

    rating = await rating_service.get_top_lecturers_with_rank(page, ascending=rating_type != RatingType.BEST)
    rated_lecturers_pages_count = await rating_service.get_lecturers_page_count()

    text = "<b>" + ("Лучшие преподаватели:" if rating_type == RatingType.BEST else "Худшие преподаватели:") + "</b>\n\n"
    for lecturer in rating:
        text += (f"{lecturer.rank}. {lecturer.name} — ⭐️{round(lecturer.avg_rating, 2)} "
                 f"({lecturer.reviews_count} оценок)\n")

    await message_manager.edit_message(
        text,
        reply_markup=get_pagination_rating_kb(
            page=page,
            total_pages=rated_lecturers_pages_count,
            rating_type=rating_type,
        ),
    )
    await callback.answer()
