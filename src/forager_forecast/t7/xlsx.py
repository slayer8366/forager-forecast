"""A minimal reader for one sheet of an .xlsx workbook, standard library only.

Used by the FungalTraits adapter, whose table is published as .xlsx (University of Pretoria
repository, http://hdl.handle.net/2263/80202). No spreadsheet package is pinned in this
repository; a workbook is a zip of XML parts, and a sheet of shared and inline strings and numbers
needs only these few lines.
"""

from __future__ import annotations

import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterator
from pathlib import Path

_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_REF = re.compile(r"([A-Z]+)")


def column_index(ref: str) -> int:
    """'A1' -> 0, 'AB7' -> 27."""
    letters = _REF.match(ref).group(1)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _text(el) -> str:
    return "".join(t.text or "" for t in el.iter(f"{_MAIN}t"))


def _sheet_part(z: zipfile.ZipFile, sheet: str) -> str:
    book = ET.fromstring(z.read("xl/workbook.xml"))
    rid = None
    for s in book.iter(f"{_MAIN}sheet"):
        if s.get("name") == sheet:
            rid = s.get(f"{_REL}id")
    if rid is None:
        raise KeyError(f"no sheet named {sheet!r}")
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    for r in rels.iter(f"{_PKG}Relationship"):
        if r.get("Id") == rid:
            target = r.get("Target")
            return target.lstrip("/") if target.startswith("/") else posixpath.join("xl", target)
    raise KeyError(f"sheet {sheet!r} has no part")


def read_sheet(path: Path, sheet: str) -> Iterator[list[str]]:
    """Each row of the named sheet as a list of cell texts, gaps filled with ''."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            shared = [_text(si) for si in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        root = ET.fromstring(z.read(_sheet_part(z, sheet)))
    for row in root.iter(f"{_MAIN}row"):
        cells: dict[int, str] = {}
        for c in row.iter(f"{_MAIN}c"):
            kind, v = c.get("t"), c.find(f"{_MAIN}v")
            if kind == "s" and v is not None:
                value = shared[int(v.text)]
            elif kind == "inlineStr":
                value = _text(c)
            else:
                value = v.text if v is not None and v.text is not None else ""
            cells[column_index(c.get("r"))] = value
        width = max(cells) + 1 if cells else 0
        yield [cells.get(i, "") for i in range(width)]


def read_table(path: Path, sheet: str) -> tuple[list[str], Iterator[dict[str, str]]]:
    """(header, rows as header name -> text) for a sheet whose first row is its header."""
    rows = read_sheet(path, sheet)
    header = [h.strip() for h in next(rows)]

    def body():
        for row in rows:
            row = row + [""] * (len(header) - len(row))
            yield dict(zip(header, row[: len(header)], strict=True))

    return header, body()
