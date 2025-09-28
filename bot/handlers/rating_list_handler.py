from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.types import CallbackQuery, Message
from loguru import logger

from app.enums import RatingType, UserRole
from app.models import User
from app.services.rating_service import RatingService
from bot.callback_data import RatingListCD
from bot.config import messages
from bot.filters import RoleFilter
from bot.keyboards import get_pagination_rating_list_kb, get_rating_list_kb
from bot.services import MessageManager

router = Router(name="rating_list_router")
router.message.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))
router.callback_query.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))


@router.message(F.text == "Рейтинг")
@router.callback_query(F.data == "rating_list")
async def get_rating_list_menu(event: Message | CallbackQuery, message_manager: MessageManager, user: User) -> None:
    logger.info(f"User {user.id} opened rating list menu")
    text = messages.lecturer_rating_list.type_request
    keyboard = get_rating_list_kb()
    if isinstance(event, CallbackQuery):
        await message_manager.edit_message(text, reply_markup=keyboard)
        await event.answer()
    else:
        await message_manager.send_message(text, reply_markup=keyboard)


@router.callback_query(
    RatingListCD.filter(),
    flags={"services": ["rating"]},
)
async def show_rating_list(
        callback: CallbackQuery,
        callback_data: RatingListCD,
        user: User,
        rating_service: RatingService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} requested {callback_data.type} rating, page {callback_data.page}")
    rating_type = callback_data.type
    page = callback_data.page

    rating = await rating_service.get_top_lecturers_with_rank(page, ascending=rating_type != RatingType.BEST)
    rated_lecturers_pages_count = await rating_service.get_lecturers_page_count()

    text = messages.lecturer_rating_list.best_header \
        if rating_type == RatingType.BEST \
        else messages.lecturer_rating_list.worst_header

    text += "\n".join(
        MessageManager.format_text(
            messages.lecturer_rating_list.lecturer,
            rank=lecturer.rank,
            name=lecturer.name,
            rating=round(lecturer.avg_rating, 2),
            ratings_count=lecturer.ratings_count,
        )
        for lecturer in rating
    )
    await message_manager.edit_message(
        text,
        reply_markup=get_pagination_rating_list_kb(
            page=page,
            total_pages=rated_lecturers_pages_count,
            rating_type=rating_type,
        ),
    )
    await callback.answer()
