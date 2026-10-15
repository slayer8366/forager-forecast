"""Daily weather on the two climate grids, as arrays, and T1's windows computed from them.

`DailyGrid` holds one variable's daily values on one grid: values[point, day] with the points
named by their index on the grid (tenths of a degree for ERA5-Land, quarters for ERA5) and day 0
at `start`. NaN is a missing value (sea on ERA5-Land, or a day not pulled).

`window_matrix` computes the same numbers as `weather_windows.window_features`, for many units at
once, from cumulative sums: a window of w days covers scored - w through scored - 1, so no unit sees
weather from its own week. A window touching any missing day is NaN here, where the scalar
function raises; the caller counts and refuses such units, never fills them.
tests/test_daily_grid.py checks the two agree on a fixture.
"""

from dataclasses import dataclass
from datetime import date

import numpy as np

from forager_forecast.t1_design import WINDOW_DAYS

# (feature prefix, variable, reduction) in window_features' order.
FEATURES = (
    ("temperature_mean", "temperature", "mean"),
    ("precipitation_sum", "precipitation", "sum"),
    ("soil_temperature_mean", "soil_temperature", "mean"),
    ("soil_moisture_mean", "soil_moisture", "mean"),
)


@dataclass
class DailyGrid:
    start: date
    index: dict[tuple[int, int], int]  # grid point (lat index, lon index) -> row
    values: np.ndarray  # [row, day], float64, NaN missing

    def rows_for(self, points: list[tuple[int, int]]) -> np.ndarray:
        return np.array([self.index.get(p, -1) for p in points])


def feature_names(windows: tuple[int, ...] = WINDOW_DAYS) -> list[str]:
    return [f"{prefix}_{w}d" for w in windows for prefix, _v, _r in FEATURES]


def window_matrix(
    grids: dict[str, DailyGrid],
    points: dict[str, list[tuple[int, int]]],
    scored: list[date],
    windows: tuple[int, ...] = WINDOW_DAYS,
) -> np.ndarray:
    """[unit, feature] in feature_names() order. NaN where any day of a window is missing or the
    unit's grid point is not in the grid."""
    n = len(scored)
    out = np.full((n, len(windows) * len(FEATURES)), np.nan)
    for v_i, (_prefix, variable, reduction) in enumerate(FEATURES):
        grid = grids[variable]
        rows = grid.rows_for(points[variable])
        values = grid.values
        filled = np.where(np.isnan(values), 0.0, values)
        csum = np.concatenate([np.zeros((len(values), 1)), np.cumsum(filled, axis=1)], axis=1)
        cmiss = np.concatenate(
            [np.zeros((len(values), 1)), np.cumsum(np.isnan(values), axis=1)], axis=1
        )
        d0 = np.array([(d - grid.start).days for d in scored])
        ok_row = rows >= 0
        for w_i, w in enumerate(windows):
            col = w_i * len(FEATURES) + v_i
            lo = d0 - w
            inside = ok_row & (lo >= 0) & (d0 <= values.shape[1])
            r, a, b = rows[inside], lo[inside], d0[inside]
            total = csum[r, b] - csum[r, a]
            missing = cmiss[r, b] - cmiss[r, a]
            result = total / w if reduction == "mean" else total
            result = np.where(missing > 0, np.nan, result)
            out[inside, col] = result
    return out
