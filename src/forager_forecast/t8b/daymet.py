"""Daymet V4 daily precipitation, as delivered, to one rain series per 0.1 degree cell (M1, M2)."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import numpy as np

class DaymetDiffers(ValueError):
    """A Daymet file is not laid out as Daymet delivers it."""

@dataclass
class DaymetCells:
    days: list[date]
    index: dict[tuple[int, int], int]
    values: np.ndarray
    pixels: dict[tuple[int, int], int]

def dropped_days(first: date, last: date) -> list[date]:
    raise NotImplementedError

def read_daymet(paths, chunk_days: int = 31) -> DaymetCells:
    raise NotImplementedError

def window_values(series: DaymetCells, cells, scored, measure, gap: int) -> np.ndarray:
    raise NotImplementedError
