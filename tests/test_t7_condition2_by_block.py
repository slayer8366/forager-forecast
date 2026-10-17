"""P10b condition 2 with its interval clustered by level III block (D145 as amended; Forager
RECORD -1164, -1167): the within-weather-cell AUC difference, every within-cell pair kept, with
condition 1's exact resampling, each row's weight multiplied by its block's draw count. Weather
cells may straddle blocks. Synthetic data only."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from forager_forecast.t7 import metrics as mt
from forager_forecast.t7.metrics import (
    Difference,
    within_cluster_auc_difference,
    within_cluster_auc_difference_rows_resampled,
)

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "t7_fit.py"


def _within(s, y, w, c):
    """Brute force: concordant pair weight over pair weight, pairs that share a cluster only."""
    num = den = 0.0
    for i in np.flatnonzero(y == 1):
        for j in np.flatnonzero(y == 0):
            if c[i] != c[j]:
                continue
            pair = w[i] * w[j]
            den += pair
            num += pair * (1.0 if s[i] > s[j] else 0.5 if s[i] == s[j] else 0.0)
    return num / den


def _straddling(seed=31, n=160, cells=16):
    """Weather cells, and blocks cut across them: a row's block depends on the row, so most cells
    hold rows of two blocks."""
    rng = np.random.default_rng(seed)
    c = rng.integers(0, cells, n)
    blocks = (c // 4) * 2 + (rng.random(n) < 0.5)  # eight blocks, each cell split over two
    y = (rng.random(n) < 0.3).astype(int)
    a = rng.integers(0, 5, n).astype(float) + y * rng.random(n)
    b = a + rng.normal(0, 1.5, n)
    w = rng.uniform(0.3, 2.5, n)
    return a, b, y, w, c, blocks


def _replayed(a, b, y, w, c, blocks, resamples, seed):
    """Condition 1's resampling rebuilt by hand: draw blocks with replacement, multiply each row's
    weight by its block's draw count, recompute both within-cell AUCs on the same draw."""
    labels, inv = np.unique(blocks, return_inverse=True)
    n = len(labels)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(resamples):
        times = np.bincount(rng.integers(0, n, size=n), minlength=n)
        wi = w * times[inv]
        out.append(_within(a, y, wi, c) - _within(b, y, wi, c))
    return np.percentile(out, [2.5, 97.5])


def test_the_point_keeps_every_within_cell_pair_including_pairs_across_blocks():
    a, b, y, w, c, blocks = _straddling()
    assert any(len(np.unique(blocks[c == k])) > 1 for k in np.unique(c))
    d = within_cluster_auc_difference_rows_resampled(a, b, y, w, c, blocks, resamples=20, seed=3)
    assert isinstance(d, Difference)
    assert d.point == pytest.approx(_within(a, y, w, c) - _within(b, y, w, c), rel=1e-10)
    assert d.point == pytest.approx(
        within_cluster_auc_difference(a, b, y, w, c, resamples=5).point, rel=1e-12
    )


def test_the_interval_is_condition_1s_resampling_rows_weighted_by_their_blocks_draw_count():
    a, b, y, w, c, blocks = _straddling()
    d = within_cluster_auc_difference_rows_resampled(a, b, y, w, c, blocks, resamples=30, seed=7)
    low, high = _replayed(a, b, y, w, c, blocks, 30, 7)
    assert d.low == pytest.approx(low, rel=1e-10)
    assert d.high == pytest.approx(high, rel=1e-10)
    assert d.low < d.high and d.resamples == 30
    # the weather-cell interval is a different figure
    cell = within_cluster_auc_difference(a, b, y, w, c, resamples=30, seed=7)
    assert (d.low, d.high) != pytest.approx((cell.low, cell.high))


def test_the_draws_are_seeded_and_paired():
    a, b, y, w, c, blocks = _straddling(seed=40)
    one = within_cluster_auc_difference_rows_resampled(a, b, y, w, c, blocks, resamples=25, seed=9)
    assert one == within_cluster_auc_difference_rows_resampled(a, b, y, w, c, blocks, 25, 9)
    same = within_cluster_auc_difference_rows_resampled(a, a, y, w, c, blocks, 25, 9)
    assert same.point == 0.0 and same.low == 0.0 and same.high == 0.0
    assert not same.excludes_zero_above


def test_a_pair_whose_rows_lie_in_different_blocks_is_counted():
    # one weather cell; the presence in block 0, the background in block 1
    y = np.array([1, 0, 1, 0])
    c = np.array([0, 0, 1, 1])
    blocks = np.array([0, 1, 2, 2])
    w = np.ones(4)
    a = np.array([0.9, 0.1, 0.2, 0.8])  # right in cell 0, wrong in cell 1
    b = np.array([0.1, 0.9, 0.2, 0.8])  # wrong in both
    d = within_cluster_auc_difference_rows_resampled(a, b, y, w, c, blocks, resamples=10, seed=1)
    assert d.point == pytest.approx(0.5)


def test_no_cell_holding_both_a_presence_and_background_is_refused():
    y = np.array([1, 1, 0, 0])
    c = np.array([0, 0, 1, 1])
    s, w = np.array([0.9, 0.8, 0.1, 0.2]), np.ones(4)
    with pytest.raises(ValueError):
        within_cluster_auc_difference_rows_resampled(s, s, y, w, c, c, resamples=5)


@pytest.fixture(scope="module")
def t7_fit():
    spec = importlib.util.spec_from_file_location("t7_fit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_fit_reports_condition_2_block_clustered_for_full_minus_a_and_b(t7_fit):
    a, b, y, w, c, blocks = _straddling(seed=44, n=200)
    preds = {"A: effort only": b, "B: forest only": b * 0.5 + a * 0.5, "full": a}
    got = t7_fit.within_cell_block_clustered_figures(y, w, c, blocks, preds, resamples=20)
    assert got["pairs"] == "inside one weather cell"
    assert got["resampled"] == "level III block, rows weighted by their block's draw count"
    for short, key in (("A", "A: effort only"), ("B", "B: forest only")):
        m = mt.within_cluster_auc_difference_rows_resampled(preds["full"], preds[key], y, w, c,
                                                            blocks, 20)  # fmt: skip
        assert got[f"full_minus_{short}"] == {
            "point": m.point, "low": m.low, "high": m.high, "resamples": 20,
            "interval_wholly_above_zero": m.excludes_zero_above,
        }  # fmt: skip
