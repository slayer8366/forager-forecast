"""Second route for ERA5-Land temperature and soil: the hourly dataset, aggregated to daily.

Run:  uv run --with cdsapi==0.7.7 python scripts/pnw_cds_hourly_pull.py --out <cds dir>

The planner's builder choice of 2026-10-10: run the hourly `reanalysis-era5-land` dataset in
parallel with the daily-statistics pull (scripts/pnw_cds_pull.py), since the store caps queued
requests per dataset and each queue is a separate cap. D54 reads "daily temperature and soil from
the ERA5-Land products", which covers this route.

- T1's PNW box only. Overlap month 2019-01 first, which the daily-statistics route also pulls, for
  the agreement check. Then the oldest months forward: 2014-09 to 2018-12, the months the daily
  route reaches last. The form takes `month` as one string, so each request is one month.
- Variables: 2m_temperature, soil_temperature_level_1, volumetric_soil_water_layer_1. All 24
  hours. NetCDF, unarchived.
- Each month is aggregated at once (hourly_daily.daily_means: the mean of the 24 UTC hours, D52)
  into `hourly-era5land-YYYY-MM.daily.h5`, with the daily-statistics file's variable names and
  units (K, m3 m-3) and valid_time in days since 2014-09-01. The hourly file is then deleted to
  save disk, and its sha256 and size are kept in the request record.
- A month the daily route already delivered is skipped (the meeting rule), except the overlap.
- Disk is checked before each request; below 3 GB free the run stops.
"""

import argparse
import hashlib
import json
import shutil
import sys
import time
from datetime import UTC, date, datetime
from pathlib import Path

import cds_jobs
import h5py
import numpy as np

from forager_forecast.hourly_daily import daily_means
from forager_forecast.t1_design import BOXES

BOX = next(b for b in BOXES if b.name == "pnw")
AREA = [BOX.north, BOX.west, BOX.south, BOX.east]
VARIABLES = {
    "2m_temperature": "t2m",
    "soil_temperature_level_1": "stl1",
    "volumetric_soil_water_layer_1": "swvl1",
}
DATASET = "reanalysis-era5-land"
MIN_FREE_BYTES = 3 * 1024**3
DAY0 = date(2014, 9, 1)
ACCOUNT = (
    "the CDS test account (D43): the ECMWF login recorded at "
    "docs/planning/evidence/cds-credentials-report.md:37; key read by cdsapi from ~/.cdsapirc, "
    "not recorded"
)
OVERLAP = (2019, 1)
# The prototype map's recent weather (Forager RECORD -814, planner 2026-10-10): 2026-07-01 to
# 2026-10-04. October stops at the 4th, the last day the planner named.
SCORING_MONTHS = [(2026, 7), (2026, 8), (2026, 9), (2026, 10)]
LAST_DAY = {(2026, 10): 4}


def months():
    """Overlap month first, then every T1 month newest first (2025-12 back to 2014-09).

    Since 2026-10-10 18:51 UTC this route carries all of T1's land months: derived
    daily-statistics jobs sat queued over 20 minutes without starting, while hourly jobs started
    within 90 s."""
    yield OVERLAP
    for y in range(2025, 2013, -1):
        for m in range(12, (8 if y == 2014 else 0), -1):
            if (y, m) != OVERLAP:
                yield (y, m)


def log(msg: str) -> None:
    print(f"{datetime.now(UTC).isoformat(timespec='seconds')} {msg}", flush=True)


def aggregate(hourly: Path, out: Path) -> dict:
    with h5py.File(hourly) as h:
        tname = "valid_time" if "valid_time" in h else "time"
        units = h[tname].attrs["units"].decode()
        if not units.startswith("seconds since 1970-01-01"):
            raise SystemExit(f"unexpected hourly time units {units!r}")
        t = h[tname][:].astype(np.int64)
        lat, lon = h["latitude"][:], h["longitude"][:]
        result = {}
        incomplete = {}
        for var in VARIABLES.values():
            days, daily, inc = daily_means(t, h[var][:].astype(np.float64))
            result[var] = daily
            incomplete[var] = inc
    with h5py.File(out, "w") as o:
        o["latitude"] = lat
        o["longitude"] = lon
        vt = o.create_dataset("valid_time", data=np.array([(d - DAY0).days for d in days]))
        vt.attrs["units"] = np.bytes_(f"days since {DAY0.isoformat()}")
        for var, arr in result.items():
            o[var] = arr.astype(np.float32)
        o.attrs["route"] = np.bytes_("hourly reanalysis-era5-land, mean of 24 UTC hours")
    return {"days": len(days), "incomplete_days": incomplete}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument(
        "--scoring",
        action="store_true",
        help="the map's months 2026-07 to 2026-10-04 instead of T1's (planner, 2026-10-10)",
    )
    args = ap.parse_args()
    import threading  # noqa: PLC0415
    from concurrent.futures import ThreadPoolExecutor  # noqa: PLC0415

    import cdsapi  # noqa: PLC0415

    local = threading.local()
    todo = SCORING_MONTHS if args.scoring else list(months())
    log(f"hourly route: {len(todo)} months, box {AREA}, {args.workers} in flight")

    def run(item):
        i, (y, m) = item
        if not hasattr(local, "client"):
            local.client = cdsapi.Client(quiet=True, progress=False)
        return one(local.client, i, y, m)

    def one(client, i, y, m):
        name = f"hourly-era5land-{y}-{m:02d}"
        daily = args.out / f"{name}.daily.h5"
        rec = args.out / f"{name}.request.json"
        if daily.exists() and rec.exists():
            log(f"[{i}/{len(todo)}] {name} skip (done)")
            return 0
        if (y, m) != OVERLAP and (args.out / f"era5land-{y}-{m:02d}.nc").exists():
            log(f"[{i}/{len(todo)}] {name} skip (daily route has it)")
            return 0
        free = shutil.disk_usage(args.out).free
        if free < MIN_FREE_BYTES:
            log(f"STOP: {free / 1024**3:.2f} GB free, under 3 GB")
            return 2
        request = {
            "variable": list(VARIABLES),
            "year": str(y),
            "month": f"{m:02d}",
            "day": [f"{d:02d}" for d in range(1, LAST_DAY.get((y, m), 31) + 1)],
            "time": [f"{h:02d}:00" for h in range(24)],
            "area": AREA,
            "data_format": "netcdf",
            "download_format": "unarchived",
        }
        attempt = 0
        while attempt < 3:
            attempt += 1
            requested_at = datetime.now(UTC).isoformat(timespec="seconds")
            t0 = time.monotonic()
            hourly = args.out / f"{name}.hourly.nc"
            try:
                adopted = cds_jobs.fetch(client, DATASET, request, str(hourly))
                seconds = round(time.monotonic() - t0, 1)
                sha = hashlib.sha256(hourly.read_bytes()).hexdigest()
                size = hourly.stat().st_size
                agg = aggregate(hourly, daily)
                if (y, m) != OVERLAP:
                    hourly.unlink()
                rec.write_text(
                    json.dumps(
                        {
                            "dataset": DATASET,
                            "request": request,
                            "requested_at_utc": requested_at,
                            "seconds": seconds,
                            "hourly_bytes": size,
                            "hourly_sha256": sha,
                            "hourly_file_kept": (y, m) == OVERLAP,
                            "aggregated_to": daily.name,
                            "aggregation": agg,
                            "account": ACCOUNT,
                            "client": "cdsapi==0.7.7 via uv run --with",
                            "adopted_job": adopted,
                        },
                        indent=2,
                    )
                    + "\n"
                )
                log(f"[{i}/{len(todo)}] {name} ok {seconds} s {size} B, {agg}")
                break
            except Exception as err:  # noqa: BLE001  logged; licence refusals stop the run
                if "temporarily limited" in str(err):
                    log(f"[{i}/{len(todo)}] {name} queue limit; waiting 120 s (not an attempt)")
                    attempt -= 1
                    time.sleep(120)
                    continue
                log(f"[{i}/{len(todo)}] {name} attempt {attempt} FAILED: {err!r}")
                if any(w in str(err).lower() for w in ("licence", "license", "terms")):
                    log("STOP: licence or terms refusal; the owner must act")
                    return 3
                time.sleep(30 * attempt)
        else:
            log(f"[{i}/{len(todo)}] {name} gave up after 3 attempts")
            return 1
        return 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        codes = list(pool.map(run, enumerate(todo, 1)))
    log(f"hourly route finished pass: {codes.count(0)} ok or skipped, {codes.count(1)} gave up")
    return max(codes) if any(c in (2, 3) for c in codes) else 0


if __name__ == "__main__":
    sys.exit(main())
