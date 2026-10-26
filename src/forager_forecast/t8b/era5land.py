"""ERA5-Land layer 2 and 2 m fields, as the store delivers them, to daily grids (M3 to M5)."""
from __future__ import annotations
import numpy as np
from forager_forecast.daily_grid import DailyGrid

class Era5Differs(ValueError):
    """A file is not laid out as the store delivers it."""

def read_daily_statistics(paths) -> dict[str, dict[tuple[int, int], dict]]:
    raise NotImplementedError

def read_hourly(paths) -> dict[str, dict[tuple[int, int], dict]]:
    raise NotImplementedError

def land_grids(raw) -> dict[str, DailyGrid]:
    raise NotImplementedError
