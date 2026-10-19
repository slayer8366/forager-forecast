"""The week-keyed scoring pulls (dispatch 2026-10-18-pnw-pilot-w42-publish.md, Amendment 1).

W42's weather goes into its own store directory, never W41's `cds/`, and nothing is written through
a link into another directory. W41's constants and `--scoring` path stay as they were. Synthetic
files only; no request is made."""

import sys
from datetime import date
from pathlib import Path

import h5py
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import pnw_cds_hourly_pull as land  # noqa: E402
import pnw_cds_precip_hourly as rain  # noqa: E402

from forager_forecast.cells import IsoWeek  # noqa: E402

W41, W42 = IsoWeek(2026, 41), IsoWeek(2026, 42)
HOURS = [f"{h:02d}:00" for h in range(24)]


def test_land_plan_for_w42_runs_to_october_11():
    months, last = land.scoring_plan(W42)
    assert months == [(2026, 7), (2026, 8), (2026, 9), (2026, 10)]
    assert last == {(2026, 10): 11}


def test_land_plan_for_w41_is_w41s_constants():
    assert land.scoring_plan(W41) == (land.SCORING_MONTHS, land.LAST_DAY)


def test_w41_constants_unchanged():
    assert land.SCORING_MONTHS == [(2026, 7), (2026, 8), (2026, 9), (2026, 10)]
    assert land.LAST_DAY == {(2026, 10): 4}
    assert [n for n, _ in rain.scoring_chunks()] == [
        "hourly-era5-precip-2026-07-09",
        "hourly-era5-precip-2026-10-01-04",
        "hourly-era5-precip-2026-10-05T00",
    ]


def test_rain_chunks_for_w42_after_w41s_rain():
    got = list(rain.scoring_chunks_for(W42, held_through=date(2026, 10, 4)))
    assert [n for n, _ in got] == [
        "hourly-era5-precip-2026-10-05-11",
        "hourly-era5-precip-2026-10-12T00",
    ]
    days, closing = got[0][1], got[1][1]
    assert days["year"] == ["2026"] and days["month"] == ["10"]
    assert days["day"] == ["05", "06", "07", "08", "09", "10", "11"]
    assert days["time"] == HOURS
    assert closing["day"] == ["12"] and closing["time"] == ["00:00"]
    for _, r in got:
        assert r["variable"] == ["total_precipitation"] and r["area"] == rain.AREA


def test_rain_chunks_refuse_a_month_boundary():
    with pytest.raises(SystemExit, match="unsupported"):
        list(rain.scoring_chunks_for(W42, held_through=date(2026, 9, 30)))


@pytest.mark.parametrize("mod", [land, rain])
def test_refuses_w41s_store(mod, tmp_path, monkeypatch):
    store = tmp_path / "cds"
    store.mkdir()
    monkeypatch.setattr(mod, "W41_STORE", store)
    with pytest.raises(SystemExit, match="W41's store"):
        mod.refuse_w41_store(store)
    via = tmp_path / "via"
    via.symlink_to(store)
    with pytest.raises(SystemExit, match="W41's store"):
        mod.refuse_w41_store(via)
    other = tmp_path / "cds-2026-W42"
    other.mkdir()
    mod.refuse_w41_store(other)


def _hourly_rain(path: Path, start: str, hours: int) -> None:
    t0 = int(np.datetime64(start, "s").astype(np.int64))
    with h5py.File(path, "w") as h:
        vt = h.create_dataset("valid_time", data=t0 + 3600 * np.arange(hours, dtype=np.int64))
        vt.attrs["units"] = np.bytes_("seconds since 1970-01-01")
        h["latitude"] = np.array([45.0, 44.75])
        h["longitude"] = np.array([-123.0, -122.75])
        h["tp"] = np.full((hours, 2, 2), 1e-4, dtype=np.float32)


def test_rain_aggregate_refuses_a_linked_target(tmp_path):
    elsewhere = tmp_path / "w41"
    elsewhere.mkdir()
    target = elsewhere / "hourly-era5-precip-2026.daily.h5"
    target.write_bytes(b"W41's file")
    out = tmp_path / "w42"
    out.mkdir()
    _hourly_rain(out / "hourly-era5-precip-2026-10-05-11.nc", "2026-10-05T00:00:00", 49)
    (out / "hourly-era5-precip-2026.daily.h5").symlink_to(target)
    with pytest.raises(SystemExit, match="link"):
        rain.aggregate(out)
    assert target.read_bytes() == b"W41's file"


def test_land_refuses_linked_targets(tmp_path):
    real = tmp_path / "real.h5"
    real.write_bytes(b"x")
    link = tmp_path / "hourly-era5land-2026-10.daily.h5"
    link.symlink_to(real)
    with pytest.raises(SystemExit, match="link"):
        land.refuse_links([tmp_path / "free.json", link])
    land.refuse_links([tmp_path / "free.json"])
