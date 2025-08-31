from datetime import date, datetime

import pytz
from google import genai
from google.genai.types import AutomaticFunctionCallingConfig, GenerateContentConfig, ThinkingConfig

from app.schemas import AiDateResponse
from app.services.schedule import is_even_week

MSK_TZ = pytz.timezone("Europe/Moscow")


class AiService:
    def __init__(self) -> None:
        self._client = genai.Client().aio

    async def date_parsing(self, message: str) -> date:
        today = datetime.now(tz=MSK_TZ).date()
        model = "gemini-2.5-flash-lite"
        generate_content_config = GenerateContentConfig(
            system_instruction=(
                f"Ты обрабатываешь запросы от пользователей.\n"
                f"Отвечай только датой в формате: YYYY-MM-DD, четность недели считай с 1 сентября 2025.\n"
                f"Сегодня: {today.strftime("%Y-%m-%d")}, {'четная' if is_even_week(today) else 'нечетная'} неделя."
            ),
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=AiDateResponse,
            automatic_function_calling=AutomaticFunctionCallingConfig(disable=True),
            thinking_config=ThinkingConfig(thinking_budget=0),
        )

        response = await self._client.models.generate_content(
            model=model,
            contents=message,
            config=generate_content_config,
        )
        date_response: AiDateResponse = response.parsed
        return date_response.date
