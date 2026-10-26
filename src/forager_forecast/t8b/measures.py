"""M1 to M5 (D159 (2), plan section 5) for T1's units, at both timings, and the swap tables.

Which series a unit reads:
- Rain (M1, M2): its own cell's Daymet series (daymet.py, B-daymet-cell). A cell with no Daymet
  pixel on land reads the nearest of its 8 neighbouring cells that has one, by coastal.land_point
  (RECORD -822's rule, applied to Daymet's land mask: PENDING B-daymet-no-land); with none, the
  unit is marked "none" and its windows are NaN.
- Land (M3 to M5): the unit's own 0.1 degree ERA5-Land point, or its nearest land neighbour where
  its own point has no value, exactly as T8 (t8/weather.py `unit_points`, RECORD -822), with
  "has a value" taken over the three land grids T8b reads.

Windows: the land measures use T8's own window code (t8/weather.py `window_values`, the window
ending `gap` days before the Monday, NaN on any missing day); rain uses daymet.window_values,
which counts Daymet days (B-daymet-leap). `measures_for_units` refuses any unit with a NaN, naming
the count; nothing is filled.

Swaps: as T8 (D136 M-swap), a unit in ISO year Y, week k reads year pi(Y)'s weather for ISO week
k; `per_source_year` computes every unit's measures for each source year, and
t8/weather.py `swapped_matrix` selects rows.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np

from forager_forecast.cells import Cell
from forager_forecast.coastal import land_point
from forager_forecast.daily_grid import DailyGrid
from forager_forecast.t8 import weather as tw
from forager_forecast.t8b import daymet as dm
from forager_forecast.t8b import design
from forager_forecast.t8b.design import LAND_VARIABLES, MEASURES, RAIN


class MissingWeather(LookupError):
    """A unit's window reaches a day or point with no value."""


@dataclass(frozen=True)
class UnitPoints:
    rain: list[tuple[int, int]]  # Daymet cell read, in tenths
    rain_kind: list[str]  # "own", "neighbour" or "none"
    land: list[tuple[int, int]]  # ERA5-Land point read, in tenths
    land_kind: list[str]  # "own", "neighbour" or "none", as T1's npz `land_point`


def land_has_value(grids: dict[str, DailyGrid]) -> set[tuple[int, int]]:
    """Points carrying a value on some day in every land grid (as t8/weather.py)."""
    sets = []
    for v in LAND_VARIABLES:
        g = grids[v]
        has = ~np.isnan(g.values).all(axis=1) if len(g.values) else np.zeros(0, bool)
        sets.append({p for p, i in g.index.items() if has[i]})
    return set.intersection(*sets)


def _pick(own: tuple[int, int], has) -> tuple[tuple[int, int], str]:
    found = land_point(own, has)
    if found is None:
        return own, "none"
    return found[0], ("neighbour" if found[1] else "own")


def unit_points(
    cells: Sequence[Cell], daymet: dm.DaymetCells, grids: dict[str, DailyGrid]
) -> UnitPoints:
    rain_has = set(daymet.index)
    land_has = land_has_value(grids)
    rain, rain_kind, land, land_kind = [], [], [], []
    for cell in cells:
        own = (cell.lat_tenths, cell.lon_tenths)
        p, k = _pick(own, rain_has)
        rain.append(p)
        rain_kind.append(k)
        p, k = _pick(own, land_has)
        land.append(p)
        land_kind.append(k)
    return UnitPoints(rain, rain_kind, land, land_kind)


def measure_matrix(
    daymet: dm.DaymetCells,
    grids: dict[str, DailyGrid],
    points: UnitPoints,
    scored: Sequence[date],
    gap: int,
) -> np.ndarray:
    """[unit, measure] in design.MEASURES order; NaN where a window has no value."""
    cols = []
    for m in MEASURES:
        if m.variable == RAIN:
            cols.append(dm.window_values(daymet, points.rain, scored, m, gap))
        else:
            cols.append(tw.window_values(grids[m.variable], points.land, scored, m, gap))
    return np.column_stack(cols)


def measures_for_units(
    daymet: dm.DaymetCells,
    grids: dict[str, DailyGrid],
    points: UnitPoints,
    scored: Sequence[date],
    gap: int,
) -> np.ndarray:
    """The fit's weather inputs. Refuses until the fit's readings are ruled, and refuses any unit
    whose window touches a missing value."""
    design.require_ruled("fit")
    x = measure_matrix(daymet, grids, points, scored, gap)
    bad = np.isnan(x).any(axis=1)
    if bad.any():
        by = {m.name: int(np.isnan(x[:, j]).sum()) for j, m in enumerate(MEASURES)}
        raise MissingWeather(
            f"{int(bad.sum())} of {len(scored)} units have a window touching a missing value "
            f"(gap {gap}; by measure {by}); they are never filled"
        )
    return x


def per_source_year(
    daymet: dm.DaymetCells,
    grids: dict[str, DailyGrid],
    points: UnitPoints,
    iso_weeks: Sequence[int],
    gap: int,
    source_years: Sequence[int],
) -> dict[int, np.ndarray]:
    """For each source year s, every unit's measures as if its weather were year s's (same ISO
    week, week 53 reading week 52 where s has none, as t8/weather.py `iso_monday`)."""
    table = {}
    for s in source_years:
        mondays = [tw.iso_monday(s, w) for w in iso_weeks]
        table[s] = measures_for_units(daymet, grids, points, mondays, gap)
    return table
