"""Small synthetic files laid out as Daymet V4 and the Climate Data Store deliver them, for the T8b
tests. No real data: every value here is made up.

Daymet V4 (V4 R1 user guide, read 2026-10-26): one file per variable and year, `prcp` [time, y, x]
in mm, 2-D `lat` and `lon` [y, x], `time` in "days since 1950-01-01 00:00:00" at noon, a
_FillValue of -9999 off land, 365 days a year (31 December dropped in leap years).

ERA5-Land from the store, as scripts/pnw_weather.py reads it: `valid_time`, `latitude`,
`longitude` and one [time, lat, lon] array per short name.
"""

from datetime import date, timedelta

import h5py
import numpy as np

DAYMET_EPOCH = date(1950, 1, 1)
FILL = -9999.0


def daymet_days(year: int) -> list[date]:
    """Daymet's 365 days of a year: every day, less 31 December in a leap year."""
    days = [date(year, 1, 1) + timedelta(days=i) for i in range(366)]
    days = [d for d in days if d.year == year]
    return days[:365]


def write_daymet(path, lat, lon, days, prcp, fill=FILL, time_units=None):
    """prcp [day, y, x]; NaN is written as the fill value."""
    data = np.where(np.isnan(prcp), fill, prcp).astype(np.float32)
    with h5py.File(path, "w") as h:
        t = h.create_dataset("time", data=np.array([(d - DAYMET_EPOCH).days + 0.5 for d in days]))
        t.attrs["units"] = np.bytes_(time_units or "days since 1950-01-01 00:00:00")
        t.attrs["calendar"] = np.bytes_("standard")
        h.create_dataset("lat", data=np.asarray(lat, dtype=np.float32))
        h.create_dataset("lon", data=np.asarray(lon, dtype=np.float32))
        p = h.create_dataset("prcp", data=data, chunks=True)
        p.attrs["_FillValue"] = np.array([fill], dtype=np.float32)
        p.attrs["units"] = np.bytes_("mm/day")


def write_era5_daily(path, days, lats, lons, fields, units="days since 1970-01-01"):
    """fields: short name -> [day, lat, lon]."""
    with h5py.File(path, "w") as h:
        base = date(1970, 1, 1)
        t = h.create_dataset("valid_time", data=np.array([(d - base).days for d in days]))
        t.attrs["units"] = np.bytes_(units)
        h.create_dataset("latitude", data=np.asarray(lats, dtype=np.float64))
        h.create_dataset("longitude", data=np.asarray(lons, dtype=np.float64))
        for k, v in fields.items():
            h.create_dataset(k, data=np.asarray(v, dtype=np.float32))


def write_era5_hourly(path, epoch_seconds, lats, lons, fields):
    with h5py.File(path, "w") as h:
        t = h.create_dataset("valid_time", data=np.asarray(epoch_seconds, dtype=np.int64))
        t.attrs["units"] = np.bytes_("seconds since 1970-01-01")
        h.create_dataset("latitude", data=np.asarray(lats, dtype=np.float64))
        h.create_dataset("longitude", data=np.asarray(lons, dtype=np.float64))
        for k, v in fields.items():
            h.create_dataset(k, data=np.asarray(v, dtype=np.float32))


def rule_all(monkeypatch, step=None):
    """Stands in for the owner's rulings in a test only: marks every T8b reading (or one step's)
    as ruled, so the code's own logic can be exercised. The real RULED stays empty."""
    from forager_forecast.t8b import design

    ids = {p.id: "test" for p in design.PENDING.values() if step is None or p.step == step}
    monkeypatch.setattr(design, "RULED", ids)
