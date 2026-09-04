"""Parser of the CT faculty schedule.

The sheet is published to the web, so it is read as rendered HTML rather than
through the Sheets API: there is no document id behind the publish link, and the
CSV export loses the merges and the hidden rows and columns this sheet relies on.

Layout (one sheet, one semester):
    row 0        group headers, one merged block of 4 columns per group;
                 the "Выбор" blocks at the tail are empty placeholders
    rows 2..     schedule body, grouped by weekday:
                     col 0  weekday abbreviation, merged over the whole day
                     col 2  lesson number, merged over the "н"/"ч" pair
                     col 3  lesson start time, implied by the number
                     col 4  week type: "н" (odd) / "ч" (even)
                 inside a group block: name, type, room, lecturer
    footer       credit-hour totals ("2+2", "0+0"), no weekday, skipped
"""

import re
from typing import Literal

from app.enums import FacultyCode, Weekday
from app.schedule.published_sheet import Sheet, fetch_published_sheet
from app.schemas import Lesson, LessonType, ParseResult

WEEKDAY_COLUMN = 0
LESSON_NUMBER_COLUMN = 2
WEEK_TYPE_COLUMN = 4
GROUP_HEADER_ROW = 0
GROUP_BLOCK_WIDTH = 4

WEEKDAY_REPLACE_MAP = {
    "пн": "monday",
    "вт": "tuesday",
    "ср": "wednesday",
    "чт": "thursday",
    "пт": "friday",
    "сб": "saturday",
    "вс": "sunday",
}
WEEK_TYPE_REPLACE_MAP: dict[str, Literal["odd_week", "even_week"]] = {
    "н": "odd_week",
    "ч": "even_week",
}
LESSON_TYPE_REPLACE_MAP: dict[str, LessonType] = {
    "лек": "лекция",
    "пр": "практика",
    "лаб": "лабораторная",
    "сем": "семинар",
    "фак": "факультатив",
}
SUBJECT_NAME_REPLACE_PATTERN = [
    (re.compile(r"^Python и АД$"), "Python и алгоритмы данных"),
    (re.compile(r"^АКОС$"), "Архитектура компьютерных систем"),
    (re.compile(r"^АиСД$"), "Алгоритмы и структуры данных"),
    (re.compile(r"^АнДан$"), "Анализ данных"),
    (re.compile(r"^АрхКомп$"), "Архитектура компьютера"),
    (re.compile(r"^БД$"), "Базы данных"),
    (re.compile(r"^ВычЛА$"), "Вычислительная линейная алгебра"),
    (re.compile(r"^Дискретка$"), "Дискретная математика"),
    (re.compile(r"^ИнЯз$"), "Английский язык"),
    (re.compile(r"^ЛинАл$"), "Линейная алгебра"),
    (re.compile(r"^МатАн$"), "Матанализ"),
    (re.compile(r"^МатЛог$"), "Математическая логика"),
    (re.compile(r"^МатСтат$"), "Математическая статистика"),
    (re.compile(r"^МашОб$"), "Машинное обучение"),
    (re.compile(r"^МетПрог$"), "Методология программирования"),
    (re.compile(r"^ОС$"), "Операционные системы"),
    (re.compile(r"^ПарПрог$"), "Параллельное программирование"),
    (re.compile(r"^Прог$"), "Программирование"),
    (re.compile(r"^СлучПроц$"), "Случайные процессы"),
    (re.compile(r"^ТеорВер$"), "Теория вероятностей"),
    (re.compile(r"^ТеорКод$"), "Теория кодирования"),
    (re.compile(r"^ФП$"), "Функциональное программирование"),
]
LECTURER_REPLACE_PATTERN = [
    (re.compile(r"\+\+$"), ""),
]
PLACEHOLDER_GROUP_NAMES = {"выбор"}
UNKNOWN_VALUES = {"?", "-", "—"}
GROUP_PREFIX = FacultyCode.CT.group_prefix
GROUP_NAME_PATTERN = re.compile(rf"^{GROUP_PREFIX}\d{{4}}$", flags=re.IGNORECASE)
COURSE_PATTERN = re.compile(rf"^{GROUP_PREFIX}\d(\d)", flags=re.IGNORECASE)
ERROR_VALUE_PATTERN = re.compile(r"^#[A-Z]+[!?]$")


class CtScheduleParser:
    def __init__(self, sheet_key: str, sheet_gid: str) -> None:
        self._sheet_key = sheet_key
        self._sheet_gid = sheet_gid

    def parse(self) -> ParseResult:
        sheet = fetch_published_sheet(self._sheet_key, self._sheet_gid)
        return self.extract(sheet)

    def extract(self, sheet: Sheet) -> ParseResult:
        return self._extract_data(sheet, self._extract_groups(sheet))

    @staticmethod
    def _extract_groups(sheet: Sheet) -> list[tuple[int, str]]:
        """Return (first column, group name) for every group block of the header row."""
        groups = []
        for row, column in sorted(sheet.cells):
            if row != GROUP_HEADER_ROW:
                continue
            cell = sheet.cells[(row, column)]
            if cell.origin != (row, column):
                continue  # a later column of a block already taken through its origin
            name = cell.text.upper()
            if not name or name.lower() in PLACEHOLDER_GROUP_NAMES or not GROUP_NAME_PATTERN.match(name):
                continue
            groups.append((column, name))
        return groups

    def _extract_data(self, sheet: Sheet, groups: list[tuple[int, str]]) -> ParseResult:
        result = ParseResult()

        for row in sheet.visible_rows:
            weekday = WEEKDAY_REPLACE_MAP.get(sheet.text(row, WEEKDAY_COLUMN).lower())
            week_type = WEEK_TYPE_REPLACE_MAP.get(sheet.text(row, WEEK_TYPE_COLUMN).lower())
            number = sheet.text(row, LESSON_NUMBER_COLUMN)
            if weekday is None or week_type is None or not number.isdigit():
                continue

            for column, group in groups:
                lesson = self._extract_lesson(sheet, row, column, int(number))
                if lesson is None:
                    continue
                result.schedule.add_lesson(
                    course=self._extract_course(group),
                    group=group,
                    week_type=week_type,
                    weekday=Weekday(weekday),
                    lesson=lesson,
                )

        return result

    def _extract_lesson(self, sheet: Sheet, row: int, column: int, number: int) -> Lesson | None:
        block = [sheet.cell(row, column + offset) for offset in range(GROUP_BLOCK_WIDTH)]
        origins = {cell.origin for cell in block if cell is not None}

        if len(origins) == 1 and block[0] is not None:
            # one cell merged over the whole block is a bare label: no room, no lecturer
            name = self._clean_name(block[0].text)
            return Lesson(name=name, number=number) if name else None

        texts = [cell.text if cell is not None else "" for cell in block]
        name = self._clean_name(texts[0])
        lesson_type = LESSON_TYPE_REPLACE_MAP.get(self._clean(texts[1], lower=True) or "")
        room = self._clean(texts[2])
        lecturer = self._clean_lecturer(texts[3])

        if name is None and lesson_type is None and room is None and lecturer is None:
            return None

        return Lesson(
            name=name,
            room=room,
            lecturer=lecturer,
            type=lesson_type,
            number=number,
        )

    @classmethod
    def _clean_name(cls, value: str) -> str | None:
        name = cls._clean(value)
        if name is None:
            return None
        for pattern, repl in SUBJECT_NAME_REPLACE_PATTERN:
            name = pattern.sub(repl, name)
        return name

    @classmethod
    def _clean_lecturer(cls, value: str) -> str | None:
        lecturer = cls._clean(value)
        if lecturer is None:
            return None
        for pattern, repl in LECTURER_REPLACE_PATTERN:
            lecturer = pattern.sub(repl, lecturer)
        return lecturer.strip() or None

    @staticmethod
    def _extract_course(group: str) -> str:
        """M3132 -> "1 курс": the digit after the faculty code is the course."""
        match = COURSE_PATTERN.match(group)
        return f"{match.group(1)} курс" if match else group

    @staticmethod
    def _clean(value: str, *, lower: bool = False) -> str | None:
        value = value.strip()
        if not value or value in UNKNOWN_VALUES or ERROR_VALUE_PATTERN.match(value):
            return None
        return value.lower() if lower else value
