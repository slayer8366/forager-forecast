"""T7: the model's construction (P5), effort held constant (P6), and the model ladder (P7, D129).

P5: LightGBM 4.7.0, binary objective, T1's determinism settings, with ``log_effort`` kept apart
from every habitat input (``interaction_constraints``) and rising only (``monotone_constraints``).
Then the raw score is a habitat part plus an effort part, so holding effort at any constant shifts
every cell by the same amount and the map's ranking does not depend on the value (P6). The test
checks this on a fitted model, at two effort levels.

P6: the held value is the median of ``log_effort`` over the frame's weather cells holding an
eligible box cell, computed once and written into the manifest.

The ladder (P7 point 5, D129 as read by D135 and D138): comparison A, effort only; comparison B,
effort plus conifer cover and broadleaf cover (share times total cover); the base model; and the
base plus each candidate band alone. A candidate is kept when its pooled held-out AUC difference
over the base has an interval wholly above zero.
"""

from __future__ import annotations

import numpy as np

_STUB = "T7 build: not written yet (tests first)"

SEED = 20260918
EFFORT = "log_effort"
CONIFER_COVER = "conifer_cover_pct"
BROADLEAF_COVER = "broadleaf_cover_pct"


def lgb_params(config: dict, features: list[str], threads: int = 1) -> dict:
    raise NotImplementedError(_STUB)


def train(config: dict, features: list[str], x, y, w, threads: int = 1):
    raise NotImplementedError(_STUB)


def fitter_for(features: list[str], threads: int = 1):
    """A folds.Fitter that trains with P5's constraints and returns probabilities."""
    raise NotImplementedError(_STUB)


def predict_at_effort(booster, features: list[str], x: np.ndarray, value: float) -> np.ndarray:
    """Raw scores with every row's log_effort set to ``value``."""
    raise NotImplementedError(_STUB)


def held_effort(log_effort_by_weather_cell: np.ndarray) -> float:
    raise NotImplementedError(_STUB)


def cover_columns(share_conifer, share_broadleaf, total_cover_pct) -> tuple:
    raise NotImplementedError(_STUB)


def ladder(base: list[str], candidates: list[str]) -> dict[str, list[str]]:
    raise NotImplementedError(_STUB)


def kept_candidates(differences: dict) -> list[str]:
    raise NotImplementedError(_STUB)
