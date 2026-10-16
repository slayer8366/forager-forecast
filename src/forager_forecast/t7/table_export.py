"""A lossless, committable export of a workbook's cell values: one gzip-compressed CSV per sheet.

Owner's ruling (Forager RECORD -1081, D143): the whole FungalTraits table goes into this
repository. The workbook (1,243,643 bytes) is over the repository's 1 MiB large-file guard, which
is not changed, so it is committed as this export instead, with the original's size, MD5 and
sha256 recorded so the original can be matched.

**What the export carries.** Every sheet the workbook lists, every row from 1 to the last row the
sheet stores, and every column from A to the widest row's last stored cell, as the cell texts the
project's own reader (``t7/xlsx.py``) gives: shared strings, inline strings and stored values. A
row or cell the sheet does not store is written as empty, so line *r* of a sheet's CSV is the
sheet's row *r* and field *c* is its column *c*.

**What it does not carry,** stated so nobody reads "lossless" wider than it is: cell styles and
number formats, column widths and row heights, rich-text formatting inside a string (its text is
kept), saved filter views, the workbook's thumbnail and document properties. Formulas would be
carried only as their stored result; ``compare_export`` counts formulas and the FungalTraits table
has none.

**Deterministic bytes.** UTF-8 CSV, ``\\n`` line ends, minimal quoting, then gzip at level 9 with
mtime 0 and no file name in the header, so the same workbook always gives the same sha256.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

from forager_forecast.t7.xlsx import _MAIN, _sheet_part, read_sheet_numbered, sheet_names


def sheet_grid(xlsx: Path, sheet: str) -> list[list[str]]:
    """The sheet as a rectangle: rows 1 to the last stored row, columns to the widest row."""
    stored = dict(read_sheet_numbered(xlsx, sheet))
    if len(stored) == 0:
        return []
    height = max(stored)
    width = max((len(cells) for cells in stored.values()), default=0)
    grid = []
    for r in range(1, height + 1):
        cells = stored.get(r, [])
        grid.append(cells + [""] * (width - len(cells)))
    return grid


def csv_bytes(grid: list[list[str]]) -> bytes:
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    w.writerows(grid)
    return buf.getvalue().encode("utf-8")


def gzip_deterministic(data: bytes) -> bytes:
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0, compresslevel=9) as g:
        g.write(data)
    return out.getvalue()


def read_csv_gz(path: Path) -> list[list[str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class SheetExport:
    sheet: str
    file_name: str
    rows: int
    columns: int
    csv_sha256: str
    csv_size: int
    gz_sha256: str
    gz_size: int


def export_sheet(xlsx: Path, sheet: str, out: Path) -> SheetExport:
    grid = sheet_grid(xlsx, sheet)
    raw = csv_bytes(grid)
    packed = gzip_deterministic(raw)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    partial = out.with_name(out.name + ".partial")
    partial.write_bytes(packed)
    partial.rename(out)
    return SheetExport(
        sheet, out.name, len(grid), len(grid[0]) if grid else 0,
        sha256_bytes(raw), len(raw), sha256_bytes(packed), len(packed),
    )  # fmt: skip


def export_file_name(sheet: str) -> str:
    """'trait states' -> 'trait_states.csv.gz'."""
    return re.sub(r"[^A-Za-z0-9]+", "_", sheet).strip("_").lower() + ".csv.gz"


@dataclass(frozen=True)
class Comparison:
    sheet: str
    stored_rows: int
    cells_compared: int
    non_empty_cells: int
    formulas: int
    mismatches: list[str]


def _formula_count(xlsx: Path, sheet: str) -> int:
    with zipfile.ZipFile(xlsx) as z:
        root = ET.fromstring(z.read(_sheet_part(z, sheet)))
    return sum(1 for _ in root.iter(f"{_MAIN}f"))


def compare_export(xlsx: Path, sheet: str, export: Path, limit: int = 20) -> Comparison:
    """Every cell of ``sheet`` as the xlsx reader gives it, against the export, field by field.

    Also checks that rows and cells the sheet does not store are empty in the export, and that
    the export has no row or column beyond the sheet's. Returns up to ``limit`` mismatches.
    """
    stored = dict(read_sheet_numbered(xlsx, sheet))
    rows = read_csv_gz(export)
    height = max(stored) if stored else 0
    width = max((len(c) for c in stored.values()), default=0)
    mismatches: list[str] = []

    def miss(text: str) -> None:
        if len(mismatches) < limit:
            mismatches.append(text)

    if len(rows) != height:
        miss(f"export has {len(rows)} rows, the sheet's last stored row is {height}")
    compared = non_empty = 0
    for r in range(1, max(height, len(rows)) + 1):
        want = stored.get(r, [])
        got = rows[r - 1] if r <= len(rows) else []
        if len(got) != width:
            miss(f"row {r}: {len(got)} fields, not {width}")
        for c in range(max(width, len(got))):
            w = want[c] if c < len(want) else ""
            g = got[c] if c < len(got) else ""
            compared += 1
            non_empty += w != ""
            if w != g:
                miss(f"row {r} column {c + 1}: sheet {w!r}, export {g!r}")
    return Comparison(sheet, len(stored), compared, non_empty, _formula_count(xlsx, sheet),
                      mismatches)  # fmt: skip


def export_workbook(xlsx: Path, out_dir: Path) -> list[SheetExport]:
    return [
        export_sheet(xlsx, sheet, Path(out_dir) / export_file_name(sheet))
        for sheet in sheet_names(xlsx)
    ]
