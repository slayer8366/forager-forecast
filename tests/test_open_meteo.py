from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest

from forager_forecast.cells import Cell
from forager_forecast.open_meteo import (
    ArchiveGap,
    api_call_units,
    archive_request_url,
    daily_weather_from_archive,
)


def test_every_archive_request_pins_era5_seamless_and_the_cell_itself():
    url = archive_request_url(Cell(470, -1230), date(2015, 1, 1), date(2025, 12, 31))
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "archive-api.open-meteo.com"
    assert parsed.path == "/v1/archive"
    query = parse_qs(parsed.query)
    assert query["models"] == ["era5_seamless"]  # D19, D21; the default is never used
    assert query["latitude"] == ["47.0"]
    assert query["longitude"] == ["-123.0"]
    assert query["elevation"] == ["nan"]
    assert query["cell_selection"] == ["nearest"]
    assert query["timezone"] == ["UTC"]
    assert query["daily"] == ["temperature_2m_mean,precipitation_sum"]
    assert query["hourly"] == ["soil_temperature_0_to_7cm,soil_moisture_0_to_7cm"]
    assert query["start_date"] == ["2015-01-01"]
    assert query["end_date"] == ["2025-12-31"]


def test_a_reversed_range_is_refused():
    with pytest.raises(ValueError):
        archive_request_url(Cell(470, -1230), date(2025, 1, 2), date(2025, 1, 1))


def test_api_call_units_match_the_pricing_page_examples():
    assert api_call_units(days=14, variables=15) == pytest.approx(1.5)
    assert api_call_units(days=28, variables=15) == pytest.approx(3.0)
    assert api_call_units(days=14, variables=10) == pytest.approx(1.0)
    assert api_call_units(days=3, variables=2) == pytest.approx(1.0)
    assert api_call_units(days=30, variables=2, locations=100) == pytest.approx(100 * 30 / 14)


def archive_payload(days=2, null_at=None):
    day_list = [f"2024-09-{d + 1:02d}" for d in range(days)]
    hourly_time = [f"{d}T{h:02d}:00" for d in day_list for h in range(24)]
    soil_t = [10.0 + h / 24 for _ in day_list for h in range(24)]
    soil_m = [0.3 for _ in hourly_time]
    if null_at is not None:
        soil_t[null_at] = None
    return {
        "latitude": 47.0,
        "longitude": -123.0,
        "daily": {
            "time": day_list,
            "temperature_2m_mean": [17.4, 18.0][:days],
            "precipitation_sum": [0.0, 1.5][:days],
        },
        "hourly": {
            "time": hourly_time,
            "soil_temperature_0_to_7cm": soil_t,
            "soil_moisture_0_to_7cm": soil_m,
        },
    }


def test_hourly_soil_values_are_averaged_per_day():
    rows = daily_weather_from_archive(archive_payload())
    assert sorted(rows) == [date(2024, 9, 1), date(2024, 9, 2)]
    first = rows[date(2024, 9, 1)]
    assert first.temperature_mean_c == 17.4
    assert first.precipitation_mm == 0.0
    assert first.soil_temperature_mean_c == pytest.approx(10.0 + sum(range(24)) / 24 / 24)
    assert first.soil_moisture_mean == pytest.approx(0.3)


def test_a_null_is_reported_not_filled():
    with pytest.raises(ArchiveGap, match="soil_temperature_0_to_7cm is null on 2024-09-02"):
        daily_weather_from_archive(archive_payload(null_at=30))


def test_an_error_payload_is_reported():
    with pytest.raises(ArchiveGap, match="Too many"):
        daily_weather_from_archive({"error": True, "reason": "Too many concurrent requests"})
