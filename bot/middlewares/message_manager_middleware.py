from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware, Bot, types
from aiogram.types import TelegramObject

from bot.services import MessageManager

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext


class MessageManagerMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        super().__init__()

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: dict[str, Any]) -> dict[str, Any]:
        state: FSMContext = data.get("state")
        if not state:
            return await handler(event, data)
        if isinstance(event, types.Message):
            message_manager = await MessageManager.from_message(self.bot, event, state)
        elif isinstance(event, types.CallbackQuery):
            message_manager = await MessageManager.from_callback(self.bot, event, state)
        else:
            return await handler(event, data)
        data["message_manager"] = message_manager
        return await handler(event, data)
