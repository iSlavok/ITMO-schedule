from datetime import datetime

import pytz
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from app.enums import UserRole
from app.models import User
from app.services.guest_service import GuestService
from app.services.rating_service import RatingService
from app.services.schedule_service import ScheduleService
from bot.callback_data import CourseCD, GroupCD
from bot.config import messages
from bot.filters import RoleFilter
from bot.keyboards import get_course_keyboard, get_group_keyboard, get_main_kb
from bot.services import MessageManager
from bot.utils import get_schedule_text

router = Router(name="registration_router")
router.message.filter(RoleFilter(UserRole.GUEST))
router.callback_query.filter(RoleFilter(UserRole.GUEST))

MSK_TZ = pytz.timezone("Europe/Moscow")


@router.message(flags={"services": ["guest"]})
async def start_registration(
        _: Message,
        user: User,
        guest_service: GuestService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} started registration")

    courses = await guest_service.get_all_courses()
    keyboard = get_course_keyboard(courses)
    await message_manager.send_message(messages.registration.course_request, reply_markup=keyboard)


@router.callback_query(
    CourseCD.filter(),
    flags={"services": ["guest"]},
)
async def course_select(
        callback: CallbackQuery,
        callback_data: CourseCD,
        user: User,
        guest_service: GuestService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} selected course {callback_data.id}")

    text = MessageManager.format_text(messages.registration.course_selected, course_name=callback_data.name)
    await message_manager.send_message(text)

    groups = await guest_service.get_course_groups(callback_data.id)
    keyboard = get_group_keyboard(groups)
    await message_manager.send_message(
        text=messages.registration.group_request,
        clear_previous=False,
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(
    GroupCD.filter(),
    flags={"services": ["guest", "rating"]},
)
async def group_select(
        callback: CallbackQuery,
        callback_data: GroupCD,
        state: FSMContext,
        user: User,
        guest_service: GuestService,
        schedule_service: ScheduleService,
        rating_service: RatingService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} selected group {callback_data.id}")

    text = MessageManager.format_text(messages.registration.group_selected, group_name=callback_data.name)
    await message_manager.send_message(text)

    await guest_service.register_user(user, group_id=callback_data.id)
    await state.clear()

    logger.info(f"User {user.id} completed registration")

    schedule_text = await get_schedule_text(
        group_name=callback_data.name,
        schedule_service=schedule_service,
        rating_service=rating_service,
        day=datetime.now(tz=MSK_TZ).date(),
        day_str="сегодня",
        is_today=True,
    )
    await message_manager.send_message(text=schedule_text, reply_markup=get_main_kb())
    await callback.answer()
