"""One command to (re)score the PNW pilot for a week and write the map's files.

Run:  uv run python scripts/pnw_pilot_publish.py --kind calendar|full [--week 2026-W41]
          [--repo-copy] [--beats-calendar true|false|null] [--t1-result '<json>']

Defaults are the pilot's paths (Forager RECORD -814, -819):
- store:  ~/Zynergy/forecast-data-pnw-pilot/cds (read only; the builder's pull writes there)
- models: ~/Zynergy/forecast-data-pnw-pilot/models/primary_t1_1000m_<kind> (read only)
- output: ~/Zynergy/forecast-data-pnw-pilot/scoring/out/pnw-pilot/<week start>/

calendar: every ERA5-Land land cell of T1's box, no weather (scripts/pnw_pilot_score.py
  --land-from-store). Rerun after the builder refits the calendar model; nothing else changes.
full: builds the week's window from the store with pnw_weather.build (scripts/
  pnw_pilot_cds_build.py; stops on a missing day or a unit error), then scores --cds-npz.

--repo-copy also copies the week's directory to samples/pnw-pilot/<week start>/ in this
repository, where the site draws it, after checking the pre-commit hook's 1 MB per-file limit.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pnw_pilot_cds_build import build_window  # noqa: E402
from pnw_t1_fit import copernicus_sources  # noqa: E402

from forager_forecast import live_weather as lw  # noqa: E402
from forager_forecast.cells import IsoWeek  # noqa: E402

DATA = Path.home() / "Zynergy" / "forecast-data-pnw-pilot"
REPO = Path(__file__).resolve().parents[1]
LIMIT = 1024 * 1024
# The banner's weather line, the owner's wording verbatim (Forager RECORD -893, -895). The technical
# detail is in the manifest's weather.source.
BRIDGE = (
    "This forecast's weather comes from the Copernicus climate archive, the same sources the "
    "model was trained on. A second weather service was checked for the same days but isn't used "
    "for scoring."
)


DATASET_SOURCE = {
    "derived-era5-land-daily-statistics": "era5_land_daily",
    "reanalysis-era5-land": "era5_land_hourly",
    "derived-era5-single-levels-daily-statistics": "era5_daily_sum",
    "reanalysis-era5-single-levels": "era5_hourly_precipitation",
    "reanalysis-era5-land-timeseries": "era5_land_timeseries",
}


def accessed_dates(record_dirs: list[Path], wanted: set[str]) -> dict[str, str]:
    """Each product's access date for its citation, from the request records in record_dirs (the
    store, and ts/ for the point time series): one date, or "first to last" when its files were
    requested on several days."""
    days: dict[str, set] = {}
    for rec in (r for d in record_dirs for r in d.glob("*.request.json")):
        r = json.loads(rec.read_text())
        key = DATASET_SOURCE.get(r.get("dataset"))
        if key in wanted and r.get("requested_at_utc"):
            days.setdefault(key, set()).add(datetime.fromisoformat(r["requested_at_utc"]).date())
    out = {}
    for key, ds in days.items():
        first, last = min(ds), max(ds)
        out[key] = first.strftime("%d-%b-%Y") + (
            "" if first == last else " to " + last.strftime("%d-%b-%Y")
        )
    return out


def _stamp_versions(path: Path, shift_hours: int, out: dict, start: date, end: date) -> None:
    import h5py  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    with h5py.File(path) as h:
        if "expver" not in h:
            return
        # A one-stamp request comes back with scalar valid_time and expver.
        t = np.atleast_1d(h["valid_time"][()]).astype(np.int64) - 3600 * shift_hours
        for stamp, ver in zip(t, np.atleast_1d(h["expver"][()]), strict=True):
            day = date(1970, 1, 1) + timedelta(days=int(stamp // 86400))
            if start <= day <= end:
                out[day].add(ver.decode() if isinstance(ver, bytes) else str(ver))


def window_versions(store: Path, start: date, end: date) -> dict[date, set[str]]:
    """The store's data versions (expver: 0001 final, 0005 preliminary) behind each window day,
    read from the hourly files' own expver: ERA5-Land by UTC day of the stamp (zip deliveries read
    member by member), hourly rain by the day its stamp closes (d 01:00 to d+1 00:00)."""
    out = {start + timedelta(days=i): set() for i in range((end - start).days + 1)}
    for path in sorted(store.glob("hourly-era5land-*.hourly.nc")):
        if not zipfile.is_zipfile(path):
            _stamp_versions(path, 0, out, start, end)
    for path in sorted(store.glob("hourly-era5land-*.hourly.zip")):
        with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(path) as z:
            for name in sorted(z.namelist()):
                _stamp_versions(Path(z.extract(name, tmp)), 0, out, start, end)
    for path in sorted(store.glob("hourly-era5-precip-*.nc")):
        _stamp_versions(path, 1, out, start, end)
    return out


def version_sentence(versions: dict[date, set[str]]) -> str:
    """One sentence on which window days are final and which preliminary; a day with any
    preliminary hour counts as preliminary."""
    kinds = []
    for day in sorted(versions):
        v = versions[day]
        kinds.append((day, "none" if not v else "prelim" if v - {"0001"} else "final"))
    runs: list[list] = []
    for day, kind in kinds:
        if runs and runs[-1][0] == kind:
            runs[-1][2] = day
        else:
            runs.append([kind, day, day])
    span = {k: [f"{a} to {b}" if a != b else str(a) for kk, a, b in runs if kk == k]
            for k in ("final", "prelim", "none")}  # fmt: skip
    parts = []
    if span["final"]:
        parts.append(f"Window days {', '.join(span['final'])} are the store's final data "
                     "(expver 0001)")  # fmt: skip
    if span["prelim"]:
        lead = "" if parts else "Window days "
        parts.append(f"{lead}{', '.join(span['prelim'])} are {'its' if parts else 'the store\'s'} "
                     "preliminary data (expver 0005), which can be revised")  # fmt: skip
    if span["none"]:
        parts.append(f"{', '.join(span['none'])} has no recorded data version")
    return "; ".join(parts) + "."


def training_sources(model_json: dict) -> set[str]:
    """The Copernicus products the weather model's training read, as its model.json records them
    (pnw_t1_fit.copernicus_sources, written at fit time)."""
    if model_json.get("copernicus_sources"):
        return set(model_json["copernicus_sources"])
    raise SystemExit(
        "model.json does not say which Copernicus products training read (copernicus_sources); "
        "attribution cannot be written without guessing"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["calendar", "full"], required=True)
    ap.add_argument("--week", default="2026-W41")
    ap.add_argument("--store", type=Path, default=DATA / "cds")
    ap.add_argument("--ts", type=Path, default=DATA / "ts", help="the point time-series records")
    ap.add_argument("--models", type=Path, default=DATA / "models")
    ap.add_argument("--out", type=Path, default=DATA / "scoring" / "out")
    ap.add_argument("--repo-copy", action="store_true")
    ap.add_argument("--beats-calendar", choices=["true", "false", "null"], default="null")
    ap.add_argument("--t1-result", default="")
    ap.add_argument("--reviewed", choices=["true", "false"], default="false")
    a = ap.parse_args()
    year, wk = a.week.split("-W")
    week = IsoWeek(int(year), int(wk))
    model = a.models / f"primary_t1_1000m_{a.kind}"
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "pnw_pilot_score.py"),
        "--week",
        week.id,
        "--model",
        str(model),
        "--kind",
        a.kind,
        "--out",
        str(a.out),
        "--beats-calendar",
        a.beats_calendar,
        "--t1-result",
        a.t1_result,
        "--reviewed",
        a.reviewed,
    ]
    if a.kind == "calendar":
        cmd += ["--land-from-store", str(a.store)]
    else:
        npz = DATA / "scoring" / "cds-npz" / f"weather_{week.id}.npz"
        npz.parent.mkdir(parents=True, exist_ok=True)
        summary = build_window(a.store, npz, week)
        missing = {k: v for k, v in summary["days_missing_on_any_point_with_data"].items() if v}
        if missing:
            raise SystemExit(f"the store lacks window days: {missing}")
        scoring = set(copernicus_sources(npz))  # the builder's reading of the build summary
        read = scoring | training_sources(json.loads((model / "model.json").read_text()))
        accessed = accessed_dates([a.store, a.ts], read)
        start, end = lw.window_span(week)
        note = version_sentence(window_versions(a.store, start, end))
        cmd += [
            "--cds-npz",
            str(npz),
            "--bridge",
            BRIDGE,
            "--copernicus-sources",
            ",".join(sorted(read)),
            "--accessed",
            json.dumps(accessed),
            "--weather-source-note",
            note,
        ]
    done = subprocess.run(cmd, cwd=REPO)
    if done.returncode:
        return done.returncode
    week_dir = a.out / "pnw-pilot" / week.monday().isoformat()
    if a.repo_copy:
        big = [p for p in week_dir.rglob("*") if p.is_file() and p.stat().st_size > LIMIT]
        if big:
            raise SystemExit(f"over the repository's 1 MB limit, not copied: {big}")
        target = REPO / "samples" / "pnw-pilot" / week.monday().isoformat()
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(week_dir, target)
        print(f"copied to {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
