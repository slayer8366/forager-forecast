"""M1 to M5 for T1's units."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

class MissingWeather(LookupError):
    pass

@dataclass(frozen=True)
class UnitPoints:
    rain: list[tuple[int, int]]
    rain_kind: list[str]
    land: list[tuple[int, int]]
    land_kind: list[str]

def unit_points(cells, daymet, grids) -> UnitPoints:
    raise NotImplementedError

def measure_matrix(daymet, grids, points, scored, gap) -> np.ndarray:
    raise NotImplementedError

def measures_for_units(daymet, grids, points, scored, gap) -> np.ndarray:
    raise NotImplementedError

def per_source_year(daymet, grids, points, iso_weeks, gap, source_years) -> dict[int, np.ndarray]:
    raise NotImplementedError
