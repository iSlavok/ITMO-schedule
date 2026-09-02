import asyncio
from datetime import date, datetime

import pytz
from google import genai
from google.genai.types import AutomaticFunctionCallingConfig, GenerateContentConfig, ThinkingConfig, ThinkingLevel
from loguru import logger

from app.config import env_config
from app.schemas import AiDateResponse, AiNoteResponse
from app.services.schedule_service import ScheduleService

MSK_TZ = pytz.timezone("Europe/Moscow")

NOTE_PARSING_ATTEMPTS = 3
NOTE_PARSING_RETRY_DELAY = 2.0

NOTE_INSTRUCTION = """\
Ты разбираешь примечания из таблицы расписания университета.
Примечание относится к одной паре, которая по умолчанию идёт каждую неделю.

Учебный год начинается 1 сентября {start_year} года.
Даты без года: сентябрь-декабрь -> {start_year}, январь-август -> {end_year}.

Определи, что примечание делает с парой, и верни список операций:
- cancel: пары не будет в перечисленные даты
- only_on: пара бывает ТОЛЬКО в перечисленные даты
- from_date: пара идёт начиная с указанной даты (ровно одна дата)
- until_date: пара идёт до указанной даты включительно (ровно одна дата)
- override: пара идёт как обычно, но в указанные даты что-то меняется

only_on ставится ТОЛЬКО если примечание — голый список дат и больше ничего.
Если в примечании есть аудитория, преподаватель или название, это override, а не only_on.

Для override заполняй room, lecturer или name, если примечание их меняет,
и note, если это просто уточнение к паре (например, время начала).
Если у override нет дат, изменение действует всегда.

Примеры:
"1 сентября не будет" -> cancel, дата 1 сентября
"2 сентября ауд. 2530" -> override, дата 2 сентября, room=2530
"14, 28 ноября" -> only_on, даты 14 и 28 ноября
"с 23 сентября" -> from_date, дата 23 сентября
"с 16:00" -> override, без дат, note="с 16:00"

Не выдумывай даты, которых нет в тексте.
Если примечание непонятно или не относится к расписанию,
верни understood=false и пустой список операций.\
"""


class AiService:
    def __init__(self) -> None:
        self._client = genai.Client().aio
    async def date_parsing(self, message: str) -> date:
        today = datetime.now(tz=MSK_TZ).date()
        generate_content_config = GenerateContentConfig(
            system_instruction=(
                f"Ты обрабатываешь запросы от пользователей.\n"
                f"Отвечай только датой в формате: YYYY-MM-DD, "
                f"четность недели считай с 1 сентября {env_config.SEMESTER_START_YEAR}.\n"
                f"Сегодня: {today.strftime("%Y-%m-%d")}, "
                f"{'четная' if ScheduleService.is_even_week(today) else 'нечетная'} неделя."
            ),
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=AiDateResponse,
            automatic_function_calling=AutomaticFunctionCallingConfig(disable=True),
            thinking_config=ThinkingConfig(thinking_level=ThinkingLevel.MINIMAL)
        )

        response = await self._client.models.generate_content(
            model=env_config.AI_MODEL,
            contents=message,
            config=generate_content_config,
        )
        date_response: AiDateResponse = response.parsed
        return date_response.date

    async def note_parsing(self, note: str) -> AiNoteResponse | None:
        """Turn a schedule footnote into structured operations.

        Returns None when the model is unreachable or answers with something the
        schema cannot hold: the caller then leaves the lesson untouched.
        """
        generate_content_config = GenerateContentConfig(
            system_instruction=NOTE_INSTRUCTION.format(
                start_year=env_config.SEMESTER_START_YEAR,
                end_year=env_config.SEMESTER_START_YEAR + 1,
            ),
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=AiNoteResponse,
            automatic_function_calling=AutomaticFunctionCallingConfig(disable=True),
            thinking_config=ThinkingConfig(thinking_level=ThinkingLevel.MEDIUM)
        )

        for attempt in range(1, NOTE_PARSING_ATTEMPTS + 1):
            try:
                response = await self._client.models.generate_content(
                    model=env_config.AI_MODEL,
                    contents=note,
                    config=generate_content_config,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to parse note {note!r}, attempt {attempt}: {type(e).__name__}: {e}",
                )
            else:
                note_response: AiNoteResponse | None = response.parsed
                if note_response is not None:
                    return note_response
                logger.warning(f"No structured answer for note {note!r}, attempt {attempt}")

            if attempt < NOTE_PARSING_ATTEMPTS:
                await asyncio.sleep(NOTE_PARSING_RETRY_DELAY)

        return None
