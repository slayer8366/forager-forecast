"""T1's models and evaluation (T1 dispatch "Models" and "Validation"; D31; D33).

- Two models, the same algorithm and the same 20 configurations: the calendar baseline (day of
  year as sine and cosine, latitude, longitude) and the full model (those plus the weather
  windows). LightGBM, binary objective.
- The 20 configurations are drawn once, with seed 20260918, from GRID below, and written to the
  repository before any fit (D31). `tuning_configurations()` is that draw; the committed JSON is
  compared with it at fit time, so a changed grid cannot pass silently.
- Outer folds: leave one year out over every year present (D33 (2): all years train). The year of
  a unit is its fold year (the ISO year of a cell-week; the calendar year of a record date in the
  secondary design).
- Inner tuning: for each outer fold, each configuration is scored by inner leave-one-year-out
  Brier score pooled over the training years only, and the lowest wins (D31). The held-out year
  is never seen by the inner loop.
- Headline: one Brier skill per box, 1 - Brier(full) / Brier(calendar), pooled over every
  held-out unit from all folds (D33 (2)), with a 95% interval from 1,000 bootstrap resamples of
  cells (clustered by cell, seed 20260918). A per-fold table sits beside it; a fold with fewer than
  30 positive units is marked uninformative.
"""

import itertools
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

SEED = 20260918
N_CONFIGURATIONS = 20
BOOTSTRAP_RESAMPLES = 1000
MIN_POSITIVES_INFORMATIVE = 30

# The grid the 20 configurations are drawn from. Fixed here before any fit (D31).
GRID: dict[str, tuple] = {
    "num_leaves": (7, 15, 31, 63),
    "learning_rate": (0.02, 0.05, 0.1),
    "num_boost_round": (100, 200, 400),
    "min_data_in_leaf": (20, 50, 100, 200),
    "feature_fraction": (0.7, 1.0),
    "lambda_l2": (0.0, 1.0, 10.0),
}


def tuning_configurations() -> list[dict]:
    """20 distinct configurations drawn without replacement from GRID with seed 20260918."""
    keys = list(GRID)
    product = list(itertools.product(*(GRID[k] for k in keys)))
    rng = np.random.default_rng(SEED)
    picks = rng.choice(len(product), size=N_CONFIGURATIONS, replace=False)
    return [
        {"id": f"c{i:02d}", **dict(zip(keys, product[int(p)], strict=True))}
        for i, p in enumerate(picks)
    ]


def brier(probabilities: np.ndarray, outcomes: np.ndarray) -> float:
    return float(np.mean((probabilities - outcomes) ** 2))


def brier_skill(model: np.ndarray, reference: np.ndarray, outcomes: np.ndarray) -> float:
    """1 - Brier(model) / Brier(reference), pooled over the units given."""
    return 1.0 - brier(model, outcomes) / brier(reference, outcomes)


def fit_predict(
    config: dict, train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray, threads: int
) -> np.ndarray:
    import lightgbm as lgb  # noqa: PLC0415

    params = {
        "objective": "binary",
        "verbose": -1,
        "seed": SEED,
        "deterministic": True,
        "force_row_wise": True,
        "num_threads": threads,
        "bagging_seed": SEED,
        "feature_fraction_seed": SEED,
        **{k: v for k, v in config.items() if k not in ("id", "num_boost_round")},
    }
    booster = lgb.train(
        params, lgb.Dataset(train_x, train_y), num_boost_round=config["num_boost_round"]
    )
    return booster.predict(test_x)


Fitter = Callable[[dict, np.ndarray, np.ndarray, np.ndarray], np.ndarray]


def inner_choice(
    configs: Sequence[dict], x: np.ndarray, y: np.ndarray, years: np.ndarray, fitter: Fitter
) -> tuple[dict, dict[str, float]]:
    """The configuration with the lowest inner leave-one-year-out Brier score, pooled over the
    years given (training years only), and every configuration's score."""
    scores: dict[str, float] = {}
    distinct = sorted(set(years.tolist()))
    for config in configs:
        predictions = np.empty(len(y))
        for year in distinct:
            held = years == year
            predictions[held] = fitter(config, x[~held], y[~held], x[held])
        scores[config["id"]] = brier(predictions, y)
    best = min(configs, key=lambda c: (scores[c["id"]], c["id"]))
    return best, scores


@dataclass
class FoldResult:
    year: int
    units: int
    positives: int
    chosen: str
    inner_scores: dict[str, float]

    @property
    def informative(self) -> bool:
        return self.positives >= MIN_POSITIVES_INFORMATIVE


def leave_one_year_out(
    configs: Sequence[dict],
    x: np.ndarray,
    y: np.ndarray,
    years: np.ndarray,
    fitter: Fitter,
    log: Callable[[str], None] = lambda _m: None,
) -> tuple[np.ndarray, list[FoldResult]]:
    """Held-out predictions for every unit, each from a model that never saw its year, with the
    configuration chosen on that fold's training years only."""
    predictions = np.full(len(y), np.nan)
    folds: list[FoldResult] = []
    for year in sorted(set(years.tolist())):
        held = years == year
        best, scores = inner_choice(configs, x[~held], y[~held], years[~held], fitter)
        predictions[held] = fitter(best, x[~held], y[~held], x[held])
        folds.append(FoldResult(year, int(held.sum()), int(y[held].sum()), best["id"], scores))
        log(f"fold {year}: {int(held.sum())} units, {int(y[held].sum())} positive, {best['id']}")
    if np.isnan(predictions).any():
        raise RuntimeError("a unit has no held-out prediction")
    return predictions, folds


def clustered_bootstrap_skill(
    model: np.ndarray,
    reference: np.ndarray,
    outcomes: np.ndarray,
    clusters: np.ndarray,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = SEED,
) -> tuple[float, float, np.ndarray]:
    """95% percentile interval of pooled Brier skill, resampling whole clusters (cells) with
    replacement. Returns (low, high, all resampled skills)."""
    ids, inverse = np.unique(clusters, return_inverse=True)
    n = len(ids)
    se_model = np.bincount(inverse, weights=(model - outcomes) ** 2, minlength=n)
    se_ref = np.bincount(inverse, weights=(reference - outcomes) ** 2, minlength=n)
    rng = np.random.default_rng(seed)
    skills = np.empty(resamples)
    for i in range(resamples):
        weights = np.bincount(rng.integers(0, n, size=n), minlength=n)
        skills[i] = 1.0 - (weights @ se_model) / (weights @ se_ref)
    low, high = np.percentile(skills, [2.5, 97.5])
    return float(low), float(high), skills


def auc(scores: np.ndarray, outcomes: np.ndarray) -> float:
    """Area under the ROC curve by the rank-sum formula, ties given average ranks."""
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores))
    sorted_scores = scores[order]
    i = 0
    while i < len(scores):
        j = i
        while j + 1 < len(scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2 + 1
        i = j + 1
    pos = outcomes == 1
    n_pos, n_neg = int(pos.sum()), int((~pos).sum())
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def reliability_by_decile(probabilities: np.ndarray, outcomes: np.ndarray) -> list[dict]:
    """Units split into ten equal-count bins by predicted probability: mean predicted against
    observed rate per bin."""
    order = np.argsort(probabilities, kind="mergesort")
    rows = []
    for d, idx in enumerate(np.array_split(order, 10), 1):
        rows.append(
            {
                "decile": d,
                "units": int(len(idx)),
                "mean_predicted": float(probabilities[idx].mean()),
                "observed_rate": float(outcomes[idx].mean()),
            }
        )
    return rows
