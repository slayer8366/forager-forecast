"""The dispatch's first test: no feature uses weather from on or after the scored date."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from forager_forecast.cell_weeks import CellWeek
from forager_forecast.cells import Cell, IsoWeek
from forager_forecast.t1_design import WINDOW_DAYS
from forager_forecast.weather_windows import (
    DailyWeather,
    MissingWeather,
    calendar_place_features,
    features_for_cell_week,
    scored_date_of,
    window_days,
    window_features,
)

START = date(2024, 1, 1)
SENTINEL = 1.0e9


def synthetic_series(days=400):
    """Deterministic, every value distinct, so any leak changes a feature."""
    series = {}
    for offset in range(days):
        day = START + timedelta(days=offset)
        series[day] = DailyWeather(
            day=day,
            temperature_mean_c=10.0 + 0.01 * offset,
            precipitation_mm=0.1 * (offset % 7),
            soil_temperature_mean_c=8.0 + 0.02 * offset,
            soil_moisture_mean=0.2 + 0.0001 * offset,
        )
    return series


def poisoned_from(series, first_day):
    """Every day on or after first_day gets sentinel values."""
    return {
        day: (
            replace(
                row,
                temperature_mean_c=SENTINEL,
                precipitation_mm=SENTINEL,
                soil_temperature_mean_c=SENTINEL,
                soil_moisture_mean=SENTINEL,
            )
            if day >= first_day
            else row
        )
        for day, row in series.items()
    }


def test_no_feature_uses_weather_from_on_or_after_the_scored_date():
    series = synthetic_series()
    unit = CellWeek(Cell(470, -1230), IsoWeek(2024, 36))
    scored = scored_date_of(unit)
    assert scored == date(2024, 9, 2), "Monday of ISO week 36"
    clean = features_for_cell_week(series, unit)
    poisoned = features_for_cell_week(poisoned_from(series, scored), unit)
    assert poisoned == clean
    assert all(abs(v) < SENTINEL / 1000 for v in poisoned.values())


def test_the_leak_check_can_see_a_leak():
    """Positive control: poisoning the day before the scored date must change every window."""
    series = synthetic_series()
    unit = CellWeek(Cell(470, -1230), IsoWeek(2024, 36))
    scored = scored_date_of(unit)
    clean = features_for_cell_week(series, unit)
    leaky = features_for_cell_week(poisoned_from(series, scored - timedelta(days=1)), unit)
    changed = {k for k in clean if clean[k] != leaky[k]}
    weather_keys = {k for k in clean if k not in calendar_place_features(scored, 0, 0)}
    assert changed == weather_keys


def test_window_days_end_the_day_before_and_have_the_stated_length():
    scored = date(2024, 9, 2)
    for window in WINDOW_DAYS:
        days = window_days(scored, window)
        assert len(days) == window
        assert days[-1] == scored - timedelta(days=1)
        assert days[0] == scored - timedelta(days=window)
        assert scored not in days


def test_window_features_have_one_row_per_variable_and_window():
    series = synthetic_series()
    features = window_features(series, date(2024, 9, 2))
    assert len(features) == 4 * len(WINDOW_DAYS)
    assert features["precipitation_sum_7d"] == pytest.approx(
        sum(series[date(2024, 9, 2) - timedelta(days=k)].precipitation_mm for k in range(1, 8))
    )
    assert features["temperature_mean_3d"] == pytest.approx(
        sum(series[date(2024, 9, 2) - timedelta(days=k)].temperature_mean_c for k in range(1, 4))
        / 3
    )


def test_a_missing_day_inside_a_window_is_an_error_not_a_shorter_window():
    series = synthetic_series()
    del series[date(2024, 8, 1)]
    with pytest.raises(MissingWeather, match="2024-08-01"):
        window_features(series, date(2024, 9, 2))


def test_calendar_place_features():
    row = calendar_place_features(date(2024, 1, 1), 47.0, -123.0)
    assert row == {"doy_sin": 0.0, "doy_cos": 1.0, "latitude": 47.0, "longitude": -123.0}
    mid = calendar_place_features(date(2023, 7, 2), 0.0, 0.0)  # day 183 of 365
    assert mid["doy_cos"] == pytest.approx(-1.0, abs=1e-3)
