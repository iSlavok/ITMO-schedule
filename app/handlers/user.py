from datetime import date, timedelta
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database import User, Role
from app.filters import RoleFilter
from app.keyboards.user import main_keyboard
from app.schedule import Lesson
from app.services import ScheduleService

router = Router()
router.message.filter(RoleFilter(Role.USER))


@router.message(
    F.text == "Сегодня",
    flags={"services": ["schedule"]}
)
async def today_schedule(message: Message, user: User, schedule_service: ScheduleService, state: FSMContext):
    await message.delete()
    today = date.today()
    schedule = schedule_service.get_schedule(today, user.group.name)
    if not schedule:
        return
    text = schedule_to_text(schedule, "сегодня", schedule_service, is_today=True)
    schedule_message = await message.answer(text, reply_markup=main_keyboard, parse_mode="html")
    data = await state.get_data()
    old_message = data.get("schedule_message_id")
    if old_message:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_message)
        except Exception:
            pass
    await state.update_data(schedule_message_id=schedule_message.message_id)


@router.message(
    F.text == "Завтра",
    flags={"services": ["schedule"]}
)
async def tomorrow_schedule(message: Message, user: User, schedule_service: ScheduleService, state: FSMContext):
    await message.delete()
    tomorrow = date.today() + timedelta(days=1)
    schedule = schedule_service.get_schedule(tomorrow, user.group.name)
    if not schedule:
        return
    text = schedule_to_text(schedule, "завтра", schedule_service)
    schedule_message = await message.answer(text, reply_markup=main_keyboard, parse_mode="html")
    data = await state.get_data()
    old_message = data.get("schedule_message_id")
    if old_message:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_message)
        except Exception:
            pass
    await state.update_data(schedule_message_id=schedule_message.message_id)


def schedule_to_text(schedule: list[Lesson], day: str, schedule_service: ScheduleService, is_today: bool = False):
    current, is_waiting = 0, False
    if is_today:
        current, is_waiting = schedule_service.get_current_lesson()
    text = (f"📆 <b>Расписание на {day}</b> 📆\n"
            "════════════════════════")
    for lesson in schedule:
        text += lesson_to_text(lesson, current, is_waiting)
    return text


def lesson_to_text(lesson: Lesson, current_lesson: int, is_waiting: bool):
    if lesson.number == current_lesson:
        if is_waiting:
            status_emoji = "🔴"
        else:
            status_emoji = "🟠"
    elif lesson.number < current_lesson:
        status_emoji = "✅"
    else:
        status_emoji = "🕒"
    text = f"\n\n{status_emoji} <b>{times[lesson.number - 1]}</b> | {lesson.number} пара\n"
    text += f"📚 {lesson.name}"
    if lesson.type:
        text += f" — {lesson.type}"
    text += "\n"
    if lesson.lecturer:
        text += f"👨 {lesson.lecturer} | ⭐️ 4.8\n"
    if lesson.room:
        text += f"🚪 Аудитория: <b>{lesson.room}</b>\n"
    text += "\n———————————————"
    return text


times = [
    "8.10-9.40",
    "9.50-11.20",
    "11.30-13.00",
    "13.30-15.00",
    "15.30-17.00",
    "17.10-18.40",
    "18:40-20:10",
]
