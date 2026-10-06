"""The master grid: 250 m cells in North America Albers equal-area (ESRI:102008).

Every static layer is computed on this grid (D8) and only finished rasters are reprojected to Web
Mercator for tiles. Defined in T4 (docs/dispatch/2026-10-06-t4-master-grid.md, item 1) as proposed in
docs/audits/2026-10-06-t4-verify-report.md, section 3, and accepted by the planner on 2026-10-06.

- The lattice sits on the projection's own false origin, (0, 0) in ESRI:102008 (lon -96, lat 40).
  Cell edges are integer multiples of 250 m, so no extent has to be chosen and a later layer over a
  wider area lands on the same cells.
- A cell is named by ``col = floor(x / 250)`` and ``row = floor(y / 250)``, row increasing north.
  It covers ``[col*250, (col+1)*250) x [row*250, (row+1)*250)``, so a point on an edge goes east or
  north, the direction D63 chose for weather-cell ties.
- The cell id is ``((row + 32768) << 16) | (col + 32768)``, an unsigned 32-bit integer, valid while
  |x| and |y| are under 8,192 km. Every North American extreme checked in the verify report sits
  inside. Outside it the id function raises rather than wrap.
- Longitude and latitude go to the grid with no datum shift: WGS84 coordinates are read as NAD83,
  which is what PROJ's "NAD83 to WGS 84 (1)" (EPSG:1188, a null transformation) does. Pinning it
  stops a run with network grids from choosing another operation and moving a point to another
  cell. The ignored shift is metres against 250 m cells.
"""

import math
from dataclasses import dataclass
from functools import cache

from pyproj import Transformer

GRID_CRS = "ESRI:102008"
CELL_SIZE_M = 250
# The geographic CRS longitude and latitude are read in. NAD83 is ESRI:102008's own datum, so this
# transformation has no datum step at all; see the module docstring.
GEOGRAPHIC_CRS = "EPSG:4269"
_ID_OFFSET = 1 << 15
_ID_LIMIT = 1 << 16


@dataclass(frozen=True, order=True)
class GridCell:
    """One 250 m master grid cell."""

    col: int
    row: int

    def __post_init__(self) -> None:
        if not (-_ID_OFFSET <= self.col < _ID_OFFSET and -_ID_OFFSET <= self.row < _ID_OFFSET):
            raise ValueError(f"cell ({self.col}, {self.row}) is outside the id range of +/-8,192 km")

    @property
    def id(self) -> int:
        return ((self.row + _ID_OFFSET) << 16) | (self.col + _ID_OFFSET)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """(left, bottom, right, top) in metres."""
        left = self.col * CELL_SIZE_M
        bottom = self.row * CELL_SIZE_M
        return (left, bottom, left + CELL_SIZE_M, bottom + CELL_SIZE_M)

    @property
    def center(self) -> tuple[float, float]:
        return ((self.col + 0.5) * CELL_SIZE_M, (self.row + 0.5) * CELL_SIZE_M)


def cell_at(x: float, y: float) -> GridCell:
    """The cell holding a point given in ESRI:102008 metres."""
    if not (math.isfinite(x) and math.isfinite(y)):
        raise ValueError(f"not a finite coordinate: ({x}, {y})")
    return GridCell(col=math.floor(x / CELL_SIZE_M), row=math.floor(y / CELL_SIZE_M))


def cell_from_id(cell_id: int) -> GridCell:
    if not (0 <= cell_id < _ID_LIMIT * _ID_LIMIT):
        raise ValueError(f"not a master grid cell id: {cell_id}")
    return GridCell(col=(cell_id & 0xFFFF) - _ID_OFFSET, row=(cell_id >> 16) - _ID_OFFSET)


@cache
def lonlat_transformer() -> Transformer:
    """Longitude and latitude to ESRI:102008, with the datum step pinned (see the docstring)."""
    return Transformer.from_crs(GEOGRAPHIC_CRS, GRID_CRS, always_xy=True)


def cell_for_lonlat(longitude: float, latitude: float) -> GridCell:
    x, y = lonlat_transformer().transform(longitude, latitude)
    return cell_at(x, y)


def snap_bounds(
    left: float, bottom: float, right: float, top: float
) -> tuple[int, int, int, int]:
    """Bounds widened outward to the 250 m lattice, as every raster on the grid must be."""
    if not (left < right and bottom < top):
        raise ValueError(f"empty bounds: {(left, bottom, right, top)}")
    step = CELL_SIZE_M
    return (
        math.floor(left / step) * step,
        math.floor(bottom / step) * step,
        math.ceil(right / step) * step,
        math.ceil(top / step) * step,
    )


@dataclass(frozen=True)
class GridWindow:
    """A raster on the master grid: snapped bounds, rows north to south as rasters run."""

    left: int
    bottom: int
    right: int
    top: int

    def __post_init__(self) -> None:
        if (self.left, self.bottom, self.right, self.top) != snap_bounds(
            self.left, self.bottom, self.right, self.top
        ):
            raise ValueError("a grid window's bounds must sit on the 250 m lattice")

    @property
    def width(self) -> int:
        return (self.right - self.left) // CELL_SIZE_M

    @property
    def height(self) -> int:
        return (self.top - self.bottom) // CELL_SIZE_M

    def cell_of_pixel(self, raster_row: int, raster_col: int) -> GridCell:
        if not (0 <= raster_row < self.height and 0 <= raster_col < self.width):
            raise IndexError(f"pixel ({raster_row}, {raster_col}) is outside the window")
        top_row = self.top // CELL_SIZE_M
        return GridCell(
            col=self.left // CELL_SIZE_M + raster_col, row=top_row - 1 - raster_row
        )

    def pixel_of_cell(self, cell: GridCell) -> tuple[int, int]:
        top_row = self.top // CELL_SIZE_M
        raster_row = top_row - 1 - cell.row
        raster_col = cell.col - self.left // CELL_SIZE_M
        if not (0 <= raster_row < self.height and 0 <= raster_col < self.width):
            raise IndexError(f"cell {cell} is outside the window")
        return raster_row, raster_col


def window_for_bounds(left: float, bottom: float, right: float, top: float) -> GridWindow:
    return GridWindow(*snap_bounds(left, bottom, right, top))
