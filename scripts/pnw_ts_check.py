"""Every time-series point against the gridded ERA5-Land months already held (planner, 2026-10-11).

Run:  uv run python scripts/pnw_ts_check.py <dir> [--probe-snap]

For each `ts/pt_<lat>_<lon>.daily.npz`, its daily values are compared with the same point's
values in every gridded land file on disk (`cds/hourly-era5land-YYYY-MM.daily.h5`, and
`cds/era5land-YYYY-MM.nc` if any), day by day. Both sides are daily means of the same 24 UTC hours
(hourly_daily.daily_means for both), so a matching point agrees to float32 packing. Daily, not
hourly: the time-series hourly zips are kept only for the 12 sample points, to save disk.

Tolerance, fixed here before the comparison was first run (as the route-overlap check, review S3):
|difference| <= 0.001 K for t2m and stl1, <= 0.00001 m3 m-3 for swvl1. Missing values must sit in
the same places. A point fails if any compared value is outside the tolerance or the NaN pattern
differs, or if no day could be compared. Failing points are written to `ts/failed_points.json`,
which the assembler leaves out (scripts/pnw_ts_assemble.py), so no fit reads through them.

Reported per class: points read by a cell's own value, points read as a RECORD -822 neighbour,
and sea-adjacent points (a land point with a sea cell among its 8 neighbours). The worst point per
variable is named. A matching value at the same grid point is also the check that the request
coordinates snapped to that point: a different neighbour would not match on every day.

--probe-snap additionally requests three off-centre coordinates from the store and records which
grid point each reply names (latitude/longitude in the reply), to confirm the snapping rule.
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from pnw_cds_timeseries import land_mask, points_needed  # noqa: E402

from forager_forecast.coastal import NEIGHBOURS, land_point  # noqa: E402

TOL = {"t2m": 0.001, "stl1": 0.001, "swvl1": 0.00001}
DAY0 = date(2014, 9, 1)


def gridded(cds: Path):
    """{var: {(lat, lon): {ordinal: value}}} over every gridded land file on disk."""
    out = {v: {} for v in TOL}
    pat = re.compile(r"^(hourly-era5land-\d{4}-\d{2}\.daily\.h5|era5land-\d{4}-\d{2}\.nc)$")
    files = sorted(p for p in cds.iterdir() if pat.match(p.name))
    for path in files:
        with h5py.File(path) as h:
            units = h["valid_time"].attrs["units"].decode()
            base = date.fromisoformat(units.split("since ")[1][:10])
            ordinals = [base.toordinal() + int(x) for x in h["valid_time"][:]]
            lat = np.rint(h["latitude"][:] * 10).astype(int)
            lon = np.rint(h["longitude"][:] * 10).astype(int)
            for v in TOL:
                a = h[v][:].astype(np.float64)
                for i, la in enumerate(lat):
                    for j, lo in enumerate(lon):
                        d = out[v].setdefault((int(la), int(lo)), {})
                        for k, o in enumerate(ordinals):
                            d[o] = a[k, i, j]
    return out, len(files)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", type=Path)
    ap.add_argument("--probe-snap", action="store_true")
    a = ap.parse_args()
    d = a.dir
    has = land_mask(d / "cds" / "hourly-era5land-2019-01.hourly.nc")
    _pts, keep = points_needed(d / "records", has)
    # Classes: neighbour points (read by some cell with no land value), sea-adjacent points.
    from pnw_t1_fit import primary_units, read_records  # noqa: PLC0415

    cells = {
        (r["cell"].lat_tenths, r["cell"].lon_tenths)
        for r in primary_units(read_records(d / "records" / "t1_1000m.csv"))
    }
    neighbour_points = set()
    for c in cells:
        found = land_point(c, has)
        if found and found[1]:
            neighbour_points.add(found[0])
    sea_adjacent = {p for p in has if any((p[0] + x, p[1] + y) not in has for x, y in NEIGHBOURS)}
    grid, n_files = gridded(d / "cds")
    results, failed = {}, []
    worst = {v: (0.0, None) for v in TOL}
    for f in sorted((d / "ts").glob("pt_*.daily.npz")):
        la, lo = (int(x) for x in f.name[3:-10].split("_"))
        z = np.load(f)
        ordinals = z["ordinal"].tolist()
        rec = {"compared": 0, "max_abs": {}, "nan_mismatch": 0}
        ok = True
        for v, tol in TOL.items():
            g = grid[v].get((la, lo), {})
            ts_vals = dict(zip(ordinals, z[v].tolist(), strict=True))
            common = [o for o in g if o in ts_vals]
            x = np.array([ts_vals[o] for o in common])
            y = np.array([g[o] for o in common])
            nan_mis = int((np.isnan(x) != np.isnan(y)).sum())
            diff = np.abs(x - y)
            m = float(np.nanmax(diff)) if np.isfinite(diff).any() else 0.0
            rec["max_abs"][v] = m
            rec["compared"] += int(np.isfinite(diff).sum())
            rec["nan_mismatch"] += nan_mis
            if nan_mis or m > tol + 1e-9:
                ok = False
            if m > worst[v][0]:
                worst[v] = (m, f"{la}_{lo}")
        if rec["compared"] == 0:
            ok = False
        rec["pass"] = ok
        results[f"{la}_{lo}"] = rec
        if not ok:
            failed.append(f"{la}_{lo}")

    def summary(points):
        keys = [f"{p[0]}_{p[1]}" for p in points if f"{p[0]}_{p[1]}" in results]
        return {
            "points": len(keys),
            "failed": sum(1 for k in keys if not results[k]["pass"]),
            "values_compared": sum(results[k]["compared"] for k in keys),
        }

    all_pts = [tuple(int(x) for x in k.split("_")) for k in results]
    out = {
        "tolerance": TOL,
        "gridded_files": n_files,
        "all": summary(all_pts),
        "own_points": summary([p for p in all_pts if p not in neighbour_points]),
        "neighbour_points_RECORD_822": summary([p for p in all_pts if p in neighbour_points]),
        "sea_adjacent_points": summary([p for p in all_pts if p in sea_adjacent]),
        "sample_points_kept_hourly": summary([p for p in all_pts if p in keep]),
        "worst_point_by_variable": {v: {"max_abs": w[0], "point": w[1]} for v, w in worst.items()},
        "failed_points": failed,
    }
    if a.probe_snap:
        out["snap_probe"] = probe_snap(d)
    (d / "ts" / "failed_points.json").write_text(json.dumps(failed) + "\n")
    (d / "ts_check.json").write_text(json.dumps(out, indent=2) + "\n")
    (d / "ts_check_points.json").write_text(json.dumps(results) + "\n")
    print(json.dumps(out, indent=1))
    return 0 if not failed else 1


def probe_snap(d: Path) -> list[dict]:
    """Three off-centre requests (one month each, to stay small): which grid point is returned."""
    import io  # noqa: PLC0415
    import zipfile  # noqa: PLC0415

    import cdsapi  # noqa: PLC0415

    c = cdsapi.Client(quiet=True, progress=False)
    out = []
    for lat, lon in ((47.03, -123.04), (47.07, -123.06), (45.449, -122.651)):
        req = {
            "variable": ["2m_temperature"],
            "location": {"longitude": lon, "latitude": lat},
            "date": ["2019-01-01/2019-01-31"],
            "data_format": "netcdf",
        }
        target = d / "ts" / f"snap_{lat}_{lon}.zip"
        c.retrieve("reanalysis-era5-land-timeseries", req).download(str(target))
        with zipfile.ZipFile(target) as z:
            name = z.namelist()[0]
            with h5py.File(io.BytesIO(z.read(name))) as h:
                got = (float(h["latitude"][()]), float(h["longitude"][()]))
        out.append(
            {
                "requested": [lat, lon],
                "returned": [round(got[0], 6), round(got[1], 6)],
                "nearest_grid_point": [round(lat, 1), round(lon, 1)],
                "same": abs(got[0] - round(lat, 1)) < 1e-6 and abs(got[1] - round(lon, 1)) < 1e-6,
            }
        )
    return out


if __name__ == "__main__":
    sys.exit(main())
