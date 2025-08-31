from collections.abc import Iterable
from datetime import date, datetime, timedelta

import pytz
from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.types import CallbackQuery, Message

from app.enums import UserRole
from app.models import Group, User
from app.schedule import Lesson
from app.services.ai import AiService
from app.services.exceptions import AiServiceError
from app.services.rating import RatingService
from app.services.schedule import ScheduleService
from bot.config import messages
from bot.filters import RoleFilter
from bot.keyboards import get_main_kb
from bot.services import MessageManager

router = Router(name="schedule_router")

router.message.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))
router.callback_query.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))

MSK_TZ = pytz.timezone("Europe/Moscow")


@router.message(
    F.text == "Сегодня",
    flags={"services": ["schedule", "rating"]},
)
@router.callback_query(
    F.data == "main",
    flags={"services": ["schedule", "rating"]},
)
async def today_schedule(_: Message | CallbackQuery, user: User, schedule_service: ScheduleService,
                         rating_service: RatingService, message_manager: MessageManager) -> None:
    group: Group = user.group
    schedule_text = await get_schedule_text(
        group_name=group.name,
        schedule_service=schedule_service,
        rating_service=rating_service,
        day=datetime.now(tz=MSK_TZ).date(),
        day_str="сегодня",
        is_today=True,
    )
    await message_manager.send_message(text=schedule_text, reply_markup=get_main_kb())


@router.message(
    F.text == "Завтра",
    flags={"services": ["schedule", "rating"]},
)
async def tomorrow_schedule(_: Message, user: User, schedule_service: ScheduleService, rating_service: RatingService,
                            message_manager: MessageManager) -> None:
    group: Group = user.group
    schedule_text = await get_schedule_text(
        group_name=group.name,
        schedule_service=schedule_service,
        rating_service=rating_service,
        day=datetime.now(tz=MSK_TZ).date() + timedelta(days=1),
        day_str="завтра",
    )
    await message_manager.send_message(text=schedule_text, reply_markup=get_main_kb())


@router.message(
    F.text.as_("date_text"),
    flags={"services": ["schedule", "rating", "ai"]},
)
async def schedule_by_date(message: Message, user: User, schedule_service: ScheduleService,  # noqa: PLR0913
                           rating_service: RatingService, message_manager: MessageManager, ai_service: AiService,
                           date_text: str) -> None:
    try:
        day = await ai_service.date_parsing(date_text)
    except AiServiceError:
        await message.delete()
        return
    group: Group = user.group
    schedule_text = await get_schedule_text(
        group_name=group.name,
        schedule_service=schedule_service,
        rating_service=rating_service,
        day=day,
        day_str=day.strftime("%Y-%m-%d"),
    )
    await message_manager.send_message(text=schedule_text, reply_markup=get_main_kb())
    return


async def get_schedule_text(group_name: str, schedule_service: ScheduleService, rating_service: RatingService,  # noqa: PLR0913
                            day: date, day_str: str, *, is_today: bool = False) -> str:
    schedule = schedule_service.get_schedule(day, group_name)
    if schedule is None:
        msg = "Schedule not found"
        raise ValueError(msg)
    return await _schedule_to_text(schedule, day_str, schedule_service, rating_service, is_today=is_today)


async def _schedule_to_text(schedule: Iterable[Lesson], day: str, schedule_service: ScheduleService,
                            rating_service: RatingService, *, is_today: bool = False) -> str:
    current, is_waiting = 0, False
    if is_today:
        current, is_waiting = schedule_service.get_current_lesson()
    text = MessageManager.format_text(messages.schedule.header, day=day)
    for lesson in schedule:
        text += await _lesson_to_text(lesson=lesson, current_lesson=current, is_waiting=is_waiting,
                                      rating_service=rating_service)
    return text


async def _lesson_to_text(lesson: Lesson, current_lesson: int, rating_service: RatingService, *,
                          is_waiting: bool) -> str:
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


def _get_lesson_status_emoji(lesson_number: int, current_lesson: int, *, is_waiting: bool) -> str:
    if lesson_number == current_lesson:
        return "🔴" if is_waiting else "🟠"
    if lesson_number < current_lesson:
        return "✅"
    return "🕒"


def _get_rating_emoji(rating: float | None) -> str:
    if rating is None or rating >= 4.5:  # noqa: PLR2004
        return "👨"
    if rating >= 4.0:  # noqa: PLR2004
        return "👨🏽"
    if rating >= 3.5:  # noqa: PLR2004
        return "👨🏾"
    if rating >= 2.0:  # noqa: PLR2004
        return "🌚"
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
