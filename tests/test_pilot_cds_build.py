"""Scoring from the store's files (owner, Forager RECORD -819): synthetic NetCDF in the layout the
store delivers, built by scripts/pnw_pilot_cds_build.py (pnw_weather.build itself), scored by
scripts/pnw_pilot_score.py --cds-npz. No network."""

import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import h5py
import numpy as np
import pytest

from forager_forecast import live_weather as lw
from forager_forecast import pilot_output as po
from forager_forecast.cells import IsoWeek
from forager_forecast.daily_grid import feature_names
from forager_forecast.weather_windows import (
    DailyWeather,
    calendar_place_features,
    window_features,
)

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pnw_pilot_cds_build import build_window  # noqa: E402

WEEK = IsoWeek(2026, 41)
START, END = lw.window_span(WEEK)
LAT = np.array([47.1, 47.0])  # descending, as the store delivers
LON = np.array([-123.0, -122.9])
QLAT = np.array([47.25, 47.0])
QLON = np.array([-123.0, -122.75])
NAMES = ["doy_sin", "doy_cos", "latitude", "longitude", *feature_names()]


def _write(path: Path, first: date, n: int, lat, lon, variables: dict) -> None:
    with h5py.File(path, "w") as h:
        h["valid_time"] = np.arange(n, dtype=np.int64)
        h["valid_time"].attrs.create("units", np.bytes_(f"days since {first.isoformat()}"))
        h["latitude"] = lat
        h["longitude"] = lon
        for k, v in variables.items():
            h[k] = v.astype(np.float32)


@pytest.fixture
def store(tmp_path):
    rng = np.random.default_rng(20260918)
    cds = tmp_path / "cds"
    cds.mkdir()
    for month, days in ((7, 31), (8, 31), (9, 30), (10, 4)):  # October only to the 4th
        shape = (days, len(LAT), len(LON))
        swvl1 = rng.uniform(0.1, 0.4, size=shape)
        swvl1[:, 0, 0] = np.nan  # one sea cell: ERA5-Land has no value
        t2m = rng.normal(285, 4, size=shape)
        t2m[:, 0, 0] = np.nan
        stl1 = rng.normal(284, 3, size=shape)
        stl1[:, 0, 0] = np.nan
        _write(
            cds / f"era5land-2026-{month:02d}.nc",
            date(2026, month, 1),
            days,
            LAT,
            LON,
            {"t2m": t2m, "stl1": stl1, "swvl1": swvl1},
        )
    n = (date(2026, 10, 4) - date(2026, 7, 1)).days + 1
    tp = rng.gamma(0.5, 0.004, size=(n, len(QLAT), len(QLON)))  # metres
    _write(cds / "era5-precip-2026.nc", date(2026, 7, 1), n, QLAT, QLON, {"tp": tp})
    return tmp_path


@pytest.mark.xfail(
    strict=True,
    raises=po.UnitMismatch,
    reason="reviewer B1: pnw_weather.build subtracts 273.15 from soil moisture; the range check "
    "must stop scoring until the builder's fix lands (strict: an XPASS fails the suite, so the "
    "marker comes off when the fix arrives)",
)
def test_store_files_build_score_and_match_independent_features(store):
    npz = store / "w41.npz"
    summary = build_window(store / "cds", npz, WEEK)
    assert summary["days_missing_on_any_point_with_data"] == {
        "temperature": [],
        "soil_temperature": [],
        "soil_moisture": [],
        "precipitation": [],
    }
    import lightgbm as lgb

    rng = np.random.default_rng(1)
    x = rng.normal(size=(300, len(NAMES)))
    y = (x[:, 5] + rng.normal(size=300) > 0.5).astype(float)
    booster = lgb.train(
        {"objective": "binary", "verbose": -1, "seed": 1, "num_leaves": 4, "min_data_in_leaf": 5},
        lgb.Dataset(x, y),
        num_boost_round=10,
    )
    model = store / "model"
    model.mkdir()
    booster.save_model(str(model / "model.txt"))
    (model / "model.json").write_text(json.dumps({"feature_names": NAMES}))
    done = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/pnw_pilot_score.py"),
            "--week",
            WEEK.id,
            "--cds-npz",
            str(npz),
            "--model",
            str(model),
            "--kind",
            "full",
            "--out",
            str(store / "out"),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert done.returncode == 0, done.stderr
    week_dir = store / "out" / "pnw-pilot" / "2026-10-05"
    got = {
        f["id"]: f["properties"]["chance"]
        for f in json.loads((week_dir / "cantharellus.geojson").read_text())["features"]
    }
    # Box cells only: of the four synthetic cells, (471, -1230) is sea; the rest are scored.
    assert sorted(got) == ["470_-1229", "470_-1230", "471_-1229"]
    with h5py.File(store / "cds" / "era5-precip-2026.nc") as h:
        tp = h["tp"][:].astype(np.float64) * 1000.0
    for cid, chance in got.items():
        la, lo = (int(v) for v in cid.split("_"))
        i, j = (
            list(np.round(LAT * 10).astype(int)).index(la),
            list(np.round(LON * 10).astype(int)).index(lo),
        )
        daily = {}
        for month in (7, 8, 9, 10):
            with h5py.File(store / "cds" / f"era5land-2026-{month:02d}.nc") as h:
                for d in range(h["t2m"].shape[0]):
                    day = date(2026, month, 1) + timedelta(days=d)
                    q = (day - date(2026, 7, 1)).days
                    qi = 1 if la <= 471 else 0  # 47.0 and 47.1 are nearest 47.0
                    qj = 0  # -123.0 and -122.9 are nearest -123.0
                    daily[day] = DailyWeather(
                        day,
                        float(h["t2m"][d, i, j]) - 273.15,
                        float(tp[q, qi, qj]),
                        float(h["stl1"][d, i, j]) - 273.15,
                        float(h["swvl1"][d, i, j]),
                    )
        monday = WEEK.monday()
        row = calendar_place_features(monday, la / 10, lo / 10)
        row.update(window_features(daily, monday))
        expected = float(booster.predict(np.array([list(row.values())]))[0])
        assert chance == pytest.approx(expected, abs=5e-5), cid
    manifest = json.loads((week_dir / "manifest.json").read_text())
    assert manifest["weather_source"] == "copernicus"
    assert manifest["weather_through"] == "2026-10-04"


def _calendar_model(path: Path):
    import lightgbm as lgb

    rng = np.random.default_rng(2)
    x = rng.normal(size=(300, 4))
    y = (x[:, 0] + rng.normal(size=300) > 0.5).astype(float)
    booster = lgb.train(
        {"objective": "binary", "verbose": -1, "seed": 1, "num_leaves": 4, "min_data_in_leaf": 5},
        lgb.Dataset(x, y),
        num_boost_round=10,
    )
    path.mkdir()
    booster.save_model(str(path / "model.txt"))
    (path / "model.json").write_text(json.dumps({"feature_names": NAMES[:4]}))
    return booster


def _score(store, *args):
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/pnw_pilot_score.py"),
            "--week",
            WEEK.id,
            *args,
            "--out",
            str(store / "out"),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def test_calendar_floor_scores_every_land_cell_without_weather(store):
    booster = _calendar_model(store / "cal")
    done = _score(
        store,
        "--land-from-store",
        str(store / "cds"),
        "--model",
        str(store / "cal"),
        "--kind",
        "calendar",
    )
    assert done.returncode == 0, done.stderr
    week_dir = store / "out" / "pnw-pilot" / "2026-10-05"
    feats = json.loads((week_dir / "cantharellus.geojson").read_text())["features"]
    got = {f["id"]: f["properties"] for f in feats}
    assert sorted(got) == ["470_-1229", "470_-1230", "471_-1229"]  # 471_-1230 is sea
    for cid, p in got.items():
        la, lo = (int(v) for v in cid.split("_"))
        row = calendar_place_features(WEEK.monday(), la / 10, lo / 10)
        expected = float(booster.predict(np.array([list(row.values())]))[0])
        assert p["chance"] == pytest.approx(expected, abs=5e-5)
        assert p["weather_through"] is None and p["drivers"] == []
    manifest = json.loads((week_dir / "manifest.json").read_text())
    assert manifest["weather_source"] == "none"
    assert manifest["model_kind"] == "calendar"
    assert manifest["weather_through"] is None


def test_the_floor_refuses_the_weather_model(store):
    done = _score(
        store,
        "--land-from-store",
        str(store / "cds"),
        "--model",
        str(store / "cal"),
        "--kind",
        "full",
    )
    assert done.returncode != 0
    assert "scores the calendar model only" in done.stderr
