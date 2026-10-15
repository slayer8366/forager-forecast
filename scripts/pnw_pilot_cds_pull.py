"""Pull the scoring week's weather from the Climate Data Store, the same products and request
shape training used (owner, Forager RECORD -819: "Copernicus for both (Recommended)").

Run:  uv run --with cdsapi==0.7.7 python scripts/pnw_pilot_cds_pull.py --week 2026-W41 --out <dir>

The requests are scripts/pnw_cds_pull.py's for T1's box (its AREA, LAND_VARIABLES, DAYS, the two
dataset names, daily_mean / daily_sum, time_zone utc+00:00, frequency 1_hourly), for the months the
week's windows read (live_weather.window_span): one ERA5-Land daily-statistics request per month and
one ERA5 daily-sum request for the year's months. Days after the window's last day are asked for
too, as whole months are in training; the builder (pnw_weather.build) keeps only what is delivered,
and the scoring script refuses any window day that is missing.

One request in flight at a time. The store's per-dataset queue cap ("temporarily limited") is
waited out and retried, as the builder's pull does; a licence refusal stops the run.
"""

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pnw_cds_pull import ACCOUNT, AREA, DAYS, LAND_VARIABLES, is_licence_refusal  # noqa: E402

from forager_forecast import live_weather as lw  # noqa: E402
from forager_forecast.cells import IsoWeek  # noqa: E402


def log(msg: str) -> None:
    print(f"{datetime.now(UTC).isoformat(timespec='seconds')} {msg}", flush=True)


def units(week: IsoWeek):
    start, end = lw.window_span(week)
    if start.year != end.year:
        raise SystemExit("a window spanning two years needs one precipitation request per year")
    months = list(range(start.month, end.month + 1))
    yield (
        f"era5-precip-{start.year}",
        "derived-era5-single-levels-daily-statistics",
        {
            "product_type": "reanalysis",
            "variable": ["total_precipitation"],
            "year": str(start.year),
            "month": [f"{m:02d}" for m in months],
            "day": DAYS,
            "daily_statistic": "daily_sum",
            "time_zone": "utc+00:00",
            "frequency": "1_hourly",
            "area": AREA,
        },
    )
    for m in reversed(months):
        yield (
            f"era5land-{start.year}-{m:02d}",
            "derived-era5-land-daily-statistics",
            {
                "variable": LAND_VARIABLES,
                "year": str(start.year),
                "month": f"{m:02d}",
                "day": DAYS,
                "daily_statistic": "daily_mean",
                "time_zone": "utc+00:00",
                "frequency": "1_hourly",
                "area": AREA,
            },
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    year, wk = a.week.split("-W")
    week = IsoWeek(int(year), int(wk))
    a.out.mkdir(parents=True, exist_ok=True)
    import cdsapi  # noqa: PLC0415

    client = cdsapi.Client(quiet=True, progress=False)
    todo = list(units(week))
    log(f"{len(todo)} requests for {week.id} into {a.out}")
    failed = 0
    for i, (name, dataset, request) in enumerate(todo, 1):
        nc, rec = a.out / f"{name}.nc", a.out / f"{name}.request.json"
        if nc.exists() and rec.exists():
            log(f"[{i}/{len(todo)}] {name} skip (done)")
            continue
        attempt = 0
        while attempt < 3:
            attempt += 1
            requested_at = datetime.now(UTC).isoformat(timespec="seconds")
            t0 = time.monotonic()
            try:
                tmp = nc.with_suffix(".nc.part")
                client.retrieve(dataset, request).download(str(tmp))
                tmp.rename(nc)
                rec.write_text(
                    json.dumps(
                        {
                            "dataset": dataset,
                            "request": request,
                            "requested_at_utc": requested_at,
                            "seconds": round(time.monotonic() - t0, 1),
                            "bytes": nc.stat().st_size,
                            "account": ACCOUNT,
                            "client": "cdsapi==0.7.7 via uv run --with",
                        },
                        indent=2,
                    )
                    + "\n"
                )
                log(f"[{i}/{len(todo)}] {name} ok {nc.stat().st_size} B")
                break
            except Exception as err:  # noqa: BLE001  logged; queue cap waited out, else retried
                if "temporarily limited" in str(err):
                    log(f"[{i}/{len(todo)}] {name} queue cap; waiting 120 s (not an attempt)")
                    attempt -= 1
                    time.sleep(120)
                    continue
                log(f"[{i}/{len(todo)}] {name} attempt {attempt} FAILED: {err!r}")
                if is_licence_refusal(err):
                    log("STOP: licence or terms refusal; the owner must act")
                    return 3
                time.sleep(30 * attempt)
        else:
            failed += 1
    log(f"done: {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
