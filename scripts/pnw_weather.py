"""The store's PNW NetCDF files as daily grids, and T1's weather windows for a list of units.

Build:  uv run python scripts/pnw_weather.py <cds dir> <out npz> [--prefix ""]

Reads every `<prefix>era5land-YYYY-MM.nc` and `<prefix>era5-precip-YYYY.nc` of one area (the
empty prefix is T1's box; see scripts/pnw_cds_pull.py) with h5py, checks each file's coordinates
sit on multiples of the grid step (D51), converts units (K to °C, m to mm), and stores four
daily grids in one npz. Day 0 is 2014-09-01. Days not delivered stay NaN and are counted.

`weather_matrix(npz, rows)` returns the 32 window features for the fit's rows: ERA5-Land values
at the unit's 0.1° cell; precipitation at the ERA5 0.25° point nearest the cell centre
(`cells.quarter_cell_for`, D46, D54), so every unit in one cell reads one rain series. Rows whose
windows touch a missing value come back NaN and are counted by the caller.
"""

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import h5py
import numpy as np

from forager_forecast.cells import quarter_cell_for
from forager_forecast.coastal import land_point
from forager_forecast.daily_grid import DailyGrid, feature_names, window_matrix

START = date(2014, 9, 1)
END = date(2025, 12, 31)
N_DAYS = (END - START).days + 1
LAND = {"t2m": "temperature", "stl1": "soil_temperature", "swvl1": "soil_moisture"}
# Unit conversion per source variable (review B1: soil moisture is m3 m-3 and takes no offset).
TO_UNITS = {
    "t2m": lambda a: a - 273.15,  # K -> °C
    "stl1": lambda a: a - 273.15,  # K -> °C
    "swvl1": lambda a: a,  # m3 m-3 as delivered
    "tp": lambda a: a * 1000.0,  # m -> mm
}


def _days(h) -> np.ndarray:
    units = h["valid_time"].attrs["units"].decode()
    m = re.fullmatch(r"(days|hours|seconds) since (\d{4}-\d{2}-\d{2})( 00:00:00)?", units)
    if not m:
        raise SystemExit(f"unexpected time units {units!r}")
    base = date.fromisoformat(m.group(2))
    raw = h["valid_time"][:]
    scale = {"days": 1, "hours": 24, "seconds": 86400}[m.group(1)]
    if np.any(raw % scale):
        raise SystemExit(f"valid_time not on whole days: {raw[:5]}")
    return np.array([((base + timedelta(days=int(v // scale))) - START).days for v in raw])


def _index(coords: np.ndarray, step: float) -> np.ndarray:
    idx = np.rint(coords / step).astype(int)
    if np.max(np.abs(idx * step - coords)) > 1e-6:
        raise SystemExit(f"coordinates not on multiples of {step} (D51)")
    return idx


def build(cds_dir: Path, out: Path, prefix: str = "") -> dict:
    stores: dict[str, dict[tuple[int, int], np.ndarray]] = {
        v: {} for v in (*LAND.values(), "precipitation")
    }
    files = {"land": 0, "precip": 0}
    pattern = re.compile(
        rf"^{re.escape(prefix)}(era5land-\d{{4}}-\d{{2}}|era5-precip-\d{{4}})\.nc$"
    )
    hourly_pattern = re.compile(r"^hourly-era5land-(\d{4}-\d{2})\.daily\.h5$")
    rain_hourly_pattern = re.compile(r"^hourly-era5-precip-(\d{4})\.daily\.h5$")
    routes: dict[str, str] = {}
    rain_routes: dict[str, str] = {}
    # Hourly-route months first, so a month both routes delivered ends up with the
    # daily-statistics values (D24's route as first planned); the overlap is checked apart.
    paths = (
        []
        if prefix
        else sorted(
            p
            for p in cds_dir.glob("*.daily.h5")
            if hourly_pattern.match(p.name) or rain_hourly_pattern.match(p.name)
        )
    )
    paths += sorted(p for p in cds_dir.glob("*.nc") if pattern.match(p.name))
    for path in paths:
        hm = hourly_pattern.match(path.name)
        if hm:
            files["land_hourly_route"] = files.get("land_hourly_route", 0) + 1
            routes[hm.group(1)] = "hourly reanalysis-era5-land, 24-hour UTC mean"
        elif path.name.startswith(f"{prefix}era5land"):
            routes[path.name[len(prefix) + 9 : len(prefix) + 16]] = "derived daily statistics"
        elif rm := rain_hourly_pattern.match(path.name):
            rain_routes[rm.group(1)] = "hourly reanalysis-era5-single-levels, summed per UTC day"
        else:
            rain_routes[path.name[len(prefix) + 12 : len(prefix) + 16]] = "derived daily sum"
        with h5py.File(path) as h:
            days = _days(h)
            if hm or path.name.startswith(f"{prefix}era5land"):
                files["land"] += 1
                lat, lon = _index(h["latitude"][:], 0.1), _index(h["longitude"][:], 0.1)
                pairs = [(k, LAND[k]) for k in LAND]
            else:
                files["precip"] += 1
                lat, lon = _index(h["latitude"][:], 0.25), _index(h["longitude"][:], 0.25)
                pairs = [("tp", "precipitation")]
            for key, variable in pairs:
                data = h[key][:].astype(np.float64)  # [time, lat, lon]
                data = TO_UNITS[key](data)
                store = stores[variable]
                for i, la in enumerate(lat):
                    for j, lo in enumerate(lon):
                        series = store.setdefault((int(la), int(lo)), np.full(N_DAYS, np.nan))
                        ok = (days >= 0) & (days < N_DAYS)
                        series[days[ok]] = data[ok, i, j]
    arrays = {}
    summary = {
        "files": files,
        "land_route_by_month": dict(sorted(routes.items())),
        "rain_route_by_year": dict(sorted(rain_routes.items())),
        "variables": {},
    }
    for variable, store in stores.items():
        points = sorted(store)
        arrays[f"{variable}_points"] = np.array(points, dtype=np.int32).reshape(-1, 2)
        arrays[f"{variable}_values"] = (
            np.vstack([store[p] for p in points]) if points else np.zeros((0, N_DAYS))
        )
        vals = arrays[f"{variable}_values"]
        days_any = np.where(~np.isnan(vals).all(axis=0))[0] if len(vals) else []
        summary["variables"][variable] = {
            "points": len(points),
            "points_all_nan": int(np.isnan(vals).all(axis=1).sum()) if len(vals) else 0,
            "first_day": str(START + timedelta(days=int(days_any[0]))) if len(days_any) else None,
            "last_day": str(START + timedelta(days=int(days_any[-1]))) if len(days_any) else None,
            "days_with_data": int(len(days_any)),
        }
    np.savez_compressed(out, start=np.array(START.isoformat()), **arrays)
    return summary


def load(npz: Path) -> dict[str, DailyGrid]:
    z = np.load(npz)
    start = date.fromisoformat(str(z["start"]))
    grids = {}
    for v in ("temperature", "soil_temperature", "soil_moisture", "precipitation"):
        pts = [tuple(int(a) for a in p) for p in z[f"{v}_points"]]
        grids[v] = DailyGrid(start, {p: i for i, p in enumerate(pts)}, z[f"{v}_values"])
    return grids


def land_has_value(grids: dict[str, DailyGrid]) -> set[tuple[int, int]]:
    """ERA5-Land points carrying a value on some day for all three land variables."""
    sets = []
    for v in ("temperature", "soil_temperature", "soil_moisture"):
        g = grids[v]
        has = ~np.isnan(g.values).all(axis=1) if len(g.values) else np.zeros(0, bool)
        sets.append({p for p, i in g.index.items() if has[i]})
    return set.intersection(*sets)


def weather_matrix(npz: Path, rows) -> tuple[np.ndarray, list[str], list[str]]:
    """The 32 window features per row, and each row's land-point class: "own" (its cell's own
    ERA5-Land point), "neighbour" (a cell with no land value of its own, filled from the nearest
    land neighbour, Forager RECORD -822, coastal.land_point) or "none" (no land point within one
    cell; its land features stay NaN and the caller drops it, counted)."""
    grids = load(npz)
    has = land_has_value(grids)
    land, kind = [], []
    for r in rows:
        cell = (r["cell"].lat_tenths, r["cell"].lon_tenths)
        found = land_point(cell, has)
        if found is None:
            land.append(cell)
            kind.append("none")
        else:
            land.append(found[0])
            kind.append("neighbour" if found[1] else "own")
    quarter = []
    for r in rows:
        q = quarter_cell_for(r["cell"].center_latitude, r["cell"].center_longitude)
        quarter.append((q.lat_quarters, q.lon_quarters))
    points = {
        "temperature": land,
        "soil_temperature": land,
        "soil_moisture": land,
        "precipitation": quarter,
    }
    x = window_matrix(grids, points, [r["scored"] for r in rows])
    return x, feature_names(), kind


def weather_status(npz: Path, rows, x: np.ndarray, kind: list[str]) -> list[str]:
    """Why each row's weather is or is not complete (review B3, RECORD -822).

    "ok": every window has every day (from its own point or a land neighbour). "sea": no ERA5-Land
    land point within one cell, or the cell's ERA5 point is absent. "missing_days": the point has
    data but a window reaches a day not delivered (a month not pulled yet)."""
    grids = load(npz)
    quarter = [
        quarter_cell_for(r["cell"].center_latitude, r["cell"].center_longitude) for r in rows
    ]
    g = grids["precipitation"]
    precip_rows = g.rows_for([(q.lat_quarters, q.lon_quarters) for q in quarter])
    precip_empty = np.isnan(g.values).all(axis=1) if len(g.values) else np.zeros(0, bool)
    status = []
    for i in range(len(rows)):
        if not np.isnan(x[i]).any():
            status.append("ok")
        elif kind[i] == "none" or precip_rows[i] < 0 or precip_empty[precip_rows[i]]:
            status.append("sea")
        else:
            status.append("missing_days")
    return status


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cds_dir", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--prefix", default="")
    a = ap.parse_args()
    summary = build(a.cds_dir, a.out, a.prefix)
    Path(str(a.out) + ".summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    sys.exit(0)
