"""W1 to W4 (plan section 5) for T1's units, at the headline and forecast timings, and the
whole-year weather swaps of C3.

Points, as T1 read them (scripts/pnw_weather.py `weather_matrix`): the land variables at the unit's
own 0.1 degree ERA5-Land point, or its nearest land neighbour where its own point has no value
(coastal.land_point, Forager RECORD -822); rain at the ERA5 0.25 degree point nearest the cell
centre (cells.quarter_cell_for, D46, D54).

Timing: a window of w days whose last day is `gap` days before the scored Monday covers
Monday - gap - w + 1 through Monday - gap. gap 1 is T1's rule (Monday - w through Monday - 1); the
forecast timing is gap 8, the same window 7 days earlier (design.FORECAST_END_GAP).

A window touching a missing day is never filled: `measure_matrix` returns NaN there and
`measures_for_units` refuses, naming the count.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np

from forager_forecast.cells import Cell, quarter_cell_for
from forager_forecast.coastal import land_point
from forager_forecast.daily_grid import DailyGrid
from forager_forecast.t8.design import MEASURES, SEED, Measure

LAND_VARIABLES = ("temperature", "soil_temperature", "soil_moisture")


class MissingWeather(LookupError):
    """A window reaches a day or point with no value."""


def land_has_value(grids: dict[str, DailyGrid]) -> set[tuple[int, int]]:
    """ERA5-Land points carrying a value on some day for all three land variables (as
    scripts/pnw_weather.py `land_has_value`)."""
    sets = []
    for v in LAND_VARIABLES:
        g = grids[v]
        has = ~np.isnan(g.values).all(axis=1) if len(g.values) else np.zeros(0, bool)
        sets.append({p for p, i in g.index.items() if has[i]})
    return set.intersection(*sets)


@dataclass(frozen=True)
class UnitPoints:
    land: list[tuple[int, int]]
    land_kind: list[str]  # "own", "neighbour" or "none", as T1's npz `land_point`
    rain: list[tuple[int, int]]


def unit_points(cells: Sequence[Cell], grids: dict[str, DailyGrid]) -> UnitPoints:
    has = land_has_value(grids)
    land, kind, rain = [], [], []
    for cell in cells:
        own = (cell.lat_tenths, cell.lon_tenths)
        found = land_point(own, has)
        if found is None:
            land.append(own)
            kind.append("none")
        else:
            land.append(found[0])
            kind.append("neighbour" if found[1] else "own")
        q = quarter_cell_for(cell.center_latitude, cell.center_longitude)
        rain.append((q.lat_quarters, q.lon_quarters))
    return UnitPoints(land, kind, rain)


def window_values(
    grid: DailyGrid,
    points: list[tuple[int, int]],
    scored: Sequence[date],
    measure: Measure,
    gap: int,
) -> np.ndarray:
    """One measure per unit; NaN where the point is absent or any day of the window is missing."""
    if gap < 1:
        raise ValueError("a window must end before the scored day")
    if len(points) != len(scored):
        raise ValueError(f"{len(points)} points for {len(scored)} scored days")
    rows = grid.rows_for(points)
    values = grid.values
    filled = np.where(np.isnan(values), 0.0, values)
    csum = np.concatenate([np.zeros((len(values), 1)), np.cumsum(filled, axis=1)], axis=1)
    cmiss = np.concatenate(
        [np.zeros((len(values), 1)), np.cumsum(np.isnan(values), axis=1)], axis=1
    )
    d0 = np.array([(d - grid.start).days for d in scored])
    hi = d0 - gap + 1  # half-open end: the window's last day is d0 - gap
    lo = hi - measure.days
    out = np.full(len(scored), np.nan)
    inside = (rows >= 0) & (lo >= 0) & (hi <= values.shape[1])
    r, a, b = rows[inside], lo[inside], hi[inside]
    total = csum[r, b] - csum[r, a]
    missing = cmiss[r, b] - cmiss[r, a]
    if measure.reduction == "sum":
        result = total
    elif measure.reduction == "mean":
        result = total / measure.days
    else:
        raise ValueError(f"unknown reduction {measure.reduction!r}")
    out[inside] = np.where(missing > 0, np.nan, result)
    return out


def measure_matrix(
    grids: dict[str, DailyGrid],
    points: UnitPoints,
    scored: Sequence[date],
    gap: int,
    measures: Sequence[Measure] = MEASURES,
) -> np.ndarray:
    """[unit, measure] in MEASURES order."""
    cols = []
    for m in measures:
        pts = points.rain if m.variable == "precipitation" else points.land
        cols.append(window_values(grids[m.variable], pts, scored, m, gap))
    return np.column_stack(cols)


def measures_for_units(
    grids: dict[str, DailyGrid],
    points: UnitPoints,
    scored: Sequence[date],
    gap: int,
    measures: Sequence[Measure] = MEASURES,
) -> np.ndarray:
    x = measure_matrix(grids, points, scored, gap, measures)
    bad = np.isnan(x).any(axis=1)
    if bad.any():
        raise MissingWeather(
            f"{int(bad.sum())} of {len(scored)} units have a window touching a missing value "
            f"(gap {gap}); they are never filled"
        )
    return x


# Whole-year swaps (C3) ----------------------------------------------------------------------


def iso_monday(year: int, week: int) -> date:
    """Monday of ISO week `week` of `year`; week 53 reads week 52 in a year that has no week 53
    (the same fold as effort.season_slot)."""
    last = date(year, 12, 28).isocalendar().week  # 28 December is always in the last ISO week
    return date.fromisocalendar(year, min(week, last), 1)


def swapped_mondays(
    iso_years: Sequence[int], iso_weeks: Sequence[int], mapping: dict[int, int]
) -> list[date]:
    """The Monday each unit reads its weather for under a swap: ISO year Y reads year mapping[Y],
    the same ISO week, for every cell alike."""
    return [iso_monday(mapping[y], w) for y, w in zip(iso_years, iso_weeks, strict=True)]


def draw_swaps(years: Sequence[int], n: int, seed: int = SEED) -> list[dict[int, int]]:
    """n distinct random derangements of the years (no year keeps its own weather), seeded."""
    years = list(years)
    if len(years) < 2:
        raise ValueError("a swap needs at least two years")
    rng = np.random.default_rng(seed)
    seen: set[tuple[int, ...]] = set()
    out = []
    while len(out) < n:
        perm = rng.permutation(len(years))
        if np.any(perm == np.arange(len(years))):
            continue
        key = tuple(int(p) for p in perm)
        if key in seen:
            continue
        seen.add(key)
        out.append({years[i]: years[int(p)] for i, p in enumerate(perm)})
    return out


def per_source_year(
    grids: dict[str, DailyGrid],
    points: UnitPoints,
    iso_years: Sequence[int],
    iso_weeks: Sequence[int],
    gap: int,
    source_years: Sequence[int],
    measures: Sequence[Measure] = MEASURES,
) -> dict[int, np.ndarray]:
    """For each source year s, every unit's measures as if its weather were year s's (same ISO
    week). A swap then only selects rows: x[i] = table[mapping[Y_i]][i]."""
    table = {}
    for s in source_years:
        mondays = [iso_monday(s, w) for w in iso_weeks]
        table[s] = measures_for_units(grids, points, mondays, gap, measures)
    return table


def swapped_matrix(
    table: dict[int, np.ndarray], iso_years: Sequence[int], mapping: dict[int, int]
) -> np.ndarray:
    years = np.asarray(iso_years)
    n_cols = next(iter(table.values())).shape[1]
    out = np.empty((len(years), n_cols))
    for y, s in mapping.items():
        rows = years == y
        out[rows] = table[s][rows]
    if len(years) and not np.isin(years, list(mapping)).all():
        raise ValueError("a unit's year has no swap")
    return out
