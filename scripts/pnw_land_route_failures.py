"""Name every hour that fails the hourly land-route comparison, reading cached bodies only.

Run:  uv run python scripts/pnw_land_route_failures.py <records> <weather npz> <cds dir> <om dir>
          [--available]

A diagnostic for the gate-override dispatch (docs/dispatch/2026-10-11-pnw-pilot-gate-override-
restart.md, step 0). It walks the same sample, points and hours as pnw_equivalence.main, with the
same tolerance and EPS imported from that script, but makes no request: a span whose Open-Meteo
body is not already cached in <om dir> stops the run. For each variable it prints the offset-0
counts (to be read against equivalence.json) and every offset-0 hour that does not match, with
both values. Each failing store value is then read a second time straight from its source file
(the gridded month or the time-series zip), without HourlyStore, and the Open-Meteo value straight
from the cached JSON, so the two readings can be compared; where the point has a time-series zip,
that route's value for the same hour is printed beside it (the other Copernicus route).
"""

import argparse
import io
import json
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from pnw_equivalence import (  # noqa: E402
    EPS,
    HOURLY_TOL,
    OM_HOURLY,
    SPAN_DAYS,
    HourlyStore,
    compare_point,
    request_cells,
    sample,
    split_span,
)
from pnw_weather import land_has_value, load  # noqa: E402

from forager_forecast.cells import quarter_cell_for  # noqa: E402


def ts_value(cds: Path, v: str, point: tuple[int, int], epoch: int):
    """The time-series route's value for the same point and hour (°C or m3 m-3), or None."""
    z = cds.parent / "ts" / f"pt_{point[0]}_{point[1]}.zip"
    if not z.exists():
        return None
    with zipfile.ZipFile(z) as zf:
        for name in zf.namelist():
            with h5py.File(io.BytesIO(zf.read(name))) as h:
                if v not in h:
                    continue
                t = h["valid_time"][:].astype(np.int64) * 3600
                k = np.flatnonzero(t == epoch)
                if not len(k):
                    return None
                raw = float(h[v][int(k[0])])
                return raw - 273.15 if v in ("t2m", "stl1") else raw
    return None


def raw_store_value(cds: Path, v: str, point: tuple[int, int], epoch: int):
    """The store value read directly from its file, in °C or m3 m-3, and which file it came from."""
    ym = datetime.fromtimestamp(epoch, UTC).strftime("%Y-%m")
    path = cds / f"hourly-era5land-{ym}.hourly.nc"
    if path.exists():
        with h5py.File(path) as h:
            t = h["valid_time"][:].astype(np.int64)
            k = np.flatnonzero(t == epoch)
            i = np.flatnonzero(np.rint(h["latitude"][:] * 10).astype(int) == point[0])
            j = np.flatnonzero(np.rint(h["longitude"][:] * 10).astype(int) == point[1])
            raw = float(h[v][int(k[0]), int(i[0]), int(j[0])])
        source = path.name
    else:
        z = cds.parent / "ts" / f"pt_{point[0]}_{point[1]}.zip"
        raw = None
        with zipfile.ZipFile(z) as zf:
            for name in zf.namelist():
                with h5py.File(io.BytesIO(zf.read(name))) as h:
                    if v not in h:
                        continue
                    t = h["valid_time"][:].astype(np.int64) * 3600
                    k = np.flatnonzero(t == epoch)
                    raw = float(h[v][int(k[0])])
                    source = f"{z.name}:{name}"
        if raw is None:
            raise SystemExit(f"{v} not in {z}")
    return (raw - 273.15 if v in ("t2m", "stl1") else raw), raw, source


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("records", type=Path)
    ap.add_argument("weather", type=Path)
    ap.add_argument("cds", type=Path)
    ap.add_argument("om", type=Path)
    ap.add_argument("--available", action="store_true")
    args = ap.parse_args()
    grids = load(args.weather)
    has = land_has_value(grids)
    store = HourlyStore(args.cds)
    counts = {v: [0, 0] for v in HOURLY_TOL}
    failures, spans = [], 0
    for cell, start in sample(args.records):
        point, kind = compare_point(cell, has)
        if point is None:
            continue
        q = quarter_cell_for(cell.center_latitude, cell.center_longitude)
        pts = {
            "temperature": point,
            "soil_temperature": point,
            "soil_moisture": point,
            "precipitation": (q.lat_quarters, q.lon_quarters),
        }
        daily = {}
        for v, p in pts.items():
            g = grids[v]
            i = g.index.get(p)
            d0 = (start - g.start).days
            daily[v] = None if i is None else g.values[i, d0 : d0 + SPAN_DAYS]
        if any(
            s is None or np.isnan(grids[v].values[grids[v].index[pts[v]]]).all()
            for v, s in daily.items()
        ):
            continue
        if not all(not np.isnan(s).any() for s in daily.values()):
            if args.available:
                continue
            raise SystemExit(f"store values missing for {cell.id} from {start}")
        land_cell, _ = request_cells(cell, point, kind)
        cache = args.om / f"{land_cell.id}_{start}.json"
        if not cache.exists():
            raise SystemExit(f"no cached body {cache}; this diagnostic makes no request")
        body = json.loads(cache.read_text())
        _, hours, stamps = split_span(body)
        spans += 1
        for v, om_name in OM_HOURLY.items():
            for h, stamp in enumerate(stamps):
                epoch = int(datetime.fromisoformat(stamp).replace(tzinfo=UTC).timestamp())
                om_value = hours[om_name][h]
                sv = store.value(v, point, epoch)
                if sv is None or np.isnan(om_value):
                    continue
                counts[v][1] += 1
                if abs(sv - om_value) <= HOURLY_TOL[v] + EPS:
                    counts[v][0] += 1
                    continue
                direct, raw, source = raw_store_value(args.cds, v, point, epoch)
                failures.append(
                    {
                        "variable": v,
                        "cell": cell.id,
                        "land_point": list(point),
                        "land_point_kind": kind,
                        "span_start": str(start),
                        "body": cache.name,
                        "hour_utc": stamp,
                        "store": sv,
                        "store_direct": direct,
                        "store_raw_file_value": raw,
                        "store_source": source,
                        "time_series_route": ts_value(args.cds, v, point, epoch),
                        "open_meteo": float(om_value),
                        "open_meteo_body_raw": body["hourly"][om_name][h],
                        "abs_diff": abs(sv - float(om_value)),
                        "bound": HOURLY_TOL[v] + EPS,
                    }
                )
    out = {
        "run_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "weather": str(args.weather),
        "om_dir": str(args.om),
        "spans_compared": spans,
        "offset0_matched_compared": counts,
        "failing_hours": failures,
    }
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
