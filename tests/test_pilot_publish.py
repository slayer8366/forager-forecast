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
