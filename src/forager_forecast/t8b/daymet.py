"""Daymet V4 daily precipitation, as delivered, to one rain series per 0.1 degree cell (M1, M2).

The layout read is the one the Daymet V4 R1 user guide describes (read at source 2026-10-26,
https://daac.ornl.gov/DAYMET/guides/Daymet_Daily_V4R1.html): one netCDF-4 file per variable and
year, `prcp` [time, y, x] in mm per day on a 1 km Lambert Conformal Conic grid, 2-D `lat` and
`lon` [y, x] giving each pixel centre, `time` in days since 1950-01-01 stamped at noon, and a
fill value off land. A gridded subset of the box (the NetCDF Subset Service's output) has the
same layout. h5py reads it, as scripts/pnw_weather.py reads the store's files.

Proposed readings, not in force until ruled (design.PENDING):
- B-daymet-cell: a cell's rain on a day is the mean of the pixels whose centre falls in the cell
  by D46's rule (cells.cell_for, the same rule records use), over the pixels that carry a value on
  every day. A pixel with no value on any day is off Daymet's land mask and is left out; a pixel
  with values on some days but not all is refused, never filled.
- B-daymet-leap: Daymet's year has 365 days, so 31 December is not delivered in a leap year
  ("The Daymet Calendar" in the same guide). A window counts Daymet days: a w-day window is the w
  delivered days ending the day before the week, reaching one calendar day further back when it
  spans a dropped 31 December. Every total is a sum of w delivered values; none is filled.
- B-daymet-day: Daymet's day d is calendar day d.
A day that should have been delivered and was not (not pulled) is missing, and any window touching
it is NaN, which measures.measures_for_units refuses, as T8's weather.py does.

Memory: values are read a chunk of days at a time and summed into cells with one bincount per day,
so the 1 km grid is never held whole (a box subset is about 427,000 pixels a day).
"""

from __future__ import annotations

import bisect
import calendar
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import h5py
import numpy as np

from forager_forecast.cells import cell_for
from forager_forecast.t8.design import Measure

EPOCH = date(1950, 1, 1)
TIME_UNITS = re.compile(r"days since 1950-01-01( 00:00:00)?")


class DaymetDiffers(ValueError):
    """A Daymet file is not laid out as Daymet delivers it."""


@dataclass
class DaymetCells:
    days: list[date]  # the delivered days, ascending
    index: dict[tuple[int, int], int]  # cell (lat tenths, lon tenths) -> row
    values: np.ndarray  # [row, day] mm, mean over the cell's pixels
    pixels: dict[tuple[int, int], int]  # cell -> pixels averaged


def dropped_days(first: date, last: date) -> list[date]:
    """31 December of every leap year from first to last: the days Daymet does not deliver."""
    return [
        date(y, 12, 31)
        for y in range(first.year, last.year + 1)
        if calendar.isleap(y) and first <= date(y, 12, 31) <= last
    ]


def _text(value) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)


def _days(h: h5py.File, path: Path) -> list[date]:
    units = _text(h["time"].attrs.get("units", b""))
    if not TIME_UNITS.fullmatch(units):
        raise DaymetDiffers(f"{path.name}: time units {units!r}, not days since 1950-01-01")
    raw = np.asarray(h["time"][:], dtype=np.float64)
    whole = np.floor(raw)
    if not np.allclose(raw - whole, 0.5):
        raise DaymetDiffers(f"{path.name}: time is not stamped at noon")
    return [EPOCH + timedelta(days=int(v)) for v in whole]


def _fill(h: h5py.File) -> float | None:
    for key in ("_FillValue", "missing_value"):
        if key in h["prcp"].attrs:
            return float(np.asarray(h["prcp"].attrs[key]).ravel()[0])
    return None


def _cell_labels(lat: np.ndarray, lon: np.ndarray) -> tuple[np.ndarray, list[tuple[int, int]]]:
    """Each pixel's cell, as an integer label, and the cells in label order."""
    cells: dict[tuple[int, int], int] = {}
    labels = np.empty(lat.size, dtype=np.int64)
    for i, (a, b) in enumerate(zip(lat.ravel().tolist(), lon.ravel().tolist(), strict=True)):
        c = cell_for(float(a), float(b))
        labels[i] = cells.setdefault((c.lat_tenths, c.lon_tenths), len(cells))
    return labels, list(cells)


def _sum_file(prcp, fill, labels, n_cells, n_days, chunk_days) -> tuple[np.ndarray, np.ndarray]:
    """Per-day cell sums over the pixels with a value, and each pixel's count of missing days."""
    missing_count = np.zeros(labels.size, dtype=np.int64)
    sums = np.zeros((n_days, n_cells))
    for t0 in range(0, n_days, chunk_days):
        block = np.asarray(prcp[t0 : t0 + chunk_days], dtype=np.float64)
        block = block.reshape(len(block), -1)
        missing = np.isnan(block) if fill is None else (np.isnan(block) | (block == fill))
        missing_count += missing.sum(axis=0)
        block = np.where(missing, 0.0, block)
        for k in range(len(block)):
            sums[t0 + k] = np.bincount(labels, weights=block[k], minlength=n_cells)
    return sums, missing_count


def read_daymet(paths: Sequence[Path], chunk_days: int = 31) -> DaymetCells:
    """Every file's days, summed into cells. Files must share one pixel grid and one land mask."""
    lat = lon = labels = None
    cells: list[tuple[int, int]] = []
    pixel_counts: np.ndarray | None = None
    by_day: dict[date, np.ndarray] = {}
    for path in map(Path, paths):
        with h5py.File(path, "r") as h:
            days = _days(h, path)
            la, lo = np.asarray(h["lat"][:]), np.asarray(h["lon"][:])
            if lat is None:
                lat, lon = la, lo
                labels, cells = _cell_labels(lat, lon)
            elif not (np.array_equal(la, lat) and np.array_equal(lo, lon)):
                raise DaymetDiffers(f"{path.name}: lat and lon differ from the first file's")
            prcp = h["prcp"]
            if prcp.shape != (len(days), *lat.shape):
                raise DaymetDiffers(f"{path.name}: prcp {prcp.shape} for {len(days)} days")
            sums, missing_count = _sum_file(
                prcp, _fill(h), labels, len(cells), len(days), chunk_days
            )
        partial = (missing_count > 0) & (missing_count < len(days))
        if partial.any():
            raise DaymetDiffers(
                f"{path.name}: {int(partial.sum())} pixel(s) carry values on some days but not all"
            )
        counts = np.bincount(labels, weights=(missing_count == 0) * 1.0, minlength=len(cells))
        if pixel_counts is None:
            pixel_counts = counts
        elif not np.array_equal(counts, pixel_counts):
            raise DaymetDiffers(f"{path.name}: the land mask differs from the first file's")
        for k, d in enumerate(days):
            if d in by_day:
                raise DaymetDiffers(f"{path.name}: {d} is delivered twice")
            by_day[d] = sums[k]
    if pixel_counts is None:
        raise DaymetDiffers("no Daymet file given")
    keep = [i for i in range(len(cells)) if pixel_counts[i] > 0]
    days_sorted = sorted(by_day)
    values = np.array([by_day[d] for d in days_sorted]).T[keep] / pixel_counts[keep, None]
    return DaymetCells(
        days=days_sorted,
        index={cells[i]: r for r, i in enumerate(keep)},
        values=values,
        pixels={cells[i]: int(pixel_counts[i]) for i in keep},
    )


def _axis(series: DaymetCells) -> tuple[list[date], np.ndarray]:
    """Daymet's calendar from the first to the last delivered day (no dropped 31 December), and
    the values on it, NaN on a day of that calendar that was not delivered."""
    first, last = series.days[0], series.days[-1]
    dropped = set(dropped_days(first, last))
    every = (first + timedelta(days=i) for i in range((last - first).days + 1))
    axis = [d for d in every if d not in dropped]
    at = {d: k for k, d in enumerate(series.days)}
    cols = np.array([at.get(d, -1) for d in axis])
    values = np.full((len(series.values), len(axis)), np.nan)
    have = cols >= 0
    values[:, have] = series.values[:, cols[have]]
    return axis, values


def window_values(
    series: DaymetCells,
    cells: Sequence[tuple[int, int]],
    scored: Sequence[date],
    measure: Measure,
    gap: int,
) -> np.ndarray:
    """One measure per unit: the `measure.days` Daymet days ending `gap` days before the scored
    Monday (B-daymet-leap, proposed). NaN where the cell has no series or the window reaches a day
    outside what was delivered."""
    if gap < 1:
        raise ValueError("a window must end before the scored day")
    if len(cells) != len(scored):
        raise ValueError(f"{len(cells)} cells for {len(scored)} scored days")
    if measure.reduction not in ("sum", "mean"):
        raise ValueError(f"unknown reduction {measure.reduction!r}")
    out = np.full(len(scored), np.nan)
    if not series.days:
        return out
    axis, values = _axis(series)
    ordinals = [d.toordinal() for d in axis]
    filled = np.where(np.isnan(values), 0.0, values)
    csum = np.concatenate([np.zeros((len(values), 1)), np.cumsum(filled, axis=1)], axis=1)
    cmiss = np.concatenate(
        [np.zeros((len(values), 1)), np.cumsum(np.isnan(values), axis=1)], axis=1
    )
    for u, (cell, monday) in enumerate(zip(cells, scored, strict=True)):
        row = series.index.get(tuple(cell))
        last_day = monday - timedelta(days=gap)
        if row is None or last_day > axis[-1]:
            continue
        hi = bisect.bisect_right(ordinals, last_day.toordinal())  # half-open end
        lo = hi - measure.days
        if lo < 0 or cmiss[row, hi] - cmiss[row, lo] > 0:
            continue
        total = csum[row, hi] - csum[row, lo]
        out[u] = total if measure.reduction == "sum" else total / measure.days
    return out
