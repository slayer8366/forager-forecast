"""The PNW pilot's scoring inputs and outputs (src/forager_forecast/pilot_output.py). Synthetic."""

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from forager_forecast import pilot_output as po
from forager_forecast.cells import Cell
from forager_forecast.daily_grid import feature_names
from forager_forecast.weather_windows import DailyWeather, window_features

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from pnw_weather import weather_matrix  # noqa: E402  the training path itself

START = date(2026, 7, 7)
END = date(2026, 10, 4)
# Two cells sharing the ERA5 point q188_-492 (47.0, -123.0), and one on q188_-491.
CELLS = [Cell(470, -1230), Cell(471, -1230), Cell(470, -1227)]


def synthetic(rng, cells=CELLS):
    out = {}
    rain_by_quarter = {}
    for c in cells:
        q = (round(c.center_latitude * 4), round(c.center_longitude * 4))
        rain = rain_by_quarter.setdefault(q, rng.gamma(0.5, 4.0, size=(END - START).days + 1))
        out[c] = {
            START + timedelta(days=i): DailyWeather(
                START + timedelta(days=i),
                float(rng.normal(12, 4)),
                float(rain[i]),
                float(rng.normal(11, 3)),
                float(rng.uniform(0.1, 0.4)),
            )
            for i in range((END - START).days + 1)
        }
    return out


def test_features_through_the_training_path_equal_window_features_on_the_same_days(tmp_path):
    per_cell = synthetic(np.random.default_rng(20260918))
    npz = tmp_path / "live.npz"
    np.savez_compressed(npz, **po.weather_arrays(per_cell, START, END))
    monday = date(2026, 10, 5)
    rows = [{"cell": c, "scored": monday} for c in CELLS]
    x, names, _kind = weather_matrix(npz, rows)
    assert names == feature_names()
    for r, c in enumerate(CELLS):
        expected = window_features(per_cell[c], monday)
        assert list(expected) == names
        assert x[r] == pytest.approx(np.array(list(expected.values())), rel=1e-12, abs=1e-12)


def test_a_missing_day_makes_the_cell_nan_never_a_shorter_window(tmp_path):
    per_cell = synthetic(np.random.default_rng(1))
    del per_cell[CELLS[2]][date(2026, 9, 1)]
    npz = tmp_path / "live.npz"
    np.savez_compressed(npz, **po.weather_arrays(per_cell, START, END))
    x, names, _kind = weather_matrix(npz, [{"cell": c, "scored": date(2026, 10, 5)} for c in CELLS])
    assert np.isfinite(x[:2]).all()
    assert np.isnan(x[2, names.index("temperature_mean_56d")])
    assert np.isfinite(x[2, names.index("temperature_mean_28d")])  # 28d starts 2026-09-07


def test_two_cells_on_one_era5_point_with_different_rain_are_refused():
    per_cell = synthetic(np.random.default_rng(2))
    d = date(2026, 8, 1)
    old = per_cell[CELLS[1]][d]
    per_cell[CELLS[1]][d] = DailyWeather(
        d, old.temperature_mean_c, old.precipitation_mm + 0.1, 1.0, 0.2
    )
    with pytest.raises(po.RainDisagrees, match="2026-08-01"):
        po.weather_arrays(per_cell, START, END)


def test_cell_polygon_is_the_tenth_degree_square_counter_clockwise():
    ring = po.cell_polygon(Cell(470, -1230))[0]
    assert ring == [
        [-123.05, 46.95],
        [-122.95, 46.95],
        [-122.95, 47.05],
        [-123.05, 47.05],
        [-123.05, 46.95],
    ]
    area2 = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:], strict=False))
    assert area2 > 0


def test_block_is_the_one_degree_square_holding_the_centre():
    assert po.block_id(Cell(470, -1230)) == "n47w123"
    assert po.block_id(Cell(479, -1221)) == "n47w123"
    assert po.block_id(Cell(469, -1230)) == "n46w123"
    assert po.block_id(Cell(470, -1231)) == "n47w124"


def test_drivers_are_weather_only_largest_contribution_first():
    names = [
        "doy_sin",
        "latitude",
        "precipitation_sum_14d",
        "temperature_mean_3d",
        "soil_moisture_mean_90d",
    ]
    values = np.array([0.5, 47.0, 23.456789, 11.2, 0.31])
    contrib = np.array([5.0, -4.0, -0.2, 0.9, 0.4])
    out = po.drivers(names, values, contrib)
    assert out == [
        {"label": "Air temperature, mean of the last 3 days (°C)", "value": 11.2},
        {"label": "Soil moisture, mean of the last 90 days (m³/m³)", "value": 0.31},
        {"label": "Rain, total of the last 14 days (mm)", "value": 23.457},
    ]
    assert po.drivers(names[:2], values[:2], contrib[:2]) == []


def test_cell_feature_carries_exactly_d55s_properties():
    f = po.cell_feature(Cell(470, -1230), date(2026, 10, 5), 0.123456, date(2026, 10, 4), "v", [])
    assert set(f["properties"]) == {
        "group",
        "week",
        "chance",
        "uncertainty_low",
        "uncertainty_high",
        "applicable",
        "drivers",
        "weather_through",
        "model_version",
    }
    p = f["properties"]
    assert (p["group"], p["week"], p["chance"], p["applicable"]) == (
        "cantharellus",
        "2026-10-05",
        0.1235,
        True,
    )
    assert p["uncertainty_low"] is None and p["uncertainty_high"] is None
    with pytest.raises(ValueError, match="outside 0 to 1"):
        po.cell_feature(Cell(470, -1230), date(2026, 10, 5), 1.2, date(2026, 10, 4), "v", [])


def test_blocks_hold_every_feature_once():
    feats = [
        po.cell_feature(c, date(2026, 10, 5), 0.1, END, "v", [])
        for c in [Cell(470, -1230), Cell(479, -1221), Cell(469, -1230)]
    ]
    b = po.blocks(feats)
    assert sorted(b) == ["n46w123", "n47w123"]
    assert sum(len(v["features"]) for v in b.values()) == 3


def _units_payload():
    return {
        "daily_units": {"time": "iso8601", "temperature_2m_mean": "°C", "precipitation_sum": "mm"},
        "hourly_units": {
            "time": "iso8601",
            "soil_temperature_0_to_7cm": "°C",
            "soil_moisture_0_to_7cm": "m³/m³",
        },
    }


def test_open_meteo_units_are_checked_per_variable():
    po.check_units(_units_payload())
    wrong = _units_payload()
    wrong["daily_units"]["temperature_2m_mean"] = "°F"
    with pytest.raises(po.UnitMismatch, match="temperature_2m_mean"):
        po.check_units(wrong)
    missing = _units_payload()
    del missing["hourly_units"]["soil_moisture_0_to_7cm"]
    with pytest.raises(po.UnitMismatch, match="soil_moisture_0_to_7cm"):
        po.check_units(missing)


def test_value_ranges_catch_a_kelvin_offset_on_soil_moisture():
    arrays = po.weather_arrays(synthetic(np.random.default_rng(3)), START, END)
    po.check_ranges(arrays)
    bad = dict(arrays)
    bad["soil_moisture_values"] = arrays["soil_moisture_values"] - 273.15  # reviewer's B1
    with pytest.raises(po.UnitMismatch, match="soil_moisture"):
        po.check_ranges(bad)
    kelvin = dict(arrays)
    kelvin["temperature_values"] = arrays["temperature_values"] + 273.15
    with pytest.raises(po.UnitMismatch, match="temperature"):
        po.check_ranges(kelvin)
