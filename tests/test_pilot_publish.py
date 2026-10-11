"""The publish script's access dates for the Copernicus citations (scripts/pnw_pilot_publish.py).
No network."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pnw_pilot_publish import accessed_dates  # noqa: E402


def _record(path: Path, dataset: str, when: str) -> None:
    path.write_text(json.dumps({"dataset": dataset, "requested_at_utc": when}))


def test_time_series_access_dates_come_from_its_own_record_directory(tmp_path):
    store, ts = tmp_path / "cds", tmp_path / "ts"
    store.mkdir()
    ts.mkdir()
    _record(store / "hourly-era5land-2026-07.request.json", "reanalysis-era5-land",
            "2026-10-11T17:20:00+00:00")  # fmt: skip
    _record(ts / "pt_478_-1212.request.json", "reanalysis-era5-land-timeseries",
            "2026-10-11T00:38:48+00:00")  # fmt: skip
    _record(ts / "pt_476_-1218.request.json", "reanalysis-era5-land-timeseries",
            "2026-10-11T14:12:50+00:00")  # fmt: skip
    got = accessed_dates([store, ts], {"era5_land_hourly", "era5_land_timeseries"})
    assert got == {"era5_land_hourly": "11-Oct-2026", "era5_land_timeseries": "11-Oct-2026"}


def test_a_product_requested_over_several_days_gets_a_range(tmp_path):
    ts = tmp_path / "ts"
    ts.mkdir()
    _record(ts / "a.request.json", "reanalysis-era5-land-timeseries", "2026-10-10T23:00:00+00:00")
    _record(ts / "b.request.json", "reanalysis-era5-land-timeseries", "2026-10-11T01:00:00+00:00")
    assert accessed_dates([ts], {"era5_land_timeseries"}) == {
        "era5_land_timeseries": "10-Oct-2026 to 11-Oct-2026"
    }


def test_publish_passes_reviewed_through_to_scoring(monkeypatch):
    import pnw_pilot_publish

    seen = {}

    def fake_run(cmd, cwd=None):
        seen["cmd"] = cmd
        return type("Done", (), {"returncode": 7})()

    monkeypatch.setattr(pnw_pilot_publish.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["pnw_pilot_publish.py", "--kind", "calendar"])
    assert pnw_pilot_publish.main() == 7
    cmd = seen["cmd"]
    assert cmd[cmd.index("--reviewed") + 1] == "false"
    monkeypatch.setattr(
        sys, "argv", ["pnw_pilot_publish.py", "--kind", "calendar", "--reviewed", "true"]
    )
    assert pnw_pilot_publish.main() == 7
    cmd = seen["cmd"]
    assert cmd[cmd.index("--reviewed") + 1] == "true"


def _hourly(path: Path, t0: str, hours: int, expver: list[str], var: str) -> None:
    import h5py
    import numpy as np

    start = int(np.datetime64(t0, "s").astype(np.int64))
    with h5py.File(path, "w") as h:
        h["valid_time"] = np.arange(start, start + 3600 * hours, 3600, dtype=np.int64)
        h["valid_time"].attrs["units"] = np.bytes_("seconds since 1970-01-01")
        h["expver"] = np.array([e.encode() for e in expver])
        h[var] = np.zeros((hours, 1, 1))


def test_window_versions_sentence_reads_expver_by_utc_day(tmp_path):
    import zipfile
    from datetime import date

    from pnw_pilot_publish import version_sentence, window_versions

    # Land: 2 days, final; then a zip delivery whose t2m turns preliminary at day 3's 01:00.
    _hourly(tmp_path / "hourly-era5land-2026-07.hourly.nc", "2026-07-30T00", 48, ["0001"] * 48,
            "t2m")  # fmt: skip
    _hourly(tmp_path / "a.nc", "2026-08-01T00", 48, ["0005"] * 48, "stl1")
    _hourly(tmp_path / "b.nc", "2026-08-01T00", 48, ["0001"] + ["0005"] * 47, "t2m")
    with zipfile.ZipFile(tmp_path / "hourly-era5land-2026-08.hourly.zip", "w") as z:
        z.write(tmp_path / "a.nc", "data_0.nc")
        z.write(tmp_path / "b.nc", "data_1.nc")
    # Rain: stamps d 01:00 to d+1 00:00 make day d; the 2026-08-01 00:00 stamp closes 07-31.
    _hourly(tmp_path / "hourly-era5-precip-2026-07-09.nc", "2026-07-30T01", 96,
            ["0001"] * 48 + ["0005"] * 48, "tp")  # fmt: skip
    got = window_versions(tmp_path, date(2026, 7, 30), date(2026, 8, 2))
    assert got == {
        date(2026, 7, 30): {"0001"},
        date(2026, 7, 31): {"0001"},
        date(2026, 8, 1): {"0001", "0005"},
        date(2026, 8, 2): {"0005"},
    }
    assert version_sentence(got) == (
        "Window days 2026-07-30 to 2026-07-31 are the store's final data (expver 0001); "
        "2026-08-01 to 2026-08-02 are its preliminary data (expver 0005), which can be revised."
    )


def test_a_window_day_with_no_version_is_said_so():
    from datetime import date

    from pnw_pilot_publish import version_sentence

    s = version_sentence({date(2026, 7, 7): {"0001"}, date(2026, 7, 8): set()})
    assert "2026-07-08 has no recorded data version" in s


def test_a_single_stamp_file_with_scalar_expver_is_read(tmp_path):
    # The store writes a one-stamp request (e.g. 2026-10-05 00:00, closing 10-04) with a scalar
    # valid_time and expver.
    from datetime import date

    import h5py
    import numpy as np
    from pnw_pilot_publish import window_versions

    with h5py.File(tmp_path / "hourly-era5-precip-2026-10-05T00.nc", "w") as h:
        h["valid_time"] = np.int64(int(np.datetime64("2026-10-05T00", "s").astype(np.int64)))
        h["expver"] = np.bytes_("0005")
        h["tp"] = np.zeros((1, 1))
    assert window_versions(tmp_path, date(2026, 10, 4), date(2026, 10, 4)) == {
        date(2026, 10, 4): {"0005"}
    }


def test_the_bridge_text_no_longer_claims_daily_statistics_only():
    from pnw_pilot_publish import BRIDGE

    assert "daily statistics" not in BRIDGE
    assert "weather.source" in BRIDGE
