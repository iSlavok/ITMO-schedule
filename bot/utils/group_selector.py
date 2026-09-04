from app.enums import FacultyCode
from app.services.catalog_query_service import CatalogQueryService
from bot.config import messages
from bot.keyboards import get_course_keyboard, get_faculty_keyboard, get_group_keyboard
from bot.services import MessageManager


async def render_faculties(
        message_manager: MessageManager,
        catalog_query_service: CatalogQueryService,
        *,
        clear_previous: bool = True,
        back_callback_data: str | None = None,
) -> None:
    faculties = await catalog_query_service.get_all_faculties()
    keyboard = get_faculty_keyboard(faculties, back_callback_data=back_callback_data)
    await message_manager.send_message(
        messages.registration.faculty_request,
        clear_previous=clear_previous,
        reply_markup=keyboard,
    )


async def announce_faculty(message_manager: MessageManager, faculty_name: str) -> None:
    text = MessageManager.format_text(messages.registration.faculty_selected, faculty_name=faculty_name)
    await message_manager.send_message(text)


async def show_courses(
        message_manager: MessageManager,
        catalog_query_service: CatalogQueryService,
        *,
        faculty_id: int,
        faculty_code: FacultyCode,
        clear_previous: bool = False,
) -> None:
    courses = await catalog_query_service.get_faculty_courses(faculty_id)
    keyboard = get_course_keyboard(courses, faculty_id=faculty_id, faculty_code=faculty_code)
    await message_manager.send_message(
        text=messages.registration.course_request,
        clear_previous=clear_previous,
        reply_markup=keyboard,
    )


async def announce_course(message_manager: MessageManager, course_name: str) -> None:
    text = MessageManager.format_text(messages.registration.course_selected, course_name=course_name)
    await message_manager.send_message(text)


async def show_groups(
        message_manager: MessageManager,
        catalog_query_service: CatalogQueryService,
        *,
        course_id: int,
        faculty_id: int,
        faculty_code: FacultyCode,
        clear_previous: bool = False,
) -> None:
    groups = await catalog_query_service.get_course_groups(course_id, faculty_id=faculty_id)
    keyboard = get_group_keyboard(groups, faculty_id=faculty_id, faculty_code=faculty_code)
    await message_manager.send_message(
        text=messages.registration.group_request,
        clear_previous=clear_previous,
        reply_markup=keyboard,
    )
