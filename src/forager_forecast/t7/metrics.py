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


# --- within one cluster (T7 part A, Forager RECORD -1156, -1157) ----------------------------------


@dataclass(frozen=True)
class WithinAUC:
    """A weighted AUC over the (presence, background) pairs that share a cluster, its percentile
    interval over cluster resamples, and the share of all pair weight those pairs hold."""

    point: float
    low: float
    high: float
    resamples: int
    pair_mass_share: float


def _within_parts(scores, outcomes, weights, index, n: int):
    """Per cluster: the concordant pair weight (ties half) and the pair weight, over the
    (presence, background) pairs inside that cluster only. One sort, no loop over clusters."""
    s = np.asarray(scores, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    pos = np.asarray(outcomes) == 1
    order = np.lexsort((s, index))  # by cluster, then score
    s, c, w, pos = s[order], index[order], w[order], pos[order]
    starts = np.r_[True, (s[1:] != s[:-1]) | (c[1:] != c[:-1])]
    group = np.cumsum(starts) - 1
    g_cluster = c[starts]
    wp = np.bincount(group, weights=np.where(pos, w, 0.0))
    wn = np.bincount(group, weights=np.where(pos, 0.0, w))
    cum = np.cumsum(wn)
    first = np.r_[True, g_cluster[1:] != g_cluster[:-1]]  # each cluster's first tie group
    before = (cum - wn)[first][np.cumsum(first) - 1]  # background weight before the cluster
    below = cum - wn - before  # background weight below this tie group, in its cluster
    concordant = np.bincount(g_cluster, weights=wp * (below + 0.5 * wn), minlength=n)
    # pair weight from the rows in their own order, so it is the same for every model's scores
    w0 = np.asarray(weights, dtype=np.float64)
    p0 = np.asarray(outcomes) == 1
    mass = np.bincount(index, weights=np.where(p0, w0, 0.0), minlength=n) * np.bincount(
        index, weights=np.where(p0, 0.0, w0), minlength=n
    )
    return concordant, mass, float(w0[p0].sum() * w0[~p0].sum())


def _cluster_index(clusters):
    _, index = np.unique(np.asarray(clusters), return_inverse=True)
    return index, int(index.max()) + 1


def _resampled(stat_parts, mass, n: int, resamples: int, seed: int, level: float):
    """Percentile interval of sum(k * part) / sum(k * mass) over whole-cluster resamples, where k
    is how many times each cluster was drawn: each drawn copy adds its own pairs once."""
    rng = np.random.default_rng(seed)
    out = np.empty(resamples)
    for i in range(resamples):
        times = np.bincount(rng.integers(0, n, size=n), minlength=n)
        m = (times * mass).sum()
        if m <= 0:
            raise ValueError("a resample drew no cluster holding both presences and background")
        out[i] = (times * stat_parts).sum() / m
    tail = (1.0 - level) / 2.0 * 100.0
    low, high = np.percentile(out, [tail, 100.0 - tail])
    return float(low), float(high)


def within_cluster_auc(scores, outcomes, weights, clusters, resamples: int = RESAMPLES,
                       seed: int = SEED, level: float = 0.95) -> WithinAUC:  # fmt: skip
    """The weighted AUC over (presence, background) pairs inside one cluster (a weather cell, where
    T6's effort is one value, so only the habitat inputs can rank the pair). Clusters are resampled
    whole, as ``clustered_auc_difference`` does, with the same draws for the same seed. This is the
    reviews' within-cell figure (`docs/audits/2026-10-16-t7-fit-review-2/recompute_auc.py`,
    ``within_cluster_auc``) with an interval added."""
    index, n = _cluster_index(clusters)
    concordant, mass, total = _within_parts(scores, outcomes, weights, index, n)
    if mass.sum() <= 0:
        raise ValueError("no cluster holds both a presence and a background point")
    low, high = _resampled(concordant, mass, n, resamples, seed, level)
    return WithinAUC(float(concordant.sum() / mass.sum()), low, high, resamples,
                     float(mass.sum() / total))  # fmt: skip


def within_cluster_auc_difference(a, b, outcomes, weights, clusters, resamples: int = RESAMPLES,
                                  seed: int = SEED, level: float = 0.95) -> Difference:  # fmt: skip
    """Within-cluster AUC(a) - AUC(b), and its percentile interval, both models on the same draw."""
    index, n = _cluster_index(clusters)
    ca, mass, _ = _within_parts(a, outcomes, weights, index, n)
    cb, mass_b, _ = _within_parts(b, outcomes, weights, index, n)
    if not np.array_equal(mass, mass_b):
        raise RuntimeError("the two models' pair weights differ on the same rows")
    if mass.sum() <= 0:
        raise ValueError("no cluster holds both a presence and a background point")
    low, high = _resampled(ca - cb, mass, n, resamples, seed, level)
    return Difference(float((ca - cb).sum() / mass.sum()), low, high, resamples)


class _WithinRanked:
    """Scores sorted once by cluster, then score, with their tie groups, so the within-cluster
    concordant pair weight under new row weights is one pass (``_within_parts``'s sum, with the
    sort held)."""

    def __init__(self, scores, outcomes, index):
        s = np.asarray(scores, dtype=np.float64)
        self.order = np.lexsort((s, index))
        s, c = s[self.order], index[self.order]
        self.pos = np.asarray(outcomes)[self.order] == 1
        starts = np.r_[True, (s[1:] != s[:-1]) | (c[1:] != c[:-1])]
        self.group = np.cumsum(starts) - 1
        self.n_groups = int(self.group[-1]) + 1 if len(s) else 0
        g_cluster = c[starts]
        self.first = np.r_[True, g_cluster[1:] != g_cluster[:-1]]
        self.first_of = np.cumsum(self.first) - 1

    def concordant(self, weights) -> float:
        w = np.asarray(weights, dtype=np.float64)[self.order]
        wp = np.bincount(self.group, np.where(self.pos, w, 0.0), self.n_groups)
        wn = np.bincount(self.group, np.where(self.pos, 0.0, w), self.n_groups)
        cum = np.cumsum(wn)
        before = (cum - wn)[self.first][self.first_of]
        return float((wp * (cum - wn - before + 0.5 * wn)).sum())


def within_cluster_auc_difference_rows_resampled(a, b, outcomes, weights, clusters, resample_by,
                                                 resamples: int = RESAMPLES, seed: int = SEED,
                                                 level: float = 0.95) -> Difference:  # fmt: skip
    """Within-cluster AUC(a) - AUC(b) over every (presence, background) pair inside one cluster
    (a weather cell), with its interval from condition 1's exact resampling (D145 condition 2 as
    amended; Forager RECORD -1164, -1167, reading (a)): draw the ``resample_by`` units (level III
    blocks) with replacement, multiply each row's weight by its unit's draw count, as
    ``clustered_auc_difference`` does, and recompute both within-cluster AUCs on the same draw.
    Clusters may straddle units; a pair whose rows lie in two units is kept, and weighs the
    product of their draw counts. The point is ``within_cluster_auc_difference``'s."""
    index, n_clusters = _cluster_index(clusters)
    w = np.asarray(weights, dtype=np.float64)
    pos = np.asarray(outcomes) == 1
    ra, rb = _WithinRanked(a, outcomes, index), _WithinRanked(b, outcomes, index)

    def stat(wi):
        mass = (np.bincount(index, np.where(pos, wi, 0.0), n_clusters)
                * np.bincount(index, np.where(pos, 0.0, wi), n_clusters)).sum()  # fmt: skip
        if mass <= 0:
            raise ValueError("no cluster holds both a presence and a background point")
        return (ra.concordant(wi) - rb.concordant(wi)) / mass

    point = stat(w)
    _, unit = np.unique(np.asarray(resample_by), return_inverse=True)
    n = int(unit.max()) + 1
    rng = np.random.default_rng(seed)
    diffs = np.empty(resamples)
    for i in range(resamples):
        times = np.bincount(rng.integers(0, n, size=n), minlength=n)
        diffs[i] = stat(w * times[unit])
    tail = (1.0 - level) / 2.0 * 100.0
    low, high = np.percentile(diffs, [tail, 100.0 - tail])
    return Difference(float(point), float(low), float(high), resamples)


# --- P10b (D145) ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class P10bVerdict:
    """Each condition: True (interval wholly above zero), False (not), or None (not supplied)."""

    block_clustered_over_b: bool
    within_cell_over_a: bool
    host_specific_contrast: bool | None
    independent_data: bool | None

    @property
    def verdict(self) -> str:
        """ "fail" if any supplied condition fails; "incomplete" if none fails but the required
        host-specific contrast is missing; "pass" only with conditions 1 to 3 (and 4 if supplied)
        all wholly above zero."""
        given = (self.block_clustered_over_b, self.within_cell_over_a,
                 self.host_specific_contrast, self.independent_data)  # fmt: skip
        if any(c is False for c in given):
            return "fail"
        if self.host_specific_contrast is None:
            return "incomplete"
        return "pass"

    @property
    def passes(self) -> bool:
        return self.verdict == "pass"


def p10b(*, block_clustered_full_minus_b: Difference, within_cell_full_minus_a: Difference,
         host_specific_contrast: Difference | None,
         independent_data: Difference | None) -> P10bVerdict:  # fmt: skip
    """D145, the owner's bar for showing T7 (Forager RECORD -1156 item 2), beside ``p10_passes``
    (D140), which it replaces for any re-fit. Each condition needs its 95% interval wholly above
    zero:

    1. the full model above B (effort plus conifer and broadleaf cover), the interval clustered by
       level III block;
    2. the full model above A (effort only) within one weather cell, the interval clustered by
       level III block with condition 1's resampling (amended 2026-10-17, Forager RECORD -1164,
       -1167: ``within_cluster_auc_difference_rows_resampled``; not the weather-cell interval);
    3. the host-specific contrast: the mycorrhizal group's gain minus the saprotroph comparison
       group's (part C), required;
    4. the map ranking independent presences above background (that AUC minus 0.5), required
       only if usable independent data exist (part D); pass None when there are none.

    A missing host-specific contrast is never read as a pass: the verdict is "incomplete" unless
    another condition already fails. Not wired into any run (part C's group is not built)."""
    return P10bVerdict(
        block_clustered_full_minus_b.excludes_zero_above,
        within_cell_full_minus_a.excludes_zero_above,
        None if host_specific_contrast is None else host_specific_contrast.excludes_zero_above,
        None if independent_data is None else independent_data.excludes_zero_above,
    )
