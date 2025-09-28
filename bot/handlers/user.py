from contextlib import suppress
from typing import cast

from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.enums import RatingType, UserRole
from app.models import Group, User
from app.services.log import LogService
from app.services.rating_service import RatingService
from app.services.schedule_service import ScheduleService
from bot.callback_data import AddRatingCD, RatingCD
from bot.filters import RoleFilter
from bot.keyboards import get_add_rating_kb, get_main_kb, get_pagination_rating_kb, get_rating_kb

router = Router()
router.message.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))
router.callback_query.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))


@router.message(
    F.text == "Рейтинг",
)
async def get_rating_menu(message: Message, state: FSMContext, log_service: LogService, user: User) -> None:
    with suppress(Exception):
        await message.delete()
    await log_service.log_action(user.id, f"message {message.text}")
    await show_rating_menu(message, state)


async def show_rating_menu(message: Message, state: FSMContext) -> None:
    new_message = await message.answer(
        "Выберите, какой рейтинг вы хотите посмотреть:",
        reply_markup=get_rating_kb(),
    )
    await delete_last_message(message, state, new_message.message_id)


@router.callback_query(
    F.data == "rating",
)
async def get_rating_menu_button(callback: CallbackQuery, state: FSMContext, log_service: LogService,
                                 user: User) -> None:
    with suppress(Exception):
        await callback.answer()
        await callback.message.delete()
    await log_service.log_action(user.id, f"button {callback.data}")
    await show_rating_menu(callback.message, state)


@router.callback_query(
    RatingCD.filter(),
    flags={"services": ["rating"]},
)
async def show_rating(callback: CallbackQuery, callback_data: RatingCD, state: FSMContext, user: User,  # noqa: PLR0913
                      rating_service: RatingService, log_service: LogService) -> None:
    with suppress(Exception):
        await callback.answer()
        await callback.message.delete()
    await log_service.log_action(user.id, f"button {callback.data}")
    rating_type = callback_data.type
    page = callback_data.page
    rating = await rating_service.get_top_lecturers_with_rank(page, ascending=rating_type != RatingType.BEST)
    text = "<b>" + ("Лучшие преподаватели:" if rating_type == RatingType.BEST else "Худшие преподаватели:") + "</b>\n\n"
    for lecturer in rating:
        text += (f"{lecturer.rank}. {lecturer.name} — ⭐️{round(lecturer.avg_rating, 2)} "
                 f"({lecturer.reviews_count} оценок)\n")
    new_message = await callback.message.answer(
        text,
        reply_markup=get_pagination_rating_kb(page, await rating_service.get_lecturers_page_count(), rating_type),
    )
    await delete_last_message(callback.message, state, new_message.message_id)


@router.message(
    F.text == "Оценить",
    flags={"services": ["rating", "schedule"]},
)
async def select_rating(message: Message, state: FSMContext, rating_service: RatingService,  # noqa: PLR0913
                        schedule_service: ScheduleService, user: User, log_service: LogService) -> None:
    with suppress(Exception):
        await message.delete()
    await log_service.log_action(user.id, f"message {message.text}")
    group = cast("Group", user.group)
    last_lecturer = schedule_service.get_last_lecturer(group.name)
    if last_lecturer:
        lecturer = await rating_service.get_lecturer_by_name(last_lecturer)
        if lecturer:
            if await rating_service.can_user_rate_lecturer(user.id, lecturer.id):
                new_message = await message.answer(
                    f"Выберите оценку для преподавателя {lecturer.name}:",
                    reply_markup=get_add_rating_kb(lecturer.id),
                )
            else:
                new_message = await message.answer(
                    f"Сегодня вы уже оценили преподавателя {lecturer.name}.",
                    reply_markup=get_main_kb(),
                )
            return await delete_last_message(message, state, new_message.message_id)
    new_message = await message.answer(
        "Нет доступного преподавателя для оценки.",
        reply_markup=get_main_kb(),
    )
    await delete_last_message(message, state, new_message.message_id)
    return None


@router.callback_query(
    AddRatingCD.filter(),
    flags={"services": ["rating", "schedule"]},
)
async def submit_rating(callback: CallbackQuery, callback_data: AddRatingCD, state: FSMContext,  # noqa: PLR0913
                        rating_service: RatingService, schedule_service: ScheduleService, user: User,
                        log_service: LogService) -> None:
    with suppress(Exception):
        await callback.answer()
        await callback.message.delete()
    await log_service.log_action(user.id, f"button {callback.data}")
    lecturer_id = callback_data.lecturer_id
    rating = callback_data.rating
    group = cast("Group", user.group)
    last_lecturer = schedule_service.get_last_lecturer(group.name)
    if not last_lecturer:
        new_message = await callback.message.answer("Нет доступного преподавателя для оценки.")
        return await delete_last_message(callback.message, state, new_message.message_id)
    lecturer = await rating_service.get_lecturer_by_name(last_lecturer)
    if lecturer is None or lecturer.id != lecturer_id:
        new_message = await callback.message.answer("Вы не можете оценить этого преподавателя.")
        return await delete_last_message(callback.message, state, new_message.message_id)
    rating = await rating_service.create_rating(
        rating=rating,
        lecturer_id=lecturer_id,
        user_id=user.id,
    )
    if rating:
        new_message = await callback.message.answer(
            f"Оценка {rating.rating} для преподавателя {lecturer.name} успешно добавлена.",
            reply_markup=get_main_kb(),
        )
    else:
        new_message = await callback.message.answer(
            "Сегодня вы уже оценили этого преподавателя.",
            reply_markup=get_main_kb(),
        )
    await delete_last_message(callback.message, state, new_message.message_id)
    return None


async def delete_last_message(message: Message, state: FSMContext, new_message_id: int) -> None:
    data = await state.get_data()
    old_message = data.get("last_message_id")
    if old_message:
        with suppress(Exception):
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_message)
    await state.update_data(last_message_id=new_message_id)
