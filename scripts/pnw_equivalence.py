"""D24's equivalence test and the hourly land-route check for the PNW pilot.

Run:  uv run python scripts/pnw_equivalence.py <records dir> <weather npz> <cds dir> <out dir>
          [--available]

Spec: docs/audits/2026-10-10-pnw-pilot-t1/equivalence_spec.md, restated per review B2 and Forager
RECORD -818, and its hourly section (review S7), both committed before any Open-Meteo body was read.

Sample: 12 cells from the eligible T1 PNW cell-weeks' cells, 3 start days each, seed 20260918.
For each 7-day span one Open-Meteo request covers 8 days (one more day so hour 24 exists), pinned
per D19, D21, D25 (open_meteo.archive_request_url, models=era5_seamless), with hourly
temperature_2m, soil_temperature_0_to_7cm, soil_moisture_0_to_7cm and precipitation added.

1. Daily (D24): the store's daily values against Open-Meteo's, within RECORD -818's bounds.
   Reported, not the pilot's gate (RECORD -819).
2. Rain convention (review B2 (c)): the store's daily rain against Open-Meteo's hourly sums over
   hours 00-23 and 01-24.
3. Hourly land route (review S7): the store's hourly ERA5-Land values (the kept hourly files)
   against Open-Meteo's hourly values, hour by hour, at offsets -1, 0 and +1 h, within Open-Meteo's
   quantisation (HOURLY_TOL). This stands as the land-route check (planner, 2026-10-10). It passes
   when offset 0 matches every compared hour and matches more hours than either other offset.

Open-Meteo bodies are cached in <out dir>/open-meteo/, so a rerun makes no request it already made.
--available compares only spans whose store data have all arrived, and labels the result partial.
"""

import argparse
import json
import sys
import time
import urllib.request
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from pnw_t1_fit import primary_units, read_records  # noqa: E402
from pnw_weather import land_has_value, load  # noqa: E402

from forager_forecast.cells import Cell, quarter_cell_for  # noqa: E402
from forager_forecast.coastal import land_point  # noqa: E402
from forager_forecast.open_meteo import archive_request_url  # noqa: E402

SEED = 20260918
FIRST, LAST_START = date(2015, 1, 1), date(2025, 12, 22)
SPAN_DAYS = 7
# Daily bounds, restated per review B2 and RECORD -818 (equivalence_spec.md, "Restated"): half
# Open-Meteo's storage step plus half its display unit; rain by the rounding of its 24 hours.
TOL = {
    "temperature": 0.075,
    "precipitation": 24 * 0.05 + 0.05,
    "soil_temperature": 0.075,
    "soil_moisture": 0.001,
}
# Hourly bounds (review S7; equivalence_spec.md, "Hourly land route"): an hourly value Open-Meteo
# stores at 1/20 °C (half-step 0.025) and displays to 0.1 °C (half-unit 0.05); soil moisture
# stored at 1/1000 and displayed to 0.001.
HOURLY_TOL = {"t2m": 0.075, "stl1": 0.075, "swvl1": 0.001}
OM_HOURLY = {
    "t2m": "temperature_2m",
    "stl1": "soil_temperature_0_to_7cm",
    "swvl1": "soil_moisture_0_to_7cm",
}
OFFSETS = (-1, 0, 1)
EPS = 1e-6


def land_route_pass(counts: dict) -> bool:
    """Review S7 and N12: for every variable, offset 0 matches every compared hour (at least one)
    and matches strictly more hours than any other offset."""
    for by_offset in counts.values():
        m0, n0 = by_offset[0]
        if not (n0 and m0 == n0 and all(by_offset[o][0] < m0 for o in by_offset if o != 0)):
            return False
    return True


def spans_complete(required: set, compared: set) -> bool:
    """Review S9: the gate needs every required span compared, and at least one required."""
    return bool(required) and required <= compared


def compare_point(cell: Cell, has_value) -> tuple[tuple[int, int] | None, str]:
    """Review S8: the ERA5-Land point a sample cell is compared at, the same one the fit reads
    (coastal.land_point, Forager RECORD -822): its own, a land neighbour, or none."""
    found = land_point((cell.lat_tenths, cell.lon_tenths), has_value)
    if found is None:
        return None, "none"
    return found[0], "neighbour" if found[1] else "own"


def sample(records_dir: Path):
    rows = primary_units(read_records(records_dir / "t1_1000m.csv"))
    cells = sorted({r["cell"] for r in rows}, key=lambda c: c.id)
    rng = np.random.default_rng(SEED)
    chosen = [cells[int(i)] for i in rng.choice(len(cells), size=12, replace=False)]
    span = (LAST_START - FIRST).days + 1
    return [(c, FIRST + timedelta(days=int(o))) for c in chosen for o in rng.integers(0, span, 3)]


def request_url(cell: Cell, start: date) -> str:
    hourly = "%2C".join([*OM_HOURLY.values(), "precipitation"])
    url = archive_request_url(cell, start, start + timedelta(days=SPAN_DAYS))
    old = "hourly=soil_temperature_0_to_7cm%2Csoil_moisture_0_to_7cm"
    if old not in url:
        raise SystemExit(f"unexpected request form: {url}")
    return url.replace(old, f"hourly={hourly}")


def split_span(body: dict) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], list[str]]:
    """Open-Meteo's 8-day body -> (the first 7 days' daily values, the full 8 x 24 hourly
    series, the hourly time stamps). Refuses any other shape (review S5)."""
    daily, hourly = body["daily"], body["hourly"]
    if len(daily["time"]) != SPAN_DAYS + 1 or len(hourly["time"]) != (SPAN_DAYS + 1) * 24:
        raise ValueError(
            f"expected {SPAN_DAYS + 1} days and {(SPAN_DAYS + 1) * 24} hours, got "
            f"{len(daily['time'])} and {len(hourly['time'])}"
        )
    hours = {k: np.array(hourly[k], float) for k in [*OM_HOURLY.values(), "precipitation"]}
    first = slice(0, SPAN_DAYS * 24)
    soil_t = hours["soil_temperature_0_to_7cm"][first].reshape(SPAN_DAYS, 24)
    soil_m = hours["soil_moisture_0_to_7cm"][first].reshape(SPAN_DAYS, 24)
    days = {
        "temperature": np.array(daily["temperature_2m_mean"][:SPAN_DAYS], float),
        "precipitation": np.array(daily["precipitation_sum"][:SPAN_DAYS], float),
        "soil_temperature": soil_t.mean(axis=1),
        "soil_moisture": soil_m.mean(axis=1),
    }
    return days, hours, hourly["time"]


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


class HourlyStore:
    """The kept hourly ERA5-Land files, by cell and epoch hour, in °C and m3 m-3."""

    def __init__(self, cds: Path):
        self.cds = cds
        self.cache: dict[str, tuple | None] = {}

    def month(self, ym: str):
        if ym not in self.cache:
            path = self.cds / f"hourly-era5land-{ym}.hourly.nc"
            if not path.exists():
                self.cache[ym] = None
            else:
                with h5py.File(path) as h:
                    t = h["valid_time"][:].astype(np.int64)
                    lat = np.rint(h["latitude"][:] * 10).astype(int)
                    lon = np.rint(h["longitude"][:] * 10).astype(int)
                    data = {}
                    for v in HOURLY_TOL:
                        a = h[v][:].astype(np.float64)
                        data[v] = a - 273.15 if v in ("t2m", "stl1") else a
                lat_i = {int(x): i for i, x in enumerate(lat)}
                lon_i = {int(x): j for j, x in enumerate(lon)}
                self.cache[ym] = (t, lat_i, lon_i, data)
        return self.cache[ym]

    def value(self, v: str, point: tuple[int, int], epoch: int) -> float | None:
        m = self.month(datetime.fromtimestamp(epoch, UTC).strftime("%Y-%m"))
        if m is None:
            return None
        t, lat, lon, data = m
        k = int(np.searchsorted(t, epoch))
        i, j = lat.get(point[0]), lon.get(point[1])
        if k >= len(t) or t[k] != epoch or i is None or j is None:
            return None
        x = data[v][k, i, j]
        return None if np.isnan(x) else float(x)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("records", type=Path)
    ap.add_argument("weather", type=Path)
    ap.add_argument("cds", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--available", action="store_true")
    ap.add_argument(
        "--require-years",
        default="",
        help="e.g. 2019-2025: the gate needs every non-sea sample span starting in these years",
    )
    args = ap.parse_args()
    grids = load(args.weather)
    has = land_has_value(grids)
    req_years = (
        set(range(int(args.require_years[:4]), int(args.require_years[-4:]) + 1))
        if args.require_years
        else set()
    )
    required, compared, kinds = set(), set(), {}
    rain_sum = {"store": 0.0, "open_meteo": 0.0}
    hourly_store = HourlyStore(args.cds)
    om_dir = args.out / "open-meteo"
    om_dir.mkdir(parents=True, exist_ok=True)
    rows, skipped, mismatches, convention, sea = [], [], [], [], []
    max_abs = {v: 0.0 for v in TOL}
    hourly_counts = {v: {o: [0, 0] for o in OFFSETS} for v in HOURLY_TOL}  # [matched, compared]
    hourly_missing = 0
    for cell, start in sample(args.records):
        q = quarter_cell_for(cell.center_latitude, cell.center_longitude)
        point, kind = compare_point(cell, has)
        kinds[cell.id] = kind
        if point is None:
            sea.append(f"{cell.id} {start}")  # no land point within one cell; counted apart
            continue
        if start.year in req_years:
            required.add((cell.id, start))
        pts = {
            "temperature": point,
            "soil_temperature": point,
            "soil_moisture": point,
            "precipitation": (q.lat_quarters, q.lon_quarters),
        }
        store = {}
        for v, p in pts.items():
            g = grids[v]
            i = g.index.get(p)
            d0 = (start - g.start).days
            store[v] = None if i is None else g.values[i, d0 : d0 + SPAN_DAYS]
        if any(
            s is None or np.isnan(grids[v].values[grids[v].index[pts[v]]]).all()
            for v, s in store.items()
        ):
            sea.append(f"{cell.id} {start}")  # review B3: a sea point, counted apart
            continue
        if not all(not np.isnan(s).any() for s in store.values()):
            if args.available:
                skipped.append(f"{cell.id} {start}")
                continue
            raise SystemExit(f"store values missing for {cell.id} from {start}: pull incomplete")
        body = fetch(request_url(cell, start), om_dir / f"{cell.id}_{start}.json")
        om, hours, stamps = split_span(body)
        compared.add((cell.id, start))
        rain_sum["store"] += float(np.sum(store["precipitation"]))
        rain_sum["open_meteo"] += float(np.sum(om["precipitation"]))
        for k in range(SPAN_DAYS):
            convention.append(
                {
                    "store": float(store["precipitation"][k]),
                    "h00_23": float(hours["precipitation"][24 * k : 24 * k + 24].sum()),
                    "h01_24": float(hours["precipitation"][24 * k + 1 : 24 * k + 25].sum()),
                }
            )
        for v in TOL:
            diff = np.abs(om[v] - store[v])
            max_abs[v] = max(max_abs[v], float(np.nanmax(diff)))
            for k in range(SPAN_DAYS):
                ok = bool(diff[k] <= TOL[v] + EPS)
                rows.append(
                    {
                        "cell": cell.id,
                        "land_point": list(point),
                        "land_point_kind": kind,
                        "om_cell": [body.get("latitude"), body.get("longitude")],
                        "day": str(start + timedelta(days=k)),
                        "variable": v,
                        "store": float(store[v][k]),
                        "open_meteo": float(om[v][k]),
                        "abs_diff": float(diff[k]),
                        "match": ok,
                    }
                )
                if not ok:
                    mismatches.append(rows[-1])
        epochs = [int(datetime.fromisoformat(s).replace(tzinfo=UTC).timestamp()) for s in stamps]
        for v, om_name in OM_HOURLY.items():
            for h, epoch in enumerate(epochs):
                om_value = hours[om_name][h]
                for o in OFFSETS:
                    sv = hourly_store.value(v, point, epoch + 3600 * o)
                    if sv is None or np.isnan(om_value):
                        if o == 0:
                            hourly_missing += 1
                        continue
                    hourly_counts[v][o][1] += 1
                    if abs(sv - om_value) <= HOURLY_TOL[v] + EPS:
                        hourly_counts[v][o][0] += 1
    st = np.array([c["store"] for c in convention])
    d00 = np.abs(st - np.array([c["h00_23"] for c in convention]))
    d01 = np.abs(st - np.array([c["h01_24"] for c in convention]))
    hourly_result = {}
    for v, counts in hourly_counts.items():
        best = max(OFFSETS, key=lambda o, c=counts: (c[o][0], o == 0))
        hourly_result[v] = {
            "matched_compared_by_offset_hours": {str(o): counts[o] for o in OFFSETS},
            "best_offset_hours": best,
        }
    land_pass = land_route_pass(hourly_counts)
    complete = spans_complete(required, compared) if req_years else None
    gate = land_pass and (complete is not False)
    result = {
        "written_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "partial": args.available,
        "daily": {
            "spans_compared": len(rows) // (SPAN_DAYS * len(TOL)),
            "spans_skipped_store_incomplete": skipped,
            "spans_skipped_sea_point": sea,
            "values_compared": len(rows),
            "mismatches": len(mismatches),
            "max_abs_diff": max_abs,
            "tolerance": TOL,
            "pass": not mismatches and bool(rows),
            "gate": "reported only; not the gate for the pilot fit (Forager RECORD -819)",
        },
        "rain_convention_test": {
            "days": len(convention),
            "mean_abs_diff_hours_00_23": float(d00.mean()) if len(d00) else None,
            "mean_abs_diff_hours_01_24": float(d01.mean()) if len(d01) else None,
            "days_closer_00_23": int((d00 < d01).sum()),
            "days_closer_01_24": int((d01 < d00).sum()),
            "days_tied": int((d00 == d01).sum()),
        },
        "hourly_land_route": {
            "tolerance": HOURLY_TOL,
            "hours_without_store_value_at_offset_0": hourly_missing,
            "by_variable": hourly_result,
            "pass": land_pass,
            "neighbour_cells_compared": sorted(c for c, k in kinds.items() if k == "neighbour"),
        },
        "rain_level": {
            "store_sum_mm": rain_sum["store"],
            "open_meteo_sum_mm": rain_sum["open_meteo"],
            "ratio_open_meteo_over_store": (
                rain_sum["open_meteo"] / rain_sum["store"] if rain_sum["store"] else None
            ),
        },
        "gate": {
            "required_years": sorted(req_years),
            "required_spans": len(required),
            "compared_required_spans": len(required & compared),
            "spans_complete": complete,
            "pass": gate,
        },
        "first_daily_mismatches": mismatches[:20],
    }
    name = "equivalence_partial" if args.available else "equivalence"
    (args.out / f"{name}.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.out / f"{name}_values.json").write_text(json.dumps(rows) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "first_daily_mismatches"}, indent=1))
    print(
        f"GATE {'PASS' if gate else 'FAIL'}: land route {land_pass}, required spans "
        f"{len(required & compared)}/{len(required)} compared"
    )
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
