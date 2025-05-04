from datetime import date

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.callback_data import CourseCD, GroupCD
from bot.config import messages
from bot.enums import UserRole
from bot.filters import RoleFilter
from bot.handlers.schedule_handler import get_schedule_text
from bot.keyboards import get_course_keyboard, get_group_keyboard, get_main_kb
from bot.models import User
from bot.services import GuestService, UserService, ScheduleService, RatingService, MessageManager
from bot.states import RegisterStates

router = Router()
router.message.filter(RoleFilter(UserRole.GUEST))
router.callback_query.filter(RoleFilter(UserRole.GUEST))


@router.message(
    StateFilter(None),
    flags={"services": ["guest"]}
)
async def start_registration(_, state: FSMContext, guest_service: GuestService, message_manager: MessageManager):
    courses = await guest_service.get_all_courses()
    keyboard = get_course_keyboard(courses)
    await message_manager.send_message(messages.registration.course_request, reply_markup=keyboard)
    await state.set_state(RegisterStates.COURSE_SELECT)


@router.callback_query(
    CourseCD.filter(),
    StateFilter(RegisterStates.COURSE_SELECT),
    flags={"services": ["guest"]}
)
async def course_select(callback: CallbackQuery, callback_data: CourseCD, state: FSMContext,
                        guest_service: GuestService, message_manager: MessageManager):
    text = MessageManager.format_text(messages.registration.course_selected, course_name=callback_data.name)
    await message_manager.send_message(text)
    groups = await guest_service.get_course_groups(callback_data.id)
    keyboard = get_group_keyboard(groups)
    await message_manager.send_message(messages.registration.group_request, clear_previous=False, reply_markup=keyboard)
    await state.set_state(RegisterStates.GROUP_SELECT)
    await callback.answer()


@router.callback_query(
    GroupCD.filter(),
    StateFilter(RegisterStates.GROUP_SELECT),
    flags={"services": ["schedule", "rating"]}
)
async def group_select(callback: CallbackQuery, callback_data: GroupCD, state: FSMContext, user: User,
                       user_service: UserService, schedule_service: ScheduleService, rating_service: RatingService,
                       message_manager: MessageManager):
    text = MessageManager.format_text(messages.registration.group_selected, group_name=callback_data.name)
    await message_manager.send_message(text)
    await user_service.register_user(user, group_id=callback_data.id)
    await state.clear()
    schedule_text = await get_schedule_text(
        group_name=callback_data.name,
        schedule_service=schedule_service,
        rating_service=rating_service,
        day=date.today(),
        day_str="сегодня",
        is_today=True
    )
    await message_manager.send_message(text=schedule_text, reply_markup=get_main_kb())
    await callback.answer()


@router.message(~StateFilter(None))
async def on_message(message: Message, state: FSMContext):
    await message.delete()
    await state.clear()
