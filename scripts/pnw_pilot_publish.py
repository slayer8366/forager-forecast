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
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pnw_pilot_cds_build import build_window  # noqa: E402

from forager_forecast.cells import IsoWeek  # noqa: E402

DATA = Path.home() / "Zynergy" / "forecast-data-pnw-pilot"
REPO = Path(__file__).resolve().parents[1]
LIMIT = 1024 * 1024
BRIDGE = (
    "None. The week is scored from the Copernicus store's daily statistics, the products "
    "training used (owner, Forager RECORD -819). Open-Meteo's archive was fetched for the same "
    "days as a cross-check only and is not used to score: its rain runs 4 to 8 percent below "
    "the store's (scoring branch feature check, 2019-10-07)."
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["calendar", "full"], required=True)
    ap.add_argument("--week", default="2026-W41")
    ap.add_argument("--store", type=Path, default=DATA / "cds")
    ap.add_argument("--models", type=Path, default=DATA / "models")
    ap.add_argument("--out", type=Path, default=DATA / "scoring" / "out")
    ap.add_argument("--repo-copy", action="store_true")
    ap.add_argument("--beats-calendar", choices=["true", "false", "null"], default="null")
    ap.add_argument("--t1-result", default="")
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
        cmd += ["--cds-npz", str(npz), "--bridge", BRIDGE]
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
