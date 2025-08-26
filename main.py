import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis

from bot.config import env_config
from bot.database import init_db
from bot.handlers import register_handlers
from bot.middlewares import register_middlewares
from bot.services import ScheduleService, AiService
from bot.schedule import ScheduleParser, ScheduleUpdater


async def main():
    await init_db()
    schedule_service = ScheduleService()
    ai_service = AiService()
    parser = ScheduleParser(
        "https://docs.google.com/spreadsheets/d/1heK_XfQjFycJY7yYjaYefjYcDbZ5_TtIkNTMyKQG1ek")
    ScheduleUpdater(schedule_service, parser, interval=600)

    bot = Bot(token=env_config.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    storage = RedisStorage(redis=Redis(host=env_config.REDIS_HOST, port=env_config.REDIS_PORT),
                           key_builder=DefaultKeyBuilder(with_destiny=True, with_bot_id=True))
    dp = Dispatcher(storage=storage)
    register_handlers(dp)
    register_middlewares(dp, schedule_service, ai_service, bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
