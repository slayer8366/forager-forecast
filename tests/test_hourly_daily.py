"""hourly_daily.daily_means: the UTC day, all 24 hours, NaN rather than a partial mean."""

from datetime import UTC, date, datetime

import numpy as np
import pytest

from forager_forecast.hourly_daily import daily_means


def stamps(start: datetime, hours: int) -> np.ndarray:
    base = int(start.timestamp())
    return np.array([base + 3600 * h for h in range(hours)], dtype=np.int64)


def test_mean_of_the_24_utc_hours_of_each_day():
    t = stamps(datetime(2019, 1, 1, tzinfo=UTC), 48)
    v = np.arange(48, dtype=float).reshape(48, 1)
    days, daily, incomplete = daily_means(t, v)
    assert days == [date(2019, 1, 1), date(2019, 1, 2)]
    assert daily[:, 0] == pytest.approx([11.5, 35.5])
    assert incomplete == 0


def test_day_boundary_is_utc_not_local():
    # Starting at 23:00 UTC: the first stamp belongs to Dec 31, alone, so that day is incomplete.
    t = stamps(datetime(2018, 12, 31, 23, tzinfo=UTC), 25)
    v = np.ones((25, 2))
    days, daily, incomplete = daily_means(t, v)
    assert days == [date(2018, 12, 31), date(2019, 1, 1)]
    assert np.isnan(daily[0]).all() and daily[1] == pytest.approx([1.0, 1.0])
    assert incomplete == 1


def test_a_nan_hour_makes_that_point_nan_not_a_23_hour_mean():
    t = stamps(datetime(2019, 1, 1, tzinfo=UTC), 24)
    v = np.ones((24, 2))
    v[5, 1] = np.nan
    _, daily, _ = daily_means(t, v)
    assert daily[0, 0] == 1.0 and np.isnan(daily[0, 1])


def test_refuses_stamps_off_the_hour():
    with pytest.raises(ValueError):
        daily_means(np.array([1800], dtype=np.int64), np.ones((1, 1)))
