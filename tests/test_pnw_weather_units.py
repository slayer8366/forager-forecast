"""scripts/pnw_weather.py converts each variable to its own unit (review B1): temperatures from K
to °C, soil moisture unchanged in m3 m-3, precipitation from m to mm. Synthetic files."""

import sys
from pathlib import Path

import h5py
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import pnw_weather  # noqa: E402


def write(path: Path, variables: dict[str, float], step: float) -> None:
    with h5py.File(path, "w") as h:
        h["latitude"] = np.array([47.0, 47.0 - step])
        h["longitude"] = np.array([-123.0, -123.0 + step])
        t = h.create_dataset("valid_time", data=np.array([0, 1]))
        t.attrs["units"] = np.bytes_("days since 2019-01-01 00:00:00")
        for k, v in variables.items():
            h[k] = np.full((2, 2, 2), v, dtype=np.float32)


def test_each_variable_in_its_own_unit(tmp_path):
    write(tmp_path / "era5land-2019-01.nc", {"t2m": 280.0, "stl1": 281.0, "swvl1": 0.3}, 0.1)
    write(tmp_path / "era5-precip-2019.nc", {"tp": 0.002}, 0.25)
    pnw_weather.build(tmp_path, tmp_path / "w.npz")
    g = pnw_weather.load(tmp_path / "w.npz")
    d = (np.datetime64("2019-01-01") - np.datetime64("2014-09-01")).astype(int)
    assert g["temperature"].values[0, d] == pytest.approx(6.85, abs=1e-4)
    assert g["soil_temperature"].values[0, d] == pytest.approx(7.85, abs=1e-4)
    assert g["soil_moisture"].values[0, d] == pytest.approx(0.3, abs=1e-6)
    assert g["precipitation"].values[0, d] == pytest.approx(2.0, abs=1e-4)


def test_weather_status_tells_sea_from_a_month_not_pulled(tmp_path):
    from datetime import date

    from forager_forecast.cells import Cell

    write(tmp_path / "era5land-2019-01.nc", {"t2m": 280.0, "stl1": 281.0, "swvl1": 0.3}, 0.1)
    write(tmp_path / "era5-precip-2019.nc", {"tp": 0.002}, 0.25)
    pnw_weather.build(tmp_path, tmp_path / "w.npz")
    rows = [
        {"cell": Cell(470, -1230), "scored": date(2019, 1, 2)},  # window reaches 2018: not pulled
        {"cell": Cell(400, -1100), "scored": date(2019, 1, 2)},  # no ERA5-Land point: sea
    ]
    x, _ = pnw_weather.weather_matrix(tmp_path / "w.npz", rows)
    assert pnw_weather.weather_status(tmp_path / "w.npz", rows, x) == ["missing_days", "sea"]
