import asyncio
from datetime import date, timedelta

from google import genai
from google.genai import errors
from google.genai.types import Content, GenerateContentConfig, GenerateContentResponse, Part

from app.config import env_config
from app.services.exceptions import DateParsingError, ClientError
from app.services.schedule import is_even_week


class AiService:
    def __init__(self):
        self._client = genai.Client(
            api_key=env_config.GEMINI_API_KEY.get_secret_value(),
        )

    async def date_parsing(self, message: str) -> date:
        today = date.today()
        model = "gemini-2.0-flash"
        contents = [
            Content(
                role="user",
                parts=[
                    Part.from_text(text="Завтра"),
                ],
            ),
            Content(
                role="model",
                parts=[
                    Part.from_text(text=(today + timedelta(days=1)).strftime("%Y-%m-%d")),
                ],
            ),
            Content(
                role="user",
                parts=[
                    Part.from_text(text=message),
                ],
            ),
        ]
        generate_content_config = GenerateContentConfig(
            system_instruction=[
                Part.from_text(text=f"""Ты обрабатываешь запросы от пользователей.
                                        Отвечай только датой в формате: YYYY-MM-DD, четность недели считай с 1 сентября 2024
                                        Сегодня: {today.strftime("%Y-%m-%d")}, {'четная' if is_even_week(today) else 'нечетная'} неделя"""),
            ],
        )

        loop = asyncio.get_running_loop()
        try:
            response = await loop.run_in_executor(None, self.call_generate_content, model, contents,
                                                  generate_content_config)
            return date.fromisoformat(response.text.strip())
        except errors.ClientError as e:
            raise ClientError(e)
        except ValueError:
            raise DateParsingError

    def call_generate_content(self, model: str, contents: list[Content],
                              generate_content_config: GenerateContentConfig) -> GenerateContentResponse:
        return self._client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
