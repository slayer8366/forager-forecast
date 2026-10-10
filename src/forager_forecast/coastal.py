"""Which ERA5-Land point a 0.1° cell reads its land weather from (owner, Forager RECORD -822).

A cell whose own ERA5-Land point carries values reads that point. A cell whose own point carries
none (sea or lake on ERA5-Land's land mask, for example coastal and island cells) reads the
nearest of its 8 neighbouring points that carries values, by great-circle distance from the cell
centre. Exact ties go toward +infinity: north on latitude first, then east on longitude, as D63
does for grid ties. A cell with no neighbour carrying values has no land point and stays out,
counted. The owner's words (RECORD -822): "Nearest land neighbour (Recommended)".

Precipitation is not affected: it comes from ERA5 at 0.25°, which covers sea and land.
"""

import math
from collections.abc import Collection

NEIGHBOURS = tuple((a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0))


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def land_point(
    cell: tuple[int, int], has_value: Collection[tuple[int, int]]
) -> tuple[tuple[int, int], bool] | None:
    """(point in tenths, filled from a neighbour?) for a cell in tenths, or None."""
    if cell in has_value:
        return cell, False
    lat, lon = cell[0] / 10, cell[1] / 10
    best = None
    for a, b in NEIGHBOURS:
        p = (cell[0] + a, cell[1] + b)
        if p not in has_value:
            continue
        d = round(_distance_km(lat, lon, p[0] / 10, p[1] / 10), 9)
        key = (d, -p[0], -p[1])  # shorter first; on a tie, north then east
        if best is None or key < best[0]:
            best = (key, p)
    return (best[1], True) if best else None
