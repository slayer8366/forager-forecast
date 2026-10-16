"""T7: P5's constraints and P6's held effort on a fitted model; the ladder; the writers (items 12,
13). Synthetic data only."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from forager_forecast.grid import CELL_SIZE_M, GridWindow
from forager_forecast.t7.metrics import Difference
from forager_forecast.t7.model import (
    BROADLEAF_COVER,
    CONIFER_COVER,
    EFFORT,
    cover_columns,
    held_effort,
    kept_candidates,
    ladder,
    lgb_params,
    predict_at_effort,
    train,
)
from forager_forecast.t7.outputs import (
    HABITAT_FILE,
    HABITAT_LABEL,
    MASK_FILE,
    REQUIRED_MANIFEST_KEYS,
    HabitatWriter,
    OutputRefused,
    attribution,
    check_output_dir,
    check_wording,
    write_manifest,
)

CONFIG = {"id": "t", "num_leaves": 15, "min_data_in_leaf": 20, "learning_rate": 0.1,
          "feature_fraction": 1.0, "lambda_l2": 0.0, "num_boost_round": 60}  # fmt: skip


def _interacting_data(n=3000, seed=11):
    """Presence depends on habitat h and on effort e, and strongly on their product: an
    unconstrained model learns the interaction, so its ranking moves with the effort held."""
    rng = np.random.default_rng(seed)
    h = rng.uniform(-1, 1, n)
    g = rng.uniform(-1, 1, n)
    e = rng.uniform(-2, 2, n)
    logit = 0.5 * h + 0.3 * g + 0.5 * e + 2.5 * h * e
    y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(float)
    return np.column_stack([h, g, e]), y


def test_lightgbm_params_carry_the_two_constraints_and_t1_determinism():
    params = lgb_params(CONFIG, ["h", "g", EFFORT])
    assert params["interaction_constraints"] == [[0, 1], [2]]
    assert params["monotone_constraints"] == [0, 0, 1]
    assert params["objective"] == "binary" and params["deterministic"] is True
    assert params["seed"] == 20260918 and "num_boost_round" not in params and "id" not in params


def test_the_map_ranking_is_the_same_at_any_held_effort_on_a_fitted_model():
    """P6: ranking identical at the 25th and 75th percentiles of effort (P5's construction)."""
    x, y = _interacting_data()
    features = ["h", "g", EFFORT]
    booster = train(CONFIG, features, x, y, np.ones(len(y)))
    grid = np.column_stack([np.linspace(-1, 1, 200), np.linspace(1, -1, 200), np.zeros(200)])
    low = predict_at_effort(booster, features, grid, -1.0)
    high = predict_at_effort(booster, features, grid, 1.0)
    assert not np.allclose(low, high)
    assert np.allclose(high - low, (high - low)[0])  # one shift for every cell
    assert (np.argsort(low, kind="stable") == np.argsort(high, kind="stable")).all()
    assert (high - low)[0] >= 0  # monotone in effort


def test_held_effort_is_the_median_and_cover_is_share_times_total():
    assert held_effort(np.array([3.0, 1.0, 2.0, 10.0])) == 2.5
    con, broad = cover_columns(np.array([0.25]), np.array([0.75]), np.array([80.0]))
    assert con.tolist() == [20.0] and broad.tolist() == [60.0]


def test_the_ladder_and_which_candidates_are_kept():
    base = ["share_Pseudotsuga", "total_cover_pct", EFFORT]
    sets = ladder(base, ["share_Larix", "share_ecm_hosts"])
    assert sets["A: effort only"] == [EFFORT]
    assert sets["B: forest only"] == [EFFORT, CONIFER_COVER, BROADLEAF_COVER]
    assert sets["base"] == base
    assert sets["base + share_Larix"] == [*base, "share_Larix"]
    assert sets["base + share_ecm_hosts"] == [*base, "share_ecm_hosts"]
    kept = kept_candidates({"share_Larix": Difference(0.01, 0.001, 0.02, 1000),
                            "share_ecm_hosts": Difference(0.01, -0.001, 0.02, 1000)})  # fmt: skip
    assert kept == ["share_Larix"]


def test_wording_no_250_m_output_may_carry_is_refused():
    check_wording(HABITAT_LABEL)
    for bad in ("30%", "a percent", "sighting chance", "Probability of x", "edible here",
                "fruiting"):  # fmt: skip
        with pytest.raises(OutputRefused):
            check_wording(bad)


def test_outputs_are_refused_on_the_flash_drive_and_inside_the_repository(tmp_path):
    with pytest.raises(OutputRefused):
        check_output_dir(Path("/run/media/someone/drive/forecast-data/t7"))
    repo = Path(__file__).parents[1]
    with pytest.raises(OutputRefused):
        check_output_dir(repo / "docs" / "t7-out")
    assert check_output_dir(Path("/mnt/work/Zynergy/forecast-data/t7/x")).name == "x"
    assert check_output_dir(tmp_path / "out") == tmp_path / "out"  # the test scratch folder


def test_the_writer_puts_each_tile_in_place_and_renames_when_whole(tmp_path):
    s = 4 * CELL_SIZE_M
    window = GridWindow(0, 0, 2 * s, s)
    out = tmp_path / "run"
    writer = HabitatWriter(out, window, {"label": HABITAT_LABEL})
    right = GridWindow(s, 0, 2 * s, s)
    scores = np.arange(16, dtype=float).reshape(4, 4)
    codes = np.ones((4, 4), dtype=np.uint8)
    scores[0, 0], codes[0, 0] = np.nan, 4
    writer.write(right, scores, codes)
    assert not (out / HABITAT_FILE).exists()
    digests = writer.close()
    assert set(digests) == {HABITAT_FILE, MASK_FILE}
    with rasterio.open(out / HABITAT_FILE) as ds:
        v = ds.read(1)
        assert ds.tags()["label"] == HABITAT_LABEL
        assert np.isnan(v[:, :4]).all() and np.isnan(v[0, 4]) and v[3, 7] == 15.0
    with rasterio.open(out / MASK_FILE) as ds:
        m = ds.read(1)
        assert (m[:, :4] == 0).all() and m[0, 4] == 4 and m[1, 5] == 1
    assert digests[MASK_FILE] == hashlib.sha256((out / MASK_FILE).read_bytes()).hexdigest()
    with pytest.raises(OutputRefused):
        HabitatWriter(tmp_path / "bad", window, {"label": "relative habitat in percent"})


def test_the_manifest_is_refused_unless_it_names_every_input_and_setting(tmp_path):
    manifest = {k: "x" for k in REQUIRED_MANIFEST_KEYS}
    sha = write_manifest(tmp_path / "manifest.json", manifest)
    assert sha == hashlib.sha256((tmp_path / "manifest.json").read_bytes()).hexdigest()
    assert json.loads((tmp_path / "manifest.json").read_text()) == manifest
    del manifest["aoa"]
    with pytest.raises(OutputRefused, match="aoa"):
        write_manifest(tmp_path / "m2.json", manifest)


def test_attribution_names_what_was_read_and_scanfi_only_if_a_canadian_value_was():
    from forager_forecast.t5_layer import SCANFI_CITATION, SCANFI_LICENCE, TREEMAP_CITATION
    from forager_forecast.t6b_layers import NALCMS_CITATION, _tree_tags
    from forager_forecast.t6b_layers import Tile as T6bTile

    tree = {_tree_tags(T6bTile(0, 0, 256))["attribution"]}
    soil = {"SOILGRIDS CITE"}
    us_only = attribution(tree, soil, False, ["CEC L3"])
    assert us_only == [TREEMAP_CITATION, NALCMS_CITATION, "SOILGRIDS CITE", "CEC L3"]
    both = attribution(tree, soil, True, [])
    assert f"{SCANFI_CITATION} ({SCANFI_LICENCE})" in both


def test_a_fit_does_not_depend_on_the_scale_of_the_weights():
    """M3's weights fix each unit's share of the total, not its size. The comparison group is one
    unit, so its weights sum to 2 over every point; LightGBM's hessian floor and its L2 penalty
    are on the weights' own scale, and would starve such a fit of splits (found in the T7 run's
    smoke pass: model B predicted exactly as model A). ``train`` rescales weights to a mean of 1."""
    x, y = _interacting_data()
    features = ["h", "g", EFFORT]
    config = {**CONFIG, "lambda_l2": 10.0}
    w = np.where(y == 1, 1.0 / (y == 1).sum(), 1.0 / (y == 0).sum())  # total 2, as one unit
    small = train(config, features, x, y, w).predict(x)
    unit = train(config, features, x, y, w * len(w) / w.sum()).predict(x)
    assert np.allclose(small, unit)
    assert np.unique(np.round(small, 12)).size > 10  # the fit split at all
