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


def months():
    yield OVERLAP
    for y in range(2014, 2019):
        for m in range(9 if y == 2014 else 1, 13):
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
    args = ap.parse_args()
    import cdsapi  # noqa: PLC0415

    client = cdsapi.Client(quiet=True, progress=False)
    todo = list(months())
    log(f"hourly route: {len(todo)} months, box {AREA}")
    for i, (y, m) in enumerate(todo, 1):
        name = f"hourly-era5land-{y}-{m:02d}"
        daily = args.out / f"{name}.daily.h5"
        rec = args.out / f"{name}.request.json"
        if daily.exists() and rec.exists():
            log(f"[{i}/{len(todo)}] {name} skip (done)")
            continue
        if (y, m) != OVERLAP and (args.out / f"era5land-{y}-{m:02d}.nc").exists():
            log(f"[{i}/{len(todo)}] {name} skip (daily route has it)")
            continue
        free = shutil.disk_usage(args.out).free
        if free < MIN_FREE_BYTES:
            log(f"STOP: {free / 1024**3:.2f} GB free, under 3 GB")
            return 2
        request = {
            "variable": list(VARIABLES),
            "year": str(y),
            "month": f"{m:02d}",
            "day": [f"{d:02d}" for d in range(1, 32)],
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
                client.retrieve(DATASET, request).download(str(hourly))
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
    log("hourly route finished pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
