"""T8's W1 to W4 and the whole-year swaps, on synthetic daily grids only."""

from datetime import date, timedelta

import numpy as np
import pytest

from forager_forecast.cells import Cell
from forager_forecast.daily_grid import DailyGrid, feature_names, window_matrix
from forager_forecast.t8 import weather as tw
from forager_forecast.t8.design import FORECAST_END_GAP, HEADLINE_END_GAP, MEASURES

START = date(2014, 9, 1)
DAYS = 4140  # 2014-09-01 to 2025-12-31, as t1_pnw.npz
LAND = {(470, -1230): 0, (471, -1230): 1}
RAIN = {(188, -492): 0, (188, -491): 1}


def grids(seed=20260918, sea_point=False):
    rng = np.random.default_rng(seed)
    out = {}
    for v in ("temperature", "soil_temperature", "soil_moisture"):
        values = rng.normal(size=(2, DAYS))
        if sea_point:
            values[1] = np.nan  # (471, -1230) carries no land value
        out[v] = DailyGrid(START, dict(LAND), values)
    out["precipitation"] = DailyGrid(START, dict(RAIN), rng.gamma(1.0, 2.0, size=(2, DAYS)))
    return out


CELLS = [Cell(470, -1230), Cell(471, -1230)]


def test_w1_to_w4_equal_t1s_windows_of_the_same_length_at_the_headline_timing():
    g = grids()
    pts = tw.unit_points(CELLS, g)
    scored = [date(2015, 1, 5), date(2019, 10, 7)]
    ours = tw.measure_matrix(g, pts, scored, HEADLINE_END_GAP)
    t1 = window_matrix(
        g,
        {
            "temperature": pts.land,
            "soil_temperature": pts.land,
            "soil_moisture": pts.land,
            "precipitation": pts.rain,
        },
        scored,
    )
    names = feature_names()
    expect = np.column_stack(
        [
            t1[:, names.index("precipitation_sum_14d")],
            t1[:, names.index("precipitation_sum_56d")],
            t1[:, names.index("soil_moisture_mean_7d")],
            t1[:, names.index("soil_temperature_mean_14d")],
        ]
    )
    assert ours == pytest.approx(expect, rel=1e-12, abs=1e-12)


def test_a_measure_is_the_plain_sum_or_mean_over_its_days():
    g = grids()
    pts = tw.unit_points(CELLS[:1], g)
    monday = date(2020, 9, 14)
    d0 = (monday - START).days
    x = tw.measure_matrix(g, pts, [monday], HEADLINE_END_GAP)[0]
    row = g["precipitation"].index[pts.rain[0]]
    assert x[0] == pytest.approx(g["precipitation"].values[row, d0 - 14 : d0].sum())
    assert x[1] == pytest.approx(g["precipitation"].values[row, d0 - 56 : d0].sum())
    assert x[2] == pytest.approx(g["soil_moisture"].values[0, d0 - 7 : d0].mean())
    assert x[3] == pytest.approx(g["soil_temperature"].values[0, d0 - 14 : d0].mean())


def test_the_forecast_timing_is_the_headline_window_seven_days_earlier():
    g = grids()
    pts = tw.unit_points(CELLS, g)
    monday = date(2021, 10, 4)
    forecast = tw.measure_matrix(g, pts, [monday, monday], FORECAST_END_GAP)
    early = tw.measure_matrix(g, pts, [monday - timedelta(days=7)] * 2, HEADLINE_END_GAP)
    assert forecast == pytest.approx(early, rel=1e-12)


@pytest.mark.parametrize("gap", [HEADLINE_END_GAP, FORECAST_END_GAP])
def test_no_weather_from_inside_the_gap_is_read(gap):
    g = grids()
    pts = tw.unit_points(CELLS, g)
    monday = date(2018, 10, 1)
    pts = tw.UnitPoints(pts.land[:1], pts.land_kind[:1], pts.rain[:1])
    before = tw.measure_matrix(g, pts, [monday], gap)
    d0 = (monday - START).days
    for v in g.values():
        v.values[:, d0 - gap + 1 :] += 1000.0
    assert np.array_equal(tw.measure_matrix(g, pts, [monday], gap), before)
    for v in g.values():
        v.values[:, d0 - gap] += 1000.0
    assert not np.array_equal(tw.measure_matrix(g, pts, [monday], gap), before)


def test_a_cell_without_land_values_reads_its_nearest_land_neighbour():
    g = grids(sea_point=True)
    pts = tw.unit_points(CELLS, g)
    assert pts.land_kind == ["own", "neighbour"]
    assert pts.land[1] == (470, -1230)


def test_a_missing_day_is_refused_never_filled():
    g = grids()
    monday = date(2017, 10, 2)
    d0 = (monday - START).days
    g["soil_moisture"].values[0, d0 - 3] = np.nan
    pts = tw.unit_points(CELLS, g)
    x = tw.measure_matrix(g, pts, [monday, monday], HEADLINE_END_GAP)
    assert np.isnan(x[0, 2]) and not np.isnan(x[1, 2])
    with pytest.raises(tw.MissingWeather, match="1 of 2"):
        tw.measures_for_units(g, pts, [monday, monday], HEADLINE_END_GAP)


def test_points_and_days_must_pair_up():
    g = grids()
    pts = tw.unit_points(CELLS, g)
    with pytest.raises(ValueError, match="2 points for 1"):
        tw.measure_matrix(g, pts, [date(2018, 10, 1)], HEADLINE_END_GAP)


def test_measures_are_the_four_fixed_in_the_plan():
    assert [(m.name, m.variable, m.reduction, m.days) for m in MEASURES] == [
        ("W1", "precipitation", "sum", 14),
        ("W2", "precipitation", "sum", 56),
        ("W3", "soil_moisture", "mean", 7),
        ("W4", "soil_temperature", "mean", 14),
    ]


def test_swaps_are_199_distinct_derangements_and_reproducible():
    years = list(range(2015, 2026))
    swaps = tw.draw_swaps(years, 199)
    assert len(swaps) == 199
    assert len({tuple(s[y] for y in years) for s in swaps}) == 199
    for s in swaps:
        assert sorted(s.values()) == years
        assert all(s[y] != y for y in years)
    assert tw.draw_swaps(years, 199) == swaps


def test_a_swap_reads_the_same_iso_week_of_the_other_year_for_every_cell():
    g = grids()
    pts = tw.unit_points(CELLS, g)
    years, weeks = [2016, 2016], [40, 40]
    table = tw.per_source_year(g, pts, years, weeks, HEADLINE_END_GAP, [2016, 2019])
    x = tw.swapped_matrix(table, years, {2016: 2019})
    direct = tw.measure_matrix(g, pts, [date.fromisocalendar(2019, 40, 1)] * 2, HEADLINE_END_GAP)
    assert x == pytest.approx(direct)


def test_week_53_reads_week_52_in_a_year_without_one():
    assert tw.iso_monday(2016, 53) == date.fromisocalendar(2016, 52, 1)
    assert tw.iso_monday(2020, 53) == date.fromisocalendar(2020, 53, 1)
