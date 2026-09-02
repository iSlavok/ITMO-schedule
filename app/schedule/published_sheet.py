"""Reading a Google Sheet published to the web as its rendered HTML.

The CSV export of a published sheet flattens everything but the text: merges
collapse to their top-left cell, hidden rows and columns come back as if they
were visible, and formatting is gone. The rendered HTML keeps all of it, which
is what a schedule sheet actually leans on, so it is read instead.

Google emits one `<th id="{gid}C{n}">` per visible column and one
`<th id="{gid}R{n}">` per visible row: that is what maps the table back onto the
sheet's own coordinates, with hidden rows and columns simply absent.
"""

import re
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser

SHEET_URL_TEMPLATE = "https://docs.google.com/spreadsheets/d/e/{key}/pubhtml/sheet?headers=false&gid={gid}"
REQUEST_TIMEOUT = 30

CELL_ID_PATTERN = re.compile(r"^\d+[RC](\d+)$")
CSS_RULE_PATTERN = re.compile(r"\.(s\d+)\s*\{([^}]*)\}")
SPACE_PATTERN = re.compile(r"[^\S\n]+")
MULTIPLE_NEWLINES_PATTERN = re.compile(r"\n{2,}")


@dataclass
class Cell:
    """One sheet cell: its text plus the style hooks the sheet renders it with."""

    text: str = ""
    classes: tuple[str, ...] = ()
    origin: tuple[int, int] | None = None

    def copy_as_merged(self) -> "Cell":
        return Cell(text=self.text, classes=self.classes, origin=self.origin)


@dataclass
class Sheet:
    """A published sheet: cells by (row, column) in the sheet's own indices."""

    cells: dict[tuple[int, int], Cell] = field(default_factory=dict)
    styles: dict[str, str] = field(default_factory=dict)
    visible_rows: list[int] = field(default_factory=list)
    visible_columns: list[int] = field(default_factory=list)

    def cell(self, row: int, column: int) -> Cell | None:
        return self.cells.get((row, column))

    def text(self, row: int, column: int) -> str:
        cell = self.cells.get((row, column))
        return cell.text if cell else ""

    def css(self, cell: Cell) -> str:
        """Raw CSS of the cell's style class: background colour, strikethrough, ..."""
        return " ".join(self.styles.get(name, "") for name in cell.classes)


class PublishedSheetParser(HTMLParser):
    """Turns the published sheet's HTML table into a `Sheet`.

    Merged cells arrive as rowspan/colspan and are expanded over every cell they
    cover, so lookups never hit a hole. `Cell.origin` holds the coordinates of the
    cell a merge started from, which is how a block-wide merge is told apart from
    neighbouring cells that happen to repeat the same text.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sheet = Sheet()
        self._in_style = False
        self._in_head_row = False
        self._in_body = False
        self._row: int | None = None
        self._position = 0
        self._positions: list[int | None] = []
        self._carry: dict[int, tuple[int, Cell]] = {}
        self._occupied: set[int] = set()
        self._cell: Cell | None = None
        self._cell_positions: list[int] = []
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "style":
            self._in_style = True
        elif tag == "thead":
            self._in_head_row = True
        elif tag == "tbody":
            self._in_head_row = False
            self._in_body = True
        elif tag == "tr":
            self._start_row()
        elif tag == "th":
            self._handle_header(attributes)
        elif tag == "td" and self._in_body:
            self._start_cell(attributes)
        elif tag == "br" and self._cell is not None:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self._in_style = False
        elif tag == "thead":
            self._in_head_row = False
        elif tag == "td":
            self._end_cell()
        elif tag == "tr":
            self._end_row()

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.sheet.styles.update(
                {name: rule.strip() for name, rule in CSS_RULE_PATTERN.findall(data)},
            )
        elif self._cell is not None:
            self._chunks.append(data)

    def _handle_header(self, attributes: dict[str, str | None]) -> None:
        index = self._index_of(attributes.get("id"))
        if self._in_head_row:
            self._add_position(index, attributes.get("class") or "")
        elif index is not None:
            self._row = index
            self.sheet.visible_rows.append(index)
            self._apply_carry()

    def _add_position(self, index: int | None, classes: str) -> None:
        """Record a table position, mapping it to a sheet column when it is one.

        The leading row-header column has no counterpart in the body rows (they
        open with a `<th>` of their own), while the freezebar separators do emit
        a `<td>`: they take a position but map to no column.
        """
        if index is None and "row-header" in classes:
            return
        self._positions.append(index)
        if index is not None:
            self.sheet.visible_columns.append(index)

    def _start_row(self) -> None:
        # every <tr> advances the grid, including the zero-height freezebar row,
        # so rowspans stay aligned; only rows with an id carry sheet data
        self._row = None
        self._position = 0
        self._occupied = set()

    def _end_row(self) -> None:
        if self._in_body and self._row is None:
            self._apply_carry()

    def _start_cell(self, attributes: dict[str, str | None]) -> None:
        while self._position in self._occupied:
            self._position += 1

        self._cell = Cell(classes=tuple((attributes.get("class") or "").split()))
        columns = self._span(attributes, "colspan")
        self._cell_positions = [self._position + offset for offset in range(columns)]
        self._position += columns
        self._chunks = []

        rows = self._span(attributes, "rowspan")
        if rows > 1:
            for position in self._cell_positions:
                self._carry[position] = (rows - 1, self._cell)

    def _end_cell(self) -> None:
        if self._cell is None:
            return
        self._cell.text = self._normalize("".join(self._chunks))
        self._cell.origin = (self._row, self._column_of(self._cell_positions[0])) if self._row is not None else None
        self._place(self._cell, self._cell_positions[:1])
        self._place(self._cell.copy_as_merged(), self._cell_positions[1:])
        self._cell = None
        self._cell_positions = []
        self._chunks = []

    def _apply_carry(self) -> None:
        """Re-emit cells that a rowspan stretches into the row being read.

        The positions they cover stay blocked for the whole row, so the row's own
        `<td>`s land to the right of them, exactly as a browser lays it out.
        """
        self._occupied = set(self._carry)
        for position, (rows_left, cell) in list(self._carry.items()):
            self._place(cell.copy_as_merged(), [position])
            if rows_left <= 1:
                del self._carry[position]
            else:
                self._carry[position] = (rows_left - 1, cell)

    def _place(self, cell: Cell, positions: list[int]) -> None:
        if self._row is None:
            return
        for position in positions:
            column = self._column_of(position)
            if column is None:
                continue
            self.sheet.cells[(self._row, column)] = cell

    def _column_of(self, position: int) -> int | None:
        return self._positions[position] if position < len(self._positions) else None

    @staticmethod
    def _index_of(cell_id: str | None) -> int | None:
        if not cell_id:
            return None
        match = CELL_ID_PATTERN.match(cell_id)
        return int(match.group(1)) if match else None

    @staticmethod
    def _span(attributes: dict[str, str | None], name: str) -> int:
        value = attributes.get(name)
        return int(value) if value and value.isdigit() else 1

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.replace("\xa0", " ").replace("\r", "")
        text = SPACE_PATTERN.sub(" ", text)
        return MULTIPLE_NEWLINES_PATTERN.sub("\n", text).strip()


def parse_published_sheet(html: str) -> Sheet:
    parser = PublishedSheetParser()
    parser.feed(html)
    return parser.sheet


def fetch_published_sheet(key: str, gid: str) -> Sheet:
    """Download a published sheet by its publish key and read it into a `Sheet`."""
    url = SHEET_URL_TEMPLATE.format(key=key, gid=gid)
    with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as response:  # noqa: S310
        html = response.read().decode("utf-8")
    return parse_published_sheet(html)
