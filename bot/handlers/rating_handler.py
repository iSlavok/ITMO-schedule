from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.types import CallbackQuery, Message

from app.enums import UserRole
from app.models import Group, User
from app.services.exceptions import UserCannotRateLecturerError
from app.services.rating_service import RatingService
from app.services.schedule_service import ScheduleService
from bot.callback_data import AddRatingCD, SelectLecturerCD
from bot.filters import RoleFilter
from bot.keyboards import get_add_rating_kb, get_rating_kb, get_to_rating_kb
from bot.services import MessageManager

router = Router(name="rating_router")
router.message.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))
router.callback_query.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))


@router.message(
    F.text == "Оценить",
    flags={"services": ["rating"]},
)
@router.callback_query(
    F.data == "rating",
    flags={"services": ["rating"]},
)
async def get_rating_list_menu(
        event: Message | CallbackQuery,
        user: User,
        schedule_service: ScheduleService,
        rating_service: RatingService,
        message_manager: MessageManager,
) -> None:
    user_group: Group = user.group
    today_lecturer_names = schedule_service.get_today_past_lecturers(user_group.name)
    lecturers = await rating_service.get_available_lecturers_for_rating(today_lecturer_names, user.id)
    keyboard = get_rating_kb(lecturers)

    text = "Нет доступных преподавателей для оценки." if not lecturers else "Выберите преподавателя для оценки:"

    if isinstance(event, CallbackQuery):
        await message_manager.edit_message(text, reply_markup=keyboard)
        await event.answer()
    else:
        await message_manager.send_message(text, reply_markup=keyboard)


@router.callback_query(
    SelectLecturerCD.filter(),
    flags={"services": ["rating"]},
)
async def select_lecturer_for_rating(
        callback: CallbackQuery,
        user: User,
        callback_data: SelectLecturerCD,
        rating_service: RatingService,
        schedule_service: ScheduleService,
        message_manager: MessageManager,
) -> None:
    user_group: Group = user.group
    lecturer_id = callback_data.lecturer_id

    lecturer = await rating_service.get_lecturer_by_id(lecturer_id)
    if not lecturer:
        await callback.answer("Преподаватель не найден.", show_alert=True)
        return

    today_lecturer_names = schedule_service.get_today_past_lecturers(user_group.name)
    if lecturer.name not in today_lecturer_names:
        await callback.answer(f"Преподаватель {lecturer.name} не вел у вас занятия сегодня.", show_alert=True)
        return

    can_rate = await rating_service.can_user_rate_lecturer(user_id=user.id, lecturer_id=lecturer.id)
    if not can_rate:
        await callback.answer(f"Сегодня вы уже оценили преподавателя {lecturer.name}. ", show_alert=True)
        return

    await message_manager.edit_message(
        f"Выберите оценку для преподавателя {lecturer.name}:",
        reply_markup=get_add_rating_kb(lecturer.id),
    )
    await callback.answer()


@router.callback_query(
    AddRatingCD.filter(),
    flags={"services": ["rating"]},
)
async def add_rating(
        callback: CallbackQuery,
        user: User,
        callback_data: AddRatingCD,
        rating_service: RatingService,
        schedule_service: ScheduleService,
        message_manager: MessageManager,
) -> None:
    user_group: Group = user.group
    lecturer_id = callback_data.lecturer_id
    rating_value = callback_data.rating

    lecturer = await rating_service.get_lecturer_by_id(lecturer_id)
    if not lecturer:
        await callback.answer("Преподаватель не найден.", show_alert=True)
        return

    today_lecturer_names = schedule_service.get_today_past_lecturers(user_group.name)
    if lecturer.name not in today_lecturer_names:
        await callback.answer(f"Преподаватель {lecturer.name} не вел у вас занятия сегодня.", show_alert=True)
        return

    try:
        rating = await rating_service.create_rating(user_id=user.id, lecturer_id=lecturer.id, rating=rating_value)
    except UserCannotRateLecturerError:
        await callback.answer(f"Сегодня вы уже оценили преподавателя {lecturer.name}.", show_alert=True)
        return

    await message_manager.edit_message(
        f"Оценка {rating.rating}⭐ для преподавателя {lecturer.name} успешно добавлена!",
        reply_markup=get_to_rating_kb(),
    )
    await callback.answer()
