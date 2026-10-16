"""T7 items 1 and 3: a 250 m master-grid cell to its 0.1 degree weather cell, and a static effort.

Item 1 (T7 verify report V11: "No production code maps a master-grid cell to a weather cell
today"). A cell's centre goes to longitude and latitude by ``t6b_mask.cell_lonlat`` and then to the
weather cell ``cells.cell_for`` names (D46, D63, D64): nearest 0.1 degree point, an exact decimal
tie toward +infinity. ``cell_for`` works on the decimal text of one float at a time, which is slow
for 65,536 cells a tile, so the vectorised path rounds in floating point and hands every value
within ``TIE_GUARD`` of a half-way point to ``cell_for`` itself. Away from a half-way point the two
cannot differ; at one, only ``cell_for`` knows the rule.

Item 3 (proposals P3 point 3): the static effort of a weather cell is its expected outings summed
over the effort frame's 573 whole ISO weeks (D101), read through ``EffortSurface.effort`` one week
at a time, so the stored surface's own refusal (D107) applies: a cell outside the frame has no
value and is listed as refused, never given one.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

from forager_forecast.cells import Cell
from forager_forecast.effort import EffortSurface
from forager_forecast.grid import GridWindow

_STUB = "T7 build: not written yet (tests first)"

# A tenth-of-a-degree value whose fractional part lies this close to one half is decided by
# cells.cell_for on its decimal text. Floating-point error in lon * 10 is about 1e-14.
TIE_GUARD = 1e-6

# Packed weather-cell key: one int64 per cell for joins and sets.
_LAT_OFFSET = 1000
_LON_OFFSET = 2000
_LON_SPAN = 10_000


def pack(lat_tenths, lon_tenths):
    """One int64 key per weather cell (arrays or scalars)."""
    raise NotImplementedError(_STUB)


def unpack(key) -> tuple:
    raise NotImplementedError(_STUB)


def pack_cell(cell: Cell) -> int:
    raise NotImplementedError(_STUB)


def weather_cells(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(lat_tenths, lon_tenths) of the weather cell each point belongs to, as cells.cell_for."""
    raise NotImplementedError(_STUB)


def weather_cells_for_window(window: GridWindow) -> tuple[np.ndarray, np.ndarray]:
    """(lat_tenths, lon_tenths), shape (height, width), for every master cell of ``window``."""
    raise NotImplementedError(_STUB)


@dataclass(frozen=True)
class StaticEffort:
    """Expected outings summed over the frame's 573 weeks, per weather cell in the frame."""

    total: dict[Cell, float]
    refused: tuple[Cell, ...]

    def log(self, cell: Cell) -> float:
        raise NotImplementedError(_STUB)

    def keys(self) -> np.ndarray:
        """Packed keys of every cell with a value, sorted."""
        raise NotImplementedError(_STUB)


def static_effort(surface: EffortSurface, cells: Iterable[Cell]) -> StaticEffort:
    raise NotImplementedError(_STUB)
