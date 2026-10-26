"""ERA5-Land layer 2 and 2 m fields, as the store delivers them, to daily grids (M3 to M5).

Two routes, as T1's land weather had (scripts/pnw_weather.py, hourly_daily.py):
- `read_daily_statistics`: the store's `derived-era5-land-daily-statistics`, daily_mean,
  time_zone utc+00:00, frequency 1_hourly (D52), one file per request with `valid_time`,
  `latitude`, `longitude` and one [time, lat, lon] array per short name.
- `read_hourly`: `reanalysis-era5-land` hourly files, each day's value the mean of its 24 UTC
  hourly stamps (hourly_daily.daily_means: the daily-statistics product's own definition); a day
  missing any stamp stays NaN.
Every file must carry all four D159 variables by their short names (design.ERA5_LAND_SHORT):
swvl2 and stl2 (layer 2, 7 to 28 cm), t2m and d2m. A file carrying the layer 1 names instead is
refused by name, so a T1-style pull cannot pass for layer 2. Coordinates must sit on multiples of
0.1 degree (D51). A day delivered twice must carry the same values (an overlap), else it is refused.

`land_grids` gives the three land measures' daily grids: soil moisture as delivered (m3 m-3),
soil temperature in deg C (K - 273.15, as pnw_weather.TO_UNITS), and the dew-point depression,
the day's mean 2 m temperature minus its mean 2 m dew point (K; a difference, so also deg C).
The mean of the 24 hourly differences equals the difference of the two means, so either route
gives the same depression.

Water points (RECORD -822) are left as delivered: a point with no value is NaN here, and
measures.unit_points sends each cell to its land point by coastal.land_point, as T8 did.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path

import h5py
import numpy as np

from forager_forecast import hourly_daily as hd
from forager_forecast.daily_grid import DailyGrid
from forager_forecast.t8b.design import ERA5_LAND_SHORT

SHORT = tuple(ERA5_LAND_SHORT)  # swvl2, stl2, t2m, d2m
UNITS = re.compile(r"(days|hours|seconds) since (\d{4}-\d{2}-\d{2})( 00:00:00)?")
SCALE = {"days": 1, "hours": 24, "seconds": 86400}


class Era5Differs(ValueError):
    """A file is not laid out as the store delivers it."""


def _text(value) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)


def _index(coords: np.ndarray, path: Path) -> np.ndarray:
    idx = np.rint(np.asarray(coords, dtype=np.float64) / 0.1).astype(int)
    if np.max(np.abs(idx * 0.1 - coords)) > 1e-6:
        raise Era5Differs(f"{path.name}: coordinates are not on multiples of 0.1 degree (D51)")
    return idx


def _check_variables(h: h5py.File, path: Path) -> None:
    missing = [k for k in SHORT if k not in h]
    if missing:
        has = sorted(k for k in h if k not in ("valid_time", "latitude", "longitude"))
        raise Era5Differs(f"{path.name}: missing {', '.join(missing)} (has {', '.join(has)})")


def _whole_days(h: h5py.File, path: Path) -> list[date]:
    m = UNITS.fullmatch(_text(h["valid_time"].attrs.get("units", b"")))
    if not m:
        raise Era5Differs(f"{path.name}: unexpected time units")
    raw = np.asarray(h["valid_time"][:], dtype=np.int64)
    scale = SCALE[m.group(1)]
    if np.any(raw % scale):
        raise Era5Differs(f"{path.name}: valid_time not on whole days")
    base = date.fromisoformat(m.group(2))
    return [base + timedelta(days=int(v // scale)) for v in raw]


class _Store:
    """The files' daily arrays, kept as delivered and laid onto one grid per short name at the
    end (about 400 MB at float64 for four variables over the box and 2014-10 to 2025-12)."""

    def __init__(self) -> None:
        self.files: list[tuple[Path, list[date], np.ndarray, np.ndarray, dict]] = []

    def add(self, path: Path, days: list[date], lat, lon, data: dict[str, np.ndarray]) -> None:
        self.files.append((path, days, np.asarray(lat), np.asarray(lon), data))

    def grids(self) -> dict[str, DailyGrid]:
        if not self.files:
            raise Era5Differs("no ERA5-Land file given")
        days = sorted({d for f in self.files for d in f[1]})
        start, n = days[0], (days[-1] - days[0]).days + 1
        points = sorted({(int(a), int(b)) for f in self.files for a in f[2] for b in f[3]})
        row = {p: r for r, p in enumerate(points)}
        out = {}
        for k in SHORT:
            values = np.full((len(points), n), np.nan)
            for path, fdays, lat, lon, data in self.files:
                rows = np.array([[row[(int(a), int(b))] for b in lon] for a in lat]).ravel()
                cols = np.array([(d - start).days for d in fdays])
                new = data[k].reshape(len(fdays), -1).T  # [point, day]
                old = values[np.ix_(rows, cols)]
                clash = ~np.isnan(old) & ~np.isnan(new) & (old != new)
                if clash.any():
                    raise Era5Differs(f"{path.name}: {k} delivered twice with differing values")
                values[np.ix_(rows, cols)] = np.where(np.isnan(new), old, new)
            out[k] = DailyGrid(start, dict(row), values)
        return out


def read_daily_statistics(paths: Sequence[Path]) -> dict[str, DailyGrid]:
    """Short name -> DailyGrid in the store's units (K, m3 m-3)."""
    store = _Store()
    for path in map(Path, paths):
        with h5py.File(path, "r") as h:
            _check_variables(h, path)
            days = _whole_days(h, path)
            lat, lon = _index(h["latitude"][:], path), _index(h["longitude"][:], path)
            data = {k: np.asarray(h[k][:], dtype=np.float64) for k in SHORT}
        store.add(path, days, lat, lon, data)
    return store.grids()


def read_hourly(paths: Sequence[Path]) -> dict[str, DailyGrid]:
    """Hourly files -> 24-hour UTC daily means, short name -> DailyGrid (store's units)."""
    store = _Store()
    for path in map(Path, paths):
        with h5py.File(path, "r") as h:
            _check_variables(h, path)
            units = _text(h["valid_time"].attrs.get("units", b""))
            if units not in ("seconds since 1970-01-01", "seconds since 1970-01-01 00:00:00"):
                raise Era5Differs(f"{path.name}: hourly time units {units!r}")
            stamps = np.asarray(h["valid_time"][:], dtype=np.int64)
            lat, lon = _index(h["latitude"][:], path), _index(h["longitude"][:], path)
            data, days = {}, None
            for k in SHORT:
                d, daily, _incomplete = hd.daily_means(stamps, np.asarray(h[k][:], np.float64))
                data[k], days = daily, d
        store.add(path, days, lat, lon, data)
    return store.grids()


def land_grids(raw: dict[str, DailyGrid]) -> dict[str, DailyGrid]:
    """The three land measures' daily grids (design.LAND_VARIABLES)."""
    t2m, d2m = raw["t2m"], raw["d2m"]
    if t2m.index != d2m.index or t2m.start != d2m.start or t2m.values.shape != d2m.values.shape:
        raise Era5Differs("2 m temperature and dew point are not on the same points and days")
    st = raw["stl2"]
    return {
        "soil_moisture_l2": raw["swvl2"],
        "soil_temperature_l2": DailyGrid(st.start, st.index, st.values - 273.15),
        "dewpoint_depression": DailyGrid(t2m.start, t2m.index, t2m.values - d2m.values),
    }
