from contextlib import suppress
from typing import cast

from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.enums import UserRole
from app.models import Group, User
from app.services.log import LogService
from app.services.rating_service import RatingService
from app.services.schedule_service import ScheduleService
from bot.callback_data import AddRatingCD
from bot.filters import RoleFilter
from bot.keyboards import get_add_rating_kb, get_main_kb

router = Router()
router.message.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))
router.callback_query.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))


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
