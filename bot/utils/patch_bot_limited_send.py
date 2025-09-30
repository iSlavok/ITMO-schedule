from aiogram import Bot
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType
from aiolimiter import AsyncLimiter


def patch_bot_limited_send(mybot: Bot, rate_limit: int = 15) -> None:
    limiter = AsyncLimiter(rate_limit, 1)

    original_call = mybot.session.make_request

    async def limited_call(
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,  # noqa: ASYNC109
    ) -> TelegramType:
        if method.__class__.__name__ in ["SendMessage", "EditMessageText", "SendPhoto", "SendDocument"]:
            async with limiter:
                return await original_call(bot, method, timeout)
        else:
            return await original_call(bot, method, timeout)

    mybot.session.make_request = limited_call
