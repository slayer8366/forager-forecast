"""T7 items 8 and 9: background inside the frame, block folds, leakage, per-block tuning."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from forager_forecast.t7.background import (
    NotEnoughBackground,
    background_weights,
    cell_list_sha256,
    draw_background,
    in_frame,
)
from forager_forecast.t7.folds import (
    GRID,
    Fold,
    LeakageError,
    assert_no_leakage,
    forested_blocks,
    informative_blocks,
    inner_choice,
    inner_groups,
    leave_one_block_out,
    leave_one_block_out_folds,
    tuning_configurations,
    weighted_log_loss,
)

GRID_FILE = (
    Path(__file__).parents[1] / "docs" / "audits" / "2026-10-15-t7-build" / "tuning_grid.json"
)


def test_only_cells_in_the_frame_are_candidates_and_the_draw_is_seeded_and_sorted():
    keys = np.array([5, 6, 7, 5, 9])
    assert in_frame(keys, np.array([5, 9])).tolist() == [True, False, False, True, True]
    candidates = np.arange(1000, dtype=np.uint32)[::-1]
    a = draw_background(candidates, n=100, seed=20260918)
    b = draw_background(candidates[::-1], n=100, seed=20260918)
    assert a.dtype == np.uint32 and len(a) == 100 and len(set(a.tolist())) == 100
    assert a.tolist() == sorted(a.tolist()) and a.tolist() == b.tolist()
    assert draw_background(candidates, n=100, seed=1).tolist() != a.tolist()
    assert cell_list_sha256(a) == hashlib.sha256(a.astype("<u4").tobytes()).hexdigest()


def test_asking_for_more_background_than_there_are_cells_is_refused():
    with pytest.raises(NotEnoughBackground):
        draw_background(np.arange(10, dtype=np.uint32), n=11)
    with pytest.raises(NotEnoughBackground):  # duplicates do not count twice
        draw_background(np.array([1, 1, 2], dtype=np.uint32), n=3)


def test_background_weights_sum_to_the_presence_total():
    w = background_weights(4, 3.0)
    assert w.tolist() == [0.75] * 4


def test_the_committed_grid_is_the_seeded_draw():
    configs = tuning_configurations()
    assert len(configs) == 20 and len({json.dumps(c, sort_keys=True) for c in configs}) == 20
    for c in configs:
        for k, v in c.items():
            if k != "id":
                assert v in GRID[k]
    assert json.loads(GRID_FILE.read_text()) == {
        "grid": {k: list(v) for k, v in GRID.items()},
        "seed": 20260918,
        "configurations": configs,
    }


def test_forested_and_informative_blocks_use_the_fixed_cuts():
    study = {1: 100, 2: 100, 3: 100}
    shares = {1: 15, 2: 14, 3: 80}
    assert forested_blocks(study, shares) == {1, 3}
    blocks = np.array([1] * 40 + [2] * 40)
    y = np.array([1] * 30 + [0] * 10 + [1] * 29 + [0] * 11)
    assert informative_blocks(blocks, y) == {1}


def test_leave_one_block_out_holds_each_block_out_once_and_the_leakage_check_bites():
    blocks = np.array([3, 1, 2, 3, 1, 2, 2])
    folds = leave_one_block_out_folds(blocks)
    assert [f.block for f in folds] == [1, 2, 3]
    assert sorted(np.concatenate([f.test for f in folds]).tolist()) == list(range(7))
    for f in folds:
        assert_no_leakage(f, blocks)
        assert not (blocks[f.train] == f.block).any()
    leaky = Fold(1, np.array([0, 1, 2]), np.array([4]))
    with pytest.raises(LeakageError):
        assert_no_leakage(leaky, blocks)


def test_inner_groups_split_the_training_blocks_four_ways_with_the_seed():
    g = inner_groups([10, 11, 12, 13, 14, 15, 16, 17, 18])
    assert set(g) == set(range(10, 19)) and set(g.values()) == {0, 1, 2, 3}
    assert g == inner_groups([18, 17, 16, 15, 14, 13, 12, 11, 10])


def test_weighted_log_loss():
    p = np.array([0.9, 0.2])
    y = np.array([1, 0])
    w = np.array([2.0, 1.0])
    expected = -(2 * np.log(0.9) + np.log(0.8)) / 3
    assert weighted_log_loss(p, y, w) == pytest.approx(expected)


def _recording_fitter(seen):
    def fit(config, tx, ty, tw, qx):
        seen.append((config["id"], set(tx[:, 0].tolist()), set(qx[:, 0].tolist())))
        rate = (ty * tw).sum() / tw.sum()
        return np.full(len(qx), rate * config["scale"])

    return fit


def test_the_outer_loop_never_shows_a_fold_its_own_block_and_tunes_inside_training_blocks():
    rng = np.random.default_rng(1)
    blocks = np.repeat(np.arange(6), 20)
    x = blocks[:, None].astype(float)  # column 0 names the block, so the fitter can see it
    y = (rng.random(120) < 0.3).astype(float)
    w = np.ones(120)
    configs = [{"id": "c00", "scale": 1.0}, {"id": "c01", "scale": 0.5}]
    seen = []
    preds, results = leave_one_block_out(configs, x, y, w, blocks, _recording_fitter(seen))
    assert not np.isnan(preds).any() and [r.block for r in results] == list(range(6))
    outer = [s for s in seen if len(s[2]) == 1 and len(s[1]) == 5]
    for _cid, train_blocks, query_blocks in seen:
        assert not (train_blocks & query_blocks)
    assert {next(iter(q)) for _c, _t, q in outer} == set(range(6))
    best, scores = inner_choice(configs, x, y, w, blocks, _recording_fitter([]))
    assert set(scores) == {"c00", "c01"} and best["id"] == min(scores, key=scores.get)


def test_a_leaky_fold_stops_the_outer_loop_before_any_fit():
    blocks = np.array([0, 0, 1, 1])
    seen = []
    bad = [Fold(0, np.array([0, 2, 3]), np.array([1])), Fold(1, np.array([0, 1]), np.array([2, 3]))]
    with pytest.raises(LeakageError):
        leave_one_block_out([{"id": "c", "scale": 1.0}], np.zeros((4, 1)), np.zeros(4),
                            np.ones(4), blocks, _recording_fitter(seen), folds=bad)  # fmt: skip
    assert seen == []
