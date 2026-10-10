"""scripts/pnw_pilot_score.py end to end on a tiny synthetic case: two land cells sharing one ERA5
rain point, one sea cell, a booster trained here on random numbers. No network."""

import hashlib
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from forager_forecast import live_weather as lw
from forager_forecast.cells import Cell, IsoWeek
from forager_forecast.daily_grid import feature_names
from forager_forecast.open_meteo import daily_weather_from_archive
from forager_forecast.weather_windows import calendar_place_features, window_features

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "pnw_pilot_score.py"
WEEK = IsoWeek(2026, 41)
START, END = lw.window_span(WEEK)
LAND = [Cell(470, -1230), Cell(471, -1230)]
SEA = Cell(470, -1250)
NAMES = ["doy_sin", "doy_cos", "latitude", "longitude", *feature_names()]


def payload(cell: Cell, rng, sea: bool = False, rain=None) -> dict:
    days = [START + timedelta(days=i) for i in range((END - START).days + 1)]
    hours = [datetime(d.year, d.month, d.day, h) for d in days for h in range(24)]

    def v(x):
        return None if sea else round(float(x), 1)

    return {
        "latitude": cell.center_latitude,
        "longitude": cell.center_longitude,
        "daily": {
            "time": [d.isoformat() for d in days],
            "temperature_2m_mean": [v(rng.normal(12, 4)) for _ in days],
            "precipitation_sum": [None if sea else r for r in rain],
        },
        "hourly": {
            "time": [h.isoformat(timespec="minutes") for h in hours],
            "soil_temperature_0_to_7cm": [v(rng.normal(11, 3)) for _ in hours],
            "soil_moisture_0_to_7cm": [
                None if sea else round(float(rng.uniform(0.1, 0.4)), 3) for _ in hours
            ],
        },
    }


@pytest.fixture
def case(tmp_path):
    rng = np.random.default_rng(20260918)
    rain = [round(float(r), 1) for r in rng.gamma(0.5, 4.0, size=(END - START).days + 1)]
    cells = [*LAND, SEA]
    body = [payload(c, rng, sea=(c == SEA), rain=rain) for c in cells]
    raw = tmp_path / "weather" / "raw"
    raw.mkdir(parents=True)
    data = json.dumps(body).encode()
    (raw / "batch_000.json").write_bytes(data)
    (raw / "batch_000.request.json").write_text(
        json.dumps(
            {
                "cells": [c.id for c in cells],
                "start": START.isoformat(),
                "end": END.isoformat(),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    )
    import lightgbm as lgb

    x = rng.normal(size=(300, len(NAMES)))
    y = (x[:, 5] + rng.normal(size=300) > 0.5).astype(float)
    booster = lgb.train(
        {"objective": "binary", "verbose": -1, "seed": 1, "num_leaves": 4, "min_data_in_leaf": 5},
        lgb.Dataset(x, y),
        num_boost_round=10,
    )
    model = tmp_path / "model"
    model.mkdir()
    booster.save_model(str(model / "model.txt"))
    (model / "model.json").write_text(json.dumps({"features": NAMES}))
    return tmp_path, body, booster


def run(tmp_path, kind="full", model=None):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--week",
            WEEK.id,
            "--weather",
            str(tmp_path / "weather"),
            "--model",
            str(model or tmp_path / "model"),
            "--kind",
            kind,
            "--out",
            str(tmp_path / "out"),
            "--bridge",
            "test",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def test_scores_land_cells_with_the_model_on_features_built_independently(case):
    tmp_path, body, booster = case
    done = run(tmp_path)
    assert done.returncode == 0, done.stderr + done.stdout
    week_dir = tmp_path / "out" / "pnw-pilot" / "2026-10-05"
    fc = json.loads((week_dir / "cantharellus.geojson").read_text())
    got = {f["id"]: f["properties"] for f in fc["features"]}
    assert sorted(got) == sorted(c.id for c in LAND)  # the sea cell is left out
    monday = WEEK.monday()
    for i, cell in enumerate(LAND):
        daily = daily_weather_from_archive(body[i])
        row = calendar_place_features(monday, cell.center_latitude, cell.center_longitude)
        row.update(window_features(daily, monday))
        assert list(row) == NAMES
        expected = float(booster.predict(np.array([list(row.values())]))[0])
        assert got[cell.id]["chance"] == pytest.approx(expected, abs=5e-5)
        assert got[cell.id]["weather_through"] == "2026-10-04"
        assert len(got[cell.id]["drivers"]) == 3
    manifest = json.loads((week_dir / "manifest.json").read_text())
    assert manifest["cells"]["scored"] == 2
    assert manifest["cells"]["omitted"]["open_meteo_null_values_(sea_or_no_era5_land_value)"] == 1
    assert (manifest["pilot"], manifest["validated"], manifest["reviewed"]) == (True, False, False)
    assert manifest["beats_calendar"] is None and manifest["t1_result"] is None
    assert manifest["weather_bridge"] == "test"
    blocks = sorted(p.name for p in (week_dir / "cantharellus").glob("*.geojson"))
    assert blocks == ["n47w123.geojson"]
    assert manifest["layers"][1]["blocks"] == ["n47w123"]


def test_a_model_whose_feature_order_differs_is_refused(case):
    tmp_path, _body, _booster = case
    swapped = NAMES[:]
    swapped[4], swapped[5] = swapped[5], swapped[4]
    (tmp_path / "model" / "model.json").write_text(json.dumps({"features": swapped}))
    done = run(tmp_path)
    assert done.returncode != 0
    assert "are not the full model's" in done.stderr
