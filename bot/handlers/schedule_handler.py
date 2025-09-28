from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.types import CallbackQuery, Message

from app.enums import UserRole
from app.models import Group, User
from app.services.ai_service import AiService
from app.services.exceptions import AiServiceError
from app.services.rating_service import RatingService
from app.services.schedule_service import ScheduleService
from bot.filters import RoleFilter
from bot.keyboards import get_main_kb
from bot.services import MessageManager
from bot.utils import get_schedule_text

router = Router(name="schedule_router")

router.message.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))
router.callback_query.filter(or_f(RoleFilter(UserRole.USER), RoleFilter(UserRole.ADMIN)))

MSK_ZONE = ZoneInfo("Europe/Moscow")


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
        day=datetime.now(tz=MSK_ZONE).date(),
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
        day=datetime.now(tz=MSK_ZONE).date() + timedelta(days=1),
        day_str="завтра",
    )
    await message_manager.send_message(text=schedule_text, reply_markup=get_main_kb())


@router.message(
    F.text.as_("date_text"),
    flags={"services": ["schedule", "rating", "ai"]},
)
async def schedule_by_date(  # noqa: PLR0913
        message: Message,
        user: User,
        schedule_service: ScheduleService,
        rating_service: RatingService,
        message_manager: MessageManager,
        ai_service: AiService,
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
