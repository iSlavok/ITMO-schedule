from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.database import get_session
from app.repositories import LecturerRepository, RatingRepository, UserRepository
from app.schemas import Lesson
from app.services.rating_service import RatingService
from app.services.schedule_service import SCHEDULE_TIMES, ScheduleService
from app.services.user_service import UserService
from bot.config import messages
from bot.keyboards import get_add_rating_kb
from bot.services import MessageManager


def schedule_jobs(bot: Bot, schedule_service: ScheduleService) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    for i, (_, end) in enumerate(SCHEDULE_TIMES, start=1):
        logger.debug(f"Scheduling job for lesson {i} at {end.hour}:{end.minute}")

        utc_hour = (end.hour - 3) % 24
        scheduler.add_job(
            _start_notifications,
            "cron",
            day_of_week="mon-sat",
            hour=utc_hour,
            minute=end.minute,
            args=[bot, schedule_service, i],
        )

    scheduler.start()
    return scheduler


async def _start_notifications(bot: Bot, schedule_service: ScheduleService, lesson_number: int) -> None:
    logger.info(f"Starting notifications for lesson {lesson_number}")

    async with get_session() as session:
        user_repository = UserRepository(session)
        user_service = UserService(session, user_repository)
        users_by_group = await user_service.get_users_with_rating_notifications_by_group()

        rating_repository = RatingRepository(session)
        lecturer_repository = LecturerRepository(session)
        rating_service = RatingService(session, lecturer_repository, rating_repository)

        lecturers = await rating_service.get_all_lecturers()
        lecturer_ids_by_name = {lecturer.name: lecturer.id for lecturer in lecturers}

        today_rated_lecturers_by_user = await rating_service.get_all_today_rated_lecturer_by_user()

    logger.info(f"Found {sum(len(users) for users in users_by_group.values())} users to notify")

    successful_notifications = 0

    for group_name, users in users_by_group.items():
        scheduled_lessons = schedule_service.get_schedule(group_name)
        current_lesson = next((
            lesson
            for lesson in scheduled_lessons
            if lesson.number == lesson_number
        ), None)

        if current_lesson is None or not current_lesson.lecturer or current_lesson.lecturer not in lecturer_ids_by_name:
            continue

        lecturer_id = lecturer_ids_by_name[current_lesson.lecturer]

        for user in users:
            if user.id in today_rated_lecturers_by_user and lecturer_id in today_rated_lecturers_by_user[user.id]:
                continue

            try:
                await _send_user_notification(bot, user.telegram_id, current_lesson, lecturer_id)
            except TelegramAPIError:
                pass
            else:
                successful_notifications += 1

    logger.info(f"Sent {successful_notifications} notifications for lesson {lesson_number}")


async def _send_user_notification(bot: Bot, user_id: int, lesson: Lesson, lecturer_id: int) -> None:
    text = MessageManager.format_text(
        messages.notification.lecturer_rating,
        lesson_name=lesson.name,
        lecturer_name=lesson.lecturer,
    )
    await bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=get_add_rating_kb(lecturer_id, "main")
    )
