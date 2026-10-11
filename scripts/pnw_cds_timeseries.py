"""Third ERA5-Land route: the store's point time-series dataset, one request per land point.

Run:  uv run --with cdsapi==0.7.7 python scripts/pnw_cds_timeseries.py --out <dir> --workers N

Why (measured 2026-10-11 00:20 to 00:40 UTC): the store runs this account's gridded ERA5-Land
jobs one at a time after 20 to 100 min of queue each (store job list), about 2 to 3 months an
hour. `reanalysis-era5-land-timeseries` answered a single point for 2014-09-01 to 2025-12-31,
three variables, in 29 s, and its hourly values equal the gridded hourly files at 47.0, -123.0
on all 50,472 compared hours to within 0.00025 K and 0 m3 m-3 (float32 packing). It is the same
ERA5-Land product (D54: "the ERA5-Land products"), served from another store.

Points: every ERA5-Land point a T1 PNW unit reads, its own cell's point or, for a cell with no
land value, its nearest land neighbour (coastal.land_point, Forager RECORD -822), plus the
equivalence sample's points. The land mask is read from a delivered gridded hourly file.

Per point: request `location` and `date` 2014-09-01/2025-12-31; the reply is a zip of three
NetCDF files. Daily means of the 24 UTC hours (hourly_daily.daily_means, D52) are written to
`ts/pt_<lat>_<lon>.daily.npz` with the request record. The zip is kept only for the equivalence
sample's points (for the hourly land-route check). Jobs the store already holds are adopted.
Disk is checked before each request (3 GB stop line).
"""

import argparse
import io
import json
import shutil
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import cds_jobs
import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from pnw_equivalence import compare_point, sample  # noqa: E402
from pnw_t1_fit import primary_units, read_records  # noqa: E402

from forager_forecast.coastal import land_point  # noqa: E402
from forager_forecast.hourly_daily import daily_means  # noqa: E402

DATASET = "reanalysis-era5-land-timeseries"
VARIABLES = {
    "2m_temperature": "t2m",
    "soil_temperature_level_1": "stl1",
    "volumetric_soil_water_level_1": "swvl1",
}
DATE = "2014-09-01/2025-12-31"
MIN_FREE_BYTES = 3 * 1024**3
ACCOUNT = (
    "the CDS test account (D43): the ECMWF login recorded at "
    "docs/planning/evidence/cds-credentials-report.md:37; key read by cdsapi from ~/.cdsapirc, "
    "not recorded"
)


def log(msg: str) -> None:
    print(f"{datetime.now(UTC).isoformat(timespec='seconds')} {msg}", flush=True)


def land_mask(hourly_nc: Path) -> set[tuple[int, int]]:
    with h5py.File(hourly_nc) as h:
        lat = np.rint(h["latitude"][:] * 10).astype(int)
        lon = np.rint(h["longitude"][:] * 10).astype(int)
        ok = np.ones((len(lat), len(lon)), bool)
        for v in VARIABLES.values():
            ok &= ~np.isnan(h[v][:]).all(axis=0)
    return {
        (int(lat[i]), int(lon[j])) for i in range(len(lat)) for j in range(len(lon)) if ok[i, j]
    }


def points_needed(records: Path, has: set) -> tuple[list[tuple[int, int]], set]:
    rows = primary_units(read_records(records / "t1_1000m.csv"))
    pts = set()
    for cell in {r["cell"] for r in rows}:
        found = land_point((cell.lat_tenths, cell.lon_tenths), has)
        if found:
            pts.add(found[0])
    keep = set()
    for cell, _start in sample(records):
        p, _kind = compare_point(cell, has)
        if p:
            keep.add(p)
            pts.add(p)
    return sorted(pts), keep


def to_daily(zip_bytes: bytes) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    out, days_ref = {}, None
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for name in z.namelist():
            with h5py.File(io.BytesIO(z.read(name))) as h:
                var = next(k for k in h if k in VARIABLES.values())
                units = h["valid_time"].attrs["units"].decode()
                if units != "hours since 1970-01-01":
                    raise ValueError(f"unexpected time units {units!r}")
                seconds = h["valid_time"][:].astype(np.int64) * 3600
                days, daily, incomplete = daily_means(seconds, h[var][:].astype(np.float64))
                if incomplete:
                    raise ValueError(f"{incomplete} incomplete days in {var}")
                days_arr = np.array([d.toordinal() for d in days])
                if days_ref is not None and not np.array_equal(days_ref, days_arr):
                    raise ValueError("variables cover different days")
                days_ref = days_arr
                out[var] = daily
    if set(out) != set(VARIABLES.values()):
        raise ValueError(f"variables in reply: {sorted(out)}")
    return days_ref, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--records", type=Path, required=True)
    ap.add_argument("--mask-from", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0, help="first N points only (a probe)")
    args = ap.parse_args()
    import cdsapi  # noqa: PLC0415

    ts = args.out / "ts"
    ts.mkdir(parents=True, exist_ok=True)
    has = land_mask(args.mask_from)
    pts, keep = points_needed(args.records, has)
    if args.limit:
        pts = pts[: args.limit]
    log(f"timeseries route: {len(pts)} points ({len(keep)} kept hourly), {args.workers} in flight")
    local = threading.local()

    def one(item):
        i, (la, lo) = item
        name = f"pt_{la}_{lo}"
        daily_path, rec = ts / f"{name}.daily.npz", ts / f"{name}.request.json"
        if daily_path.exists() and rec.exists():
            return 0
        if shutil.disk_usage(args.out).free < MIN_FREE_BYTES:
            log("STOP: under 3 GB free")
            return 2
        if not hasattr(local, "client"):
            local.client = cdsapi.Client(quiet=True, progress=False)
        request = {
            "variable": list(VARIABLES),
            "location": {"longitude": lo / 10, "latitude": la / 10},
            "date": [DATE],
            "data_format": "netcdf",
        }
        for attempt in range(1, 4):
            requested_at = datetime.now(UTC).isoformat(timespec="seconds")
            t0 = time.monotonic()
            tmp = ts / f"{name}.zip.part"
            try:
                adopted = cds_jobs.fetch(local.client, DATASET, request, str(tmp))
                raw = tmp.read_bytes()
                days, daily = to_daily(raw)
                np.savez_compressed(daily_path, ordinal=days, **daily)
                if (la, lo) in keep:
                    tmp.rename(ts / f"{name}.zip")
                else:
                    tmp.unlink()
                rec.write_text(
                    json.dumps(
                        {
                            "dataset": DATASET,
                            "request": request,
                            "requested_at_utc": requested_at,
                            "seconds": round(time.monotonic() - t0, 1),
                            "bytes": len(raw),
                            "adopted_job": adopted,
                            "days": len(days),
                            "account": ACCOUNT,
                            "client": "cdsapi==0.7.7 via uv run --with",
                        },
                        indent=2,
                    )
                    + "\n"
                )
                if i % 25 == 0:
                    log(f"[{i}/{len(pts)}] {name} ok {round(time.monotonic() - t0, 1)} s")
                return 0
            except Exception as err:  # noqa: BLE001  logged; cap waits; licence stops
                if "temporarily limited" in str(err):
                    time.sleep(60)
                    continue
                log(f"[{i}/{len(pts)}] {name} attempt {attempt} FAILED: {err!r}"[:400])
                time.sleep(20 * attempt)
        log(f"[{i}/{len(pts)}] {name} gave up after 3 attempts")
        return 1

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        codes = list(pool.map(one, enumerate(pts, 1)))
    done = sum(1 for p in pts if (ts / f"pt_{p[0]}_{p[1]}.daily.npz").exists())
    log(f"timeseries route finished pass: {done}/{len(pts)} points done, {codes.count(1)} gave up")
    return 0 if done == len(pts) else 1


if __name__ == "__main__":
    sys.exit(main())
