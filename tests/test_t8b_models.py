"""D159 (2) and (4): the clamp, the main tree model in T1's form with effort and M1 to M5, its
no-weather twin, and T8's additive model on the clamped measures. Synthetic worlds only."""

from datetime import date

import numpy as np
import pytest

from forager_forecast.t8 import models as md
from forager_forecast.t8b import clamp as cl
from forager_forecast.t8b import models as bm


def world(per_year=300, seed=5, effect=1.5):
    rng = np.random.default_rng(seed)
    years = np.repeat(np.arange(2015, 2026), per_year)
    n = len(years)
    week = rng.integers(1, 53, size=n)
    mondays = [date.fromisocalendar(int(y), int(w), 1) for y, w in zip(years, week, strict=True)]
    lat = rng.uniform(42, 49.5, n)
    lon = rng.uniform(-125, -121, n)
    log_e = rng.normal(0, 0.7, n)
    weather = rng.normal(size=(n, 5))
    angle = md.day_of_year_angle(mondays)
    eta = -3.0 + 1.2 * np.cos(angle - 4.9) + 0.6 * log_e + effect * np.tanh(weather[:, 1])
    y = (rng.random(n) < 1 / (1 + np.exp(-eta))).astype(float)
    effort = {int(h): log_e for h in np.unique(years)}
    return md.Inputs(y, years, mondays, lat, lon, effort, weather)


# The clamp ---------------------------------------------------------------------------------------


def test_the_range_comes_from_the_training_rows_only():
    w = np.array([[1.0, 5.0], [3.0, -2.0], [100.0, 50.0]])
    train = np.array([True, True, False])
    low, high = cl.training_range(w, train)
    assert low.tolist() == [1.0, -2.0] and high.tolist() == [3.0, 5.0]


def test_values_outside_the_range_take_its_nearest_end_and_inside_stay_as_they_are():
    w = np.array([[0.0, 6.0], [2.0, 0.0], [100.0, -50.0]])
    out = cl.clamp(w, np.array([1.0, -2.0]), np.array([3.0, 5.0]))
    assert out.tolist() == [[1.0, 5.0], [2.0, 0.0], [3.0, -2.0]]
    assert w[2, 0] == 100.0  # the input is not changed in place


def test_clamp_to_training_clamps_held_out_rows_to_the_training_range():
    w = np.array([[1.0], [3.0], [1279.0], [-4.0]])
    train = np.array([True, True, False, False])
    assert cl.clamp_to_training(w, train)[:, 0].tolist() == [1.0, 3.0, 3.0, 1.0]


# The tree model ----------------------------------------------------------------------------------


def test_the_tree_inputs_are_t1s_calendar_effort_and_the_five_measures():
    inputs = world(per_year=20)
    seen = []

    def fitter(config, train_x, train_y, test_x):
        seen.append(train_x.shape[1])
        return np.full(len(test_x), train_y.mean())

    configs = [{"id": "a"}]
    bm.loyo_trees(inputs, True, configs, fitter)
    assert set(seen) == {10}
    seen.clear()
    bm.loyo_trees(inputs, False, configs, fitter)
    assert set(seen) == {5}


def test_the_held_out_year_reaches_the_trees_clamped_to_its_folds_training_range():
    inputs = world(per_year=20)
    w = inputs.weather.copy()
    held = inputs.years == 2021
    w[held, 1] = 1e6
    inputs = md.Inputs(inputs.y, inputs.years, inputs.mondays, inputs.latitude,
                       inputs.longitude, inputs.log_effort, w)  # fmt: skip
    finals = []

    def fitter(config, train_x, train_y, test_x):
        if len(train_x) + len(test_x) == len(inputs.y):
            finals.append((train_x[:, 5:], test_x[:, 5:]))
        return np.full(len(test_x), train_y.mean())

    bm.loyo_trees(inputs, True, [{"id": "a"}], fitter)
    assert len(finals) == 11
    for train, test in finals:
        assert (test <= train.max(axis=0)).all() and (test >= train.min(axis=0)).all()


def test_tuning_is_on_training_years_only_and_a_fixed_choice_skips_it():
    inputs = world(per_year=20)
    calls = {"n": 0}

    def fitter(config, train_x, train_y, test_x):
        calls["n"] += 1
        return np.full(len(test_x), train_y.mean() + (0.01 if config["id"] == "b" else 0.0))

    configs = [{"id": "a"}, {"id": "b"}]
    _p, chosen = bm.loyo_trees(inputs, True, configs, fitter)
    assert set(chosen) == set(range(2015, 2026))
    # 11 outer folds x (2 configurations x 10 inner folds + 1 final fit).
    assert calls["n"] == 11 * (2 * 10 + 1)
    calls["n"] = 0
    _p2, again = bm.loyo_trees(inputs, True, configs, fitter, fixed_choice=chosen)
    assert again == chosen and calls["n"] == 11


def test_the_tree_model_predicts_every_unit_from_a_fit_that_never_saw_its_year():
    inputs = world(per_year=20)

    def fitter(config, train_x, train_y, test_x):
        return np.full(len(test_x), train_y.mean())

    p, _ = bm.loyo_trees(inputs, True, [{"id": "a"}], fitter)
    for h in range(2015, 2026):
        held = inputs.years == h
        assert p[held] == pytest.approx(inputs.y[~held].mean())


# The readable additive model ---------------------------------------------------------------------


def test_the_readable_model_does_not_extrapolate_past_a_folds_training_range():
    inputs = world()
    held = inputs.years == 2021
    top = inputs.weather[~held, 1].max()
    extreme = inputs.weather.copy()
    extreme[held, 1] = 5 * abs(top) + 10
    at_top = inputs.weather.copy()
    at_top[held, 1] = top
    spec = md.PROPOSED_SPEC
    p_extreme = bm.loyo_readable(inputs, spec, weather=extreme)
    p_top = bm.loyo_readable(inputs, spec, weather=at_top)
    assert p_extreme[held] == pytest.approx(p_top[held], rel=1e-9, abs=1e-12)


def test_the_readable_model_matches_t8s_additive_model_when_nothing_is_out_of_range():
    inputs = world()
    w = inputs.weather.copy()
    # Every held-out value inside its fold's training range: the clamp changes nothing.
    for h in range(2015, 2026):
        held = inputs.years == h
        lo, hi = w[~held].min(axis=0), w[~held].max(axis=0)
        w[held] = np.clip(w[held], lo, hi)
    inputs = md.Inputs(inputs.y, inputs.years, inputs.mondays, inputs.latitude,
                       inputs.longitude, inputs.log_effort, w)  # fmt: skip
    spec = md.PROPOSED_SPEC
    assert bm.loyo_readable(inputs, spec) == pytest.approx(
        md.loyo_additive(inputs, spec, True), rel=1e-9
    )
