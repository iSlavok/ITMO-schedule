from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database import User
from app.database.enums import Role
from app.filters.role import RoleFilter
from app.keyboards.guest import get_course_keyboard, get_group_keyboard
from app.services.guest import GuestService
from app.services.user import UserService
from app.states.register import RegisterStates

router = Router()
router.message.filter(RoleFilter(Role.GUEST))
router.callback_query.filter(RoleFilter(Role.GUEST))


@router.message(StateFilter(None), flags={"required_data": ["guest_service"]})
async def start_registration(message: Message, state: FSMContext, guest_service: GuestService):
    keyboard = get_course_keyboard(guest_service.get_all_courses())
    await message.delete()
    await message.answer("Выберите курс", reply_markup=keyboard)
    await state.set_state(RegisterStates.COURSE_SELECT)


@router.callback_query(F.data.startswith("course_"), StateFilter(RegisterStates.COURSE_SELECT), flags={"required_data": ["guest_service"]})
async def course_select(callback: CallbackQuery, state: FSMContext, guest_service: GuestService):
    course_id = int(callback.data.split("_")[1])
    keyboard = get_group_keyboard(guest_service.get_course_groups(course_id))
    await callback.message.edit_text("Выберите группу", reply_markup=keyboard)
    await state.set_state(RegisterStates.GROUP_SELECT)


@router.callback_query(F.data.startswith("group_"), StateFilter(RegisterStates.GROUP_SELECT))
async def group_select(callback: CallbackQuery, state: FSMContext, user: User, user_service: UserService):
    group_id = int(callback.data.split("_")[1])
    user_service.register_user(user, group_id)
    await state.clear()


@router.message(~StateFilter(None))
async def on_message(message: Message):
    await message.delete()
