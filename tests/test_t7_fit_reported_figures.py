"""scripts/t7_fit.py's figures reported beside every fit (T7 part A, Forager RECORD -1156, -1157):
base minus B with both intervals, the within-weather-cell AUCs with intervals, block-clustered
intervals beside the weather-cell ones, and the cache reader that never fits. Synthetic data."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from forager_forecast.t7 import metrics as mt

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "t7_fit.py"


def _fit_module():
    spec = importlib.util.spec_from_file_location("t7_fit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def t7_fit():
    return _fit_module()


def _rows(seed=21, n=600):
    rng = np.random.default_rng(seed)
    clusters = rng.integers(0, 60, n)  # weather cells
    blocks = clusters // 10  # six blocks, each a run of weather cells
    y = (rng.random(n) < 0.25).astype(int)
    w = rng.uniform(0.5, 2.0, n)
    effort = rng.normal(0, 1, 60)[clusters]
    preds = {
        "A: effort only": effort + 0.0,
        "B: forest only": effort + rng.normal(0, 1.0, n) * 0.3 + y * 0.2,
        "base": effort + rng.normal(0, 1.0, n) * 0.3 + y * 0.4,
        "full": effort + rng.normal(0, 1.0, n) * 0.3 + y * 0.6,
    }
    forested = np.isin(blocks, [0, 2, 3])
    return y, w, clusters, blocks, preds, forested


def _same(d: dict, m: mt.Difference):
    assert d["point"] == m.point and d["low"] == m.low and d["high"] == m.high
    assert d["resamples"] == m.resamples
    assert d["interval_wholly_above_zero"] == m.excludes_zero_above


def test_base_minus_b_is_reported_with_its_weather_cell_and_its_block_clustered_interval(t7_fit):
    y, w, clusters, blocks, preds, _ = _rows()
    got = t7_fit.base_minus_b_figures(y, w, clusters, blocks, preds, resamples=40)
    _same(got["weather_cell"],
          mt.clustered_auc_difference(preds["base"], preds["B: forest only"], y, w, clusters, 40))
    _same(got["block_clustered"],
          mt.clustered_auc_difference(preds["base"], preds["B: forest only"], y, w, blocks, 40))
    assert got["weather_cell"]["low"] != got["block_clustered"]["low"]


def test_the_within_cell_auc_of_every_model_is_reported_with_its_interval(t7_fit):
    y, w, clusters, _, preds, _ = _rows()
    got = t7_fit.within_cell_figures(y, w, clusters, preds, resamples=40)
    assert set(got["auc"]) == {"A", "B", "base", "full"}
    for short, key in (("A", "A: effort only"), ("B", "B: forest only"), ("base", "base"),
                       ("full", "full")):  # fmt: skip
        m = mt.within_cluster_auc(preds[key], y, w, clusters, 40)
        assert got["auc"][short] == {"point": m.point, "low": m.low, "high": m.high,
                                     "resamples": 40}  # fmt: skip
        assert got["pair_mass_share"] == m.pair_mass_share
    # model A is constant within a weather cell here, so it is exactly one half within
    assert got["auc"]["A"]["point"] == pytest.approx(0.5)
    for short, key in (("A", "A: effort only"), ("B", "B: forest only")):
        _same(got[f"full_minus_{short}"],
              mt.within_cluster_auc_difference(preds["full"], preds[key], y, w, clusters, 40))
    assert got["full_minus_A"]["low"] > 0


def test_a_run_without_a_base_model_reports_the_within_cell_figures_it_has(t7_fit):
    y, w, clusters, _, preds, _ = _rows()
    side = {k: v for k, v in preds.items() if k != "base"}
    got = t7_fit.within_cell_figures(y, w, clusters, side, resamples=20)
    assert set(got["auc"]) == {"A", "B", "full"}


def test_block_clustered_intervals_sit_beside_the_weather_cell_ones_all_and_forested(t7_fit):
    y, w, clusters, blocks, preds, forested = _rows()
    got = t7_fit.block_clustered_figures(y, w, blocks, preds, forested, resamples=40)
    f = forested
    for short, key in (("A", "A: effort only"), ("B", "B: forest only")):
        _same(got["all"][short],
              mt.clustered_auc_difference(preds["full"], preds[key], y, w, blocks, 40))
        _same(got["forested"][short],
              mt.clustered_auc_difference(preds["full"][f], preds[key][f], y[f], w[f],
                                          blocks[f], 40))  # fmt: skip


def test_the_cache_reader_returns_the_saved_predictions_and_refuses_rather_than_fit(t7_fit, tmp_path):
    p = np.linspace(0, 1, 7)
    np.save(tmp_path / "lobo_full.npy", p)
    (tmp_path / "lobo_full.json").write_text(json.dumps({"features": [], "n": 7, "chosen": {}}))
    assert np.array_equal(t7_fit.cached_predictions(tmp_path, "full", 7), p)
    with pytest.raises(SystemExit, match="not in the cache"):
        t7_fit.cached_predictions(tmp_path, "base", 7)
    with pytest.raises(SystemExit, match="rows"):
        t7_fit.cached_predictions(tmp_path, "full", 8)
