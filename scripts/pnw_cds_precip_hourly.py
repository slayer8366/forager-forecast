"""Rain by the hourly route: ERA5 single-levels hourly total_precipitation, summed per UTC day.

Run:  uv run --with cdsapi==0.7.7 python scripts/pnw_cds_precip_hourly.py --out <dir> STEP
      (STEP is pull, aggregate or check)

The owner's ruling (Forager RECORD -826): "Hourly, checked against 2019 (Recommended)". Rain years
not delivered by the daily-statistics route come from `reanalysis-era5-single-levels` hourly
`total_precipitation`, summed over the UTC day with the accumulation convention handled explicitly
(hourly_daily.daily_sums_previous_hour: day d = stamps d 01:00 to d+1 00:00).

pull: year-array requests (the form takes `year` and `month` as arrays), T1's box, newest chunk
first, two years per request (the size limit; see chunks()), 2019-2020 first for the check, then
2014-09 to 2014-12, then the single stamp 2025-01-01 00:00 that closes 2024-12-31. Each request
is stored with its time and account (D52); jobs the store already holds are adopted
(cds_jobs.fetch). Disk is checked first (3 GB stop line).

aggregate: reads every downloaded hourly file, merges stamps, writes
`hourly-era5-precip-YYYY.daily.h5` per year with `tp` in m (as the daily-statistics file),
valid_time in days since 2014-09-01.

check: compares the 2019 sums with the store's own daily-statistics file `era5-precip-2019.nc` at
every point and day. The tolerance is fixed here, before the comparison was first run:
|difference| <= 1e-5 m (0.01 mm), a tenth of Open-Meteo's display unit, allowing only float32
summation order, since both sides are the store's own hourly fields. Any value beyond it stops
for the owner (RECORD -826). The other convention (stamps 00:00 to 23:00) is shown beside it as a
diagnostic, never a pass condition.
"""

import argparse
import json
import shutil
import sys
import time
from datetime import UTC, date, datetime
from pathlib import Path

import cds_jobs
import h5py
import numpy as np

from forager_forecast.hourly_daily import daily_sums_previous_hour
from forager_forecast.t1_design import BOXES

BOX = next(b for b in BOXES if b.name == "pnw")
AREA = [BOX.north, BOX.west, BOX.south, BOX.east]
DATASET = "reanalysis-era5-single-levels"
DAY0 = date(2014, 9, 1)
TOL_M = 1e-5
MIN_FREE_BYTES = 3 * 1024**3
ACCOUNT = (
    "the CDS test account (D43): the ECMWF login recorded at "
    "docs/planning/evidence/cds-credentials-report.md:37; key read by cdsapi from ~/.cdsapirc, "
    "not recorded"
)
ALL_DAYS = [f"{d:02d}" for d in range(1, 32)]
ALL_MONTHS = [f"{m:02d}" for m in range(1, 13)]
ALL_HOURS = [f"{h:02d}:00" for h in range(24)]


def chunks():
    """Two years per request: the store's size limit is 121,000 fields and one year of hourly
    rain is 52,560 (client.estimate_costs, 2026-10-10; three years were refused, "cost limits
    exceeded"). Newest first, 2019-2020 first for the check."""
    base = {"product_type": ["reanalysis"], "variable": ["total_precipitation"], "area": AREA}
    tail = {"data_format": "netcdf", "download_format": "unarchived"}
    for first, last in ((2019, 2020), (2021, 2022), (2023, 2024), (2017, 2018), (2015, 2016)):
        yield (
            f"hourly-era5-precip-{first}-{last}",
            {
                **base,
                "year": [str(y) for y in range(first, last + 1)],
                "month": ALL_MONTHS,
                "day": ALL_DAYS,
                "time": ALL_HOURS,
                **tail,
            },
        )
    yield (
        "hourly-era5-precip-2014-09-12",
        {
            **base,
            "year": ["2014"],
            "month": ["09", "10", "11", "12"],
            "day": ALL_DAYS,
            "time": ALL_HOURS,
            **tail,
        },
    )
    yield (
        "hourly-era5-precip-2025-01-01T00",
        {
            **base,
            "year": ["2025"],
            "month": ["01"],
            "day": ["01"],
            "time": ["00:00"],
            **tail,
        },
    )
    # Rain 2025 and the stamp that closes 2025-12-31. 267e3ad's message said these were added;
    # that edit did not apply (its anchor text did not match the formatted code) and was not
    # checked. Added here on 2026-10-11; the derived 2025 job was dismissed at 20:20:10 UTC.
    yield (
        "hourly-era5-precip-2025",
        {
            **base,
            "year": ["2025"],
            "month": ALL_MONTHS,
            "day": ALL_DAYS,
            "time": ALL_HOURS,
            **tail,
        },
    )
    yield (
        "hourly-era5-precip-2026-01-01T00",
        {
            **base,
            "year": ["2026"],
            "month": ["01"],
            "day": ["01"],
            "time": ["00:00"],
            **tail,
        },
    )


def scoring_chunks():
    """The map's rain, 2026-07-01 to 2026-10-04, by the same checked route (RECORD -826; planner,
    2026-10-10, if d6ae24ed has not delivered). The 2026-10-05 00:00 stamp closes 2026-10-04."""
    base = {"product_type": ["reanalysis"], "variable": ["total_precipitation"], "area": AREA}
    tail = {"data_format": "netcdf", "download_format": "unarchived"}
    yield "hourly-era5-precip-2026-07-09", {
        **base, "year": ["2026"], "month": ["07", "08", "09"], "day": ALL_DAYS,
        "time": ALL_HOURS, **tail,
    }  # fmt: skip
    yield "hourly-era5-precip-2026-10-01-04", {
        **base, "year": ["2026"], "month": ["10"], "day": ["01", "02", "03", "04"],
        "time": ALL_HOURS, **tail,
    }  # fmt: skip
    yield "hourly-era5-precip-2026-10-05T00", {
        **base, "year": ["2026"], "month": ["10"], "day": ["05"], "time": ["00:00"], **tail,
    }  # fmt: skip


def log(msg: str) -> None:
    print(f"{datetime.now(UTC).isoformat(timespec='seconds')} {msg}", flush=True)


def pull(out: Path, scoring: bool = False) -> int:
    import cdsapi  # noqa: PLC0415

    client = cdsapi.Client(quiet=True, progress=False)
    for name, request in scoring_chunks() if scoring else chunks():
        nc, rec = out / f"{name}.nc", out / f"{name}.request.json"
        if nc.exists() and rec.exists():
            log(f"{name} skip (done)")
            continue
        if shutil.disk_usage(out).free < MIN_FREE_BYTES:
            log("STOP: under 3 GB free")
            return 2
        while True:
            requested_at = datetime.now(UTC).isoformat(timespec="seconds")
            t0 = time.monotonic()
            try:
                tmp = nc.with_suffix(".nc.part")
                adopted = cds_jobs.fetch(client, DATASET, request, str(tmp))
                tmp.rename(nc)
                break
            except Exception as err:  # noqa: BLE001  logged; cap waits, others stop
                if "temporarily limited" in str(err):
                    log(f"{name} queue limit; waiting 120 s")
                    time.sleep(120)
                    continue
                log(f"{name} FAILED: {err!r}")
                return 1
        seconds = round(time.monotonic() - t0, 1)
        rec.write_text(
            json.dumps(
                {
                    "dataset": DATASET,
                    "request": request,
                    "requested_at_utc": requested_at,
                    "seconds": seconds,
                    "bytes": nc.stat().st_size,
                    "adopted_job": adopted,
                    "account": ACCOUNT,
                    "client": "cdsapi==0.7.7 via uv run --with",
                },
                indent=2,
            )
            + "\n"
        )
        log(f"{name} ok {seconds} s {nc.stat().st_size} B")
    return 0


def _read(path: Path):
    with h5py.File(path) as h:
        tname = "valid_time" if "valid_time" in h else "time"
        units = h[tname].attrs["units"].decode()
        if not units.startswith("seconds since 1970-01-01"):
            raise SystemExit(f"{path.name}: unexpected time units {units!r}")
        return h[tname][:].astype(np.int64), h["latitude"][:], h["longitude"][:], h["tp"][:]


def aggregate(out: Path) -> dict:
    stamps, data, grid = [], [], None
    for path in sorted(out.glob("hourly-era5-precip-*.nc")):
        t, lat, lon, tp = _read(path)
        if grid is None:
            grid = (lat, lon)
        elif not (np.allclose(grid[0], lat) and np.allclose(grid[1], lon)):
            raise SystemExit(f"{path.name}: grid differs from the first file")
        stamps.append(t)
        data.append(tp.astype(np.float64))
    if grid is None:
        return {"files": 0}
    t = np.concatenate(stamps)
    v = np.concatenate(data, axis=0)
    order = np.argsort(t, kind="stable")
    t, v = t[order], v[order]
    if np.any(np.diff(t) == 0):
        keep = np.concatenate([[True], np.diff(t) != 0])
        t, v = t[keep], v[keep]
    days, daily, incomplete = daily_sums_previous_hour(t, v)
    written = {}
    years = sorted({d.year for d in days})
    for y in years:
        idx = [k for k, d in enumerate(days) if d.year == y and not np.isnan(daily[k]).all()]
        if not idx:
            continue
        path = out / f"hourly-era5-precip-{y}.daily.h5"
        with h5py.File(path, "w") as o:
            o["latitude"], o["longitude"] = grid
            vt = o.create_dataset("valid_time", data=np.array([(days[k] - DAY0).days for k in idx]))
            vt.attrs["units"] = np.bytes_(f"days since {DAY0.isoformat()}")
            o["tp"] = daily[idx].astype(np.float32)
            o.attrs["route"] = np.bytes_(
                "hourly reanalysis-era5-single-levels total_precipitation,"
                " stamps d 01:00 to d+1 00:00"
            )
        written[str(y)] = len(idx)
    return {"files": len(stamps), "days_written_by_year": written, "days_incomplete": incomplete}


def check(out: Path) -> int:
    lat, lon = None, None
    stamps, data = [], []
    for path in sorted(out.glob("hourly-era5-precip-*.nc")):
        a = _read(path)
        stamps.append(a[0])
        data.append(a[3].astype(np.float64))
        lat, lon = a[1], a[2]
    t = np.concatenate(stamps)
    v = np.concatenate(data, axis=0)
    order = np.argsort(t, kind="stable")
    t, v = t[order], v[order]
    days, daily, _ = daily_sums_previous_hour(t, v)
    # Diagnostic: the other convention, stamps 00:00 to 23:00 of the day.
    from forager_forecast.hourly_daily import utc_days  # noqa: PLC0415

    with h5py.File(out / "era5-precip-2019.nc") as h:
        ref = h["tp"][:].astype(np.float64)
        rlat, rlon = h["latitude"][:], h["longitude"][:]
        units = h["valid_time"].attrs["units"].decode()
        base = date.fromisoformat(units.split("since ")[1][:10])
        rdays = [date.fromordinal(base.toordinal() + int(x)) for x in h["valid_time"][:]]
    if not (np.allclose(rlat, lat) and np.allclose(rlon, lon)):
        raise SystemExit("the two 2019 files are on different grids")
    pos = {d: k for k, d in enumerate(days)}
    mine = np.stack([daily[pos[d]] for d in rdays])
    diff = np.abs(mine - ref)
    alt_days = utc_days(t)
    alt = np.stack([v[alt_days == np.datetime64(d)].sum(axis=0) for d in rdays])
    alt_diff = np.abs(alt - ref)
    result = {
        "compared_values": int(np.isfinite(diff).sum()),
        "days": len(rdays),
        "points": int(ref.shape[1] * ref.shape[2]),
        "tolerance_m": TOL_M,
        "max_abs_diff_m": float(np.nanmax(diff)),
        "over_tolerance": int(np.nansum(diff > TOL_M)),
        "nan_positions_equal": bool(np.array_equal(np.isnan(mine), np.isnan(ref))),
        "diagnostic_convention_00_23_max_abs_diff_m": float(np.nanmax(alt_diff)),
        "diagnostic_convention_00_23_over_tolerance": int(np.nansum(alt_diff > TOL_M)),
    }
    result["agree"] = result["over_tolerance"] == 0 and result["nan_positions_equal"]
    (out / "precip_hourly_vs_daily_2019.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["agree"] else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("step", choices=["pull", "aggregate", "check"])
    ap.add_argument("--scoring", action="store_true")
    a = ap.parse_args()
    if a.step == "pull":
        sys.exit(pull(a.out, a.scoring))
    if a.step == "aggregate":
        print(json.dumps(aggregate(a.out), indent=2))
        sys.exit(0)
    sys.exit(check(a.out))
