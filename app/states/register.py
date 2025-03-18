from aiogram.fsm.state import StatesGroup, State


class RegisterStates(StatesGroup):
    COURSE_SELECT = State()
    GROUP_SELECT = State()
