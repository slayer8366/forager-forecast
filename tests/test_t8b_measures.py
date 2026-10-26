"""M1 to M5 for units: which series each unit reads (Daymet cell, ERA5-Land point under RECORD
-822), the windows at both timings, the refusal of a missing window, and the swap tables.
Synthetic grids only."""

from datetime import date, timedelta

import numpy as np
import pytest
from t8b_files import rule_all

from forager_forecast.cells import Cell
from forager_forecast.daily_grid import DailyGrid
from forager_forecast.t8 import weather as tw
from forager_forecast.t8b import daymet as dm
from forager_forecast.t8b import design
from forager_forecast.t8b import measures as ms

START = date(2015, 9, 1)
N = 500
DAYS = [START + timedelta(days=i) for i in range(N)]


def rain_series(cells):
    vals = np.array([[(k + 1) * 100 + i % 50 for i in range(N)] for k in range(len(cells))], float)
    return dm.DaymetCells(DAYS, {c: k for k, c in enumerate(cells)}, vals, {c: 1 for c in cells})


def land(points, offset):
    vals = np.array([[offset + k + 0.01 * i for i in range(N)] for k in range(len(points))])
    return DailyGrid(START, {p: k for k, p in enumerate(points)}, vals)


LAND_POINTS = [(450, -1230), (450, -1229), (451, -1230)]


def grids():
    return {
        "soil_moisture_l2": land(LAND_POINTS, 0.2),
        "soil_temperature_l2": land(LAND_POINTS, 10.0),
        "dewpoint_depression": land(LAND_POINTS, 3.0),
    }


def test_each_unit_reads_its_own_cell_or_its_nearest_neighbour_and_none_is_marked():
    daymet = rain_series([(450, -1230), (451, -1229)])
    cells = [Cell(450, -1230), Cell(450, -1229), Cell(455, -1240)]
    p = ms.unit_points(cells, daymet, grids())
    assert p.rain == [(450, -1230), (450, -1230), (455, -1240)]
    assert p.rain_kind == ["own", "neighbour", "none"]
    assert p.land[:2] == [(450, -1230), (450, -1229)]
    assert p.land_kind == ["own", "own", "none"]


def test_the_measures_are_d159s_windows_ending_the_day_before_the_week():
    daymet = rain_series([(450, -1230)])
    g = grids()
    cells = [Cell(450, -1230)]
    monday = date(2016, 3, 7)
    p = ms.unit_points(cells, daymet, g)
    x = ms.measure_matrix(daymet, g, p, [monday], design.HEADLINE_END_GAP)
    d0 = (monday - START).days
    rain = daymet.values[0]
    assert x[0, 0] == pytest.approx(rain[d0 - 14 : d0].sum())
    assert x[0, 1] == pytest.approx(rain[d0 - 56 : d0].sum())
    for j, (v, w) in enumerate(
        [("soil_moisture_l2", 14), ("soil_temperature_l2", 14), ("dewpoint_depression", 7)], 2
    ):
        assert x[0, j] == pytest.approx(g[v].values[0, d0 - w : d0].mean())


def test_the_week_late_timing_moves_every_window_7_days_earlier():
    daymet = rain_series([(450, -1230)])
    g = grids()
    cells = [Cell(450, -1230)]
    monday = date(2016, 3, 7)
    p = ms.unit_points(cells, daymet, g)
    late = ms.measure_matrix(daymet, g, p, [monday], design.FORECAST_END_GAP)
    early = ms.measure_matrix(daymet, g, p, [monday - timedelta(days=7)], design.HEADLINE_END_GAP)
    assert late == pytest.approx(early)


def test_a_unit_with_a_missing_window_is_refused_and_counted(monkeypatch):
    rule_all(monkeypatch, "fit")
    daymet = rain_series([(450, -1230)])
    g = grids()
    cells = [Cell(450, -1230), Cell(455, -1240)]
    p = ms.unit_points(cells, daymet, g)
    mondays = [date(2016, 3, 7)] * 2
    with pytest.raises(ms.MissingWeather, match="1 of 2 units"):
        ms.measures_for_units(daymet, g, p, mondays, 1)


def test_building_the_fit_inputs_refuses_while_the_readings_are_open():
    daymet = rain_series([(450, -1230)])
    g = grids()
    p = ms.unit_points([Cell(450, -1230)], daymet, g)
    with pytest.raises(design.NotRuled):
        ms.measures_for_units(daymet, g, p, [date(2016, 3, 7)], 1)


def test_the_swap_table_under_the_identity_reproduces_the_true_measures(monkeypatch):
    rule_all(monkeypatch, "fit")
    daymet = rain_series([(450, -1230)])
    g = grids()
    cells = [Cell(450, -1230)] * 2
    mondays = [date(2016, 3, 7), date(2016, 3, 14)]
    p = ms.unit_points(cells, daymet, g)
    weeks = [10, 11]
    table = ms.per_source_year(daymet, g, p, weeks, 1, [2016])
    x = ms.measures_for_units(daymet, g, p, mondays, 1)
    assert np.array_equal(tw.swapped_matrix(table, [2016, 2016], {2016: 2016}), x)
