"""T8's bar (plan section 7, D133 (5)) on synthetic data built to pass, and to fail each condition
separately. No real record, outcome or weather is read."""

import numpy as np
import pytest

from forager_forecast.t8 import bar
from forager_forecast.t8.design import N_SWAPS

N_CELLS = 300
PER_CELL = 40


def world(seed=1):
    """Units in cells; a true chance that varies by unit; outcomes drawn from it."""
    rng = np.random.default_rng(seed)
    cells = np.repeat(np.arange(N_CELLS), PER_CELL)
    true = np.clip(rng.beta(0.6, 8.0, size=cells.size), 0.001, 0.95)
    y = (rng.random(cells.size) < true).astype(float)
    flat = np.full(cells.size, y.mean())
    lichen_true = np.clip(rng.beta(1.0, 6.0, size=cells.size), 0.001, 0.95)
    lichen_y = (rng.random(cells.size) < lichen_true).astype(float)
    lichen_flat = np.full(cells.size, lichen_y.mean())
    return cells, true, y, flat, lichen_true, lichen_y, lichen_flat


def passing_inputs(seed=1):
    cells, true, y, flat, _lt, lichen_y, lichen_flat = world(seed)
    observed = float(np.mean((true - y) ** 2))
    swaps = np.full(N_SWAPS, observed + 0.01)  # every swap scores worse
    return dict(
        y=y,
        p_model=true,
        p_calendar=flat,
        p_no_weather=flat,
        cells=cells,
        swap_briers=swaps,
        lichen_y=lichen_y,
        lichen_p_weather=lichen_flat,  # weather adds nothing for lichens
        lichen_p_no_weather=lichen_flat,
    )


def failed(result):
    return [c.name for c in result.conditions if not c.passed]


def test_built_to_pass_passes_all_four():
    result = bar.evaluate_bar(**passing_inputs())
    assert [c.name for c in result.conditions] == ["C1", "C2", "C3", "C4"]
    assert failed(result) == []
    assert result.passed is True


def test_c1_fails_alone_when_the_model_does_not_beat_t1s_calendar():
    inputs = passing_inputs()
    inputs["p_calendar"] = inputs["p_model"].copy()  # skill exactly 0 in every resample
    result = bar.evaluate_bar(**inputs)
    assert failed(result) == ["C1"]
    assert result.passed is False
    assert "C1" in result.reason


def test_c2_fails_alone_when_the_model_does_not_beat_the_no_weather_model():
    inputs = passing_inputs()
    inputs["p_no_weather"] = inputs["p_model"].copy()
    result = bar.evaluate_bar(**inputs)
    assert failed(result) == ["C2"]
    assert result.passed is False


def test_c2_fails_when_the_interval_reaches_zero_though_the_point_is_above():
    inputs = passing_inputs()
    cells, true, y, _f, _lt, _ly, _lf = world()
    rng = np.random.default_rng(7)
    # A reference a hair worse than the model on average, in a few cells only.
    noisy = true.copy()
    few = np.isin(cells, rng.choice(N_CELLS, 3, replace=False))
    noisy[few] = np.clip(true[few] + 0.05, 0, 1)
    inputs["p_no_weather"] = noisy
    result = bar.evaluate_bar(**inputs)
    c2 = next(c for c in result.conditions if c.name == "C2")
    assert c2.figures["skill"] > 0
    assert c2.figures["low"] <= 0
    assert not c2.passed


def test_c3_fails_alone_with_ten_swaps_at_or_above_and_passes_with_nine():
    inputs = passing_inputs()
    observed = float(np.mean((inputs["p_model"] - inputs["y"]) ** 2))
    swaps = np.full(N_SWAPS, observed + 0.01)
    swaps[:10] = observed  # a tie counts against the model
    inputs["swap_briers"] = swaps
    result = bar.evaluate_bar(**inputs)
    assert failed(result) == ["C3"]
    c3 = next(c for c in result.conditions if c.name == "C3")
    assert c3.figures["swaps_at_or_above"] == 10
    assert c3.figures["p"] == pytest.approx(11 / 200)
    swaps[9] = observed + 0.01
    inputs["swap_briers"] = swaps
    result = bar.evaluate_bar(**inputs)
    assert failed(result) == []
    c3 = next(c for c in result.conditions if c.name == "C3")
    assert c3.figures["p"] == pytest.approx(10 / 200)


def test_c4_fails_alone_when_weather_also_predicts_lichen_reports():
    inputs = passing_inputs()
    _c, _t, _y, _f, lichen_true, lichen_y, lichen_flat = world()
    inputs["lichen_p_weather"] = lichen_true  # weather "predicts" lichens well
    inputs["lichen_p_no_weather"] = lichen_flat
    result = bar.evaluate_bar(**inputs)
    assert failed(result) == ["C4"]
    c4 = next(c for c in result.conditions if c.name == "C4")
    assert c4.figures["low"] > 0


def test_the_bar_refuses_a_swap_count_other_than_199():
    inputs = passing_inputs()
    inputs["swap_briers"] = inputs["swap_briers"][:198]
    with pytest.raises(ValueError, match="199"):
        bar.evaluate_bar(**inputs)


def test_the_bar_refuses_mismatched_lengths_and_non_finite_values():
    inputs = passing_inputs()
    inputs["p_calendar"] = inputs["p_calendar"][:-1]
    with pytest.raises(ValueError, match="length"):
        bar.evaluate_bar(**inputs)
    inputs = passing_inputs()
    inputs["p_model"] = inputs["p_model"].copy()
    inputs["p_model"][0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        bar.evaluate_bar(**inputs)


def test_intervals_use_1000_cell_resamples_with_the_seed():
    result = bar.evaluate_bar(**passing_inputs())
    c1 = result.conditions[0]
    assert c1.figures["resamples"] == 1000
    assert c1.figures["seed"] == 20260918
    again = bar.evaluate_bar(**passing_inputs())
    assert again.conditions[0].figures == c1.figures
