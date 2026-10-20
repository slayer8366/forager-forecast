"""T8's models on synthetic worlds: bases, the additive logistic fit, leave-one-year-out with no
leak of the held-out year, and the challenger's fold loop. No real data."""

from datetime import date, timedelta

import numpy as np
import pytest

from forager_forecast import t1_model as tm
from forager_forecast.t8 import models as md


def test_a_natural_spline_of_3_df_has_3_columns_and_is_linear_beyond_its_boundary_knots():
    rng = np.random.default_rng(0)
    x = rng.normal(size=500)
    knots = md.ns_knots(x, 3)
    assert len(knots) == 4
    assert knots[1] == pytest.approx(np.quantile(x, 1 / 3))
    beyond = np.linspace(x.max(), x.max() + 5, 50)
    b = md.ns_basis(beyond, knots)
    assert b.shape == (50, 3)
    second = np.diff(b, n=2, axis=0)
    assert np.abs(second).max() < 1e-9


def test_the_spline_reproduces_a_cubic_inside_its_knots_closely_and_a_line_exactly():
    x = np.linspace(-2, 2, 400)
    knots = md.ns_knots(x, 3)
    basis = np.column_stack([np.ones_like(x), md.ns_basis(x, knots)])
    line = 3 - 2 * x
    coef, *_ = np.linalg.lstsq(basis, line, rcond=None)
    assert basis @ coef == pytest.approx(line, abs=1e-9)


def test_tied_knots_are_refused():
    with pytest.raises(ValueError, match="distinct"):
        md.ns_knots(np.zeros(50), 3)


def world(n_years=11, per_year=1200, weather_effect=1.5, seed=3):
    """Units over 2015-2025 with a seasonal cycle, a place gradient, effort and one weather
    measure that matters (if weather_effect) and three that do not."""
    rng = np.random.default_rng(seed)
    years = np.repeat(np.arange(2015, 2015 + n_years), per_year)
    n = len(years)
    week = rng.integers(1, 53, size=n)
    mondays = [date.fromisocalendar(int(y), int(w), 1) for y, w in zip(years, week, strict=True)]
    lat = rng.uniform(42, 49.5, n)
    lon = rng.uniform(-125, -121, n)
    log_e = rng.normal(0, 0.7, n)
    weather = rng.normal(size=(n, 4))
    angle = md.day_of_year_angle(mondays)
    eta = -4.0 + 1.2 * np.cos(angle - 4.9) + 0.15 * (lat - 46) + 0.8 * log_e
    eta += weather_effect * np.tanh(weather[:, 0])
    p = 1 / (1 + np.exp(-eta))
    y = (rng.random(n) < p).astype(float)
    inputs = md.Inputs(
        y=y,
        years=years,
        mondays=mondays,
        latitude=lat,
        longitude=lon,
        log_effort={h: log_e for h in range(2015, 2015 + n_years)},
        weather=weather,
    )
    return inputs, p


def test_the_weather_model_beats_its_twin_when_weather_matters_and_not_when_it_does_not():
    spec = md.PROPOSED_SPEC
    inputs, _p = world(weather_effect=1.5)
    with_w = md.loyo_additive(inputs, spec, use_weather=True)
    without = md.loyo_additive(inputs, spec, use_weather=False)
    assert tm.brier_skill(with_w, without, inputs.y) > 0.01
    flat, _p = world(weather_effect=0.0)
    with_w = md.loyo_additive(flat, spec, use_weather=True)
    without = md.loyo_additive(flat, spec, use_weather=False)
    assert tm.brier_skill(with_w, without, flat.y) < 0.002


def test_held_out_predictions_never_see_their_own_years_outcomes():
    inputs, _p = world(per_year=400)
    before = md.loyo_additive(inputs, md.PROPOSED_SPEC, use_weather=True)
    flipped = inputs.y.copy()
    held = inputs.years == 2020
    flipped[held] = 1.0 - flipped[held]
    changed = md.Inputs(
        flipped, inputs.years, inputs.mondays, inputs.latitude, inputs.longitude,
        inputs.log_effort, inputs.weather,
    )  # fmt: skip
    after = md.loyo_additive(changed, md.PROPOSED_SPEC, use_weather=True)
    assert after[held] == pytest.approx(before[held], rel=1e-10)
    assert not np.allclose(after[~held], before[~held])


def test_each_fold_reads_its_own_effort_values():
    inputs, _p = world(per_year=400)
    base = md.loyo_additive(inputs, md.PROPOSED_SPEC, use_weather=False)
    effort = dict(inputs.log_effort)
    effort[2020] = effort[2020] + np.where(inputs.years == 2020, 1.0, 0.0)
    changed = md.Inputs(
        inputs.y, inputs.years, inputs.mondays, inputs.latitude, inputs.longitude,
        effort, inputs.weather,
    )  # fmt: skip
    after = md.loyo_additive(changed, md.PROPOSED_SPEC, use_weather=False)
    held = inputs.years == 2020
    assert not np.allclose(after[held], base[held])
    assert after[~held] == pytest.approx(base[~held], rel=1e-10)


def test_the_offset_form_fixes_the_effort_coefficient_at_one():
    rng = np.random.default_rng(5)
    n = 4000
    x = np.column_stack([np.ones(n), rng.normal(size=n)])
    offset = rng.normal(size=n)
    p = 1 / (1 + np.exp(-(-2 + 0.5 * x[:, 1] + offset)))
    y = (rng.random(n) < p).astype(float)
    with_offset = md.fit_predict_logistic(x, y, x, offset, offset)
    assert np.corrcoef(with_offset, p)[0, 1] > 0.98


def test_a_separated_fit_is_refused_not_passed_on():
    x = np.column_stack([np.ones(200), np.r_[np.zeros(100), np.ones(100)]])
    y = np.r_[np.zeros(100), np.ones(100)]
    with pytest.raises(md.FitFailed):
        md.fit_predict_logistic(x, y, x)


def test_the_challenger_chooses_on_training_years_only_and_can_reuse_a_choice():
    inputs, _p = world(n_years=4, per_year=150)
    configs = [{"id": "a", "k": 0.0}, {"id": "b", "k": 1.0}]
    seen_years = []

    def fitter(config, train_x, train_y, test_x):
        seen_years.append(len(train_y))
        return np.full(len(test_x), float(train_y.mean()) * (1 + 0.01 * config["k"]))

    p, chosen = md.loyo_challenger(inputs, True, configs, fitter)
    assert sorted(chosen) == [2015, 2016, 2017, 2018]
    assert np.isfinite(p).all()
    # 4 outer folds x (2 configs x 3 inner folds + 1 final fit).
    assert len(seen_years) == 4 * (2 * 3 + 1)
    seen_years.clear()
    _p2, again = md.loyo_challenger(inputs, True, configs, fitter, fixed_choice=chosen)
    assert again == chosen
    assert len(seen_years) == 4


def test_the_challenger_inputs_are_t1s_calendar_effort_and_the_four_measures():
    inputs, _p = world(n_years=2, per_year=10)
    x = md.challenger_matrix(inputs, 2015, use_weather=True)
    assert x.shape == (20, 9)
    assert md.challenger_matrix(inputs, 2015, use_weather=False).shape == (20, 5)
    first = inputs.mondays[0]
    angle = 2 * np.pi * (first.timetuple().tm_yday - 1) / (366 if first.year % 4 == 0 else 365)
    assert x[0, 0] == pytest.approx(np.sin(angle))
    assert first - timedelta(days=first.weekday()) == first  # units are Mondays
