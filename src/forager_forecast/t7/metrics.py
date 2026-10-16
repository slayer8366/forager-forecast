"""T7 item 10: weighted AUC and a bootstrap of AUC differences clustered by weather cell (P7, P10).

The AUC is ``t1_model.auc``'s rank-sum measure with weights: the weighted share of
(presence, background) pairs the scores put in the right order, ties counted half. The bootstrap
draws whole weather cells with replacement (1,000 resamples, seed 20260918; D31, D105) and
recomputes both models' AUC on the same draw, so the interval is for their difference.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SEED = 20260918
RESAMPLES = 1000


class _Ranked:
    """Scores sorted once, with their tie groups, so an AUC under new weights is one pass."""

    def __init__(self, scores, outcomes):
        scores = np.asarray(scores, dtype=np.float64)
        self.order = np.argsort(scores, kind="mergesort")
        s = scores[self.order]
        starts = np.r_[True, s[1:] != s[:-1]]
        self.group = np.cumsum(starts) - 1
        self.n_groups = int(self.group[-1]) + 1 if len(s) else 0
        self.pos = np.asarray(outcomes)[self.order] == 1

    def auc(self, weights) -> float:
        w = np.asarray(weights, dtype=np.float64)[self.order]
        wp = np.bincount(self.group, weights=np.where(self.pos, w, 0.0), minlength=self.n_groups)
        wn = np.bincount(self.group, weights=np.where(self.pos, 0.0, w), minlength=self.n_groups)
        below = np.cumsum(wn) - wn
        total_p, total_n = wp.sum(), wn.sum()
        if total_p <= 0 or total_n <= 0:
            raise ValueError("an AUC needs weight on both presences and background")
        return float((wp * (below + 0.5 * wn)).sum() / (total_p * total_n))


def weighted_auc(scores: np.ndarray, outcomes: np.ndarray, weights: np.ndarray) -> float:
    return _Ranked(scores, outcomes).auc(weights)


@dataclass(frozen=True)
class Difference:
    point: float
    low: float
    high: float
    resamples: int

    @property
    def excludes_zero_above(self) -> bool:
        return self.low > 0.0


def clustered_auc_difference(a, b, outcomes, weights, clusters, resamples: int = RESAMPLES,
                             seed: int = SEED, level: float = 0.95) -> Difference:  # fmt: skip
    """AUC(a) - AUC(b) and its percentile interval over cluster resamples."""
    ra, rb = _Ranked(a, outcomes), _Ranked(b, outcomes)
    w = np.asarray(weights, dtype=np.float64)
    _, index = np.unique(np.asarray(clusters), return_inverse=True)
    n = int(index.max()) + 1
    point = ra.auc(w) - rb.auc(w)
    rng = np.random.default_rng(seed)
    diffs = np.empty(resamples)
    for i in range(resamples):
        times = np.bincount(rng.integers(0, n, size=n), minlength=n)
        wi = w * times[index]
        diffs[i] = ra.auc(wi) - rb.auc(wi)
    tail = (1.0 - level) / 2.0 * 100.0
    low, high = np.percentile(diffs, [tail, 100.0 - tail])
    return Difference(float(point), float(low), float(high), resamples)


def p10_passes(all_blocks: dict[str, Difference], forested: dict[str, Difference]) -> bool:
    """D140: full minus A and full minus B, pooled over all blocks and over forested blocks,
    each interval wholly above zero."""
    return all(d[k].excludes_zero_above for d in (all_blocks, forested) for k in ("A", "B"))
