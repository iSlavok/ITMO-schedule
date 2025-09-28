from datetime import date

from app.schemas import Lesson
from app.services.exceptions import ScheduleNotLoadedError
from app.services.rating_service import RatingService
from app.services.schedule_service import ScheduleService
from bot.config import messages
from bot.services import MessageManager

TIMES: list[str] = [
    "8.10-9.40",
    "9.50-11.20",
    "11.30-13.00",
    "13.30-15.00",
    "15.30-17.00",
    "17.10-18.40",
    "18:50-20:20",
]


async def get_schedule_text(
        schedule_service: ScheduleService,
        rating_service: RatingService,
        group_name: str,
        day: date,
        day_str: str,
        *, is_today: bool = False,
) -> str:
    try:
        schedule = schedule_service.get_schedule(day, group_name)
    except ScheduleNotLoadedError:
        return "⚠️ Расписание еще не загружено. Пожалуйста, попробуйте позже."

    return await _schedule_to_text(
        schedule=schedule,
        schedule_service=schedule_service,
        rating_service=rating_service,
        day=day_str,
        is_today=is_today,
    )


async def _schedule_to_text(
        schedule: list[Lesson],
        schedule_service: ScheduleService,
        rating_service: RatingService,
        day: str,
        *, is_today: bool = False,
) -> str:
    text = MessageManager.format_text(messages.schedule.header, day=day)

    current, is_waiting = 0, False
    if is_today:
        current, is_waiting = schedule_service.get_current_lesson()

    lecturer_names = [lesson.lecturer for lesson in schedule if lesson.lecturer]
    lecturer_ratings = await rating_service.get_lecturers_rating(lecturer_names)

    for lesson in schedule:
        text += _lesson_to_text(
            lesson=lesson,
            current_lesson=current,
            lecturer_ratings=lecturer_ratings,
            is_waiting=is_waiting,
        )
    return text


def _lesson_to_text(
        lesson: Lesson,
        current_lesson: int,
        lecturer_ratings: dict[str, float],
        *, is_waiting: bool,
) -> str:
    lesson_message = messages.schedule.lesson
    status_emoji = _get_lesson_status_emoji(
        lesson_number=lesson.number,
        current_lesson=current_lesson,
        is_waiting=is_waiting,
    )
    text = MessageManager.format_text(
        lesson_message.number,
        status_emoji=status_emoji,
        time=TIMES[lesson.number - 1],
        number=lesson.number,
    )

    text += "\n" + MessageManager.format_text(lesson_message.name, name=lesson.name)
    if lesson.type:
        text += MessageManager.format_text(lesson_message.type, type=lesson.type)
    text += "\n"

    if lesson.lecturer:
        rating = lecturer_ratings.get(lesson.lecturer)
        emoji = _get_rating_emoji(rating)
        text += MessageManager.format_text(lesson_message.lecturer, emoji=emoji, name=lesson.lecturer)
        if rating is not None:
            text += MessageManager.format_text(lesson_message.lecturer_rating, rating=round(rating, 1))
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
    if rating is None or rating >= 8.5:  # noqa: PLR2004
        return "👨"
    if rating >= 7.5:  # noqa: PLR2004
        return "👨🏽"
    if rating >= 6.5:  # noqa: PLR2004
        return "👨🏾"
    if rating >= 4.0:  # noqa: PLR2004
        return "🌚"
    return "🤡"


