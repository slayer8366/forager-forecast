"""T7 items 10 and 11: weighted AUC, the clustered bootstrap, P10, and the area of applicability."""

import numpy as np
import pytest

from forager_forecast.t1_model import auc
from forager_forecast.t7.aoa import (
    di_threshold,
    fit_aoa,
    importance_weights,
    mean_pairwise_distance,
)
from forager_forecast.t7.metrics import (
    Difference,
    clustered_auc_difference,
    p10_passes,
    weighted_auc,
)


def _brute(s, y, w):
    num = den = 0.0
    for i in np.flatnonzero(y == 1):
        for j in np.flatnonzero(y == 0):
            pair = w[i] * w[j]
            den += pair
            num += pair * (1.0 if s[i] > s[j] else 0.5 if s[i] == s[j] else 0.0)
    return num / den


def test_weighted_auc_matches_the_pair_count_with_ties_and_t1_auc_unweighted():
    rng = np.random.default_rng(3)
    s = rng.integers(0, 8, 60).astype(float)
    y = (rng.random(60) < 0.4).astype(int)
    w = rng.uniform(0.1, 3.0, 60)
    assert weighted_auc(s, y, w) == pytest.approx(_brute(s, y, w), rel=1e-12)
    assert weighted_auc(s, y, np.ones(60)) == pytest.approx(auc(s, y), rel=1e-12)


def test_the_bootstrap_resamples_whole_clusters_and_is_seeded():
    rng = np.random.default_rng(4)
    n = 400
    y = (rng.random(n) < 0.3).astype(int)
    good = y + rng.normal(0, 0.6, n)
    poor = y + rng.normal(0, 3.0, n)
    clusters = rng.integers(0, 40, n)
    w = np.ones(n)
    d = clustered_auc_difference(good, poor, y, w, clusters, resamples=200, seed=7)
    assert d.point == pytest.approx(weighted_auc(good, y, w) - weighted_auc(poor, y, w))
    assert d.low < d.point < d.high and d.low > 0 and d.excludes_zero_above
    assert d == clustered_auc_difference(good, poor, y, w, clusters, resamples=200, seed=7)
    # one cluster: every resample is the same data, so the interval collapses to the point
    one = clustered_auc_difference(good, poor, y, w, np.zeros(n), resamples=20, seed=7)
    assert one.low == pytest.approx(one.point) and one.high == pytest.approx(one.point)
    same = clustered_auc_difference(good, good, y, w, clusters, resamples=50, seed=7)
    assert same.point == 0.0 and not same.excludes_zero_above


def test_p10_needs_both_differences_above_zero_on_all_blocks_and_on_forested_blocks():
    up = Difference(0.05, 0.01, 0.09, 1000)
    straddle = Difference(0.02, -0.01, 0.05, 1000)
    assert p10_passes({"A": up, "B": up}, {"A": up, "B": up})
    assert not p10_passes({"A": up, "B": straddle}, {"A": up, "B": up})
    assert not p10_passes({"A": up, "B": up}, {"A": up, "B": straddle})
    with pytest.raises(KeyError):
        p10_passes({"A": up}, {"A": up, "B": up})


def test_the_threshold_is_q75_plus_1_5_iqr_capped_at_the_largest_training_di():
    di = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 5.0])
    q1, q3 = np.quantile(di, [0.25, 0.75])
    assert di_threshold(di) == pytest.approx(q3 + 1.5 * (q3 - q1))
    # q25 0, q75 1, so q75 + 1.5 IQR = 2.5, above the largest DI: capped at 1
    assert di_threshold(np.array([0.0, 0.0, 1.0, 1.0])) == pytest.approx(1.0)


def test_importance_weights_set_negatives_to_zero_and_refuse_all_zero():
    assert importance_weights(np.array([2.0, -1.0, 0.0])).tolist() == [2.0, 0.0, 0.0]
    with pytest.raises(ValueError):
        importance_weights(np.array([0.0, -3.0]))


def test_mean_pairwise_distance_exact_and_estimated():
    rng = np.random.default_rng(5)
    z = rng.normal(size=(300, 3))
    diffs = np.linalg.norm(z[:, None, :] - z[None, :, :], axis=2)
    exact = diffs.sum() / (300 * 299)
    value, is_exact = mean_pairwise_distance(z)
    assert is_exact and value == pytest.approx(exact, rel=1e-10)
    est, est_exact = mean_pairwise_distance(z, max_exact=100, pairs=200_000, seed=1)
    assert not est_exact and est == pytest.approx(exact, rel=0.02)


def test_the_area_of_applicability_keeps_the_training_cloud_and_drops_a_far_point():
    rng = np.random.default_rng(6)
    x = rng.uniform(0, 1, size=(400, 2))
    folds = (x[:, 0] * 4).astype(int)  # four strips, as blocks would be
    aoa = fit_aoa(x, np.array([1.0, 1.0]), folds)
    assert aoa.mean_distance_exact
    assert np.isfinite(aoa.train_di).all() and aoa.threshold <= aoa.train_di.max()
    new = np.array([[0.5, 0.5], [0.2, 0.9], [5.0, 5.0], [np.nan, 0.5]])
    inside = aoa.inside(new)
    assert inside.tolist() == [True, True, False, False]
    di = aoa.dissimilarity(new)
    assert np.isnan(di[3]) and di[2] > aoa.threshold
    # a predictor with weight 0 is ignored: far along it is still inside
    zero = fit_aoa(x, np.array([1.0, 0.0]), folds)
    assert zero.inside(np.array([[0.5, 50.0]])).tolist() == [True]


def test_the_training_di_is_cross_validated_by_fold():
    # Two folds far apart: every training point's nearest point outside its fold is far away,
    # so its DI is large; without the fold rule its nearest neighbour would sit next to it.
    a = np.column_stack([np.linspace(0, 1, 50), np.zeros(50)])
    b = a + np.array([100.0, 0.0])
    x = np.vstack([a, b])
    folds = np.array([0] * 50 + [1] * 50)
    aoa = fit_aoa(x, np.array([1.0, 1.0]), folds)
    assert aoa.train_di.min() > 0.5
    with pytest.raises(ValueError):
        fit_aoa(x, np.array([1.0, 1.0]), np.zeros(100, dtype=int))
