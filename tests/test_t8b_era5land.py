"""ERA5-Land layer 2 and 2 m fields, from daily-statistics and hourly files laid out as the store
delivers them, to M3 to M5's daily grids. Small synthetic files only."""

from datetime import UTC, date, datetime, timedelta

import numpy as np
import pytest
from t8b_files import write_era5_daily, write_era5_hourly

from forager_forecast.t8b import era5land as el

LATS = [45.1, 45.0]
LONS = [-123.1, -123.0, -122.9]
DAYS = [date(2017, 6, 1) + timedelta(days=i) for i in range(5)]


def fields(n_days, water=None):
    rng = np.random.default_rng(1)
    shape = (n_days, len(LATS), len(LONS))
    out = {
        "swvl2": rng.uniform(0.1, 0.4, shape),
        "stl2": rng.uniform(275, 290, shape),
        "t2m": rng.uniform(278, 295, shape),
        "d2m": rng.uniform(270, 285, shape),
    }
    if water:
        for v in out.values():
            v[:, water[0], water[1]] = np.nan
    return out


def test_daily_statistics_give_layer_2_and_the_dewpoint_depression(tmp_path):
    f = fields(len(DAYS), water=(0, 2))
    path = tmp_path / "era5land-2017-06.nc"
    write_era5_daily(path, DAYS, LATS, LONS, f)
    grids = el.land_grids(el.read_daily_statistics([path]))
    assert set(grids) == {"soil_moisture_l2", "soil_temperature_l2", "dewpoint_depression"}
    g = grids["dewpoint_depression"]
    assert g.start == DAYS[0]
    i = g.index[(450, -1230)]
    want = f["t2m"][:, 1, 1].astype(np.float64) - f["d2m"][:, 1, 1].astype(np.float64)
    assert g.values[i, :5] == pytest.approx(want, abs=1e-4)
    st = grids["soil_temperature_l2"]
    assert st.values[st.index[(451, -1231)], 2] == pytest.approx(
        float(np.float32(f["stl2"][2, 0, 0])) - 273.15, abs=1e-4
    )
    sm = grids["soil_moisture_l2"]
    assert sm.values[sm.index[(450, -1229)], 4] == pytest.approx(float(f["swvl2"][4, 1, 2]))
    assert np.isnan(sm.values[sm.index[(451, -1229)]]).all()


def test_a_file_carrying_layer_1_instead_of_layer_2_is_refused(tmp_path):
    f = fields(len(DAYS))
    f["stl1"] = f.pop("stl2")
    path = tmp_path / "era5land-2017-06.nc"
    write_era5_daily(path, DAYS, LATS, LONS, f)
    with pytest.raises(el.Era5Differs, match="stl2"):
        el.read_daily_statistics([path])


def test_coordinates_off_the_tenth_degree_grid_are_refused(tmp_path):
    path = tmp_path / "era5land-2017-06.nc"
    write_era5_daily(path, DAYS, [45.05, 45.0], LONS, fields(len(DAYS)))
    with pytest.raises(el.Era5Differs, match="multiples of 0.1"):
        el.read_daily_statistics([path])


def test_a_day_delivered_twice_with_different_values_is_refused(tmp_path):
    a, b = tmp_path / "a.nc", tmp_path / "b.nc"
    write_era5_daily(a, DAYS, LATS, LONS, fields(len(DAYS)))
    f = fields(len(DAYS))
    f["t2m"] = f["t2m"] + 1.0
    write_era5_daily(b, DAYS, LATS, LONS, f)
    with pytest.raises(el.Era5Differs, match="twice"):
        el.read_daily_statistics([a, b])


def test_hourly_files_become_24_hour_utc_means_and_an_incomplete_day_stays_missing(tmp_path):
    start = int(datetime(2017, 6, 1, tzinfo=UTC).timestamp())
    stamps = np.array([start + 3600 * h for h in range(48 + 23)])  # day 3 lacks 23:00
    f = fields(len(stamps))
    path = tmp_path / "hourly-era5land-2017-06.nc"
    write_era5_hourly(path, stamps, LATS, LONS, f)
    grids = el.land_grids(el.read_hourly([path]))
    g = grids["dewpoint_depression"]
    i = g.index[(450, -1230)]
    diff = f["t2m"][:, 1, 1].astype(np.float64) - f["d2m"][:, 1, 1].astype(np.float64)
    assert g.values[i, 0] == pytest.approx(diff[:24].mean(), abs=1e-4)
    assert g.values[i, 1] == pytest.approx(diff[24:48].mean(), abs=1e-4)
    assert np.isnan(g.values[i, 2])
