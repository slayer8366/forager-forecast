"""T7 item 9: folds by level III block (D125), the leakage check, and per-block tuning (D31).

P7 as ruled (D135, D139): leave one level III block out; each point predicted once, by the fold
that held its block out. For each outer fold the configuration is chosen by inner grouped 4-fold
cross-validation over that fold's training blocks only, by weighted log loss. Before any fit, each
fold is checked so that no point of the held-out block is in its training set; a fold that fails
stops the run.

The 20 configurations are drawn once from ``GRID`` with seed 20260918 and are committed as
``docs/audits/2026-10-15-t7-build/tuning_grid.json`` before any fit; a test holds the two equal.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

SEED = 20260918
N_CONFIGURATIONS = 20
INNER_GROUPS = 4
MIN_PRESENCES_INFORMATIVE = 30  # D139
FORESTED_CUT = 0.15  # D139

GRID: dict[str, tuple] = {
    "num_leaves": (15, 31, 63),
    "min_data_in_leaf": (50, 200, 1000),
    "learning_rate": (0.03, 0.1),
    "feature_fraction": (0.7, 1.0),
    "lambda_l2": (0.0, 10.0),
    "num_boost_round": (200, 500),
}

Fitter = Callable[[dict, np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray]


class LeakageError(RuntimeError):
    pass


def tuning_configurations() -> list[dict]:
    """20 distinct configurations drawn without replacement from GRID with seed 20260918."""
    keys = list(GRID)
    product = list(itertools.product(*(GRID[k] for k in keys)))
    picks = np.random.default_rng(SEED).choice(len(product), size=N_CONFIGURATIONS, replace=False)
    return [
        {"id": f"c{i:02d}", **dict(zip(keys, product[int(p)], strict=True))}
        for i, p in enumerate(picks)
    ]


def forested_blocks(study_cells: dict[int, int], share_cells: dict[int, int],
                    cut: float = FORESTED_CUT) -> set[int]:  # fmt: skip
    """Blocks with at least ``cut`` of their study cells carrying shares (canopy >= 10%)."""
    return {b for b, n in study_cells.items() if n > 0 and share_cells.get(b, 0) / n >= cut}


def informative_blocks(blocks: np.ndarray, y: np.ndarray,
                       minimum: int = MIN_PRESENCES_INFORMATIVE) -> set[int]:  # fmt: skip
    blocks = np.asarray(blocks)
    return {int(b) for b in np.unique(blocks) if int((np.asarray(y)[blocks == b] == 1).sum())
            >= minimum}  # fmt: skip


@dataclass(frozen=True)
class Fold:
    block: int
    train: np.ndarray
    test: np.ndarray


def leave_one_block_out_folds(blocks: np.ndarray) -> list[Fold]:
    blocks = np.asarray(blocks)
    return [
        Fold(int(b), np.flatnonzero(blocks != b), np.flatnonzero(blocks == b))
        for b in np.unique(blocks)
    ]


def assert_no_leakage(fold: Fold, blocks: np.ndarray) -> None:
    blocks = np.asarray(blocks)
    leaked = int((blocks[fold.train] == fold.block).sum())
    if leaked:
        raise LeakageError(f"fold for block {fold.block}: {leaked} of its points in training")
    if (blocks[fold.test] != fold.block).any():
        raise LeakageError(f"fold for block {fold.block}: its test set holds other blocks")
    if np.intersect1d(fold.train, fold.test).size:
        raise LeakageError(f"fold for block {fold.block}: a point is in both sets")


def inner_groups(blocks: Sequence[int], k: int = INNER_GROUPS, seed: int = SEED) -> dict:
    distinct = sorted({int(b) for b in blocks})
    order = np.random.default_rng(seed).permutation(len(distinct))
    return {distinct[int(j)]: i % k for i, j in enumerate(order)}


def weighted_log_loss(p: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    p = np.clip(np.asarray(p, dtype=np.float64), 1e-15, 1 - 1e-15)
    y = np.asarray(y, dtype=np.float64)
    w = np.asarray(w, dtype=np.float64)
    return float(-(w * (y * np.log(p) + (1 - y) * np.log(1 - p))).sum() / w.sum())


def inner_choice(configs, x, y, w, blocks, fitter: Fitter) -> tuple[dict, dict[str, float]]:
    """The configuration with the lowest weighted log loss over inner grouped folds of the
    blocks given (one outer fold's training blocks only)."""
    blocks = np.asarray(blocks)
    group_of = inner_groups(blocks.tolist())
    groups = np.array([group_of[int(b)] for b in blocks])
    scores: dict[str, float] = {}
    for config in configs:
        predictions = np.empty(len(y))
        for g in sorted(set(groups.tolist())):
            held = groups == g
            predictions[held] = fitter(config, x[~held], y[~held], w[~held], x[held])
        scores[config["id"]] = weighted_log_loss(predictions, y, w)
    best = min(configs, key=lambda c: (scores[c["id"]], c["id"]))
    return best, scores


@dataclass
class FoldResult:
    block: int
    points: int
    presences: int
    chosen: str


def leave_one_block_out(configs, x, y, w, blocks, fitter: Fitter, folds=None,
                        log=lambda _m: None) -> tuple[np.ndarray, list[FoldResult]]:  # fmt: skip
    """Held-out predictions for every point, each from a model that never saw its block, with
    the configuration chosen on that fold's training blocks only. Every fold is checked for
    leakage before the first fit."""
    blocks = np.asarray(blocks)
    folds = leave_one_block_out_folds(blocks) if folds is None else folds
    for fold in folds:
        assert_no_leakage(fold, blocks)
    predictions = np.full(len(y), np.nan)
    results = []
    for fold in folds:
        tr, te = fold.train, fold.test
        best, _ = inner_choice(configs, x[tr], y[tr], w[tr], blocks[tr], fitter)
        predictions[te] = fitter(best, x[tr], y[tr], w[tr], x[te])
        results.append(FoldResult(fold.block, len(te), int((y[te] == 1).sum()), best["id"]))
        log(
            f"block {fold.block}: {len(te)} points, {results[-1].presences} presences, {best['id']}"
        )
    if np.isnan(predictions).any():
        raise RuntimeError("a point has no held-out prediction")
    return predictions, results
