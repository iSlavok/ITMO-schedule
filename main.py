import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from loguru import logger
from redis.asyncio.client import Redis

from app.config import env_config
from app.database import close_db, init_db
from app.enums import FacultyCode
from app.schedule import CtScheduleParser, DatedScheduleBuilder, ScheduleParser, ScheduleUpdater
from app.services.ai_service import AiService
from app.services.lecturer_service import LecturerService
from app.services.schedule_service import ScheduleService
from bot.handlers import (
    admin_router,
    rating_list_router,
    rating_router,
    registration_router,
    schedule_router,
    settings_router,
    schedule_jobs
)
from bot.middlewares import MessageManagerMiddleware, ServicesMiddleware, UserMiddleware
from bot.utils import patch_bot_limited_send


async def main() -> None:
    await init_db()
    schedule_service = ScheduleService()
    ai_service = AiService()
    lecturer_service = LecturerService()
    schedule_updaters = [
        ScheduleUpdater(
            schedule_service=schedule_service,
            schedule_parser=ScheduleParser(spreadsheet_key=env_config.SPREADSHEET_ID),
            faculty=FacultyCode.PHYSICS,
            lecturer_service=lecturer_service,
            dated_schedule_builder=DatedScheduleBuilder(ai_service=ai_service),
            interval=600,
        ),
        ScheduleUpdater(
            schedule_service=schedule_service,
            schedule_parser=CtScheduleParser(
                sheet_key=env_config.CT_SHEET_KEY,
                sheet_gid=env_config.CT_SHEET_GID,
            ),
            faculty=FacultyCode.CT,
            lecturer_service=lecturer_service,
            interval=600,
        ),
    ]

    for updater in schedule_updaters:
        await updater.update_schedule()
        updater.start_update_loop()

    try:
        await start_bot(schedule_service, ai_service)
    finally:
        for updater in schedule_updaters:
            await updater.stop()
        await close_db()


async def start_bot(schedule_service: ScheduleService, ai_service: AiService) -> None:
    logger.info("Starting Telegram bot...")
    bot = Bot(
        token=env_config.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    storage = RedisStorage(
        redis=Redis(
            host=env_config.REDIS_HOST,
            port=env_config.REDIS_PORT,
        ),
        key_builder=DefaultKeyBuilder(
            with_destiny=True,
            with_bot_id=True,
        ),
    )
    dp = Dispatcher(storage=storage)

    patch_bot_limited_send(bot, 15)

    dp["ai_service"] = ai_service
    dp["schedule_service"] = schedule_service

    schedule_jobs(bot=bot, schedule_service=schedule_service)

    dp.update.outer_middleware(UserMiddleware())
    dp.message.middleware(ServicesMiddleware())
    dp.callback_query.middleware(ServicesMiddleware())
    dp.message.middleware(MessageManagerMiddleware(bot=bot))
    dp.callback_query.middleware(MessageManagerMiddleware(bot=bot))

    dp.include_router(admin_router)
    dp.include_router(registration_router)
    dp.include_router(rating_list_router)
    dp.include_router(rating_router)
    dp.include_router(settings_router)
    dp.include_router(schedule_router)

    commands = [
        BotCommand(command="settings", description="Настройки"),
    ]
    await bot.set_my_commands(commands=commands)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
