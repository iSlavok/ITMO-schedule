from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database.enums import Role
from app.filters.role import RoleFilter
from app.keyboards.guest import get_course_keyboard, get_group_keyboard
from app.services.guest import GuestService
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
    course_name = guest_service.get_course_name_by_id(course_id)
    await state.update_data(course_name=course_name)
    keyboard = get_group_keyboard(guest_service.get_course_groups(course_id))
    await callback.message.edit_text("Выберите группу", reply_markup=keyboard)
    await state.set_state(RegisterStates.GROUP_SELECT)


@router.callback_query(F.data.startswith("group_"), StateFilter(RegisterStates.GROUP_SELECT), flags={"required_data": ["guest_service"]})
async def group_select(callback: CallbackQuery, state: FSMContext, guest_service: GuestService):
    group_id = int(callback.data.split("_")[1])
    group_name = guest_service.get_group_name_by_id(group_id)
    await state.update_data(group_name=group_name)
    data = await state.get_data()
    await callback.message.edit_text(f"Вы выбрали курс: {data.get('course_name')}\nГруппа: {data.get('group_name')}")
    await state.clear()


@router.message(~StateFilter(None))
async def on_message(message: Message):
    await message.delete()
