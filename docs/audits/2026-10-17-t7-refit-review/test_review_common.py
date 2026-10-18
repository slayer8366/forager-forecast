"""Tests of the review's own AUC and resampling code (review_common.py) against brute force on
small synthetic data, so that a figure the review reports rests on code shown to compute what it
claims. Run from this folder: ``pytest test_review_common.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_common as rc  # noqa: E402


def _data(seed=3, n=120):
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < 0.3).astype(float)
    s = np.round(rng.random(n) * 6) / 6 + 0.5 * y  # many ties
    w = rng.random(n) + 0.1
    clusters = rng.integers(0, 9, n)
    blocks = rng.integers(0, 4, n)
    return s, y, w, clusters, blocks


def test_weighted_auc_matches_brute_force_with_ties():
    s, y, w, _, _ = _data()
    fast, brute = rc.weighted_auc(s, y, w), rc.weighted_auc_bruteforce(s, y, w)
    assert abs(fast - brute) < 1e-12, f"weighted AUC {fast} differs from the pair count {brute} (ties must count half)"


def _within_brute(a, y, w, clusters):
    """Pairs inside one cluster only, ties half; returns (concordant weight, pair weight)."""
    con = mass = 0.0
    for c in np.unique(clusters):
        p = np.flatnonzero((clusters == c) & (y == 1))
        n = np.flatnonzero((clusters == c) & (y == 0))
        for i in p:
            for j in n:
                ww = w[i] * w[j]
                mass += ww
                con += ww * (1.0 if a[i] > a[j] else 0.5 if a[i] == a[j] else 0.0)
    return con, mass


def test_within_cluster_auc_matches_brute_force():
    s, y, w, clusters, _ = _data()
    con, mass = _within_brute(s, y, w, clusters)
    assert abs(rc.within_cluster_auc(s, y, w, clusters) - con / mass) < 1e-12


def test_within_cluster_block_resampled_interval_matches_brute_force():
    """D145 as amended: each row's weight times its block's draw count; a pair straddling two
    blocks weighs the product. The brute force redraws with the same generator and recomputes
    the within-cluster difference pair by pair for a handful of resamples."""
    s, y, w, clusters, blocks = _data()
    b = s[::-1].copy()  # a second model: the scores reversed
    mine = rc.within_cluster_difference(s, b, y, w, clusters, blocks, resamples=25, seed=11)
    _, bidx = np.unique(blocks, return_inverse=True)
    nb = int(bidx.max()) + 1
    rng = np.random.default_rng(11)
    diffs = []
    for _ in range(25):
        t = np.bincount(rng.integers(0, nb, size=nb), minlength=nb)[bidx]
        wi = w * t
        ca, m = _within_brute(s, y, wi, clusters)
        cb, _ = _within_brute(b, y, wi, clusters)
        diffs.append((ca - cb) / m)
    lo, hi = rc.interval(np.array(diffs))
    assert abs(mine["low"] - lo) < 1e-12 and abs(mine["high"] - hi) < 1e-12, (
        f"block-resampled within-cell interval [{mine['low']:.6f}, {mine['high']:.6f}] is not the "
        f"brute-force [{lo:.6f}, {hi:.6f}]: rows must be weighted by their block's draw count")


def test_auc_difference_interval_matches_brute_force():
    s, y, w, _, blocks = _data()
    b = s[::-1].copy()
    mine = rc.auc_difference(s, b, y, w, blocks, resamples=25, seed=5)
    _, bidx = np.unique(blocks, return_inverse=True)
    nb = int(bidx.max()) + 1
    rng = np.random.default_rng(5)
    diffs = []
    for _ in range(25):
        t = np.bincount(rng.integers(0, nb, size=nb), minlength=nb)[bidx]
        diffs.append(rc.weighted_auc_bruteforce(s, y, w * t) - rc.weighted_auc_bruteforce(b, y, w * t))
    lo, hi = rc.interval(np.array(diffs))
    assert abs(mine["low"] - lo) < 1e-12 and abs(mine["high"] - hi) < 1e-12, (
        f"block-clustered difference interval [{mine['low']:.6f}, {mine['high']:.6f}] is not the "
        f"brute-force [{lo:.6f}, {hi:.6f}]")
