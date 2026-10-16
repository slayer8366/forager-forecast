"""T7 item 11: the area of applicability in Python, after CAST (P8).

Method as implemented by CAST 1.2.0 (Meyer, Ludwig, Schumacher; GPL >= 2), whose source was read
on 2026-10-16 (https://github.com/HannaMeyer/CAST, ``R/trainDI.R``, ``R/aoa.R``,
``R/aoa-helpers.R``); the published paper (Meyer and Pebesma 2021, doi 10.1111/2041-210X.13650)
was refused by the publisher's page and is not read. What is re-implemented, not copied:

- Each predictor is centred and scaled by the training mean and standard deviation (R's
  ``scale``, n - 1), then multiplied by its weight, the model's importance, negatives set to 0,
  all zero refused (``.check_weights``, ``.apply_weights``).
- Training DI: each training point's distance to its nearest training point outside its own
  cross-validation fold, divided by the mean distance between training points
  (``trainDist_avrgmean``: the mean over points of each point's mean distance to all others).
- Threshold (``.di_threshold``): ``quantile(trainDI, 0.75) + 1.5 * IQR(trainDI)``, R's default
  quantile type 7, capped at the largest training DI.
- New data: DI is the distance to the nearest training point over the same mean; a cell is
  outside when DI exceeds the threshold.

One departure, disclosed: CAST computes the mean training distance exactly in chunks. Over about
half a million training points that is about 10^11 pairs, so above ``MAX_EXACT`` points it is
estimated from ``PAIRS`` random pairs (seed 20260918); at or below it, it is exact.
``log_effort`` is not a predictor here (P8): it is held constant for the map.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_STUB = "T7 build: not written yet (tests first)"

SEED = 20260918
MAX_EXACT = 5000
PAIRS = 2_000_000


def importance_weights(gains: np.ndarray) -> np.ndarray:
    raise NotImplementedError(_STUB)


def di_threshold(train_di: np.ndarray) -> float:
    raise NotImplementedError(_STUB)


def mean_pairwise_distance(z: np.ndarray, max_exact: int = MAX_EXACT, pairs: int = PAIRS,
                           seed: int = SEED) -> tuple[float, bool]:  # fmt: skip
    """(mean distance between distinct training points, exact or not)."""
    raise NotImplementedError(_STUB)


@dataclass
class Aoa:
    center: np.ndarray
    scale: np.ndarray
    weights: np.ndarray
    train: np.ndarray
    mean_distance: float
    mean_distance_exact: bool
    train_di: np.ndarray
    threshold: float

    def dissimilarity(self, x: np.ndarray) -> np.ndarray:
        raise NotImplementedError(_STUB)

    def inside(self, x: np.ndarray) -> np.ndarray:
        raise NotImplementedError(_STUB)


def fit_aoa(x: np.ndarray, gains: np.ndarray, folds: np.ndarray, max_exact: int = MAX_EXACT,
            pairs: int = PAIRS, seed: int = SEED) -> Aoa:  # fmt: skip
    """``folds``: the cross-validation fold (level III block) of each training point."""
    raise NotImplementedError(_STUB)
