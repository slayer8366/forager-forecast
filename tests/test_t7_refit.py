"""T7 re-fit, Phase 1 (dispatch 2026-10-17-T7R, Forager RECORD -1182, -1183): the road band as
access beside effort, condition 3's joint block resampling, the specimen filters, P10b in the fit
report, and the output folder guard. Synthetic data only; no real record or layer is read."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from forager_forecast.t7 import metrics as mt
from forager_forecast.t7 import model as md
from forager_forecast.t7 import specimens as sp
from forager_forecast.t7.membership import (
    MAIN_RUN,
    MYCORRHIZAL_GROUP,
    Join,
    ListRow,
    load_list,
    write_list,
)

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "t7_fit.py"
CONFIG = {"id": "t", "num_leaves": 15, "min_data_in_leaf": 20, "learning_rate": 0.1,
          "feature_fraction": 1.0, "lambda_l2": 0.0, "num_boost_round": 60}  # fmt: skip


@pytest.fixture(scope="module")
def t7_fit():
    spec = importlib.util.spec_from_file_location("t7_fit_refit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- access in every model, never a candidate --------------------------------------------------


def test_access_joins_effort_in_the_held_interaction_group_with_the_ruled_direction():
    params = md.lgb_params(CONFIG, ["h", "g", md.EFFORT, md.ACCESS], access_monotone=-1)
    assert params["interaction_constraints"] == [[0, 1], [2, 3]]
    assert params["monotone_constraints"] == [0, 0, 1, -1]
    params = md.lgb_params(CONFIG, ["h", md.ACCESS, md.EFFORT], access_monotone=0)
    assert params["interaction_constraints"] == [[0], [1, 2]]
    assert params["monotone_constraints"] == [0, 0, 1]


def test_access_with_no_ruled_direction_is_refused_and_no_access_is_unchanged():
    with pytest.raises(ValueError, match="monotone"):
        md.lgb_params(CONFIG, ["h", md.EFFORT, md.ACCESS])
    with pytest.raises(ValueError, match="monotone"):
        md.lgb_params(CONFIG, ["h", md.EFFORT, md.ACCESS], access_monotone=2)
    old = md.lgb_params(CONFIG, ["h", "g", md.EFFORT])
    assert old["interaction_constraints"] == [[0, 1], [2]]
    assert old["monotone_constraints"] == [0, 0, 1]


def test_access_is_in_every_model_that_carries_effort_and_is_never_a_candidate():
    base = ["share_a", "share_b", md.EFFORT]
    sets = md.ladder_with_access(base, ["share_c", "share_d"])
    assert set(sets) == {"A: effort only", "B: forest only", "base", "base + share_c",
                         "base + share_d"}  # fmt: skip
    for name, features in sets.items():
        assert features.count(md.ACCESS) == 1, name
        assert features.count(md.EFFORT) == 1, name
    assert sets["A: effort only"] == [md.EFFORT, md.ACCESS]
    assert sets["B: forest only"] == [md.EFFORT, md.ACCESS, md.CONIFER_COVER, md.BROADLEAF_COVER]
    assert sets["base + share_c"] == [*sets["base"], "share_c"]
    with pytest.raises(ValueError, match="candidate"):
        md.ladder_with_access(base, ["share_c", md.ACCESS])


def _interacting(n=3000, seed=5):
    """Presence depends on habitat h, effort e and access a, and strongly on h times a: an
    unconstrained model would learn it, so its ranking would move with the access held."""
    rng = np.random.default_rng(seed)
    h, g = rng.uniform(-1, 1, n), rng.uniform(-1, 1, n)
    e, a = rng.uniform(-2, 2, n), rng.uniform(0, 4, n)
    logit = 0.5 * h + 0.3 * g + 0.5 * e - 0.4 * a + 2.0 * h * (a - 2)
    y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(float)
    return np.column_stack([h, g, e, a]), y


def test_access_held_on_the_map_and_the_ranking_unchanged_when_it_moves(t7_fit):
    """P6 for access: on a fitted model, the map's columns hold access at one value, and moving
    that value shifts every cell by the same amount."""
    x, y = _interacting()
    features = ["h", "g", md.EFFORT, md.ACCESS]
    booster = md.train(CONFIG, features, x, y, np.ones(len(y)), access_monotone=-1)
    names = ["h", "g"]
    f = np.column_stack([np.linspace(-1, 1, 200), np.linspace(1, -1, 200)])
    cols = t7_fit.map_columns(f, names, features, held_effort=0.5, held_access=1.0)
    assert (cols[:, features.index(md.ACCESS)] == 1.0).all()
    assert (cols[:, features.index(md.EFFORT)] == 0.5).all()
    low = md.predict_held(booster, features, cols, {md.EFFORT: 0.5, md.ACCESS: 0.5})
    high = md.predict_held(booster, features, cols, {md.EFFORT: 0.5, md.ACCESS: 3.5})
    assert not np.allclose(low, high)
    assert np.allclose(high - low, (high - low)[0])  # one shift for every cell
    assert (np.argsort(low, kind="stable") == np.argsort(high, kind="stable")).all()
    assert (high - low)[0] <= 0  # monotone falling, as asked for here


def test_held_access_is_the_median_and_refuses_undefined_values():
    assert md.held_access(np.array([30.0, 10.0, 20.0, 1000.0])) == 25.0
    with pytest.raises(ValueError):
        md.held_access(np.array([10.0, np.nan]))


# --- access excluded from the area of applicability --------------------------------------------


def test_access_is_excluded_from_the_area_of_applicability(t7_fit):
    rng = np.random.default_rng(3)
    n = 400
    x = np.column_stack([rng.normal(0, 1, n), rng.normal(0, 1, n), rng.normal(0, 1, n),
                         rng.uniform(0, 5000, n)])  # fmt: skip
    columns = ["h", "g", md.EFFORT, md.ACCESS]
    data = SimpleNamespace(cols=lambda fs: x[:, [columns.index(c) for c in fs]],
                           blocks=rng.integers(0, 5, n))  # fmt: skip
    gains = np.array([3.0, 1.0, 50.0, 80.0])  # effort and access carry most of the gain
    aoa, habitat = t7_fit.area_of_applicability(data, columns, gains)
    assert habitat == ["h", "g"]
    assert aoa.weights.tolist() == [3.0, 1.0]
    assert md.habitat_features(columns) == ["h", "g"]


# --- condition 3: one block resampling for both groups -------------------------------------------


def _group(seed, n=900, lift=0.4):
    rng = np.random.default_rng(seed)
    blocks = rng.integers(0, 8, n)
    y = (rng.random(n) < 0.3).astype(int)
    w = rng.uniform(0.5, 2.0, n)
    a = rng.normal(0, 1, n) + 0.3 * y
    full = a + rng.normal(0, 0.5, n) + lift * y
    return mt.GroupScores(full, a, y, w, blocks)


def test_contrast_point_is_the_mycorrhizal_gain_minus_the_saprotroph_gain():
    m, s = _group(1, lift=0.6), _group(2, lift=0.1)
    got = mt.host_specific_contrast(m, s, resamples=50)
    gain_m = mt.weighted_auc(m.full, m.y, m.w) - mt.weighted_auc(m.a, m.y, m.w)
    gain_s = mt.weighted_auc(s.full, s.y, s.w) - mt.weighted_auc(s.a, s.y, s.w)
    assert got.point == pytest.approx(gain_m - gain_s, abs=1e-12)
    assert got.resamples == 50 and got.low <= got.point <= got.high


def test_contrast_resamples_blocks_once_for_both_groups():
    """Two identical groups give a contrast of exactly 0 in every resample only if each resample
    draws one set of blocks and applies it to both groups; separate draws would scatter it."""
    m = _group(4)
    s = mt.GroupScores(m.full.copy(), m.a.copy(), m.y.copy(), m.w.copy(), m.blocks.copy())
    got = mt.host_specific_contrast(m, s, resamples=200)
    assert got.point == 0.0 and got.low == 0.0 and got.high == 0.0


def test_contrast_draw_is_by_block_with_the_ruled_seed():
    m, s = _group(7, lift=0.6), _group(8, lift=0.1)
    got = mt.host_specific_contrast(m, s, resamples=30, seed=mt.SEED)
    blocks = np.unique(np.concatenate([m.blocks, s.blocks]))
    rng = np.random.default_rng(mt.SEED)
    diffs = []
    for _ in range(30):
        times = np.bincount(rng.integers(0, len(blocks), size=len(blocks)),
                            minlength=len(blocks))  # fmt: skip
        tm = times[np.searchsorted(blocks, m.blocks)]
        ts = times[np.searchsorted(blocks, s.blocks)]
        gm = mt.weighted_auc(m.full, m.y, m.w * tm) - mt.weighted_auc(m.a, m.y, m.w * tm)
        gs = mt.weighted_auc(s.full, s.y, s.w * ts) - mt.weighted_auc(s.a, s.y, s.w * ts)
        diffs.append(gm - gs)
    low, high = np.percentile(diffs, [2.5, 97.5])
    assert got.low == pytest.approx(low, abs=1e-12) and got.high == pytest.approx(high, abs=1e-12)


def test_shared_forested_blocks_need_thirty_presences_in_both_groups(t7_fit):
    blocks_a = np.array([1] * 40 + [2] * 40 + [3] * 40 + [4] * 5 + [1, 2, 3, 4] * 10)
    y_a = np.array([1] * 125 + [0] * 40)
    blocks_b = np.array([1] * 30 + [2] * 29 + [3] * 50 + [4] * 60 + [1, 2, 3, 4] * 10)
    y_b = np.array([1] * 169 + [0] * 40)
    got = t7_fit.shared_forested_blocks({1, 2, 4}, blocks_a, y_a, blocks_b, y_b)
    assert got == [1]  # 2: 29 in b; 3: not forested; 4: 5 in a


# --- the specimen filters ------------------------------------------------------------------------

CC0 = "http://creativecommons.org/publicdomain/zero/1.0/legalcode"
CC_BY = "http://creativecommons.org/licenses/by/4.0/legalcode"
CC_BY_NC = "http://creativecommons.org/licenses/by-nc/4.0/legalcode"


@pytest.fixture
def join(tmp_path):
    rows = [ListRow("Suillus", None, "Suillaceae", "ectomycorrhizal", "clear", "s", ""),
            ListRow("Tricholoma", None, "Tricholomataceae", "ectomycorrhizal", "mixed", "s", ""),
            ListRow("Mycena", None, "Mycenaceae", "other", "clear", "s", "")]  # fmt: skip
    digest = write_list(tmp_path / "list.tsv", rows)
    return Join(load_list(tmp_path / "list.tsv", digest), digest, MYCORRHIZAL_GROUP, MAIN_RUN)


def _row(**kw):
    base = {"license": "CC0_1_0", "coordinateUncertaintyInMeters": "250", "genus": "Suillus",
            "family": "Suillaceae", "order": "Boletales", "taxonRank": "SPECIES"}  # fmt: skip
    return {**base, **kw}


def test_licence_class_reads_cc0_and_cc_by_only():
    assert sp.licence_class(CC0) == "CC0" and sp.licence_class("CC0_1_0") == "CC0"
    assert sp.licence_class(CC_BY) == "CC BY" and sp.licence_class("CC_BY_4_0") == "CC BY"
    for other in (CC_BY_NC, "CC_BY_NC_4_0", "", "http://creativecommons.org/licenses/by-sa/4.0/"):
        assert sp.licence_class(other) is None, other


def test_specimen_licence_filter_keeps_cc0_and_cc_by_by_dataset_and_by_record(join):
    assert sp.classify(_row(), CC0, join) == sp.KEPT
    assert sp.classify(_row(license="CC_BY_4_0"), CC_BY, join) == sp.KEPT
    assert sp.classify(_row(), CC_BY_NC, join) != sp.KEPT  # the dataset is BY-NC
    assert sp.classify(_row(license="CC_BY_NC_4_0"), CC0, join) != sp.KEPT  # the record is


def test_specimen_uncertainty_filter_keeps_a_stated_value_of_1000_m_or_less(join):
    assert sp.classify(_row(coordinateUncertaintyInMeters="1000"), CC0, join) == sp.KEPT
    assert sp.classify(_row(coordinateUncertaintyInMeters="1000.5"), CC0, join) != sp.KEPT
    assert sp.classify(_row(coordinateUncertaintyInMeters=""), CC0, join) != sp.KEPT
    assert sp.classify(_row(coordinateUncertaintyInMeters="5000"), CC0, join) != sp.KEPT


def test_specimen_genus_filter_is_the_main_runs_membership(join):
    assert sp.classify(_row(genus="Tricholoma"), CC0, join) != sp.KEPT  # mixed: side run only
    assert sp.classify(_row(genus="Mycena"), CC0, join) != sp.KEPT
    assert sp.classify(_row(genus="", taxonRank="FAMILY"), CC0, join) != sp.KEPT


def test_a_licence_other_than_cc0_or_cc_by_in_the_kept_set_stops_the_run():
    sp.assert_open_licences([{"license": "CC0_1_0", "datasetKey": "d1"}], {"d1": CC0})
    with pytest.raises(RuntimeError, match="licence"):
        sp.assert_open_licences([{"license": "CC0_1_0", "datasetKey": "d1"}], {"d1": CC_BY_NC})
    with pytest.raises(RuntimeError, match="licence"):
        sp.assert_open_licences([{"license": "CC_BY_NC_4_0", "datasetKey": "d1"}], {"d1": CC0})


def test_the_specimen_predicate_is_the_dispatchs():
    p = sp.specimen_predicate()
    assert p["type"] == "and"
    leaves = {(q.get("key"), q.get("value")) for q in p["predicates"] if q["type"] == "equals"}
    assert ("BASIS_OF_RECORD", "PRESERVED_SPECIMEN") in leaves
    assert ("HAS_COORDINATE", "true") in leaves
    assert ("HAS_GEOSPATIAL_ISSUE", "false") in leaves
    assert ("TAXON_KEY", "5") in leaves
    within = [q for q in p["predicates"] if q["type"] == "within"]
    assert within == [{"type": "within",
                       "geometry": "POLYGON((-125.0 40.0,-111.0 40.0,-111.0 49.0,-125.0 49.0,"
                                   "-125.0 40.0))"}]  # fmt: skip


# --- P10b in the fit report; the output folder --------------------------------------------------


def _d(point, low, high):
    return mt.Difference(point, low, high, 1000)


def test_p10b_verdict_and_every_condition_are_written_with_p10_beside_marked_no_verdict(t7_fit):
    got = t7_fit.p10b_figures(_d(0.003, -0.0004, 0.008), _d(0.05, 0.01, 0.06),
                              _d(-0.01, -0.02, 0.0), "no usable data", p10_passes=True)  # fmt: skip
    assert got["verdict"] == "fail"
    c = got["conditions"]
    assert c["1_block_clustered_full_minus_B"]["point"] == 0.003
    assert c["1_block_clustered_full_minus_B"]["interval_wholly_above_zero"] is False
    assert c["2_within_cell_full_minus_A_block_resampled"]["low"] == 0.01
    assert c["3_host_specific_contrast"]["high"] == 0.0
    assert c["4_independent_data"] == {"status": "no usable data"}
    assert got["p10_d140"] == {"passes": True, "reading": "no verdict"}


def test_p10b_with_condition_4_pending_is_never_reported_as_a_pass(t7_fit):
    ok = _d(0.01, 0.005, 0.02)
    got = t7_fit.p10b_figures(ok, ok, ok, t7_fit.CONDITION_4_PENDING, p10_passes=True)
    assert got["verdict"] != "pass"
    assert got["verdict"].startswith("incomplete")
    assert got["conditions"]["4_independent_data"] == {"status": t7_fit.CONDITION_4_PENDING}
    got = t7_fit.p10b_figures(ok, ok, ok, "no usable data", p10_passes=False)
    assert got["verdict"] == "pass"


def test_the_fit_refuses_to_write_into_the_judged_runs_folders(t7_fit, tmp_path):
    for judged in t7_fit.JUDGED:
        with pytest.raises(SystemExit, match="judged"):
            t7_fit.check_out_dir(judged)
        with pytest.raises(SystemExit, match="judged"):
            t7_fit.check_out_dir(judged / "sub")
    assert t7_fit.check_out_dir(tmp_path / "refit-smoke") == tmp_path / "refit-smoke"
    (tmp_path / "full").mkdir()
    (tmp_path / "full" / "x").write_text("x")
    with pytest.raises(SystemExit, match="not empty"):
        t7_fit.check_out_dir(tmp_path / "full")
