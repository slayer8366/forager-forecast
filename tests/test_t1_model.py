"""T1's evaluation machinery (src/forager_forecast/t1_model.py). Synthetic numbers only."""

import json
from pathlib import Path

import numpy as np
import pytest

from forager_forecast import t1_model as tm

GRID_FILE = Path(__file__).parents[1] / "docs/audits/2026-10-10-pnw-pilot-t1/tuning_grid.json"


def test_twenty_distinct_configurations_drawn_by_the_production_seed():
    configs = tm.tuning_configurations()
    assert len(configs) == 20
    assert len({tuple(sorted((k, v) for k, v in c.items() if k != "id")) for c in configs}) == 20
    assert configs == tm.tuning_configurations()


def test_committed_grid_equals_the_draw():
    committed = json.loads(GRID_FILE.read_text())
    assert committed["seed"] == 20260918
    assert committed["grid"] == {k: list(v) for k, v in tm.GRID.items()}
    assert committed["configurations"] == tm.tuning_configurations()


def test_inner_tuning_never_sees_the_outer_held_out_year():
    years = np.repeat(np.arange(2015, 2020), 10)
    x = years.reshape(-1, 1).astype(float)
    y = (np.arange(50) % 2).astype(float)
    seen: list[set] = []

    def spy(config, train_x, train_y, test_x):
        seen.append(set(train_x[:, 0].tolist()) | set(test_x[:, 0].tolist()))
        return np.full(len(test_x), 0.5)

    configs = tm.tuning_configurations()[:2]
    _, folds = tm.leave_one_year_out(configs, x, y, years, spy)
    # Per outer fold: 2 configs x 4 inner years, then 1 outer fit. The inner fits see 4 years.
    per_fold = 2 * 4 + 1
    for f, fold in enumerate(folds):
        for call in seen[f * per_fold : f * per_fold + 8]:
            assert fold.year not in call
    assert [f.year for f in folds] == list(range(2015, 2020))


def test_held_out_predictions_come_from_a_model_without_that_year():
    years = np.repeat(np.arange(2015, 2018), 4)
    x = years.reshape(-1, 1).astype(float)
    y = np.zeros(12)

    def leaky(config, train_x, train_y, test_x):
        # Predicts 1 for any test row whose year was in training: a leak would show as 1.
        return np.isin(test_x[:, 0], train_x[:, 0]).astype(float)

    predictions, _ = tm.leave_one_year_out(tm.tuning_configurations()[:1], x, y, years, leaky)
    assert np.all(predictions == 0)


def test_brier_skill_and_bootstrap_cluster_by_cell():
    outcomes = np.array([1, 0, 1, 0, 0, 1], float)
    model = np.array([0.9, 0.1, 0.8, 0.2, 0.1, 0.7])
    reference = np.full(6, 0.5)
    skill = tm.brier_skill(model, reference, outcomes)
    assert skill == pytest.approx(1 - np.mean((model - outcomes) ** 2) / 0.25)
    # One cluster only: every resample is the whole set, so the interval collapses on the skill.
    low, high, _ = tm.clustered_bootstrap_skill(model, reference, outcomes, np.zeros(6))
    assert low == pytest.approx(skill) and high == pytest.approx(skill)
    low2, high2, _ = tm.clustered_bootstrap_skill(model, reference, outcomes, np.arange(6))
    assert low2 < skill < high2 or low2 <= skill <= high2


def test_auc_matches_the_pairwise_definition():
    rng = np.random.default_rng(1)
    scores = rng.integers(0, 5, size=40).astype(float)
    outcomes = (rng.random(40) > 0.6).astype(float)
    pos, neg = scores[outcomes == 1], scores[outcomes == 0]
    pairs = [(p > n) + 0.5 * (p == n) for p in pos for n in neg]
    assert tm.auc(scores, outcomes) == pytest.approx(np.mean(pairs))


def test_fold_with_under_30_positives_is_uninformative():
    assert not tm.FoldResult(2015, 100, 29, "c00", {}).informative
    assert tm.FoldResult(2015, 100, 30, "c00", {}).informative
