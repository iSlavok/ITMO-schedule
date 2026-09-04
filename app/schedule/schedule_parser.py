import re
from typing import cast

import gspread
from google.oauth2.service_account import Credentials

from app.enums import FacultyCode, Week, Weekday
from app.schemas import (
    Lesson,
    LessonType,
    ParseResult,
    Schedule,
    ScheduleGroup,
    ScheduleNote,
)

MULTIPLE_NEWLINES_PATTERN = re.compile(r"\n{2,}")
SPACE_PATTERN = re.compile(r"\s+")
SKIP_LESSON_PATTERN = re.compile(r"(?<!-)\b(?:[1-9]|[12]\d|3[01])\b(?!:\d{2})")
LECTURE_TYPE_PATTERN = re.compile(r"\b(лекция|практика|лабораторная|факультатив|ZOOM)\b", flags=re.IGNORECASE)
ROOM_PATTERN = re.compile(r"ауд(?:\.?\s*|\s+)(\d+)", flags=re.IGNORECASE)
COURSE_HEADER_PATTERN = re.compile(r"^\s*\d+\s+курс\s*$", flags=re.IGNORECASE)
BLANK_LINE_PATTERN = re.compile(r"\n\s*\n")
GROUP_PREFIX = FacultyCode.PHYSICS.group_prefix
SUBGROUP_PATTERN = re.compile(rf"^{GROUP_PREFIX}\d{{3,4}}$", flags=re.IGNORECASE)
GROUP_NUMBER_PATTERN = re.compile(rf"^{GROUP_PREFIX}?(\d{{4}}.*)$", flags=re.IGNORECASE)


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
    (re.compile(r"\bМатан\b"), "Матанализ"),
    (re.compile(r"\bДиффуры\b"), "Дифференциальные уравнения"),
    (re.compile(r"\bДиффур\b"), "Дифференциальные уравнения"),
    (re.compile(r"Дифф\.\s*ур\."), "Дифференциальные уравнения"),
    (re.compile(r"Техническая электродимика"), "Техническая электродинамика"),
    (re.compile(r"\bШендерович\b(?!\s+И\.Е\.)"), "Шендерович И.Е."),
    (re.compile(r"\bСмирнов\b(?!\s+[А-Я]\.)"), "Смирнов А.В."),
    (re.compile(r"\bБатракова\b(?!\s+П\.)"), "Батракова П."),
    (re.compile(r"\bГилев П\.(?!А)"), "Гилев П.А."),
    (re.compile(r"\bЯковлев З\.А\.\."), "Яковлев З.А."),
    (re.compile(r"\bДенисов\b(?!\s+[А-Я]\.)"), "Денисов К.М."),
    (re.compile(r"\bМысляева\b(?!\s+[А-Я]\.)"), "Мысляева Д."),
    (re.compile(r"\bВасильев\b(?!\s+[А-Я]\.)"), "Васильев Д.В."),
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

    def parse(self) -> ParseResult:
        worksheet = self._open_worksheet()
        values = worksheet.get_all_values()
        self._merge_cells(worksheet, values)
        values = self._replace_values(values)
        result = self._extract_data(values)
        renames = self._split_subgroups(result.schedule)
        self._rename_note_groups(result, renames)
        return result

    def _open_worksheet(self) -> gspread.Worksheet:
        spreadsheet = self._gc.open_by_key(self._spreadsheet_key)
        return spreadsheet.get_worksheet(0)

    @staticmethod
    def _merge_cells(worksheet: gspread.Worksheet, values: list[list[str]]) -> None:
        sheet_id = worksheet.id
        sheets = worksheet.spreadsheet.fetch_sheet_metadata().get("sheets", [])
        merged_cells = next(
            (s.get("merges", []) for s in sheets if s.get("properties", {}).get("sheetId") == sheet_id),
            [],
        )

        for merge in merged_cells:
            sr, er = merge.get("startRowIndex"), merge.get("endRowIndex")
            sc, ec = merge.get("startColumnIndex"), merge.get("endColumnIndex")

            if sr < len(values) and sc < len(values[sr]):
                value = values[sr][sc]
                for r in range(sr, er):
                    if r >= len(values):
                        continue
                    row = values[r]
                    for c in range(sc, min(ec, len(row))):
                        row[c] = value

            target_row = sr + 1
            if target_row % 2 == 0 and 3 < target_row < len(values):  # noqa: PLR2004
                row = values[target_row]
                next_value = next((row[c] for c in range(sc, min(ec, len(row))) if row[c]), None)
                if next_value:
                    for c in range(sc, min(ec, len(row))):
                        row[c] = next_value

    @staticmethod
    def _replace_values(values: list[list[str]]) -> list[list[str]]:
        def fill_and_replace(row: list[str], replace_map: dict[str, str]) -> None:
            for i, value in enumerate(row[2:], 2):
                data_value = value.strip()
                if not data_value:
                    row[i] = row[i - 1]
                elif data_value in replace_map:
                    row[i] = replace_map[data_value]

        fill_and_replace(values[1], WEEK_TYPE_REPLACE_MAP)
        fill_and_replace(values[2], GROUP_NAME_REPLACE_MAP)

        transposed = [list(r) for r in zip(*values, strict=False)]
        values = transposed[:3] + [
            column for column in transposed[3:] if COURSE_HEADER_PATTERN.search(column[0])
        ]

        fill_and_replace(values[0], WEEKDAY_REPLACE_MAP)
        return values

    def _extract_data(self, values: list[list[str]]) -> ParseResult:
        result = ParseResult()
        for row in values[3:]:

            year = row[0].strip()
            week_type = row[1].strip()
            group = self._normalize_group_name(row[2])
            if week_type not in ("odd_week", "even_week"):
                continue

            for j, value in enumerate(row[3:], 3):
                if j % 2 == 0 or not value.strip():
                    continue
                if j + 1 >= len(values[1]):
                    continue

                second_value = row[j + 1] if j + 1 < len(row) else ""
                lesson_parts, note_text = self._split_blocks(value)
                room = self._extract_room(second_value, value)
                lesson_number = int(values[1][j + 1])
                weekday = Weekday(values[0][j])

                for subgroup, raw_block in lesson_parts:
                    block = raw_block
                    for pattern, repl in LESSON_DATA_REPLACE_PATTERN:
                        block = pattern.sub(repl, block)
                    block = block.replace(",", "").replace('"', "")
                    block = MULTIPLE_NEWLINES_PATTERN.sub("\n", block)

                    lecture_type, block = self._extract_lecture_type(block)
                    name, lecturer = self._extract_name_and_lecturer(block)

                    if (room is None) and (lecture_type is None) and (name is None) and (lecturer is None):
                        continue

                    result.schedule.add_lesson(
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
                            subgroup=subgroup,
                        ),
                    )

                if note_text:
                    result.notes.append(ScheduleNote(
                        course=year,
                        group=group,
                        week=Week(week_type),
                        weekday=weekday,
                        number=lesson_number,
                        text=note_text,
                    ))

        return result

    @staticmethod
    def _normalize_group_name(value: str) -> str:
        """Prefix the group number with the faculty letter.

        The sheet writes the prefix on some numbers and omits it on others, while
        group numbers are shared with the other faculty, so it is always added.
        Senior years are taught in tracks instead of numbered groups, and a track
        goes by its name ("радио", "стф"); the letter belongs in front of a number,
        so those are left as they are written.
        """
        name = value.strip()
        match = GROUP_NUMBER_PATTERN.match(name)
        return f"{GROUP_PREFIX}{match.group(1)}" if match else name

    @staticmethod
    def _split_subgroups(schedule: Schedule) -> dict[tuple[str, str], list[str]]:
        """Turn a group holding subgroup-tagged lessons into one group per subgroup.

        Third-year track columns (радио / навигация / телеком) are shared by two
        subgroups, Z3300 and Z3301, which have different lessons in the same slot.
        A student belongs to a track and to a subgroup at once, so the two are
        merged into a single group named "<track> <subgroup>". Untagged lessons are
        common to both and land in every resulting group.

        Returns the (course, old group) -> new group names map, so that footnotes
        collected under the old name can be moved onto the new ones.
        """
        renames: dict[tuple[str, str], list[str]] = {}
        for course_name, course in schedule.courses.items():
            for group_name, group in list(course.groups.items()):
                subgroups = sorted({
                    lesson.subgroup
                    for week in (group.odd_week, group.even_week)
                    for day in week.days.values()
                    for lesson in day.lessons
                    if lesson.subgroup
                })
                if not subgroups:
                    continue

                for subgroup in subgroups:
                    new_group = ScheduleGroup()
                    for source_week, target_week in (
                        (group.odd_week, new_group.odd_week),
                        (group.even_week, new_group.even_week),
                    ):
                        for weekday, day in source_week.days.items():
                            lessons = [
                                lesson for lesson in day.lessons
                                if lesson.subgroup in (None, subgroup)
                            ]
                            if lessons:
                                target_week.days[weekday].lessons.extend(lessons)
                    course.groups[f"{group_name} {subgroup}"] = new_group

                renames[(course_name, group_name)] = [f"{group_name} {sub}" for sub in subgroups]
                del course.groups[group_name]

        return renames

    @staticmethod
    def _rename_note_groups(result: ParseResult, renames: dict[tuple[str, str], list[str]]) -> None:
        """Point footnotes at the groups produced by the subgroup split."""
        if not renames:
            return

        moved = []
        for note in result.notes:
            new_names = renames.get((note.course, note.group))
            if new_names is None:
                moved.append(note)
                continue
            moved.extend(note.model_copy(update={"group": name}) for name in new_names)

        result.notes = moved

    @classmethod
    def _split_blocks(cls, value: str) -> tuple[list[tuple[str | None, str]], str | None]:
        """Split a cell into lesson blocks and a footnote.

        Blocks are separated by a blank line. Blocks starting with a subgroup
        marker (Z3300 / Z3301) are separate lessons for those subgroups. Without
        such markers the first block is the lesson and everything after it is a
        footnote about it: a cancellation, a date list or an extra remark.

        A first block that is itself about dates means there is no recurring
        lesson at all, so the whole cell becomes the footnote.
        """
        blocks = [block.strip() for block in BLANK_LINE_PATTERN.split(value)]
        blocks = [block for block in blocks if block]
        if not blocks:
            return [], None

        subgroup_blocks = []
        for block in blocks:
            marker, _, rest = block.partition("\n")
            if SUBGROUP_PATTERN.match(marker.strip()):
                subgroup_blocks.append((marker.strip().upper(), rest))

        if subgroup_blocks:
            return subgroup_blocks, None

        if cls._is_note_only(blocks[0]):
            return [], value.strip()

        return [(None, blocks[0])], "\n".join(blocks[1:]).strip() or None

    @staticmethod
    def _is_note_only(block: str) -> bool:
        """Whether a block carries dates instead of a lesson."""
        has_date = re.search(SKIP_LESSON_PATTERN, block)
        has_skip_word = any(skip_word in block.lower() for skip_word in SKIP_WORDS)
        has_keep_word = any(keep_word in block for keep_word in NOT_SKIP_WORDS)
        return bool(has_date or has_skip_word) and not has_keep_word

    @staticmethod
    def _extract_room(value: str, lesson_value: str) -> str | None:
        """Take the room cell as a whole string.

        Rooms are not always numeric, so pulling a number out of the cell is
        meaningless. A cell equal to the lesson cell is a merged cell spanning
        both columns, not a room.
        """
        room = SPACE_PATTERN.sub(" ", value).strip()
        if not room or room == SPACE_PATTERN.sub(" ", lesson_value).strip():
            return None
        return room

    @staticmethod
    def _extract_lecture_type(value: str) -> tuple[LessonType | None, str]:
        lecture_types = re.findall(LECTURE_TYPE_PATTERN, value)
        # the pattern also strips ZOOM, which is not one of the lesson types
        lecture_type = cast("LessonType", lecture_types[0].lower()) if lecture_types else None

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
