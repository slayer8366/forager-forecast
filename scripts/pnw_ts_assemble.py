"""Assemble the time-series route's per-point daily files into one gridded daily file.

Run:  uv run python scripts/pnw_ts_assemble.py <dir>

Reads <dir>/ts/pt_<lat>_<lon>.daily.npz (scripts/pnw_cds_timeseries.py) and writes
<dir>/cds/ts-era5land-t1box.daily.h5 on T1's PNW box grid at 0.1° (lat 49.5 to 42.0 descending,
lon -125.0 to -121.0), with t2m and stl1 in K and swvl1 in m3 m-3 as the daily-statistics files
carry them, NaN at points not fetched, and valid_time in days since 2014-09-01. The weather builder
reads it as the lowest-precedence land source (pnw_weather.py); gridded files win where both exist.
"""

import json
import sys
from datetime import date
from pathlib import Path

import h5py
import numpy as np

DAY0 = date(2014, 9, 1)
LATS = np.arange(495, 419, -1)  # tenths, 49.5 to 42.0
LONS = np.arange(-1250, -1209, 1)  # tenths, -125.0 to -121.0


def main(d: Path) -> int:
    files = sorted((d / "ts").glob("pt_*.daily.npz"))
    if not files:
        print("no points yet")
        return 1
    first = np.load(files[0])
    ordinals = first["ordinal"]
    days = ordinals - DAY0.toordinal()
    n = len(days)
    out = {
        v: np.full((n, len(LATS), len(LONS)), np.nan, np.float32) for v in ("t2m", "stl1", "swvl1")
    }
    li = {int(x): i for i, x in enumerate(LATS)}
    lj = {int(x): j for j, x in enumerate(LONS)}
    placed = 0
    for f in files:
        la, lo = (int(x) for x in f.name[3:-10].split("_"))
        z = np.load(f)
        if not np.array_equal(z["ordinal"], ordinals):
            raise SystemExit(f"{f.name} covers different days")
        if la not in li or lo not in lj:
            raise SystemExit(f"{f.name} lies outside the box grid")
        for v in out:
            out[v][:, li[la], lj[lo]] = z[v]
        placed += 1
    target = d / "cds" / "ts-era5land-t1box.daily.h5"
    tmp = target.with_suffix(".h5.part")
    with h5py.File(tmp, "w") as o:
        o["latitude"] = LATS / 10
        o["longitude"] = LONS / 10
        vt = o.create_dataset("valid_time", data=days)
        vt.attrs["units"] = np.bytes_(f"days since {DAY0.isoformat()}")
        for v, a in out.items():
            o[v] = a
        o.attrs["route"] = np.bytes_("reanalysis-era5-land-timeseries, mean of 24 UTC hours")
    tmp.rename(target)
    print(json.dumps({"points": placed, "days": n, "file": str(target)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
