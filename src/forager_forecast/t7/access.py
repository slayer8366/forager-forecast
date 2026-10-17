"""T7 part B: each 250 m cell's distance to the nearest road, trail, and either.

Dispatch 2026-10-17-T7B (Forager RECORD -1163; the owner's rulings and the planner's calls in
-1168).

- **Distance** is exact: from each cell centre to the nearest line, in metres on the grid plane
  (ESRI:102008), by shapely's STRtree. That plane is equal-area, not equidistant: over the PNW box
  its scale is 0.940 to 0.945 along parallels and 1.058 to 1.063 along meridians (pyproj), so a
  distance is off from the ground distance by up to about 6%, depending on direction. Kept in grid
  metres by the planner's call (-1168), the unit the cells themselves are measured in.
- **Blocks.** A block of cells is answered from the lines whose envelopes meet the block widened by
  a radius R. Any line within R of a cell meets that rectangle, so every cell whose nearest line
  lies within R is exact; the rest are asked again with R four times larger, up to a ceiling,
  beyond which a cell has no value (NaN, counted by the caller), never a made-up one.
- **Bands.** Roads (with roads closed to motor vehicles, the owner's ruling 3); trails (federal
  sources only, ruling 2); the nearer of the two. Where the Forest Service publishes trail records
  without lines (Umatilla and Wallowa-Whitman, ruling 1) the trail and combined bands are NaN and a
  separate mask says why. They are never filled.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import shapely

from forager_forecast.grid import CELL_SIZE_M, GridWindow

BAND_ROAD = "dist_road_m"
BAND_TRAIL = "dist_trail_m"
BAND_ANY = "dist_any_m"
OUTPUT_BANDS = (BAND_ROAD, BAND_TRAIL, BAND_ANY)

# NTD road classes (``tnmfrc``) left out: 7 ferry crossings (MTFCC L4165) and 8 tunnels, as the
# national service's "Ferries and Tunnels" layer groups them (read 2026-10-17). A ferry is not a
# road, and a tunnel's line is not reachable along its length. Every other class is kept: limited
# access, secondary, local connecting, local, ramps, 4WD. The NTD file carries no closed-roads class
# (no field for it); the Forest Service file carries its closed roads (maintenance level 1), kept.
NTD_ROAD_CLASSES_LEFT_OUT = frozenset({7, 8})
# The two forests whose trail records carry no lines (verify report: Umatilla 549 records, 0 with
# a line; Wallowa-Whitman 936, 3), by the Forest Service's forest org code (the owner's ruling 1).
TRAILS_UNPUBLISHED_FORESTS = {"0614": "Umatilla National Forest",
                              "0616": "Wallowa-Whitman National Forest"}  # fmt: skip
PAD_M = 50_000

FEDERAL_TRAIL_ORIGINATORS = frozenset({
    "U.S. Forest Service", "Bureau of Land Management", "National Park Service",
    "U.S. Fish and Wildlife Service",
})  # fmt: skip


def cell_centres(window: GridWindow) -> tuple[np.ndarray, np.ndarray]:
    """(x, y) of every cell centre, shape (height, width), rows north to south: the centres
    ``t6b_mask.cell_lonlat`` projects, so this layer keys to T7's cells by construction."""
    xs = window.left + (np.arange(window.width) + 0.5) * CELL_SIZE_M
    ys = window.top - (np.arange(window.height) + 0.5) * CELL_SIZE_M
    gx, gy = np.meshgrid(xs, ys)
    return gx.astype(np.float64), gy.astype(np.float64)


def nearest_distance(geoms, x: np.ndarray, y: np.ndarray, max_distance: float | None = None
                     ) -> np.ndarray:  # fmt: skip
    """Distance from each point to the nearest of ``geoms``; NaN with no line (within
    ``max_distance`` when given)."""
    x = np.asarray(x, dtype=np.float64)
    out = np.full(x.shape, np.nan)
    geoms = np.asarray(geoms, dtype=object)
    if len(geoms) == 0 or x.size == 0:
        return out
    tree = shapely.STRtree(geoms)
    points = shapely.points(x, np.asarray(y, dtype=np.float64))
    (idx, _), dist = tree.query_nearest(points, max_distance=max_distance,
                                        return_distance=True, all_matches=False)  # fmt: skip
    out[idx] = dist
    return out


def block_distances(read_lines: Callable[[tuple[float, float, float, float]], np.ndarray],
                    window: GridWindow, inside: np.ndarray, start_radius: float = 8000.0,
                    max_radius: float = 2_000_000.0) -> np.ndarray:  # fmt: skip
    """Exact nearest-line distance for the cells of ``window`` where ``inside``; NaN elsewhere
    and where no line lies within ``max_radius``. ``read_lines(bbox)`` returns at least every
    line whose envelope meets ``bbox`` (minx, miny, maxx, maxy)."""
    out = np.full((window.height, window.width), np.nan)
    gx, gy = cell_centres(window)
    todo = np.asarray(inside, dtype=bool).copy()
    radius = float(start_radius)
    while todo.any():
        r = min(radius, max_radius)
        bbox = (float(window.left - r), float(window.bottom - r), float(window.right + r),
                float(window.top + r))  # fmt: skip
        lines = read_lines(bbox)
        d = nearest_distance(lines, gx[todo], gy[todo], max_distance=r)
        found = ~np.isnan(d)
        rows, cols = np.nonzero(todo)
        out[rows[found], cols[found]] = d[found]
        todo[rows[found], cols[found]] = False
        if r >= max_radius:
            break
        radius *= 4.0
    return out


def combine(road: np.ndarray, trail: np.ndarray, unpublished: np.ndarray):
    """(trail, any): the trail band with unpublished cells set to NaN, and the nearer of road
    and trail, NaN wherever either is (so it is never the road alone where trails are unknown)."""
    trail = np.where(unpublished, np.nan, trail)
    either = np.fmin(road, trail)
    either[np.isnan(road) | np.isnan(trail)] = np.nan
    return trail, either


def keep_trail(originators) -> np.ndarray:
    """True for a trail segment whose source is a federal agency (the owner's ruling 2)."""
    return np.array([o in FEDERAL_TRAIL_ORIGINATORS for o in originators], dtype=bool)


def keep_road_class(tnmfrc) -> np.ndarray:
    """True for an NTD road segment of a kept class (see ``NTD_ROAD_CLASSES_LEFT_OUT``)."""
    v = np.asarray(tnmfrc, dtype=object)
    return np.array([x is not None and int(x) not in NTD_ROAD_CLASSES_LEFT_OUT for x in v],
                    dtype=bool)  # fmt: skip
