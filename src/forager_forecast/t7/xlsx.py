"""A minimal reader for one sheet of an .xlsx workbook, standard library only.

Used by the FungalTraits adapter, whose table is published as .xlsx (University of Pretoria
repository, http://hdl.handle.net/2263/80202). No spreadsheet package is pinned in this
repository; a workbook is a zip of XML parts, and a sheet of shared and inline strings and numbers
needs only these few lines.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

_STUB = "T7 build: not written yet (tests first)"


def column_index(ref: str) -> int:
    """'A1' -> 0, 'AB7' -> 27."""
    raise NotImplementedError(_STUB)


def read_sheet(path: Path, sheet: str) -> Iterator[list[str]]:
    """Each row of the named sheet as a list of cell texts, gaps filled with ''."""
    raise NotImplementedError(_STUB)


def read_table(path: Path, sheet: str) -> tuple[list[str], Iterator[dict[str, str]]]:
    """(header, rows as header name -> text) for a sheet whose first row is its header."""
    raise NotImplementedError(_STUB)
