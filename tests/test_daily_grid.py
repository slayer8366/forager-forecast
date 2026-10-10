"""daily_grid.window_matrix gives weather_windows.window_features' numbers, and sees no weather from
on or after the scored date. Synthetic values only."""

from datetime import date, timedelta

import numpy as np
import pytest

from forager_forecast.daily_grid import DailyGrid, feature_names, window_matrix
from forager_forecast.weather_windows import DailyWeather, window_features

START = date(2014, 9, 1)
DAYS = 400


def grids(rng):
    return {
        v: DailyGrid(START, {(470, -1230): 0, (471, -1230): 1}, rng.normal(size=(2, DAYS)))
        for v in ("temperature", "precipitation", "soil_temperature", "soil_moisture")
    }


def scalar(g, row, scored):
    daily = {
        START + timedelta(days=d): DailyWeather(
            START + timedelta(days=d),
            g["temperature"].values[row, d],
            g["precipitation"].values[row, d],
            g["soil_temperature"].values[row, d],
            g["soil_moisture"].values[row, d],
        )
        for d in range(DAYS)
    }
    return window_features(daily, scored)


def test_matches_window_features():
    g = grids(np.random.default_rng(20260918))
    scored = [date(2014, 12, 29), date(2015, 3, 2), date(2015, 9, 28)]
    pts = {v: [(470, -1230), (471, -1230), (470, -1230)] for v in g}
    m = window_matrix(g, pts, scored)
    for i, (row, d) in enumerate([(0, scored[0]), (1, scored[1]), (0, scored[2])]):
        expect = scalar(g, row, d)
        assert list(expect) == feature_names()
        assert m[i] == pytest.approx(np.array(list(expect.values())), rel=1e-12, abs=1e-12)


def test_no_weather_from_on_or_after_the_scored_date():
    g = grids(np.random.default_rng(1))
    scored = [date(2015, 3, 2)]
    pts = {v: [(470, -1230)] for v in g}
    before = window_matrix(g, pts, scored)
    d0 = (scored[0] - START).days
    for v in g.values():
        v.values[:, d0:] += 1000.0
    assert np.array_equal(window_matrix(g, pts, scored), before)
    for v in g.values():
        v.values[0, d0 - 1] += 1000.0
    assert not np.array_equal(window_matrix(g, pts, scored), before)


def test_a_missing_day_or_point_gives_nan_not_a_filled_value():
    g = grids(np.random.default_rng(2))
    scored = [date(2015, 3, 2), date(2015, 3, 2)]
    pts = {v: [(470, -1230), (999, 999)] for v in g}
    g["soil_moisture"].values[0, (scored[0] - START).days - 5] = np.nan
    m = window_matrix(g, pts, scored)
    names = feature_names()
    assert np.isnan(m[0, names.index("soil_moisture_mean_7d")])
    assert not np.isnan(m[0, names.index("soil_moisture_mean_3d")])
    assert not np.isnan(m[0, names.index("temperature_mean_90d")])
    assert np.isnan(m[1]).all()
