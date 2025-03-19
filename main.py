import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis


from app.database import init_db
from app.handlers import register_handlers
from app.middlewares import register_middlewares
from app.services import ScheduleService
from app.schedule import ScheduleParser, ScheduleUpdater


async def main():
    init_db()
    service = ScheduleService()
    parser = ScheduleParser(
        "https://docs.google.com/spreadsheets/d/1rlpvp-aGnJor98piGlejZ-talaUclG8aZWZM9wSt6qo/edit?gid=239775900#gid=239775900")
    ScheduleUpdater(service, parser, interval=600)

    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=RedisStorage(Redis()))
    register_handlers(dp)
    register_middlewares(dp, service)
    # await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
