"""T6's evaluation (D104, D105): nested choice, ladder, pooling, bootstrap intervals, raw ratios."""

import numpy as np
import pytest
from test_effort import synthetic

from forager_forecast import effort as ef
from forager_forecast import effort_evaluation as ev
from forager_forecast.cells import Cell

YEARS = (2016, 2017, 2018, 2019)
GRID = (ef.Config(0.1, 1), ef.Config(10.0, 9))


@pytest.fixture(scope="module")
def evaluated():
    fungi, _mu, _rate = synthetic(seed=21, integer=True)
    lichen_raw, _m, _r = synthetic(seed=22, integer=True)
    lichen = ef.OutingCounts.from_entries(
        fungi.cells,
        zip(lichen_raw.cell, lichen_raw.week, lichen_raw.day, lichen_raw.count, strict=True),
    )
    return fungi, lichen, ev.evaluate(fungi, lichen, grid=GRID, years=YEARS)


def test_each_fold_takes_the_configuration_with_the_lowest_inner_deviance(evaluated):
    _fungi, _lichen, result = evaluated
    for h in YEARS:
        totals = {c: sum(result.inner[c][(h, j)] for j in YEARS if j != h) for c in GRID}
        assert result.chosen[h] == min(GRID, key=lambda c: (totals[c], GRID.index(c)))


def test_inner_score_is_the_effort_surface_fitted_without_both_years(evaluated):
    fungi, lichen, result = evaluated
    config = GRID[0]
    train = [2018, 2019]
    fungal = ef.fit(fungi, train, config)
    surface = ef.combine(fungal, ef.fit(lichen, train, config), fungi, train)
    assert result.inner[config][(2016, 2017)] == pytest.approx(
        ef.surface_deviance(surface, fungi, 2017).sum()
    )
    assert result.inner[config][(2017, 2016)] == pytest.approx(
        ef.surface_deviance(surface, fungi, 2016).sum()
    )


def test_pooled_per_cell_values_sum_to_the_per_fold_table(evaluated):
    _fungi, _lichen, result = evaluated
    assert set(result.per_cell) == {ev.CONSTANT, *(n for n, _ in ev.LADDER), ev.EFFORT}
    for name, values in result.per_cell.items():
        assert values.sum() == pytest.approx(sum(result.per_fold[h][name] for h in YEARS))


def test_outer_fold_constant_is_the_constant_model_on_that_year(evaluated):
    fungi, _lichen, result = evaluated
    assert result.per_fold[2018][ev.CONSTANT] == pytest.approx(
        ef.constant_deviance(fungi, 2018).sum()
    )


def test_the_true_shape_beats_constant_effort(evaluated):
    _fungi, _lichen, result = evaluated
    full = result.per_cell[ev.LADDER[-1][0]].sum()
    assert full < result.per_cell[ev.CONSTANT].sum()


def test_final_configuration_is_the_lowest_plain_leave_one_year_out(evaluated):
    _fungi, _lichen, result = evaluated
    assert result.final_config == min(
        GRID, key=lambda c: (result.outer_by_config[c], GRID.index(c))
    )


def test_difference_interval_of_identical_models_is_zero():
    values = np.arange(10.0)
    point, interval = ev.difference_interval(values, values, resamples=20)
    assert point == 0.0 and interval == (0.0, 0.0)


def test_difference_interval_sign_and_point():
    model = np.full(30, 1.0)
    comparison = np.full(30, 3.0)
    point, interval = ev.difference_interval(model, comparison, resamples=50)
    assert point == -60.0
    assert interval == pytest.approx((-60.0, -60.0))


def test_weekend_ratio_interval_brackets_a_known_ratio():
    counts, _mu, rate = synthetic(seed=23)
    point, interval = ev.weekend_ratio_interval(counts, ef.Config(0.1, 1), resamples=20)
    assert point == pytest.approx(rate[0] / rate[1], rel=1e-6)
    assert interval[0] == pytest.approx(point, rel=1e-6)
    assert interval[1] == pytest.approx(point, rel=1e-6)


def test_raw_weekend_ratio_is_per_day():
    cells = [Cell(450, -1220)]
    counts = ef.OutingCounts.from_entries(
        cells, [(0, 10, ef.WEEKEND, 4.0), (0, 10, ef.WEEKDAY, 5.0), (0, 400, ef.WEEKEND, 2.0)]
    )
    raw = ev.raw_weekend_ratios(counts)
    assert raw["by_year"]["2015"] == pytest.approx((4 / 2) / (5 / 5))
    assert raw["by_year"]["2022"] is None
    assert raw["overall"] == pytest.approx((6 / 2) / (5 / 5))
    assert raw["by_band"]["45"] == pytest.approx(3.0)
