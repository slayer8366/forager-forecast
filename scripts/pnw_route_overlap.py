"""Agreement of the two ERA5-Land routes on the overlap month (planner's condition (a), 2026-10-10).

Run:  uv run python scripts/pnw_route_overlap.py <cds dir> [YYYY-MM] > result.json

Compares `hourly-era5land-<month>.daily.h5` (24-UTC-hour mean of the hourly dataset) with
`era5land-<month>.nc` (the store's daily statistics) point by point and day by day. Tolerances
are fixed in TOL below before any overlap value was read (review S3): 0.001 K for both
temperatures, 0.00001 m3 m-3 for soil moisture, plus 1e-6. Missing values must sit in the
same places. Exit 0 when every value agrees.
"""

import json
import sys
from pathlib import Path

import h5py
import numpy as np

# Fixed before the overlap month was compared (review S3): tighter than the Open-Meteo test,
# since both sides are the store's own unquantised values from the same hourly fields; the
# allowance is float32 storage and summation order (float32 spacing at 300 K is about 3e-5).
TOL = {"t2m": 0.001, "stl1": 0.001, "swvl1": 0.00001}


def main(cds: Path, month: str) -> int:
    with (
        h5py.File(cds / f"hourly-era5land-{month}.daily.h5") as a,
        h5py.File(cds / f"era5land-{month}.nc") as b,
    ):
        same_grid = np.allclose(a["latitude"][:], b["latitude"][:]) and np.allclose(
            a["longitude"][:], b["longitude"][:]
        )
        out = {"month": month, "same_grid": bool(same_grid), "variables": {}}
        ok = same_grid
        for v, tol in TOL.items():
            x, y = a[v][:].astype(np.float64), b[v][:].astype(np.float64)
            if x.shape != y.shape:
                out["variables"][v] = {"shape_hourly": x.shape, "shape_daily": y.shape}
                ok = False
                continue
            nan_same = bool(np.array_equal(np.isnan(x), np.isnan(y)))
            d = np.abs(x - y)
            worst = float(np.nanmax(d)) if np.isfinite(d).any() else None
            over = int(np.nansum(d > tol + 1e-6))
            out["variables"][v] = {
                "values": int(np.isfinite(d).sum()),
                "nan_positions_equal": nan_same,
                "max_abs_diff": worst,
                "over_tolerance": over,
                "tolerance": tol,
            }
            ok = ok and nan_same and over == 0
        out["agree"] = bool(ok)
    print(json.dumps(out, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else "2019-01"))
