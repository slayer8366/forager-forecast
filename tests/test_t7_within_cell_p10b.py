"""T7 part A (Forager RECORD -1156, -1157): the within-weather-cell AUC with its interval, and the
stricter bar P10b (D145). Synthetic data only."""

import numpy as np
import pytest

from forager_forecast.t7.metrics import (
    Difference,
    P10bVerdict,
    clustered_auc_difference,
    p10b,
    weighted_auc,
    within_cluster_auc,
    within_cluster_auc_difference,
)


def _brute_within(s, y, w, c):
    """Concordant pair weight over pair weight, only pairs that share a cluster; and those pairs'
    share of all (presence, background) pair weight."""
    num = den = total = 0.0
    for i in np.flatnonzero(y == 1):
        for j in np.flatnonzero(y == 0):
            pair = w[i] * w[j]
            total += pair
            if c[i] != c[j]:
                continue
            den += pair
            num += pair * (1.0 if s[i] > s[j] else 0.5 if s[i] == s[j] else 0.0)
    return num / den, den / total


def _data(seed=5, n=300, k=25):
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < 0.3).astype(int)
    c = rng.integers(0, k, n)
    s = rng.integers(0, 6, n).astype(float) + y * rng.random(n)  # ties, and some signal
    w = rng.uniform(0.2, 3.0, n)
    return s, y, w, c


def test_the_within_cell_auc_counts_only_pairs_that_share_a_cluster_ties_half():
    s, y, w, c = _data()
    point, share = _brute_within(s, y, w, c)
    got = within_cluster_auc(s, y, w, c, resamples=20, seed=1)
    assert got.point == pytest.approx(point, rel=1e-12)
    assert got.pair_mass_share == pytest.approx(share, rel=1e-12)
    assert got.point != pytest.approx(weighted_auc(s, y, w))


def test_a_score_constant_within_each_cluster_scores_one_half_within_however_it_ranks_between():
    # an effort-like score: one value per cluster, and the cluster decides most of the outcome
    rng = np.random.default_rng(8)
    k, n = 40, 2000
    c = rng.integers(0, k, n)
    level = rng.normal(0, 2, k)
    y = (rng.random(n) < 1 / (1 + np.exp(-level[c]))).astype(int)
    effort = level[c]
    w = np.ones(n)
    assert weighted_auc(effort, y, w) > 0.75
    got = within_cluster_auc(effort, y, w, c, resamples=50, seed=2)
    assert got.point == pytest.approx(0.5, abs=1e-12)
    assert got.low == pytest.approx(0.5, abs=1e-12) and got.high == pytest.approx(0.5, abs=1e-12)


def _replayed_bootstrap(s, y, w, c, resamples, seed, b=None):
    """The resample statistic rebuilt by hand: each drawn cluster copied in as a distinct cluster,
    as many times as it was drawn, and the within-cluster AUC (or the difference) recomputed."""
    labels, inv = np.unique(c, return_inverse=True)
    n = len(labels)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(resamples):
        draw = rng.integers(0, n, size=n)
        idx, cl = [], []
        for copy, g in enumerate(draw):
            members = np.flatnonzero(inv == g)
            idx.append(members)
            cl.append(np.full(len(members), copy))
        idx, cl = np.concatenate(idx), np.concatenate(cl)
        a_val, _ = _brute_within(s[idx], y[idx], w[idx], cl)
        if b is None:
            out.append(a_val)
        else:
            b_val, _ = _brute_within(b[idx], y[idx], w[idx], cl)
            out.append(a_val - b_val)
    return np.percentile(out, [2.5, 97.5])


def test_the_interval_resamples_whole_clusters_each_drawn_copy_counted_once_and_is_seeded():
    s, y, w, c = _data(seed=9, n=120, k=12)
    got = within_cluster_auc(s, y, w, c, resamples=30, seed=11)
    low, high = _replayed_bootstrap(s, y, w, c, 30, 11)
    assert got.low == pytest.approx(low, rel=1e-10)
    assert got.high == pytest.approx(high, rel=1e-10)
    assert got.low < got.high and got.resamples == 30
    assert got == within_cluster_auc(s, y, w, c, resamples=30, seed=11)
    one = within_cluster_auc(s, y, w, np.zeros(len(y)), resamples=20, seed=3)
    assert one.low == pytest.approx(one.point) and one.high == pytest.approx(one.point)


def test_the_difference_is_paired_on_the_same_cluster_draws():
    s, y, w, c = _data(seed=12, n=120, k=12)
    rng = np.random.default_rng(13)
    other = s + rng.normal(0, 2.0, len(s))
    d = within_cluster_auc_difference(s, other, y, w, c, resamples=30, seed=4)
    assert isinstance(d, Difference)
    pa, _ = _brute_within(s, y, w, c)
    pb, _ = _brute_within(other, y, w, c)
    assert d.point == pytest.approx(pa - pb, rel=1e-10)
    low, high = _replayed_bootstrap(s, y, w, c, 30, 4, b=other)
    assert d.low == pytest.approx(low, rel=1e-10) and d.high == pytest.approx(high, rel=1e-10)
    same = within_cluster_auc_difference(s, s, y, w, c, resamples=20, seed=4)
    assert same.point == 0.0 and same.low == 0.0 and not same.excludes_zero_above
    # the pooled difference is a different figure
    assert d.point != pytest.approx(clustered_auc_difference(s, other, y, w, c, 20, 4).point)


def test_no_cluster_holding_both_a_presence_and_background_is_refused():
    y = np.array([1, 1, 0, 0])
    c = np.array([0, 0, 1, 1])
    s, w = np.array([0.9, 0.8, 0.1, 0.2]), np.ones(4)
    with pytest.raises(ValueError):
        within_cluster_auc(s, y, w, c, resamples=5)
    with pytest.raises(ValueError):
        within_cluster_auc_difference(s, s, y, w, c, resamples=5)


UP = Difference(0.004, 0.001, 0.007, 1000)
STRADDLE = Difference(0.003, -0.0004, 0.008, 1000)  # point above zero, interval not


def test_p10b_passes_only_when_every_required_interval_is_wholly_above_zero():
    v = p10b(block_clustered_full_minus_b=UP, within_cell_full_minus_a=UP,
             host_specific_contrast=UP, independent_data=None)  # fmt: skip
    assert v.verdict == "pass" and v.passes
    assert v == P10bVerdict(True, True, True, None)
    for name in ("block_clustered_full_minus_b", "within_cell_full_minus_a",
                 "host_specific_contrast"):  # fmt: skip
        kw = {"block_clustered_full_minus_b": UP, "within_cell_full_minus_a": UP,
              "host_specific_contrast": UP, "independent_data": None, name: STRADDLE}  # fmt: skip
        v = p10b(**kw)
        assert v.verdict == "fail" and not v.passes, name


def test_p10b_condition_4_binds_only_when_independent_data_are_supplied():
    ok = {"block_clustered_full_minus_b": UP, "within_cell_full_minus_a": UP,
          "host_specific_contrast": UP}  # fmt: skip
    assert p10b(**ok, independent_data=UP).verdict == "pass"
    v = p10b(**ok, independent_data=STRADDLE)
    assert v.verdict == "fail" and v.independent_data is False


def test_p10b_without_the_host_specific_contrast_is_incomplete_never_a_pass():
    v = p10b(block_clustered_full_minus_b=UP, within_cell_full_minus_a=UP,
             host_specific_contrast=None, independent_data=None)  # fmt: skip
    assert v.verdict == "incomplete" and not v.passes
    assert v.host_specific_contrast is None
    # a failed condition already decides it, contrast or not (the existing run's case)
    v = p10b(block_clustered_full_minus_b=STRADDLE, within_cell_full_minus_a=UP,
             host_specific_contrast=None, independent_data=None)  # fmt: skip
    assert v.verdict == "fail" and v.block_clustered_over_b is False


def test_p10b_takes_its_conditions_by_name_only():
    with pytest.raises(TypeError):
        p10b(UP, UP, UP, None)  # type: ignore[misc]
    with pytest.raises(TypeError):
        p10b(block_clustered_full_minus_b=UP, within_cell_full_minus_a=UP)  # type: ignore[call-arg]
