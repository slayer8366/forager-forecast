"""C5: the unseen season."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

class C5Refused(RuntimeError):
    pass

@dataclass(frozen=True)
class C5Units:
    unit: np.ndarray
    cell: np.ndarray
    iso_year: np.ndarray
    iso_week: np.ndarray
    y: np.ndarray
    x_main: np.ndarray
    x_calendar: np.ndarray

def check_download(created) -> None:
    raise NotImplementedError

def score_c5(main, calendar, units, download_created, excluded_weeks=()):
    raise NotImplementedError
