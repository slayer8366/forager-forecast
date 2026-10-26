"""T8b's fixed choices against D159, and the refusal while readings are open. No real data."""

from datetime import date

import pytest

from forager_forecast.t8 import design as t8d
from forager_forecast.t8b import design


def test_the_five_measures_are_d159s_and_nothing_else():
    got = [(m.name, m.variable, m.reduction, m.days) for m in design.MEASURES]
    assert got == [
        ("M1", "rain", "sum", 14),
        ("M2", "rain", "sum", 56),
        ("M3", "soil_moisture_l2", "mean", 14),
        ("M4", "soil_temperature_l2", "mean", 14),
        ("M5", "dewpoint_depression", "mean", 7),
    ]


def test_land_measures_read_era5_land_layer_2_and_the_2m_fields():
    assert design.ERA5_LAND_SHORT == {
        "swvl2": "volumetric_soil_water_layer_2",
        "stl2": "soil_temperature_level_2",
        "t2m": "2m_temperature",
        "d2m": "2m_dewpoint_temperature",
    }


def test_the_bar_and_the_timings_are_t8s_own_values():
    # D159 (6): C1 to C4 exactly as D133 (5), seed 20260918.
    assert design.SEED == t8d.SEED == 20260918
    assert design.N_SWAPS == 199 and design.BOOTSTRAP_RESAMPLES == 1000
    assert design.C3_ALPHA == 0.05
    assert design.HEADLINE_END_GAP == 1 and design.FORECAST_END_GAP == 8
    assert design.YEARS == tuple(range(2015, 2026))
    assert design.T1_HEADLINE_UNITS == 52718


def test_c5_is_weeks_27_to_52_of_2026_after_mid_february_2027():
    assert design.C5_YEAR == 2026
    assert design.C5_WEEKS == tuple(range(27, 53))
    assert design.C5_DOWNLOAD_AFTER == date(2027, 2, 15)


@pytest.mark.parametrize("step", ["fit", "c5", "count", "pull"])
def test_every_step_refuses_while_its_readings_are_open(step):
    assert design.RULED == {}
    with pytest.raises(design.NotRuled, match=f"for the {step} are not ruled"):
        design.require_ruled(step)


def test_every_pending_reading_has_a_proposal_and_at_least_one_alternative():
    for p in design.PENDING.values():
        assert p.proposed and p.alternatives, p.id
        assert p.step in ("fit", "c5", "count", "pull"), p.id
