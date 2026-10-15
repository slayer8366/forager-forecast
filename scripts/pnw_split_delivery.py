"""Finish a month the store delivered as a zip of several NetCDF files instead of one.

Run:  uv run python scripts/pnw_split_delivery.py <cds dir> YYYY-MM <job id>

Seen for hourly ERA5-Land 2026-08 (scoring window for 2026-W41): the month straddles final
(expver 0001) and preliminary (expver 0005) data, the store reported "Structural differences in
grib fields", and it returned a zip of data_0.nc (swvl1, stl1) and data_1.nc (t2m) although the
request asked for download_format unarchived. pnw_cds_hourly_pull.py cannot open a zip, so this
merges the members into the one hourly file it expects, refusing members on different hours or
grids and any missing variable, then aggregates with that script's own `aggregate` and writes its
request record. The zip is kept beside the result.
"""

import hashlib
import json
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from pnw_cds_hourly_pull import ACCOUNT, AREA, DATASET, VARIABLES, aggregate  # noqa: E402


def merge_zip(zip_path: Path, out: Path) -> dict:
    """Merge every member's variables into out; returns {member: {variables, expver}}."""
    members, merged, axes = {}, {}, None
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(zip_path) as z:
        for name in sorted(z.namelist()):
            path = Path(z.extract(name, tmp))
            with h5py.File(path) as h:
                t = h["valid_time"][:].astype(np.int64)
                units = h["valid_time"].attrs["units"]
                lat, lon = h["latitude"][:], h["longitude"][:]
                if axes is None:
                    axes = (t, units, lat, lon)
                elif not np.array_equal(axes[0], t):
                    raise SystemExit(f"{name} holds other hours than the first member")
                elif not (np.array_equal(axes[2], lat) and np.array_equal(axes[3], lon)):
                    raise SystemExit(f"{name} is on another grid than the first member")
                got = [v for v in VARIABLES.values() if v in h]
                for v in got:
                    if v in merged:
                        raise SystemExit(f"{v} is in more than one member")
                    merged[v] = h[v][:]
                expver = sorted({x.decode() for x in h["expver"][:]}) if "expver" in h else None
                members[name] = {"variables": got, "expver": expver}
    missing = [v for v in VARIABLES.values() if v not in merged]
    if missing:
        raise SystemExit(f"no member holds {missing}")
    t, units, lat, lon = axes
    with h5py.File(out, "w") as o:
        o["valid_time"] = t
        o["valid_time"].attrs["units"] = units
        o["latitude"], o["longitude"] = lat, lon
        for v, arr in merged.items():
            o[v] = arr
    return members


def main(cds: Path, month: str, job: str) -> int:
    y, m = (int(x) for x in month.split("-"))
    name = f"hourly-era5land-{y}-{m:02d}"
    delivered = cds / f"{name}.hourly.nc"
    kept = cds / f"{name}.hourly.zip"
    if zipfile.is_zipfile(delivered):
        delivered.rename(kept)
    if not kept.exists():
        raise SystemExit(f"no zip delivery for {name}")
    hourly = cds / f"{name}.hourly.nc"
    members = merge_zip(kept, hourly)
    daily = cds / f"{name}.daily.h5"
    agg = aggregate(hourly, daily)
    last = {(2026, 10): 4}.get((y, m), 31)
    record = {
        "dataset": DATASET,
        "request": {
            "variable": list(VARIABLES),
            "year": str(y),
            "month": f"{m:02d}",
            "day": [f"{d:02d}" for d in range(1, last + 1)],
            "time": [f"{h:02d}:00" for h in range(24)],
            "area": AREA,
            "data_format": "netcdf",
            "download_format": "unarchived",
        },
        "adopted_job": job,
        "requested_at_utc": None,
        "requested_note": "the job was submitted by pnw_cds_hourly_pull.py --scoring; its time is "
        "in the store's job record",
        "delivered_as": "zip of several NetCDF files (store split by expver structure)",
        "zip_file": kept.name,
        "zip_sha256": hashlib.sha256(kept.read_bytes()).hexdigest(),
        "members": members,
        "merged_hourly_sha256": hashlib.sha256(hourly.read_bytes()).hexdigest(),
        "hourly_file_kept": True,
        "aggregated_to": daily.name,
        "aggregation": agg,
        "merged_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "account": ACCOUNT,
    }
    (cds / f"{name}.request.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), sys.argv[2], sys.argv[3]))
