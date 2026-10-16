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
``log_effort`` is not a predictor here (P8): it is held constant for the map. A predictor with no
spread in the training data (R's ``scale`` would divide by zero) is scaled by 1, so it adds no
distance.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import pdist

SEED = 20260918
MAX_EXACT = 5000
PAIRS = 2_000_000


def importance_weights(gains: np.ndarray) -> np.ndarray:
    w = np.asarray(gains, dtype=np.float64).copy()
    w[w < 0] = 0.0
    if w.sum() == 0:
        raise ValueError("importance weights sum to 0")
    return w


def di_threshold(train_di: np.ndarray) -> float:
    di = np.asarray(train_di, dtype=np.float64)
    di = di[np.isfinite(di)]
    q25, q75 = np.quantile(di, [0.25, 0.75])  # numpy's default is R's type 7
    return float(min(q75 + 1.5 * (q75 - q25), di.max()))


def mean_pairwise_distance(z: np.ndarray, max_exact: int = MAX_EXACT, pairs: int = PAIRS,
                           seed: int = SEED) -> tuple[float, bool]:  # fmt: skip
    """(mean distance between distinct training points, exact or not)."""
    z = np.asarray(z, dtype=np.float64)
    n = len(z)
    if n < 2:
        raise ValueError("a mean distance needs two training points")
    if n <= max_exact:
        return float(pdist(z).mean()), True
    rng = np.random.default_rng(seed)
    i = rng.integers(0, n, size=pairs)
    j = rng.integers(0, n - 1, size=pairs)
    j = np.where(j >= i, j + 1, j)  # uniform over j != i
    return float(np.linalg.norm(z[i] - z[j], axis=1).mean()), False


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

    def _z(self, x: np.ndarray) -> np.ndarray:
        return (np.asarray(x, dtype=np.float64) - self.center) / self.scale * self.weights

    def dissimilarity(self, x: np.ndarray) -> np.ndarray:
        z = self._z(np.atleast_2d(x))
        ok = np.isfinite(z).all(axis=1)
        di = np.full(len(z), np.nan)
        if ok.any():
            if getattr(self, "_tree", None) is None:
                self._tree = cKDTree(self.train)
            d, _ = self._tree.query(z[ok], k=1)
            di[ok] = d / self.mean_distance
        return di

    def inside(self, x: np.ndarray) -> np.ndarray:
        di = self.dissimilarity(x)
        return np.isfinite(di) & (di <= self.threshold)


def fit_aoa(x: np.ndarray, gains: np.ndarray, folds: np.ndarray, max_exact: int = MAX_EXACT,
            pairs: int = PAIRS, seed: int = SEED) -> Aoa:  # fmt: skip
    """``folds``: the cross-validation fold (level III block) of each training point."""
    x = np.asarray(x, dtype=np.float64)
    folds = np.asarray(folds)
    if not np.isfinite(x).all():
        raise ValueError("training predictors must all be defined")
    if len(np.unique(folds)) < 2:
        raise ValueError("cross-validated DI needs at least two folds")
    weights = importance_weights(gains)
    center = x.mean(axis=0)
    scale = x.std(axis=0, ddof=1)
    scale = np.where(scale > 0, scale, 1.0)
    z = (x - center) / scale * weights
    nearest = np.empty(len(z))
    for f in np.unique(folds):
        held = folds == f
        d, _ = cKDTree(z[~held]).query(z[held], k=1)
        nearest[held] = d
    mean_distance, exact = mean_pairwise_distance(z, max_exact, pairs, seed)
    train_di = nearest / mean_distance
    return Aoa(center, scale, weights, z, mean_distance, exact, train_di, di_threshold(train_di))
