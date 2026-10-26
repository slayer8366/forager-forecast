"""T8b's bar on the tree model (D159 (4), (6)): C1 to C4 as T8's bar.py, tuning once per fold on
true weather and held fixed for the 199 swaps, and the per-measure shuffle. Synthetic worlds and a
cheap stand-in fitter only; t8's own tests cover bar.py's conditions."""

import numpy as np
import pytest
from t8b_files import rule_all
from test_t8b_models import world

from forager_forecast.t8 import weather as tw
from forager_forecast.t8b import bar_run as br
from forager_forecast.t8b import design


def setup(per_year=8):
    inputs = world(per_year=per_year)
    n = len(inputs.y)
    rng = np.random.default_rng(9)
    table = {int(y): rng.normal(size=(n, 5)) for y in design.YEARS}
    true = tw.swapped_matrix(table, inputs.years, {y: y for y in design.YEARS})
    inputs = type(inputs)(inputs.y, inputs.years, inputs.mondays, inputs.latitude,
                          inputs.longitude, inputs.log_effort, true)  # fmt: skip
    cells = np.array([f"c{i % 7}" for i in range(n)])
    lichen_y = (rng.random(n) < 0.2).astype(float)
    t1_p = np.full(n, 0.2)
    swaps = tw.draw_swaps(design.YEARS, design.N_SWAPS, design.SEED)
    return inputs, table, cells, lichen_y, t1_p, swaps


class Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, config, train_x, train_y, test_x):
        self.calls.append((config["id"], train_x.copy(), test_x.copy()))
        bump = 0.01 if config["id"] == "b" else 0.0
        return np.clip(np.full(len(test_x), train_y.mean() + bump), 0.01, 0.99)


CONFIGS = [{"id": "a"}, {"id": "b"}]


def test_the_tree_bar_refuses_while_the_fit_readings_are_open():
    inputs, table, cells, lichen_y, t1_p, swaps = setup(per_year=3)
    with pytest.raises(design.NotRuled):
        br.tree_bar(inputs, t1_p, cells, lichen_y, CONFIGS, Recorder(), table, swaps)


def test_tuning_runs_once_per_fold_and_the_199_swaps_reuse_it(monkeypatch):
    rule_all(monkeypatch, "fit")
    inputs, table, cells, lichen_y, t1_p, swaps = setup()
    rec = Recorder()
    run = br.tree_bar(inputs, t1_p, cells, lichen_y, CONFIGS, rec, table, swaps)
    tuned = 11 * (2 * 10 + 1)  # one model family, tuned in each of 11 folds
    # weather, no-weather, lichen weather and lichen no-weather are tuned; each swap only refits.
    assert len(rec.calls) == 4 * tuned + design.N_SWAPS * 11
    assert run.swap_briers.shape == (design.N_SWAPS,)
    assert set(run.chosen["weather"]) == set(design.YEARS)


def test_each_swap_fits_on_the_swapped_years_weather(monkeypatch):
    rule_all(monkeypatch, "fit")
    inputs, table, cells, lichen_y, t1_p, swaps = setup()
    rec = Recorder()
    br.tree_bar(inputs, t1_p, cells, lichen_y, CONFIGS, rec, table, swaps)
    widths = {c[1].shape[1] for c in rec.calls}
    assert widths == {5, 10}
    first_swap = rec.calls[2 * 11 * 21 : 2 * 11 * 21 + 11]
    w = tw.swapped_matrix(table, inputs.years, swaps[0])
    held = inputs.years == 2015
    _id, train_x, _test_x = first_swap[0]
    assert np.array_equal(train_x[:, 5:], w[~held])


def test_the_conditions_carry_1000_resamples_and_seed_20260918(monkeypatch):
    rule_all(monkeypatch, "fit")
    inputs, table, cells, lichen_y, t1_p, swaps = setup()
    run = br.tree_bar(inputs, t1_p, cells, lichen_y, CONFIGS, Recorder(), table, swaps)
    names = [c.name for c in run.bar.conditions]
    assert names == ["C1", "C2", "C3", "C4"]
    for c in run.bar.conditions:
        if c.name != "C3":
            assert c.figures["resamples"] == 1000 and c.figures["seed"] == 20260918


def test_a_measures_own_shuffle_swaps_only_that_column(monkeypatch):
    rule_all(monkeypatch, "fit")
    inputs, table, cells, _lichen_y, _t1_p, swaps = setup()
    chosen = {y: "a" for y in design.YEARS}
    rec = Recorder()
    out = br.measure_shuffle(
        inputs, CONFIGS, rec, chosen, np.full(len(inputs.y), 0.2), cells, table, swaps, 3
    )
    assert out["measure"] == "M4" and out["label"] == "no verdict"
    assert out["swaps"] == design.N_SWAPS
    held = inputs.years == 2015
    w = tw.swapped_matrix(table, inputs.years, swaps[0])
    _id, train_x, _ = rec.calls[11]  # the first swap's first fold
    assert np.array_equal(train_x[:, 5 + 3], w[~held, 3])
    others = [0, 1, 2, 4]
    assert np.array_equal(train_x[:, [5 + k for k in others]], inputs.weather[~held][:, others])
