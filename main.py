import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis

from app.database import init_db
from app.handlers import register_handlers
from app.middlewares import register_middlewares
from app.services import ScheduleService, AiService
from app.schedule import ScheduleParser, ScheduleUpdater


async def main():
    init_db()
    schedule_service = ScheduleService()
    ai_service = AiService()
    parser = ScheduleParser(
        "https://docs.google.com/spreadsheets/d/1rlpvp-aGnJor98piGlejZ-talaUclG8aZWZM9wSt6qo/edit?gid=239775900#gid=239775900")
    ScheduleUpdater(schedule_service, parser, interval=600)

    bot = Bot(token=os.getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher(storage=RedisStorage(Redis()))
    register_handlers(dp)
    register_middlewares(dp, schedule_service, ai_service)
    # await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
