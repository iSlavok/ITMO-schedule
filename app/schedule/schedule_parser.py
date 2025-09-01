import re

import gspread
from google.oauth2.service_account import Credentials


class ScheduleParser:
    def __init__(self, spreadsheet_key: str) -> None:
        self._spreadsheet_key = spreadsheet_key
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_file(
            "google-credentials.json", scopes=scope)
        self._gc = gspread.authorize(credentials)
        self._worksheet = None
        self._values = None
        self._data = None
        self._replace = {
            "ПОНЕДЕЛЬНИК": "monday",
            "ВТОРНИК": "tuesday",
            "СРЕДА": "wednesday",
            "ЧЕТВЕРГ": "thursday",
            "ПЯТНИЦА": "friday",
            "СУББОТА": "saturday",
            "нечетная неделя": "odd_week",
            "четная неделя": "even_week",
            "радио": "z34433",
            "Z3300\nБеспроводные технологии": "z3300Б",
            "Z3300\nТелеком": "z3300Т",
            "3244-3345": "3244-3245",
        }
        self._lesson_replace = [
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
        self._lecturer_in_name = [
            "Клещенко В.",
            "Яковлев З.",
        ]
        self._lecturer_by_name = {
            "Физхимия": "Королев Д.А.",
        }
        self._skip_words = [
            "с ноября",
            "ноябрь/декабрь",
        ]

    def parse(self) -> dict:
        self._parse_google_sheet()
        self._merge_cells()
        self._replace_values()
        self._extract_data()
        self._remove_empty_lessons()
        self._worksheet = None
        self._values = None
        return {"courses": self._data}

    def _parse_google_sheet(self) -> None:
        spreadsheet = self._gc.open_by_key(self._spreadsheet_key)
        self._worksheet = spreadsheet.get_worksheet(0)
        self._values = self._worksheet.get_all_values()

    def _merge_cells(self) -> None:  # noqa: PLR0912
        sheet_id = self._worksheet.id
        merged_ranges = self._worksheet.spreadsheet.fetch_sheet_metadata().get("sheets", [])
        merged_cells = []
        for sheet in merged_ranges:
            if sheet.get("properties", {}).get("sheetId") == sheet_id and "merges" in sheet:
                merged_cells = sheet["merges"]
                break
        for merge in merged_cells:
            start_row = merge.get("startRowIndex")
            end_row = merge.get("endRowIndex")
            start_col = merge.get("startColumnIndex")
            end_col = merge.get("endColumnIndex")
            if len(self._values) > start_row and len(self._values[start_row]) > start_col:
                value = self._values[start_row][start_col]
                for r in range(start_row, end_row):
                    if r >= len(self._values):
                        continue
                    for c in range(start_col, end_col):
                        if c >= len(self._values[r]):
                            continue
                        self._values[r][c] = value

            target_row = start_row + 1
            if target_row % 2 == 0 and target_row > 3:  # noqa: PLR2004
                next_value = None
                if target_row < len(self._values):
                    for c in range(start_col, end_col):
                        if c < len(self._values[target_row]) and self._values[target_row][c]:
                            next_value = self._values[target_row][c]
                            break
                if next_value is not None:
                    for c in range(start_col, end_col):
                        if target_row < len(self._values) and c < len(self._values[target_row]):
                            self._values[target_row][c] = next_value

    def _replace_values(self) -> None:
        for n in range(3):
            for i, value in enumerate(self._values[n][2:], 2):
                data_value = value.strip()
                if data_value == "":
                    self._values[n][i] = self._values[n][i - 1]
                if data_value in self._replace:
                    self._values[n][i] = self._replace[data_value]
        self._values = list(map(list, zip(*self._values, strict=False)))
        for i, value in enumerate(self._values[0][3:], 3):
            if value == "":
                self._values[0][i] = self._values[0][i - 1]
            if value in self._replace:
                self._values[0][i] = self._replace[value]

    def _extract_data(self) -> None:
        self._data = {}
        for _i, row in enumerate(self._values[3:], 3):
            year = row[0].strip()
            week = row[1].strip()
            group = row[2].strip().split("\n")[0].strip()
            if year not in self._data:
                self._data[year] = {"groups": {}}
            if group not in self._data[year]["groups"]:
                self._data[year]["groups"][group] = {}
            if week not in self._data[year]["groups"][group]:
                self._data[year]["groups"][group][week] = {"days": {}}
            for j, value in enumerate(row[3:], 3):
                data_value = value
                if j % 2 == 0:
                    continue
                if (re.search(r"(?<!-)\b(?:[1-9]|[1-9]\d)\b", data_value)
                        or any(skip_word in data_value.lower() for skip_word in self._skip_words)):
                    continue
                for pattern, repl in self._lesson_replace:
                    data_value = pattern.sub(repl, data_value)
                if self._values[0][j] not in self._data[year]["groups"][group][week]["days"]:
                    self._data[year]["groups"][group][week]["days"][self._values[0][j]] = {"lessons": []}
                data_value = re.sub(r"\n{2,}", "\n", data_value.replace(",", "").replace('"', ""))
                room, data_value = self._extract_room(data_value, row, j)
                lecture_type, data_value = self._extract_lecture_type(data_value)
                name, lecturer = self._extract_name_and_lecturer(data_value)
                number = len(self._data[year]["groups"][group][week]["days"][self._values[0][j]]["lessons"]) + 1
                self._data[year]["groups"][group][week]["days"][self._values[0][j]]["lessons"].append({
                    "name": name,
                    "room": room,
                    "lecturer": lecturer,
                    "type": lecture_type,
                    "number": number,
                })

    @staticmethod
    def _extract_room(value: str, row: list[str], j: int) -> tuple[int | str | None, str]:
        room_match = re.search(r"\d+", row[j + 1] if j + 1 < len(row) else "")
        room = int(room_match.group()) if room_match else None
        room_pattern = r"ауд(?:\.?\s*|\s+)(\d+)"
        room_match = re.search(room_pattern, value, flags=re.IGNORECASE)
        if room_match:
            room = room_match.group(1).strip()
            value = re.sub(room_pattern, "", value, flags=re.IGNORECASE)
        return room, value

    @staticmethod
    def _extract_lecture_type(value: str) -> tuple[str | None, str]:
        types_pattern = r"\b(лекция|практика|лабораторная|факультатив|ZOOM)\b"
        lecture_type = re.findall(types_pattern, value, flags=re.IGNORECASE)
        lecture_type = lecture_type[0].lower() if lecture_type else None
        value = re.sub(types_pattern, "", value, flags=re.IGNORECASE)
        value = re.sub(r"\n{2,}", "\n", value)
        return lecture_type, value

    def _extract_name_and_lecturer(self, value: str) -> tuple[str | None, str | None]:
        parts = value.split("\n", 1)
        name = parts[0].strip()
        lecturer = re.sub(r"\s+", " ", parts[1].replace("\n", ", ")).strip() if len(parts) > 1 else ""
        name = re.sub(r"\s+", " ", name).strip()
        name = name if name != "" else None
        lecturer = re.sub(r"\s+", " ", lecturer).strip(" ,\n")
        lecturer = lecturer.lstrip(" .,")
        lecturer = lecturer if lecturer != "" else None
        if not lecturer and name:
            for _lecturer in self._lecturer_in_name:
                if _lecturer in name:
                    name = name.replace(_lecturer, "").strip()
                    lecturer = _lecturer
                    break
            if name in self._lecturer_by_name:
                lecturer = self._lecturer_by_name[name]
        return name, lecturer

    def _remove_empty_lessons(self) -> None:
        for year in self._data:
            for group in self._data[year]["groups"]:
                for week in self._data[year]["groups"][group]:
                    for day in self._data[year]["groups"][group][week]["days"]:
                        lessons = self._data[year]["groups"][group][week]["days"][day]["lessons"]
                        self._data[year]["groups"][group][week]["days"][day]["lessons"] = [
                            lesson for lesson in lessons if lesson["name"] is not None]
