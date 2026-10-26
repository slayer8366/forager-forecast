"""T8b's models (plan section 6; D159 (4)).

- Main model: gradient-boosted trees in T1's form, the same as T8's challenger
  (t8/models.py `challenger_matrix`: day-of-year sine and cosine, latitude, longitude, the log of
  T6's expected outings for the fold, then the weather), with M1 to M5 clamped to the fold's
  training range (clamp.py). Each fold's configuration is chosen by T1's inner leave-one-year-out
  on that fold's training years (t1_model.inner_choice, T1's 20 configurations); `fixed_choice`
  reuses it, which is how the 199 swaps hold the tuning fixed (D159 (4)).
- No-weather twin: the same without M1 to M5 (`use_weather=False`), tuned on its own.
- Readable model, reported beside with no verdict: T8's additive logistic model (t8/models.py
  `design_matrix`, `fit_predict_logistic`, its PROPOSED_SPEC as D136 ruled) on the clamped
  measures, fold by fold.

The inner tuning folds see the outer fold's clamped weather and are not clamped again; for trees
this changes nothing (clamp.py).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from forager_forecast import t1_model as tm
from forager_forecast.t8 import models as md
from forager_forecast.t8b import clamp as cl


def _weather(inputs: md.Inputs, weather: np.ndarray | None) -> np.ndarray:
    w = inputs.weather if weather is None else weather
    if w is None:
        raise ValueError("the weather model needs weather")
    return w


def loyo_trees(
    inputs: md.Inputs,
    use_weather: bool,
    configs: Sequence[dict],
    fitter: md.Fitter,
    weather: np.ndarray | None = None,
    fixed_choice: dict[int, str] | None = None,
) -> tuple[np.ndarray, dict[int, str]]:
    """Held-out predictions for every unit and each fold's configuration id."""
    by_id = {c["id"]: c for c in configs}
    w = _weather(inputs, weather) if use_weather else None
    out = np.full(len(inputs.y), np.nan)
    chosen: dict[int, str] = {}
    for h in sorted(set(inputs.years.tolist())):
        held = inputs.years == h
        fold_w = cl.clamp_to_training(w, ~held) if use_weather else None
        x = md.challenger_matrix(inputs, h, use_weather, fold_w)
        if fixed_choice is None:
            best, _scores = tm.inner_choice(
                configs, x[~held], inputs.y[~held], inputs.years[~held], fitter
            )
        else:
            best = by_id[fixed_choice[h]]
        chosen[h] = best["id"]
        out[held] = fitter(best, x[~held], inputs.y[~held], x[held])
    if np.isnan(out).any():
        raise RuntimeError("a unit has no held-out prediction")
    return out, chosen


def loyo_readable(
    inputs: md.Inputs, spec: md.ModelSpec, weather: np.ndarray | None = None
) -> np.ndarray:
    """T8's additive model on M1 to M5 clamped to each fold's training range. No verdict."""
    w = _weather(inputs, weather)
    angle = md.day_of_year_angle(inputs.mondays)
    out = np.full(len(inputs.y), np.nan)
    for h in sorted(set(inputs.years.tolist())):
        held = inputs.years == h
        train = ~held
        fold_w = cl.clamp_to_training(w, train)
        x, offset = md.design_matrix(
            spec, angle, inputs.latitude, inputs.longitude, inputs.log_effort[h], fold_w, train
        )
        out[held] = md.fit_predict_logistic(
            x[train],
            inputs.y[train],
            x[held],
            None if offset is None else offset[train],
            None if offset is None else offset[held],
        )
    if np.isnan(out).any():
        raise RuntimeError("a unit has no held-out prediction")
    return out
