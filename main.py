import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis

from app.config import env_config
from app.database import close_db, init_db
from app.schedule import ScheduleParser, ScheduleUpdater
from app.services.ai import AiService
from app.services.schedule import ScheduleService
from bot.handlers import register_handlers
from bot.middlewares import register_middlewares


async def main() -> None:
    await init_db()
    schedule_service = ScheduleService()
    ai_service = AiService()
    parser = ScheduleParser(
        "https://docs.google.com/spreadsheets/d/1heK_XfQjFycJY7yYjaYefjYcDbZ5_TtIkNTMyKQG1ek")
    ScheduleUpdater(schedule_service, parser, interval=600)

    bot = Bot(token=env_config.BOT_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode="HTML"))
    storage = RedisStorage(redis=Redis(host=env_config.REDIS_HOST, port=env_config.REDIS_PORT),
                           key_builder=DefaultKeyBuilder(with_destiny=True, with_bot_id=True))
    dp = Dispatcher(storage=storage)
    register_handlers(dp)
    register_middlewares(dp, schedule_service, ai_service, bot)
    await dp.start_polling(bot)
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())
