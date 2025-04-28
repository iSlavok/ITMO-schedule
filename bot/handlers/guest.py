from contextlib import suppress
from datetime import date

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.enums import UserRole
from bot.filters import RoleFilter
from bot.handlers.user import send_schedule
from bot.keyboards.guest import get_course_keyboard, get_group_keyboard
from bot.models import User
from bot.services import GuestService, UserService, ScheduleService, RatingService
from bot.states import RegisterStates

router = Router()
router.message.filter(RoleFilter(UserRole.GUEST))
router.callback_query.filter(RoleFilter(UserRole.GUEST))


@router.message(
    StateFilter(None),
    flags={"services": ["guest"]}
)
async def start_registration(message: Message, state: FSMContext, guest_service: GuestService):
    keyboard = get_course_keyboard(await guest_service.get_all_courses())
    await message.delete()
    await message.answer("Выберите курс", reply_markup=keyboard)
    await state.set_state(RegisterStates.COURSE_SELECT)


@router.callback_query(
    F.data.startswith("course_"),
    StateFilter(RegisterStates.COURSE_SELECT),
    flags={"services": ["guest"]}
)
async def course_select(callback: CallbackQuery, state: FSMContext, guest_service: GuestService):
    course_id = int(callback.data.split("_")[1])
    keyboard = get_group_keyboard(await guest_service.get_course_groups(course_id))
    await callback.message.edit_text("Выберите группу", reply_markup=keyboard)
    await state.set_state(RegisterStates.GROUP_SELECT)


@router.callback_query(
    F.data.startswith("group_"),
    StateFilter(RegisterStates.GROUP_SELECT),
    flags={"services": ["schedule", "rating"]}
)
async def group_select(callback: CallbackQuery, state: FSMContext, user: User, user_service: UserService,
                       schedule_service: ScheduleService, rating_service: RatingService):
    group_id = int(callback.data.split("_")[1])
    await user_service.register_user(user, group_id)
    with suppress(Exception):
        await callback.answer()
        await callback.message.delete()
    await state.clear()
    await send_schedule(callback.message, user, schedule_service, rating_service, state, date.today(), "сегодня", is_today=True)


@router.message(~StateFilter(None))
async def on_message(message: Message, state: FSMContext):
    await message.delete()
    await state.clear()
