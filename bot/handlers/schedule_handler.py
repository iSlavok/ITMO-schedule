from datetime import date, timedelta
from typing import Iterable

from aiogram import Router, F
from aiogram.filters import or_f

from bot.config import messages
from bot.enums import UserRole
from bot.filters import RoleFilter
from bot.keyboards import get_main_kb
from bot.models import User, Group
from bot.schedule import Lesson
from bot.services import ScheduleService, RatingService, MessageManager, AiService

router = Router(name="schedule_router")

router.message.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))
router.callback_query.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))


@router.message(
    F.text == "Сегодня",
    flags={"services": ["schedule", "rating"]},
)
async def today_schedule(_, user: User, schedule_service: ScheduleService, rating_service: RatingService,
                         message_manager: MessageManager):
    group: Group = user.group
    schedule_text = await get_schedule_text(
        group_name=group.name,
        schedule_service=schedule_service,
        rating_service=rating_service,
        day=date.today(),
        day_str="сегодня",
        is_today=True
    )
    await message_manager.send_message(text=schedule_text, reply_markup=get_main_kb())


@router.message(
    F.text == "Завтра",
    flags={"services": ["schedule", "rating"]},
)
async def tomorrow_schedule(_, user: User, schedule_service: ScheduleService, rating_service: RatingService,
                            message_manager: MessageManager):
    group: Group = user.group
    schedule_text = await get_schedule_text(
        group_name=group.name,
        schedule_service=schedule_service,
        rating_service=rating_service,
        day=date.today() + timedelta(days=1),
        day_str="завтра"
    )
    await message_manager.send_message(text=schedule_text, reply_markup=get_main_kb())


@router.message(
    F.text.as_("date_text"),
    flags={"services": ["schedule", "rating", "ai"]},
)
async def schedule_by_date(_, user: User, schedule_service: ScheduleService, rating_service: RatingService,
                           message_manager: MessageManager, ai_service: AiService, date_text: str):
    day = await ai_service.date_parsing(date_text)
    group: Group = user.group
    schedule_text = await get_schedule_text(
        group_name=group.name,
        schedule_service=schedule_service,
        rating_service=rating_service,
        day=day,
        day_str=day.strftime("%Y-%m-%d")
    )
    await message_manager.send_message(text=schedule_text, reply_markup=get_main_kb())


async def get_schedule_text(group_name: str, schedule_service: ScheduleService, rating_service: RatingService,
                            day: date, day_str: str, is_today: bool = False) -> str:
    schedule = schedule_service.get_schedule(day, group_name)
    if schedule is None:
        raise ValueError("Schedule not found")
    return await _schedule_to_text(schedule, day_str, schedule_service, rating_service, is_today=is_today)


async def _schedule_to_text(schedule: Iterable[Lesson], day: str, schedule_service: ScheduleService,
                            rating_service: RatingService, is_today: bool = False) -> str:
    current, is_waiting = 0, False
    if is_today:
        current, is_waiting = schedule_service.get_current_lesson()
    text = MessageManager.format_text(messages.schedule.header, day=day)
    for lesson in schedule:
        text += await _lesson_to_text(lesson=lesson, current_lesson=current, is_waiting=is_waiting,
                                      rating_service=rating_service)
    return text


async def _lesson_to_text(lesson: Lesson, current_lesson: int, is_waiting: bool, rating_service: RatingService) -> str:
    lesson_message = messages.schedule.lesson
    status_emoji = _get_lesson_status_emoji(lesson_number=lesson.number, current_lesson=current_lesson,
                                            is_waiting=is_waiting)
    text = MessageManager.format_text(lesson_message.number, status_emoji=status_emoji,
                                      time=_times[lesson.number - 1], number=lesson.number)
    text += "\n" + MessageManager.format_text(lesson_message.name, name=lesson.name)
    if lesson.type:
        text += MessageManager.format_text(lesson_message.type, type=lesson.type)
    text += "\n"
    if lesson.lecturer:
        rating = await rating_service.get_lecturer_rating(lesson.lecturer)
        emoji = _get_rating_emoji(rating)
        text += MessageManager.format_text(lesson_message.lecturer, emoji=emoji, name=lesson.lecturer)
        if rating is not None:
            text += MessageManager.format_text(lesson_message.lecturer_rating, rating=rating)
        text += "\n"
    if lesson.room:
        text += MessageManager.format_text(lesson_message.room, room=lesson.room)
    text += lesson_message.end
    return text


def _get_lesson_status_emoji(lesson_number: int, current_lesson: int, is_waiting: bool) -> str:
    if lesson_number == current_lesson:
        return "🔴" if is_waiting else "🟠"
    elif lesson_number < current_lesson:
        return "✅"
    else:
        return "🕒"


def _get_rating_emoji(rating: float | None) -> str:
    if rating is None or rating >= 4.5:
        return "👨"
    elif rating >= 4.0:
        return "👨🏽"
    elif rating >= 3.5:
        return "👨🏾"
    elif rating >= 2.0:
        return "🌚"
    else:
        return "🤡"


_times: list[str] = [
    "8.10-9.40",
    "9.50-11.20",
    "11.30-13.00",
    "13.30-15.00",
    "15.30-17.00",
    "17.10-18.40",
    "18:40-20:10",
]
