"""Pull PNW weather from the Climate Data Store (D24, D52, D54; Forager RECORD -811, -812).

Run:  uv run --with cdsapi==0.7.7 python scripts/pnw_cds_pull.py --out <dir>

- Area: T1's PNW box first (t1_design.BOXES "pnw", 42.0 to 49.5 N, 125.0 to 121.0 W), then the
  rest of the union 40.0 to 49.5 N, 125.0 to 111.0 W (RECORD -812). Every edge is a multiple of
  0.1 and 0.25, so the delivered points are the global grid's (D51, grid positions part 2
  report). The East box and the rest of the continent are not pulled (RECORD -811).
- Days: 2014-09 to 2025-12. T1's earliest scored Monday is 2014-12-29 and the longest window is 90
  days, so features need weather from 2014-09-30 onward. Whole months are pulled.
- ERA5-Land daily statistics (`derived-era5-land-daily-statistics`): daily_mean of 2m_temperature,
  soil_temperature_level_1 and volumetric_soil_water_layer_1 (the 0 to 7 cm layer). One request
  per month, because that form takes `month` as one string (grid positions report, CDS schema).
- ERA5 single-levels daily statistics: daily_sum of total_precipitation, product_type reanalysis
  (D54). One request per year, all months.
- time_zone utc+00:00 and frequency 1_hourly in every request (D52, as the grid-position pulls).
- Order: newest month first, 2025-12 back to 2014-09, each year's precipitation request before its
  months (planner, 2026-10-10). The hourly route walks forward from 2014-09 and the two meet; each
  skips months the other has delivered. The owner allowed training on years as they arrive
  ("Train as it downloads if you need to", relayed by the planner on 2026-10-10).
- Resumable: a unit whose NetCDF and `.request.json` both exist is skipped. Each request is
  stored with its UTC request time and the account (D52) after its file has arrived (review N1);
  a failed attempt leaves only its log line. For an adopted job, requested_at_utc is the time it
  was adopted, not the time it was first submitted (review N9); `adopted_job` names the job.
- Stops before any request if the output disk has less than 3 GB free.
- Retries a failed unit three times with backoff. A refusal that names a licence or terms stops
  the whole run at once, with the message, since that needs the owner.
"""

import argparse
import json
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import cds_jobs

from forager_forecast.t1_design import BOXES

BOX = next(b for b in BOXES if b.name == "pnw")
AREA = [BOX.north, BOX.west, BOX.south, BOX.east]
# The rest of the union box 40.0 to 49.5 N, 125.0 to 111.0 W (owner, Forager RECORD -812:
# "Bigger box (Recommended)"), pulled after T1's box so T1 never waits on it. Two rectangles; they
# share the 121.0 W column and the 42.0 N row with T1's box, which is harmless duplication.
REST_AREAS = {
    "east": [49.5, -121.0, 40.0, -111.0],
    "south": [42.0, -125.0, 40.0, -121.0],
}
# Newest first (planner, 2026-10-10): this route walks back from 2025 while the hourly route
# (scripts/pnw_cds_hourly_pull.py) walks forward from 2014-09; each skips months the other has.
YEAR_ORDER = [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014]
LAND_VARIABLES = ["2m_temperature", "soil_temperature_level_1", "volumetric_soil_water_layer_1"]
MIN_FREE_BYTES = 3 * 1024**3
ACCOUNT = (
    "the CDS test account (D43): the ECMWF login recorded at "
    "docs/planning/evidence/cds-credentials-report.md:37; key read by cdsapi from ~/.cdsapirc, "
    "not recorded"
)
DAYS = [f"{d:02d}" for d in range(1, 32)]


def units():
    yield from _units_for("", AREA)
    for prefix, area in REST_AREAS.items():
        yield from _units_for(f"{prefix}-", area)


def _units_for(prefix: str, area: list[float]):
    for year in YEAR_ORDER:
        months = range(9, 13) if year == 2014 else range(1, 13)
        yield (
            f"{prefix}era5-precip-{year}",
            "derived-era5-single-levels-daily-statistics",
            {
                "product_type": "reanalysis",
                "variable": ["total_precipitation"],
                "year": str(year),
                "month": [f"{m:02d}" for m in months],
                "day": DAYS,
                "daily_statistic": "daily_sum",
                "time_zone": "utc+00:00",
                "frequency": "1_hourly",
                "area": area,
            },
        )
        for m in reversed(months):
            yield (
                f"{prefix}era5land-{year}-{m:02d}",
                "derived-era5-land-daily-statistics",
                {
                    "variable": LAND_VARIABLES,
                    "year": str(year),
                    "month": f"{m:02d}",
                    "day": DAYS,
                    "daily_statistic": "daily_mean",
                    "time_zone": "utc+00:00",
                    "frequency": "1_hourly",
                    "area": area,
                },
            )


def log(msg: str) -> None:
    print(f"{datetime.now(UTC).isoformat(timespec='seconds')} {msg}", flush=True)


def is_licence_refusal(err: Exception) -> bool:
    text = str(err).lower()
    return any(w in text for w in ("licence", "license", "terms", "required licences"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--only", default="", help="pull this one unit name only (overlap month)")
    ap.add_argument(
        "--precip-only",
        action="store_true",
        help="T1-box precipitation only; land months go by the hourly route (2026-10-10, measured)",
    )
    ap.add_argument(
        "--per-dataset",
        type=int,
        default=1,
        help="requests in flight per dataset; the store rejects extra queued ones (observed)",
    )
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    import cdsapi  # noqa: PLC0415  (only this script needs it; run with --with cdsapi==0.7.7)

    todo = [u for u in units() if not args.only or u[0] == args.only]
    if args.precip_only:
        todo = [u for u in todo if u[0].startswith("era5-precip-")]
    log(
        f"{len(todo)} units, T1 box {AREA} then {REST_AREAS}, out {args.out},"
        f" {args.workers} in flight"
    )
    stop = threading.Event()
    slots = {
        d: threading.Semaphore(args.per_dataset)
        for d in (
            "derived-era5-land-daily-statistics",
            "derived-era5-single-levels-daily-statistics",
        )
    }
    local = threading.local()

    def one(i: int, name: str, dataset: str, request: dict) -> int:
        nc = args.out / f"{name}.nc"
        rec = args.out / f"{name}.request.json"
        if stop.is_set():
            return 0
        if nc.exists() and nc.stat().st_size > 0 and rec.exists():
            log(f"[{i}/{len(todo)}] {name} skip (done)")
            return 0
        if name.startswith("era5land-") and (args.out / f"hourly-{name}.daily.h5").exists():
            log(f"[{i}/{len(todo)}] {name} skip (hourly route has it)")
            return 0
        free = shutil.disk_usage(args.out).free
        if free < MIN_FREE_BYTES:
            log(f"STOP: {free / 1024**3:.2f} GB free, under 3 GB")
            stop.set()
            return 2
        if not hasattr(local, "client"):
            local.client = cdsapi.Client(quiet=True, progress=False)
        attempt = 0
        while attempt < 3 and not stop.is_set():
            attempt += 1
            requested_at = datetime.now(UTC).isoformat(timespec="seconds")
            t0 = time.monotonic()
            try:
                tmp = nc.with_suffix(".nc.part")
                with slots[dataset]:
                    requested_at = datetime.now(UTC).isoformat(timespec="seconds")
                    t0 = time.monotonic()
                    adopted = cds_jobs.fetch(local.client, dataset, request, str(tmp))
                tmp.rename(nc)
                seconds = round(time.monotonic() - t0, 1)
                rec.write_text(
                    json.dumps(
                        {
                            "dataset": dataset,
                            "request": request,
                            "requested_at_utc": requested_at,
                            "seconds": seconds,
                            "bytes": nc.stat().st_size,
                            "account": ACCOUNT,
                            "client": "cdsapi==0.7.7 via uv run --with",
                            "adopted_job": adopted,
                            "in_flight": args.workers,
                        },
                        indent=2,
                    )
                    + "\n"
                )
                log(f"[{i}/{len(todo)}] {name} ok {seconds} s {nc.stat().st_size} B")
                return 0
            except Exception as err:  # noqa: BLE001  every failure is logged and counted
                if "temporarily limited" in str(err):
                    # The store's per-dataset queue limit, not a fault of this request.
                    log(f"[{i}/{len(todo)}] {name} queue limit; waiting 120 s (not an attempt)")
                    attempt -= 1
                    time.sleep(120)
                    continue
                log(f"[{i}/{len(todo)}] {name} attempt {attempt} FAILED: {err!r}")
                if is_licence_refusal(err):
                    log("STOP: the store refused for a licence or terms reason; the owner must act")
                    stop.set()
                    return 3
                time.sleep(30 * attempt)
        log(f"[{i}/{len(todo)}] {name} gave up after 3 attempts; continuing, rerun to resume")
        return 1

    # Units are submitted in order, so T1's box (and within it 2019 to 2025) goes out first.
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        codes = list(pool.map(lambda t: one(t[0], *t[1]), enumerate(todo, 1)))
    log(f"finished pass: {codes.count(0)} ok or skipped, {codes.count(1)} gave up")
    return max(codes) if any(c in (2, 3) for c in codes) else 0


if __name__ == "__main__":
    sys.exit(main())
