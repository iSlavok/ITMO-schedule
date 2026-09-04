from datetime import datetime

import pytz
from aiogram import F, Router
from aiogram.filters import Command, or_f
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from loguru import logger

from app.enums import UserRole
from app.models import User
from app.schemas import UserSettings
from app.services.catalog_query_service import CatalogQueryService
from app.services.rating_service import RatingService
from app.services.schedule_service import ScheduleService
from app.services.user_service import UserService
from bot.callback_data import CourseCD, CourseListCD, FacultyCD, FacultyListCD, GroupCD
from bot.config import messages
from bot.filters import RoleFilter
from bot.keyboards import get_main_kb, get_user_setting_kb
from bot.services import MessageManager
from bot.utils import (
    announce_course,
    announce_faculty,
    get_schedule_text,
    get_user_group,
    render_faculties,
    show_courses,
    show_groups,
)

router = Router(name="settings_router")
router.message.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))
router.callback_query.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))

MSK_TZ = pytz.timezone("Europe/Moscow")

BACK_TO_SETTINGS = "settings_menu"


def _read_group_labels(user: User) -> tuple[str, str, str]:
    """Read the group off the user while its relations are still loaded.

    A commit that refreshes the user drops the eager loads the middleware asked
    for, and the reload the next access would need cannot run on an async
    session. So the labels are taken before anything writes.
    """
    group = get_user_group(user)
    return group.faculty.name, group.course.name, group.name


def _settings_text_and_kb(
        user: User,
        group_labels: tuple[str, str, str],
) -> tuple[str, InlineKeyboardMarkup]:
    faculty_name, course_name, group_name = group_labels
    user_settings = UserSettings(rating_notifications=user.rating_notifications)
    text = MessageManager.format_text(
        messages.settings.main,
        faculty_name=faculty_name,
        course_name=course_name,
        group_name=group_name,
        rating_notifications_status="✅ Включены" if user_settings.rating_notifications else "❌ Выключены",
    )
    return text, get_user_setting_kb(user_settings)


@router.message(Command("settings"))
async def get_settings_menu(_: Message, message_manager: MessageManager, user: User) -> None:
    logger.info(f"User {user.id} opened settings menu")
    text, keyboard = _settings_text_and_kb(user, _read_group_labels(user))
    await message_manager.send_message(text, reply_markup=keyboard)


@router.callback_query(F.data == BACK_TO_SETTINGS)
async def open_settings_menu(query: CallbackQuery, message_manager: MessageManager, user: User) -> None:
    logger.info(f"User {user.id} went back to the settings menu")
    text, keyboard = _settings_text_and_kb(user, _read_group_labels(user))
    await message_manager.edit_message(text, reply_markup=keyboard)
    await query.answer()


@router.callback_query(F.data == "settings_rating_notifications")
async def toggle_rating_notifications(
    query: CallbackQuery,
    message_manager: MessageManager,
    user_service: UserService,
    user: User,
) -> None:
    group_labels = _read_group_labels(user)
    user = await user_service.change_settings(user=user, rating_notifications=not user.rating_notifications)
    logger.info(f"User {user.id} changed rating notifications to {user.rating_notifications}")

    text, keyboard = _settings_text_and_kb(user, group_labels)
    await message_manager.edit_message(text, reply_markup=keyboard)
    await query.answer()


@router.callback_query(F.data == "change_group", flags={"services": ["catalog"]})
async def start_group_change(
        query: CallbackQuery,
        user: User,
        catalog_query_service: CatalogQueryService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} started changing their group")
    await render_faculties(message_manager, catalog_query_service, back_callback_data=BACK_TO_SETTINGS)
    await query.answer()


@router.callback_query(FacultyListCD.filter(), flags={"services": ["catalog"]})
async def back_to_faculties(
        callback: CallbackQuery,
        user: User,
        catalog_query_service: CatalogQueryService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} went back to the faculty list")
    await render_faculties(message_manager, catalog_query_service, back_callback_data=BACK_TO_SETTINGS)
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
    logger.info(f"User {user.id} selected faculty {callback_data.id} to change their group")

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
    logger.info(f"User {user.id} selected course {callback_data.id} to change their group")

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
        user: User,
        user_service: UserService,
        schedule_service: ScheduleService,
        rating_service: RatingService,
        message_manager: MessageManager,
) -> None:
    logger.info(f"User {user.id} changed their group to {callback_data.id}")

    text = MessageManager.format_text(messages.settings.group_changed, group_name=callback_data.name)
    await message_manager.send_message(text)

    await user_service.change_group(user, group_id=callback_data.id)

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
