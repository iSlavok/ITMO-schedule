import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger
from redis.asyncio.client import Redis

from app.config import env_config
from app.database import close_db, init_db
from app.schedule import ScheduleParser, ScheduleUpdater
from app.services.ai_service import AiService
from app.services.schedule_service import ScheduleService
from bot.handlers import admin_router, registration_router, schedule_router, user_router
from bot.middlewares import MessageManagerMiddleware, ServicesMiddleware, UserMiddleware


async def main() -> None:
    await init_db()
    schedule_service = ScheduleService()
    ai_service = AiService()
    schedule_parser = ScheduleParser(spreadsheet_key=env_config.SPREADSHEET_ID)
    schedule_updater = ScheduleUpdater(schedule_service=schedule_service, schedule_parser=schedule_parser, interval=600)

    schedule_updater.update_schedule()
    schedule_updater.start_update_loop()

    try:
        await start_bot(schedule_service, ai_service)
    finally:
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

    dp["ai_service"] = ai_service
    dp["schedule_service"] = schedule_service

    dp.update.outer_middleware(UserMiddleware())
    dp.message.middleware(ServicesMiddleware())
    dp.callback_query.middleware(ServicesMiddleware())
    dp.message.middleware(MessageManagerMiddleware(bot=bot))
    dp.callback_query.middleware(MessageManagerMiddleware(bot=bot))

    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(registration_router)
    dp.include_router(schedule_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
