"""T7 item 10: weighted AUC and a bootstrap of AUC differences clustered by weather cell (P7, P10).

The AUC is ``t1_model.auc``'s rank-sum measure with weights: the weighted share of
(presence, background) pairs the scores put in the right order, ties counted half. The bootstrap
draws whole weather cells with replacement (1,000 resamples, seed 20260918; D31, D105) and
recomputes both models' AUC on the same draw, so the interval is for their difference.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_STUB = "T7 build: not written yet (tests first)"

SEED = 20260918
RESAMPLES = 1000


def weighted_auc(scores: np.ndarray, outcomes: np.ndarray, weights: np.ndarray) -> float:
    raise NotImplementedError(_STUB)


@dataclass(frozen=True)
class Difference:
    point: float
    low: float
    high: float
    resamples: int

    @property
    def excludes_zero_above(self) -> bool:
        raise NotImplementedError(_STUB)


def clustered_auc_difference(a, b, outcomes, weights, clusters, resamples: int = RESAMPLES,
                             seed: int = SEED, level: float = 0.95) -> Difference:  # fmt: skip
    """AUC(a) - AUC(b) and its percentile interval over cluster resamples."""
    raise NotImplementedError(_STUB)


def p10_passes(all_blocks: dict[str, Difference], forested: dict[str, Difference]) -> bool:
    """D141: full minus A and full minus B, pooled over all blocks and over forested blocks,
    each interval wholly above zero."""
    raise NotImplementedError(_STUB)
