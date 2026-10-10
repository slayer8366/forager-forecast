"""Hourly ERA5-Land values to daily means, by the daily-statistics product's definition.

The store's `derived-era5-land-daily-statistics`, as this project requests it (D52, D54;
scripts/pnw_cds_pull.py), uses `daily_statistic` `daily_mean`, `time_zone` `utc+00:00` and
`frequency` `1_hourly`. That is the mean of the 24 hourly values stamped 00:00 to 23:00 of one UTC
day. This module computes the same thing from the hourly `reanalysis-era5-land` dataset, so months
pulled by that second route (planner's builder choice, 2026-10-10) carry the same daily values. A
day with fewer than 24 hourly stamps is not given a value: it stays NaN and is counted, never
averaged over what is there.

Instantaneous variables only (2m temperature, soil temperature level 1, volumetric soil water
layer 1). Accumulated variables such as precipitation are not handled here (D54 takes rain from
ERA5's daily sum).
"""

from datetime import UTC, date, datetime

import numpy as np


def utc_days(epoch_seconds: np.ndarray) -> np.ndarray:
    """The UTC calendar day of each hourly stamp, as numpy datetime64[D]."""
    return epoch_seconds.astype("datetime64[s]").astype("datetime64[D]")


def daily_means(
    epoch_seconds: np.ndarray, values: np.ndarray
) -> tuple[list[date], np.ndarray, int]:
    """values[time, ...] hourly -> (days, daily[day, ...], days_incomplete).

    Each day's value is the mean of its 24 hourly values; a day with any stamp missing, or any
    NaN among its 24 values at a point, is NaN at that point."""
    if values.shape[0] != len(epoch_seconds):
        raise ValueError("time axis and stamps differ in length")
    seconds = epoch_seconds.astype(np.int64)
    if np.any(seconds % 3600):
        raise ValueError("stamps are not on whole hours")
    days = utc_days(seconds)
    unique = np.unique(days)
    out = np.full((len(unique), *values.shape[1:]), np.nan)
    incomplete = 0
    for k, d in enumerate(unique):
        idx = np.where(days == d)[0]
        hours = (seconds[idx] // 3600) % 24
        if len(idx) != 24 or sorted(hours.tolist()) != list(range(24)):
            incomplete += 1
            continue
        out[k] = values[idx].mean(axis=0)  # NaN at a point if any hour is NaN there
    as_dates = [
        datetime.fromtimestamp(int(d.astype("datetime64[s]").astype(np.int64)), UTC).date()
        for d in unique
    ]
    return as_dates, out, incomplete
