"""T7 item 9: folds by level III block (D125), the leakage check, and per-block tuning (D31).

P7 as ruled (D139, D140): leave one level III block out; each point predicted once, by the fold
that held its block out. For each outer fold the configuration is chosen by inner grouped 4-fold
cross-validation over that fold's training blocks only, by weighted log loss. Before any fit, each
fold is checked so that no point of the held-out block is in its training set; a fold that fails
stops the run.

The 20 configurations are drawn once from ``GRID`` with seed 20260918 and are committed as
``docs/audits/2026-10-15-t7-build/tuning_grid.json`` before any fit; a test holds the two equal.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

_STUB = "T7 build: not written yet (tests first)"

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
    raise NotImplementedError(_STUB)


def forested_blocks(study_cells: dict[int, int], share_cells: dict[int, int],
                    cut: float = FORESTED_CUT) -> set[int]:  # fmt: skip
    raise NotImplementedError(_STUB)


def informative_blocks(blocks: np.ndarray, y: np.ndarray,
                       minimum: int = MIN_PRESENCES_INFORMATIVE) -> set[int]:  # fmt: skip
    raise NotImplementedError(_STUB)


@dataclass(frozen=True)
class Fold:
    block: int
    train: np.ndarray
    test: np.ndarray


def leave_one_block_out_folds(blocks: np.ndarray) -> list[Fold]:
    raise NotImplementedError(_STUB)


def assert_no_leakage(fold: Fold, blocks: np.ndarray) -> None:
    raise NotImplementedError(_STUB)


def inner_groups(blocks: Sequence[int], k: int = INNER_GROUPS, seed: int = SEED) -> dict:
    raise NotImplementedError(_STUB)


def weighted_log_loss(p: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    raise NotImplementedError(_STUB)


def inner_choice(configs, x, y, w, blocks, fitter: Fitter) -> tuple[dict, dict[str, float]]:
    raise NotImplementedError(_STUB)


@dataclass
class FoldResult:
    block: int
    points: int
    presences: int
    chosen: str


def leave_one_block_out(configs, x, y, w, blocks, fitter: Fitter, folds=None,
                        log=lambda _m: None) -> tuple[np.ndarray, list[FoldResult]]:  # fmt: skip
    raise NotImplementedError(_STUB)
