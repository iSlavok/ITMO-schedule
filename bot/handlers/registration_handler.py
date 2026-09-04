from datetime import datetime

import pytz
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from app.enums import UserRole
from app.models import User
from app.services.catalog_query_service import CatalogQueryService
from app.services.rating_service import RatingService
from app.services.schedule_service import ScheduleService
from app.services.user_service import UserService
from bot.callback_data import CourseCD, CourseListCD, FacultyCD, FacultyListCD, GroupCD
from bot.config import messages
from bot.filters import RoleFilter
from bot.keyboards import get_main_kb
from bot.services import MessageManager
from bot.utils import announce_course, announce_faculty, get_schedule_text, render_faculties, show_courses, show_groups

router = Router(name="registration_router")
router.message.filter(RoleFilter(UserRole.GUEST))
router.callback_query.filter(RoleFilter(UserRole.GUEST))

MSK_TZ = pytz.timezone("Europe/Moscow")


@router.message(flags={"services": ["catalog"]})
async def start_registration(
        _: Message,
        user: User,
        catalog_query_service: CatalogQueryService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} started registration")
    await render_faculties(message_manager, catalog_query_service)


@router.callback_query(FacultyListCD.filter(), flags={"services": ["catalog"]})
async def back_to_faculties(
        callback: CallbackQuery,
        user: User,
        catalog_query_service: CatalogQueryService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} went back to the faculty list")
    await render_faculties(message_manager, catalog_query_service)
    await callback.answer()


@router.callback_query(
    FacultyCD.filter(),
    flags={"services": ["catalog"]},
)
async def faculty_select(
        callback: CallbackQuery,
        callback_data: FacultyCD,
        user: User,
        catalog_query_service: CatalogQueryService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} selected faculty {callback_data.id}")

    await announce_faculty(message_manager, callback_data.name)
    await show_courses(
        message_manager,
        catalog_query_service,
        faculty_id=callback_data.id,
        faculty_code=callback_data.code,
    )
    await callback.answer()


@router.callback_query(CourseListCD.filter(), flags={"services": ["catalog"]})
async def back_to_courses(
        callback: CallbackQuery,
        callback_data: CourseListCD,
        user: User,
        catalog_query_service: CatalogQueryService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} went back to the course list")
    await show_courses(
        message_manager,
        catalog_query_service,
        faculty_id=callback_data.faculty_id,
        faculty_code=callback_data.faculty_code,
        clear_previous=True,
    )
    await callback.answer()


@router.callback_query(
    CourseCD.filter(),
    flags={"services": ["catalog"]},
)
async def course_select(
        callback: CallbackQuery,
        callback_data: CourseCD,
        user: User,
        catalog_query_service: CatalogQueryService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} selected course {callback_data.id}")

    await announce_course(message_manager, callback_data.name)
    await show_groups(
        message_manager,
        catalog_query_service,
        course_id=callback_data.id,
        faculty_id=callback_data.faculty_id,
        faculty_code=callback_data.faculty_code,
    )
    await callback.answer()


@router.callback_query(
    GroupCD.filter(),
    flags={"services": ["rating"]},
)
async def group_select(
        callback: CallbackQuery,
        *,
        callback_data: GroupCD,
        state: FSMContext,
        user: User,
        user_service: UserService,
        schedule_service: ScheduleService,
        rating_service: RatingService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} selected group {callback_data.id}")

    text = MessageManager.format_text(messages.registration.group_selected, group_name=callback_data.name)
    await message_manager.send_message(text)

    await user_service.register_user(user, group_id=callback_data.id)
    await state.clear()

    logger.info(f"User {user.id} completed registration")

    schedule_text = await get_schedule_text(
        group_name=callback_data.name,
        faculty=callback_data.faculty_code,
        faculty_id=callback_data.faculty_id,
        schedule_service=schedule_service,
        rating_service=rating_service,
        day=datetime.now(tz=MSK_TZ).date(),
        day_str="сегодня",
        is_today=True,
    )
    await message_manager.send_message(text=schedule_text, reply_markup=get_main_kb())
    await callback.answer()
