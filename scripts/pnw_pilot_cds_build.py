"""Build the scoring week's store weather into pnw_weather's npz, with pnw_weather.build itself.

Run:  uv run python scripts/pnw_pilot_cds_build.py --week 2026-W41 --cds <dir> --out <npz>

pnw_weather.build fixes its day range in module constants (START 2014-09-01, END 2025-12-31,
N_DAYS) and drops any day outside them. Scoring needs the days of one window in 2026, so this
script sets those three constants to the window's first day, its last day and the count, then calls
build unchanged: every conversion (kelvin to °C, m to mm), grid check (D51) and file pattern is the
builder's own, so a fix there reaches scoring with no copy to update. The values are then checked
against their plausible ranges (pilot_output.check_ranges), so a unit error stops here.
"""

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import pnw_weather  # noqa: E402

from forager_forecast import live_weather as lw  # noqa: E402
from forager_forecast import pilot_output as po  # noqa: E402
from forager_forecast.cells import IsoWeek  # noqa: E402


def build_window(cds_dir: Path, out: Path, week: IsoWeek) -> dict:
    start, end = lw.window_span(week)
    pnw_weather.START = start
    pnw_weather.END = end
    pnw_weather.N_DAYS = (end - start).days + 1
    summary = pnw_weather.build(cds_dir, out)
    z = np.load(out)
    po.check_ranges(z)
    missing = {}
    for v in ("temperature", "soil_temperature", "soil_moisture", "precipitation"):
        vals = z[f"{v}_values"]
        land_rows = ~np.isnan(vals).all(axis=1)
        gaps = np.isnan(vals[land_rows]).any(axis=0)
        missing[v] = [str(start + timedelta(days=int(d))) for d in np.where(gaps)[0]]
    summary["window"] = [start.isoformat(), end.isoformat()]
    summary["days_missing_on_any_point_with_data"] = missing
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", required=True)
    ap.add_argument("--cds", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    year, wk = a.week.split("-W")
    summary = build_window(a.cds, a.out, IsoWeek(int(year), int(wk)))
    print(json.dumps(summary, indent=1))
    return 1 if any(summary["days_missing_on_any_point_with_data"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())
