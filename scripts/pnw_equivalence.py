"""D24's equivalence test for the PNW pilot, as fixed in
docs/audits/2026-10-10-pnw-pilot-t1/equivalence_spec.md before any weather was read.

Run:  uv run python scripts/pnw_equivalence.py <records dir> <weather npz> <out dir> [--available]

Draws the sample (12 cells from the eligible T1 PNW cell-weeks' cells, 3 start days each, seed
20260918), requests each 7-day span from Open-Meteo pinned per D19, D21, D25
(open_meteo.archive_request_url), and compares the four daily values with the store's. Open-Meteo
bodies are cached in <out dir>/open-meteo/, so a rerun makes no request it already made.

--available compares only the sample spans whose store days have all arrived, and labels the
result partial. The full test is the run without it. Exit 0 on pass, 1 on any mismatch.
"""

import argparse
import json
import sys
import time
import urllib.request
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from pnw_t1_fit import primary_units, read_records  # noqa: E402
from pnw_weather import load  # noqa: E402

from forager_forecast.cells import quarter_cell_for  # noqa: E402
from forager_forecast.open_meteo import archive_request_url  # noqa: E402

SEED = 20260918
FIRST, LAST_START = date(2015, 1, 1), date(2025, 12, 22)
TOL = {
    "temperature": 0.05,
    "precipitation": 0.05,
    "soil_temperature": 0.05,
    "soil_moisture": 0.0005,
}
EPS = 1e-6


def sample(records_dir: Path):
    rows = primary_units(read_records(records_dir / "t1_1000m.csv"))
    cells = sorted({r["cell"] for r in rows}, key=lambda c: c.id)
    rng = np.random.default_rng(SEED)
    chosen = [cells[int(i)] for i in rng.choice(len(cells), size=12, replace=False)]
    span = (LAST_START - FIRST).days + 1
    return [(c, FIRST + timedelta(days=int(o))) for c in chosen for o in rng.integers(0, span, 3)]


def fetch(url: str, cache: Path) -> dict:
    if cache.exists():
        return json.loads(cache.read_text())
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                body = resp.read()
            cache.write_bytes(body)
            time.sleep(1.0)
            return json.loads(body)
        except Exception as err:  # noqa: BLE001  logged, retried, then raised
            print(f"open-meteo attempt {attempt + 1} failed: {err!r}", flush=True)
            time.sleep(10 * (attempt + 1))
    raise SystemExit(f"Open-Meteo did not answer: {url}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("records", type=Path)
    ap.add_argument("weather", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--available", action="store_true")
    a = ap.parse_args()
    grids = load(a.weather)
    om_dir = a.out / "open-meteo"
    om_dir.mkdir(parents=True, exist_ok=True)
    rows, skipped, mismatches, convention, sea = [], [], [], [], []
    max_abs = {v: 0.0 for v in TOL}
    for cell, start in sample(a.records):
        end = start + timedelta(days=6)
        q = quarter_cell_for(cell.center_latitude, cell.center_longitude)
        pts = {
            "temperature": (cell.lat_tenths, cell.lon_tenths),
            "soil_temperature": (cell.lat_tenths, cell.lon_tenths),
            "soil_moisture": (cell.lat_tenths, cell.lon_tenths),
            "precipitation": (q.lat_quarters, q.lon_quarters),
        }
        store = {}
        for v, p in pts.items():
            g = grids[v]
            i = g.index.get(p)
            d0 = (start - g.start).days
            store[v] = None if i is None else g.values[i, d0 : d0 + 7]
        if any(
            s is None or np.isnan(grids[v].values[grids[v].index[pts[v]]]).all()
            for v, s in store.items()
        ):
            # Review B3: a sea point has no ERA5-Land value on any day; counted, never "incomplete".
            sea.append(f"{cell.id} {start}")
            continue
        complete = all(not np.isnan(s).any() for s in store.values())
        if not complete:
            if a.available:
                skipped.append(f"{cell.id} {start}")
                continue
            raise SystemExit(f"store values missing for {cell.id} {start}..{end}: pull incomplete")
        # One extra day so hour 24 (00:00 of the next day) exists for the convention test, and
        # hourly precipitation added; every D19/D25 pin is kept from archive_request_url.
        url = archive_request_url(cell, start, end + timedelta(days=1)).replace(
            "hourly=soil_temperature_0_to_7cm%2Csoil_moisture_0_to_7cm",
            "hourly=soil_temperature_0_to_7cm%2Csoil_moisture_0_to_7cm%2Cprecipitation",
        )
        if "precipitation&" not in url and not url.endswith("precipitation"):
            raise SystemExit(f"hourly precipitation not in the request: {url}")
        body = fetch(url, om_dir / f"{cell.id}_{start}.json")
        daily = body["daily"]
        hourly = body["hourly"]
        om = {
            "temperature": np.array(daily["temperature_2m_mean"], float),
            "precipitation": np.array(daily["precipitation_sum"], float),
            "soil_temperature": np.array(hourly["soil_temperature_0_to_7cm"], float)
            .reshape(7, 24)
            .mean(axis=1),
            "soil_moisture": np.array(hourly["soil_moisture_0_to_7cm"], float)
            .reshape(7, 24)
            .mean(axis=1),
        }
        for v in TOL:
            diff = np.abs(om[v] - store[v])
            max_abs[v] = max(max_abs[v], float(np.nanmax(diff)))
            for k in range(7):
                ok = diff[k] <= TOL[v] + EPS
                rows.append(
                    {
                        "cell": cell.id,
                        "om_cell": [body.get("latitude"), body.get("longitude")],
                        "day": str(start + timedelta(days=k)),
                        "variable": v,
                        "store": float(store[v][k]),
                        "open_meteo": float(om[v][k]),
                        "abs_diff": float(diff[k]),
                        "match": bool(ok),
                    }
                )
                if not ok:
                    mismatches.append(rows[-1])
    st = np.array([c["store"] for c in convention])
    a = np.abs(st - np.array([c["h00_23"] for c in convention]))
    b = np.abs(st - np.array([c["h01_24"] for c in convention]))
    convention_result = {
        "days": len(convention),
        "mean_abs_diff_hours_00_23": float(a.mean()) if len(a) else None,
        "mean_abs_diff_hours_01_24": float(b.mean()) if len(b) else None,
        "days_closer_00_23": int((a < b).sum()),
        "days_closer_01_24": int((b < a).sum()),
        "days_tied": int((a == b).sum()),
    }
    result = {
        "written_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "partial": a.available,
        "spans_compared": len(rows) // 28,
        "spans_skipped_store_incomplete": skipped,
        "spans_skipped_sea_point": sea,
        "values_compared": len(rows),
        "mismatches": len(mismatches),
        "max_abs_diff": max_abs,
        "tolerance": TOL,
        "pass": not mismatches and bool(rows),
        "gate": "reported only; not the gate for the pilot fit (Forager RECORD -819)",
        "rain_convention_test": convention_result,
        "first_mismatches": mismatches[:20],
    }
    name = "equivalence_partial" if a.available else "equivalence"
    (a.out / f"{name}.json").write_text(json.dumps(result, indent=2) + "\n")
    (a.out / f"{name}_values.json").write_text(json.dumps(rows) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "first_mismatches"}, indent=1))
    for m in mismatches[:10]:
        print(m)
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
