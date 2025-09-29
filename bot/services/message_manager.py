import asyncio
import contextlib
from collections import defaultdict
from string import Template
from typing import Self

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

_user_locks = defaultdict(asyncio.Lock)


class MessageManager:
    def __init__(self, bot: Bot, chat_id: int, state: FSMContext, message: Message) -> None:
        self.bot = bot
        self.chat_id = chat_id
        self.state = state
        self.message = message
        self._lock = _user_locks[chat_id]

        self._bot_messages_key = "bot_messages"
        self._user_messages_key = "user_messages"

    @classmethod
    async def from_message(cls, bot: Bot, message: Message, state: FSMContext) -> Self:
        manager = cls(
            bot=bot,
            chat_id=message.chat.id,
            state=state,
            message=message,
        )
        await manager._add_user_message(message.message_id)
        return manager

    @classmethod
    async def from_callback(cls, bot: Bot, callback: CallbackQuery, state: FSMContext) -> Self:
        manager = cls(
            bot=bot,
            chat_id=callback.message.chat.id,
            state=state,
            message=callback.message,
        )
        await manager._add_bot_message(callback.message.message_id)
        return manager

    async def send_message(self, text: str, *, clear_previous: bool = True, **kwargs: object) -> Message:
        async with self._lock:
            message = await self.bot.send_message(chat_id=self.chat_id, text=text, **kwargs)
            if clear_previous:
                await self._clear_messages()
            await self._add_bot_message(message.message_id)
            return message

    async def edit_message(self, text: str, **kwargs: object) -> Message | bool:
        async with self._lock:
            bot_messages = await self._get_bot_messages()
            if not bot_messages:
                return await self.send_message(text, clear_previous=True, **kwargs)
            try:
                last_bot_msg_id = bot_messages[-1]
                logger.debug(f"Editing message {last_bot_msg_id} in chat {self.chat_id}")
                return await self.bot.edit_message_text(
                    text=text,
                    chat_id=self.chat_id,
                    message_id=last_bot_msg_id,
                    **kwargs,
                )
            except TelegramBadRequest:
                return await self.send_message(text, clear_previous=True, **kwargs)

    async def _get_bot_messages(self) -> list[int]:
        data = await self.state.get_data()
        return data.get(self._bot_messages_key, [])

    async def _get_user_messages(self) -> list[int]:
        data = await self.state.get_data()
        return data.get(self._user_messages_key, [])

    async def _add_bot_message(self, message_id: int) -> None:
        messages = await self._get_bot_messages()
        if message_id not in messages:
            messages.append(message_id)
            await self.state.update_data({self._bot_messages_key: messages})

    async def _add_user_message(self, message_id: int) -> None:
        async with self._lock:
            messages = await self._get_user_messages()
            if message_id not in messages:
                messages.append(message_id)
                await self.state.update_data({self._user_messages_key: messages})

    async def _clear_messages(self) -> None:
        bot_messages = await self._get_bot_messages()
        for msg_id in bot_messages:
            try:
                await self.bot.delete_message(self.chat_id, msg_id)
            except TelegramBadRequest:
                with contextlib.suppress(TelegramBadRequest):
                    await self.bot.edit_message_text(
                        chat_id=self.chat_id,
                        message_id=msg_id,
                        text="[Сообщение устарело]",
                    )
        user_messages = await self._get_user_messages()
        for msg_id in user_messages:
            with contextlib.suppress(TelegramBadRequest):
                await self.bot.delete_message(self.chat_id, msg_id)
        await self.state.update_data({
            self._bot_messages_key: [],
            self._user_messages_key: [],
        })

    @staticmethod
    def format_text(text: str, **kwargs: object) -> str:
        return Template(text).safe_substitute(**kwargs)
