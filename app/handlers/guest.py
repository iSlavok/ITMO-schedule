from datetime import date

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database import User, Role
from app.filters import RoleFilter
from app.handlers.user import send_schedule
from app.keyboards.guest import get_course_keyboard, get_group_keyboard
from app.services import GuestService, UserService, ScheduleService
from app.states import RegisterStates

router = Router()
router.message.filter(RoleFilter(Role.GUEST))
router.callback_query.filter(RoleFilter(Role.GUEST))


@router.message(
    StateFilter(None),
    flags={"services": ["guest"]}
)
async def start_registration(message: Message, state: FSMContext, guest_service: GuestService):
    keyboard = get_course_keyboard(guest_service.get_all_courses())
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
    keyboard = get_group_keyboard(guest_service.get_course_groups(course_id))
    await callback.message.edit_text("Выберите группу", reply_markup=keyboard)
    await state.set_state(RegisterStates.GROUP_SELECT)


@router.callback_query(
    F.data.startswith("group_"),
    StateFilter(RegisterStates.GROUP_SELECT),
    flags={"services": ["schedule"]}
)
async def group_select(callback: CallbackQuery, state: FSMContext, user: User, user_service: UserService, schedule_service: ScheduleService):
    group_id = int(callback.data.split("_")[1])
    user_service.register_user(user, group_id)
    await send_schedule(callback.message, user, schedule_service, state, date.today(), "сегодня", is_today=True)
    await state.clear()


@router.message(~StateFilter(None))
async def on_message(message: Message, state: FSMContext):
    await message.delete()
    await state.clear()
