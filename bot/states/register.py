from aiogram.fsm.state import State, StatesGroup


class RegisterStates(StatesGroup):
    COURSE_SELECT = State()
    GROUP_SELECT = State()
