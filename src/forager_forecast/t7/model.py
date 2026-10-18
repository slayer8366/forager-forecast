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

The re-fit (dispatch 2026-10-17-T7R) adds the access band beside effort in every model
(``ladder_with_access``): effort and access form one interaction group, so the raw score is a
habitat part plus a part in effort and access, and holding both at constants keeps the map's
ranking (``predict_held``).
"""

from __future__ import annotations

import numpy as np

SEED = 20260918
EFFORT = "log_effort"
CONIFER_COVER = "conifer_cover_pct"
BROADLEAF_COVER = "broadleaf_cover_pct"
# The re-fit's access band (part B's distance to the nearest road, D149, D150), "like effort"
# (Forager RECORD -1182): held apart from every habitat input with effort, held at one value on
# the map, out of the area of applicability. Its monotone direction is an open ruling, so a model
# with it refuses to build until a direction is passed (``access_monotone``).
ACCESS = "access_dist_m"
HELD = (EFFORT, ACCESS)


def lgb_params(config: dict, features: list[str], threads: int = 1,
               access_monotone: int | None = None) -> dict:  # fmt: skip
    if EFFORT not in features:
        raise ValueError(f"{EFFORT} is not among the features")
    held = [i for i, f in enumerate(features) if f in HELD]
    others = [i for i in range(len(features)) if i not in held]
    direction = {EFFORT: 1}
    if ACCESS in features:
        if access_monotone not in (-1, 0, 1):
            raise ValueError(
                f"{ACCESS} is a feature but its monotone direction is not ruled "
                f"(access_monotone={access_monotone!r}; -1, 0 or 1)"
            )
        direction[ACCESS] = access_monotone
    params = {
        "objective": "binary",
        "verbose": -1,
        "seed": SEED,
        "deterministic": True,
        "force_row_wise": True,
        "num_threads": threads,
        "bagging_seed": SEED,
        "feature_fraction_seed": SEED,
        "monotone_constraints": [direction.get(f, 0) for f in features],
        **{k: v for k, v in config.items() if k not in ("id", "num_boost_round")},
    }
    groups = [others, held] if others else [held]
    params["interaction_constraints"] = groups
    return params


def unit_mean_weights(w) -> np.ndarray:
    """Weights rescaled to a mean of 1. M3 and P3 fix each unit's share of the total weight, not
    its size; LightGBM's hessian floor (``min_sum_hessian_in_leaf``) and its L2 penalty act on the
    weights' own scale, so a run whose weights sum to 2 (the comparison group, one unit) would be
    starved of splits. Every share is unchanged; a weighted AUC or log loss is unchanged."""
    w = np.asarray(w, dtype=np.float64)
    total = w.sum()
    if not np.isfinite(total) or total <= 0:
        raise ValueError("weights must have a positive finite sum")
    return w * (len(w) / total)


def train(config: dict, features: list[str], x, y, w, threads: int = 1,
          access_monotone: int | None = None):  # fmt: skip
    import lightgbm as lgb  # noqa: PLC0415

    data = lgb.Dataset(np.asarray(x), np.asarray(y), weight=unit_mean_weights(w),
                       feature_name=list(features), free_raw_data=True)  # fmt: skip
    return lgb.train(lgb_params(config, features, threads, access_monotone), data,
                     num_boost_round=config["num_boost_round"])  # fmt: skip


def fitter_for(features: list[str], threads: int = 1, access_monotone: int | None = None):
    """A folds.Fitter that trains with P5's constraints and returns probabilities."""

    def fit(config, train_x, train_y, train_w, test_x):
        return train(config, features, train_x, train_y, train_w, threads,
                     access_monotone).predict(test_x)  # fmt: skip

    return fit


def predict_at_effort(booster, features: list[str], x: np.ndarray, value: float) -> np.ndarray:
    """Raw scores with every row's log_effort set to ``value``."""
    held = np.array(x, dtype=np.float64, copy=True)
    held[:, features.index(EFFORT)] = value
    return booster.predict(held, raw_score=True)


def held_effort(log_effort_by_weather_cell: np.ndarray) -> float:
    values = np.asarray(log_effort_by_weather_cell, dtype=np.float64)
    if not np.isfinite(values).all() or len(values) == 0:
        raise ValueError("held effort needs finite log effort values")
    return float(np.median(values))


def cover_columns(share_conifer, share_broadleaf, total_cover_pct) -> tuple:
    total = np.asarray(total_cover_pct, dtype=np.float64)
    return (np.asarray(share_conifer, dtype=np.float64) * total,
            np.asarray(share_broadleaf, dtype=np.float64) * total)  # fmt: skip


def ladder(base: list[str], candidates: list[str]) -> dict[str, list[str]]:
    sets = {
        "A: effort only": [EFFORT],
        "B: forest only": [EFFORT, CONIFER_COVER, BROADLEAF_COVER],
        "base": list(base),
    }
    for c in candidates:
        sets[f"base + {c}"] = [*base, c]
    return sets


def kept_candidates(differences: dict) -> list[str]:
    return [name for name, d in differences.items() if d.excludes_zero_above]


# --- the access band (T7 re-fit, dispatch 2026-10-17-T7R; Forager RECORD -1182) ------------------


def ladder_with_access(base: list[str], candidates: list[str]) -> dict[str, list[str]]:
    """``ladder``'s models with the access band beside effort in every one of them (A, B, the
    base, each add-one, and so the full model built from them). Access is never a candidate."""
    if ACCESS in candidates or ACCESS in base:
        raise ValueError(f"{ACCESS} is held beside effort, never a candidate or a base band")
    out = {}
    for name, features in ladder(base, candidates).items():
        k = features.index(EFFORT)
        out[name] = [*features[: k + 1], ACCESS, *features[k + 1 :]]
    return out


def habitat_features(features: list[str]) -> list[str]:
    """The features that are not held for the map (effort, access): the area of applicability's
    predictors (P8)."""
    return [f for f in features if f not in HELD]


def predict_held(booster, features: list[str], x: np.ndarray, held: dict) -> np.ndarray:
    """Raw scores with each held feature named in ``held`` set to its value in every row."""
    x = np.array(x, dtype=np.float64, copy=True)
    for name, value in held.items():
        x[:, features.index(name)] = value
    return booster.predict(x, raw_score=True)


def held_access(values) -> float:
    """The access band's held value for the map: the median over the background draw (the
    planner's proposal, dispatch 2026-10-17-T7R). Refuses undefined values."""
    v = np.asarray(values, dtype=np.float64)
    if len(v) == 0 or not np.isfinite(v).all():
        raise ValueError("held access needs finite access values")
    return float(np.median(v))
