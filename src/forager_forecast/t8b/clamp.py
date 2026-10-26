"""D159 (2): each measure is clamped to the range of its own fold's training years.

Plan section 5, against the reviews' finding 1 (review-fable.md): in T8, 56-day rain in weeks 45
to 49 of 2021 on the NW Olympic coast was 1,279 to 1,324 mm, above that fold's training maximum of
1,162 mm, and the natural splines ran on linearly past it. With the clamp, a held-out week wetter
than any training week is treated as the wettest training week. It drops and changes no unit.

The range is taken from the training rows of the weather matrix the model is fitted on (PENDING
B-clamp-range, proposed). Training rows are never changed by it.

For the tree models the clamp changes no prediction: a gradient-boosted tree splits only at
thresholds between training values, so any value beyond the training maximum (or minimum) takes
the same branch as the maximum (or minimum) itself. It is applied there anyway, so the frozen
model and the fold models carry the rule D159 names; it bites in the additive model.
"""

from __future__ import annotations

import numpy as np


def training_range(weather: np.ndarray, train: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-column minimum and maximum over the training rows."""
    w = np.asarray(weather, dtype=np.float64)
    t = np.asarray(train, dtype=bool)
    if w.ndim != 2 or t.shape != (len(w),):
        raise ValueError("weather is [unit, measure] and train one flag per unit")
    if not t.any():
        raise ValueError("a clamp needs at least one training row")
    return w[t].min(axis=0), w[t].max(axis=0)


def clamp(weather: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
    """A copy with every value below its column's low set to it, and above its high likewise."""
    low, high = np.asarray(low, dtype=np.float64), np.asarray(high, dtype=np.float64)
    if np.any(low > high):
        raise ValueError("a clamp's low end is above its high end")
    return np.clip(np.asarray(weather, dtype=np.float64), low, high)


def clamp_to_training(weather: np.ndarray, train: np.ndarray) -> np.ndarray:
    low, high = training_range(weather, train)
    return clamp(weather, low, high)
