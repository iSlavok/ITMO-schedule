from contextlib import suppress

from aiogram import Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.services.log import LogService
from app.services.rating import RatingService
from app.services.schedule import ScheduleService
from bot.callback_data import RatingCD, AddRatingCD
from app.enums import UserRole, RatingType
from bot.filters import RoleFilter
from bot.keyboards import (
    get_main_kb,
    get_rating_kb,
    get_pagination_rating_kb,
    get_add_rating_kb
)
from app.models import User

router = Router()
router.message.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))
router.callback_query.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))


@router.message(
    F.text == "Рейтинг"
)
async def get_rating_menu(message: Message, state: FSMContext, log_service: LogService):
    with suppress(Exception):
        await message.delete()
    await log_service.log_action(message.from_user.id, f"message {message.text}")
    await show_rating_menu(message, state)


async def show_rating_menu(message: Message, state: FSMContext):
    new_message = await message.answer(
        f"Выберите, какой рейтинг вы хотите посмотреть:",
        reply_markup=get_rating_kb()
    )
    await delete_last_message(message, state, new_message.message_id)


@router.callback_query(
    F.data == "rating",
)
async def get_rating_menu_button(callback: CallbackQuery, state: FSMContext, log_service: LogService):
    with suppress(Exception):
        await callback.answer()
        await callback.message.delete()
    await log_service.log_action(callback.from_user.id, f"button {callback.data}")
    await show_rating_menu(callback.message, state)


@router.callback_query(
    RatingCD.filter(),
    flags={"services": ["rating"]}
)
async def show_rating(callback: CallbackQuery, callback_data: RatingCD, state: FSMContext,
                      rating_service: RatingService, log_service: LogService):
    with suppress(Exception):
        await callback.answer()
        await callback.message.delete()
    await log_service.log_action(callback.from_user.id, f"button {callback.data}")
    rating_type = callback_data.type
    page = callback_data.page
    rating = await rating_service.get_top_lecturers_with_rank(page, ascending=rating_type != RatingType.BEST)
    text = "<b>" + ("Лучшие преподаватели:" if rating_type == RatingType.BEST else "Худшие преподаватели:") + "</b>\n\n"
    for lecturer, rank, avg_rating, reviews_count in rating:
        text += f"{rank}. {lecturer} — ⭐️{avg_rating} ({reviews_count} оценок)\n"
    new_message = await callback.message.answer(
        text,
        reply_markup=get_pagination_rating_kb(page, await rating_service.get_lecturers_page_count(), rating_type),
    )
    await delete_last_message(callback.message, state, new_message.message_id)


@router.message(
    F.text == "Оценить",
    flags={"services": ["rating", "schedule"]}
)
async def select_rating(message: Message, state: FSMContext, rating_service: RatingService,
                        schedule_service: ScheduleService, user: User, log_service: LogService):
    with suppress(Exception):
        await message.delete()
    await log_service.log_action(message.from_user.id, f"message {message.text}")
    last_lecturer = schedule_service.get_last_lecturer(user.group.name)
    if last_lecturer:
        lecturer = await rating_service.get_lecturer(last_lecturer)
        if lecturer:
            if await rating_service.can_user_rate_lecturer(user, lecturer.id):
                new_message = await message.answer(
                    f"Выберите оценку для преподавателя {lecturer.name}:",
                    reply_markup=get_add_rating_kb(lecturer.id)
                )
            else:
                new_message = await message.answer(
                    f"Сегодня вы уже оценили преподавателя {lecturer.name}.",
                    reply_markup=get_main_kb()
                )
            return await delete_last_message(message, state, new_message.message_id)
    new_message = await message.answer(
        "Нет доступного преподавателя для оценки.",
        reply_markup=get_main_kb()
    )
    await delete_last_message(message, state, new_message.message_id)


@router.callback_query(
    AddRatingCD.filter(),
    flags={"services": ["rating", "schedule"]}
)
async def submit_rating(callback: CallbackQuery, callback_data: AddRatingCD, state: FSMContext,
                        rating_service: RatingService, schedule_service: ScheduleService, user: User,
                        log_service: LogService):
    with suppress(Exception):
        await callback.answer()
        await callback.message.delete()
    await log_service.log_action(callback.from_user.id, f"button {callback.data}")
    lecturer_id = callback_data.lecturer_id
    rating = callback_data.rating
    last_lecturer = schedule_service.get_last_lecturer(user.group.name)
    if not last_lecturer:
        new_message = await callback.message.answer("Нет доступного преподавателя для оценки.")
        return await delete_last_message(callback.message, state, new_message.message_id)
    lecturer = await rating_service.get_lecturer(last_lecturer)
    if lecturer is None or lecturer.id != lecturer_id:
        new_message = await callback.message.answer("Вы не можете оценить этого преподавателя.")
        return await delete_last_message(callback.message, state, new_message.message_id)
    rating = await rating_service.create_rating(rating, lecturer_id, user)
    if rating:
        new_message = await callback.message.answer(
            f"Оценка {rating.rating} для преподавателя {lecturer.name} успешно добавлена.",
            reply_markup=get_main_kb()
        )
    else:
        new_message = await callback.message.answer(
            "Сегодня вы уже оценили этого преподавателя.",
            reply_markup=get_main_kb()
        )
    await delete_last_message(callback.message, state, new_message.message_id)


async def delete_last_message(message: Message, state: FSMContext, new_message_id: int):
    data = await state.get_data()
    old_message = data.get("last_message_id")
    if old_message:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_message)
        except Exception:
            pass
    await state.update_data(last_message_id=new_message_id)
