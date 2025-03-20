import asyncio
import os

from datetime import date, timedelta
from google import genai
from google.genai import types

from app.services.schedule import is_even_week


class AiService:
    def __init__(self):
        self._client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )

    async def date_parsing(self, message: str) -> date | None:
        today = date.today()
        model = "gemini-2.0-flash-lite"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="Завтра"),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text=(today + timedelta(days=1)).strftime("%Y-%m-%d")),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=message),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            system_instruction=[
                types.Part.from_text(text=f"""Ты обрабатываешь запросы от пользователей.
                                              Отвечай только датой в формате: YYYY-MM-DD, четность недели считай с 1 сентября 2024
                                              Сегодня: {today.strftime("%Y-%m-%d")}, {'четная' if is_even_week(today) else 'нечетная'} неделя"""),
            ],
        )

        loop = asyncio.get_running_loop()
        try:
            response = await loop.run_in_executor(None, self.call_generate_content, model, contents,
                                                  generate_content_config)
            return date.fromisoformat(response.text.strip())
        except ValueError:
            return None

    def call_generate_content(self, model: str, contents: list[types.Content],
                              generate_content_config: types.GenerateContentConfig) -> types.GenerateContentResponse:
        return self._client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )