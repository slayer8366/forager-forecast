"""T7 item 2: a CEC level III ecoregion code per master-grid cell (D125's validation blocks).

The study-area mask stores no level III code (T7 verify report V12; ``t6b_mask.py`` band 2 holds
none, Arctic or other), so T7 burns level III itself, by cell centre, with the same rule as the
mask's ``_burn`` (GDAL's default rasterize rule; only rings whose bounding box meets the window are
passed). Codes are 1 to n over the file's level III identifiers in sorted order; 0 is "in no level
III polygon". The table of codes is part of every output's manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from forager_forecast.grid import GridWindow

_STUB = "T7 build: not written yet (tests first)"
NO_BLOCK = 0


@dataclass(frozen=True)
class Level3:
    code: int
    level3: str
    level1: str
    name: str


def read_dbf_text(path: Path, names: tuple[str, ...]) -> dict[str, list[str]]:
    """Named character columns of a dBase table, decoded as UTF-8 (the CEC file's .cpg)."""
    raise NotImplementedError(_STUB)


def read_level3(shp: Path) -> tuple[list[Level3], list[tuple[int, list[np.ndarray]]]]:
    """(code table, (code, rings on the master grid) per polygon) from the level III file."""
    raise NotImplementedError(_STUB)


def burn_level3(polygons: list[tuple[int, list[np.ndarray]]], window: GridWindow) -> np.ndarray:
    """uint16 level III code per cell of ``window`` by cell centre; 0 where none."""
    raise NotImplementedError(_STUB)
