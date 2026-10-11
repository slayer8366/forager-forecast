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
    x, _, kind = pnw_weather.weather_matrix(tmp_path / "w.npz", rows)
    assert kind == ["own", "none"]
    assert pnw_weather.weather_status(tmp_path / "w.npz", rows, x, kind) == ["missing_days", "sea"]


def test_a_cell_with_no_land_value_reads_its_nearest_land_neighbour(tmp_path):
    """RECORD -822 through the real builder and weather_matrix: a cell whose own point is NaN on
    every day takes the east neighbour (nearer than north at 47 N), flagged "neighbour"."""
    from datetime import date

    from forager_forecast.cells import Cell

    with h5py.File(tmp_path / "era5land-2019-01.nc", "w") as h:
        h["latitude"] = np.array([47.1, 47.0])
        h["longitude"] = np.array([-123.0, -122.9])
        t = h.create_dataset("valid_time", data=np.arange(31))
        t.attrs["units"] = np.bytes_("days since 2019-01-01 00:00:00")
        for k, base in (("t2m", 280.0), ("stl1", 281.0), ("swvl1", 0.3)):
            a = np.full((31, 2, 2), base, dtype=np.float32)
            a[:, 1, 0] = np.nan  # (47.0, -123.0): sea
            a[:, 1, 1] = base + 1.0  # (47.0, -122.9): east neighbour, the nearest land
            h[k] = a
    write(tmp_path / "era5-precip-2019.nc", {"tp": 0.002}, 0.25)
    pnw_weather.build(tmp_path, tmp_path / "w.npz")
    rows = [{"cell": Cell(470, -1230), "scored": date(2019, 1, 10)}]
    x, names, kind = pnw_weather.weather_matrix(tmp_path / "w.npz", rows)
    assert kind == ["neighbour"]
    assert x[0, names.index("temperature_mean_3d")] == pytest.approx(281.0 - 273.15, abs=1e-4)
    assert x[0, names.index("soil_moisture_mean_3d")] == pytest.approx(1.3, abs=1e-6)


def test_timeseries_file_is_read_and_gridded_files_win_where_both_exist(tmp_path):
    from datetime import date

    lat = np.arange(495, 419, -1) / 10
    lon = np.arange(-1250, -1209, 1) / 10
    n = (date(2025, 12, 31) - date(2014, 9, 1)).days + 1
    with h5py.File(tmp_path / "ts-era5land-t1box.daily.h5", "w") as h:
        h["latitude"], h["longitude"] = lat, lon
        t = h.create_dataset("valid_time", data=np.arange(n))
        t.attrs["units"] = np.bytes_("days since 2014-09-01")
        for k, v in (("t2m", 290.0), ("stl1", 291.0), ("swvl1", 0.2)):
            h[k] = np.full((n, len(lat), len(lon)), v, dtype=np.float32)
    write(tmp_path / "era5land-2019-01.nc", {"t2m": 280.0, "stl1": 281.0, "swvl1": 0.3}, 0.1)
    write(tmp_path / "era5-precip-2019.nc", {"tp": 0.002}, 0.25)
    summary = pnw_weather.build(tmp_path, tmp_path / "w.npz")
    g = pnw_weather.load(tmp_path / "w.npz")
    i = g["temperature"].index[(470, -1230)]
    d19 = (date(2019, 1, 1) - date(2014, 9, 1)).days
    d18 = (date(2018, 6, 1) - date(2014, 9, 1)).days
    assert g["temperature"].values[i, d19] == pytest.approx(6.85, abs=1e-4)  # gridded wins
    assert g["temperature"].values[i, d18] == pytest.approx(16.85, abs=1e-4)  # time series
    assert summary["land_route_by_month"]["2019-01"] == "derived daily statistics"
    assert summary["land_route_by_month"]["2018-06"].startswith("reanalysis-era5-land-timeseries")
