import re

import gspread
from google.oauth2.service_account import Credentials

from app.enums import Weekday
from app.schemas import Lesson, Schedule

MULTIPLE_NEWLINES_PATTERN = re.compile(r"\n{2,}")
NUMBER_PATTERN = re.compile(r"\d+")
SPACE_PATTERN = re.compile(r"\s+")
SKIP_LESSON_PATTERN = re.compile(r"(?<!-)\b(?:[1-9]|[12]\d|3[01])\b(?!:\d{2})")
LECTURE_TYPE_PATTERN = re.compile(r"\b(лекция|практика|лабораторная|факультатив|ZOOM)\b", flags=re.IGNORECASE)
ROOM_PATTERN = re.compile(r"ауд(?:\.?\s*|\s+)(\d+)", flags=re.IGNORECASE)


WEEKDAY_REPLACE_MAP = {
    "ПОНЕДЕЛЬНИК": "monday",
    "ВТОРНИК": "tuesday",
    "СРЕДА": "wednesday",
    "ЧЕТВЕРГ": "thursday",
    "ПЯТНИЦА": "friday",
    "СУББОТА": "saturday",
}
WEEK_TYPE_REPLACE_MAP = {
    "нечетная неделя": "odd_week",
    "четная неделя": "even_week",
}
GROUP_NAME_REPLACE_MAP = {
    "3244-3345": "3244-3245",
}
LESSON_DATA_REPLACE_PATTERN = [
    (re.compile(r"лабораторные"), "лабораторная"),
    (re.compile(r"лаб"), "лабораторная"),
    (re.compile(r"лекции"), "лекция"),
    (re.compile(r"парктика"), "практика"),
    (re.compile(r"Линейная\nалгебра"), "Линейная алгебра"),
    (re.compile(r"\bКривосенко Ю\.(?!С)"), "Кривосенко Ю.С."),
    (re.compile(r"\bКоробков М\.(?!П)"), "Коробков М.П."),
    (re.compile(r"\bУздин В.М(?!\.)"), "Уздин В.М."),
    (re.compile(r"\bГросман М\.(?!В)"), "Гросман Д.В."),
    (re.compile(r"\bСвинцов М(?:\.?\s*В)?\.?"), "Свинцов М.В."),
    (re.compile(r"Сминов А.В."), "Смирнов А.В."),
    (re.compile(r"Математический анализ"), "Матанализ"),
    (re.compile(r"Физическая химия"), "Физхимия"),
    (re.compile(r"АНГЛИЙСКИЙ ЯЗЫК"), "Английский язык"),
    (re.compile(r"АНГЛИЙСКИЙ"), "Английский язык"),
    (re.compile(r"ВОЕННАЯ КАФЕДРА"), "Военная кафедра"),
    (re.compile(r"ИСТОРИЯ"), "История"),
    (re.compile(r"soft skills"), "Soft Skills"),
    (re.compile(r"Доп.главы статфизики"), "Доп. главы статфизики"),
    (re.compile(r"Математическая физика"), "Матфизика"),
    (re.compile(r"Теоретическая механика"), "Теормех"),
    (re.compile(r"Английский язык в профессиональной деятельности"), "Английский язык в проф. деятельности"),
    (re.compile(r"Дополнительные главы квантовой механики"), "Доп. главы квантмеха"),
    (re.compile(r"Машинное обучение в физических задачах"), "ML в физических задачах"),
]
SKIP_WORDS = [
    "с ноября",
    "ноябрь/декабрь",
]
NOT_SKIP_WORDS = [
    "ВТП",
]


class ScheduleParser:
    def __init__(self, spreadsheet_key: str) -> None:
        self._spreadsheet_key = spreadsheet_key
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_file("google-credentials.json", scopes=scope)
        self._gc: gspread.Client = gspread.authorize(credentials)
        self._worksheet: gspread.Worksheet | None = None
        self._values: list[list[str]] | None = None

    def parse(self) -> Schedule:
        self._parse_google_sheet()
        self._merge_cells()
        self._replace_values()
        schedule = self._extract_data()
        self._worksheet = None
        self._values = None
        return schedule

    def _parse_google_sheet(self) -> None:
        spreadsheet = self._gc.open_by_key(self._spreadsheet_key)
        self._worksheet = spreadsheet.get_worksheet(0)
        self._values = self._worksheet.get_all_values()

    def _merge_cells(self) -> None:
        sheet_id = self._worksheet.id
        sheets = self._worksheet.spreadsheet.fetch_sheet_metadata().get("sheets", [])
        merged_cells = next(
            (s.get("merges", []) for s in sheets if s.get("properties", {}).get("sheetId") == sheet_id),
            [],
        )

        for merge in merged_cells:
            sr, er = merge.get("startRowIndex"), merge.get("endRowIndex")
            sc, ec = merge.get("startColumnIndex"), merge.get("endColumnIndex")

            if sr < len(self._values) and sc < len(self._values[sr]):
                value = self._values[sr][sc]
                for r in range(sr, er):
                    if r >= len(self._values):
                        continue
                    row = self._values[r]
                    for c in range(sc, min(ec, len(row))):
                        row[c] = value

            target_row = sr + 1
            if target_row % 2 == 0 and 3 < target_row < len(self._values):  # noqa: PLR2004
                row = self._values[target_row]
                next_value = next((row[c] for c in range(sc, min(ec, len(row))) if row[c]), None)
                if next_value:
                    for c in range(sc, min(ec, len(row))):
                        row[c] = next_value

    def _replace_values(self) -> None:
        def fill_and_replace(row: list[str], replace_map: dict[str, str]) -> None:
            for i, value in enumerate(row[2:], 2):
                data_value = value.strip()
                if not data_value:
                    row[i] = row[i - 1]
                elif data_value in replace_map:
                    row[i] = replace_map[data_value]

        fill_and_replace(self._values[1], WEEK_TYPE_REPLACE_MAP)
        fill_and_replace(self._values[2], GROUP_NAME_REPLACE_MAP)

        self._values = [list(r) for r in zip(*self._values, strict=False)][:44]

        fill_and_replace(self._values[0], WEEKDAY_REPLACE_MAP)

    def _extract_data(self) -> Schedule:
        schedule = Schedule()
        for _i, row in enumerate(self._values[3:], 3):

            year = row[0].strip()
            week_type = row[1].strip()
            group = row[2].strip()

            for j, value in enumerate(row[3:], 3):
                if j % 2 == 0:
                    continue

                data_value = value
                second_value = row[j + 1] if j + 1 < len(row) else ""

                if ((re.search(SKIP_LESSON_PATTERN, data_value)
                        or any(skip_word in data_value.lower() for skip_word in SKIP_WORDS))
                        and not any(not_skip_word in data_value for not_skip_word in NOT_SKIP_WORDS)):
                    continue

                for pattern, repl in LESSON_DATA_REPLACE_PATTERN:
                    data_value = pattern.sub(repl, data_value)

                data_value = data_value.replace(",", "").replace('"', "")
                data_value = MULTIPLE_NEWLINES_PATTERN.sub("\n", data_value)

                room = self._extract_room(second_value)
                lecture_type, data_value = self._extract_lecture_type(data_value)
                name, lecturer = self._extract_name_and_lecturer(data_value)

                if (room is None) and (lecture_type is None) and (name is None) and (lecturer is None):
                    continue

                lesson_number = int(self._values[1][j+1])
                weekday = Weekday(self._values[0][j])

                schedule.add_lesson(
                    course=year,
                    group=group,
                    week_type=week_type,
                    weekday=weekday,
                    lesson=Lesson(
                        name=name,
                        room=room,
                        lecturer=lecturer,
                        type=lecture_type,
                        number=lesson_number,
                    ),
                )

        return schedule

    @staticmethod
    def _extract_room(value: str) -> int | None:
        room_match = re.search(NUMBER_PATTERN, value)
        return int(room_match.group()) if room_match else None

    @staticmethod
    def _extract_lecture_type(value: str) -> tuple[str | None, str]:
        lecture_types = re.findall(LECTURE_TYPE_PATTERN, value)
        lecture_type = lecture_types[0].lower() if lecture_types else None

        if lecture_type is not None:
            value = LECTURE_TYPE_PATTERN.sub("", value)
            value = MULTIPLE_NEWLINES_PATTERN.sub("\n", value)

        return lecture_type, value

    @staticmethod
    def _extract_name_and_lecturer(value: str) -> tuple[str | None, str | None]:
        parts = value.split("\n", 1)
        name = SPACE_PATTERN.sub(" ", parts[0]).strip(" ,\n") or None

        if len(parts) > 1:
            lecturer = SPACE_PATTERN.sub(
                repl=" ",
                string=parts[1].replace("\n", ", "),
            ).strip(" ,\n").lstrip(" .,") or None
        else:
            lecturer = None

        return name, lecturer
