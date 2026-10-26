"""C5's frozen model."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

class ChecksumDiffers(RuntimeError):
    pass

@dataclass(frozen=True)
class FrozenModel:
    name: str
    config: dict
    features: tuple[str, ...]
    clamp_low: tuple[float, ...]
    clamp_high: tuple[float, ...]
    weather_columns: tuple[int, ...]
    training_years: tuple[int, ...]
    booster: str
    meta: dict

def fit_frozen(name, x, y, years, configs, features, weather_columns, threads=1, meta=None):
    raise NotImplementedError

def predict(model: FrozenModel, x: np.ndarray) -> np.ndarray:
    raise NotImplementedError

def save(model: FrozenModel, path) -> str:
    raise NotImplementedError

def load(path, expected_sha256: str) -> FrozenModel:
    raise NotImplementedError
