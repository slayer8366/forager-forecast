"""Daymet V4 precipitation files to 0.1 degree cell series, and M1/M2's windows on Daymet's
calendar (31 December dropped in leap years). Small synthetic files only."""

from datetime import date, timedelta

import numpy as np
import pytest
from t8b_files import FILL, daymet_days, write_daymet

from forager_forecast.t8.design import Measure
from forager_forecast.t8b import daymet as dm

# 2 x 5 pixels: columns 0-1 fall in cell (450, -1230), columns 2-3 in (450, -1229), column 4 is
# water (fill on every day) and would fall in (450, -1228).
LAT = np.array([[45.01] * 5, [45.03] * 5])
LON = np.array([[-123.02, -123.01, -122.91, -122.89, -122.79]] * 2)
OFFSET = np.array([[0.0, 1.0, 10.0, 11.0, 0.0], [2.0, 3.0, 12.0, 13.0, 0.0]])
A, B = (450, -1230), (450, -1229)


def day_value(d: date) -> float:
    return float(d.toordinal() % 97)


def year_file(tmp_path, year, lat=LAT, lon=LON, skip=()):
    days = [d for d in daymet_days(year) if d not in skip]
    prcp = np.array([day_value(d) + OFFSET for d in days])
    prcp[:, :, 4] = np.nan
    path = tmp_path / f"daymet_v4_daily_na_prcp_{year}.nc"
    write_daymet(path, lat, lon, days, prcp)
    return path


def test_pixels_are_averaged_into_the_cell_their_centre_falls_in(tmp_path):
    s = dm.read_daymet([year_file(tmp_path, 2017)])
    assert set(s.index) == {A, B}
    assert s.pixels == {A: 4, B: 4}
    d = date(2017, 3, 5)
    k = s.days.index(d)
    assert s.values[s.index[A], k] == pytest.approx(day_value(d) + 1.5)
    assert s.values[s.index[B], k] == pytest.approx(day_value(d) + 11.5)


def test_a_cell_of_fill_pixels_only_carries_no_series(tmp_path):
    s = dm.read_daymet([year_file(tmp_path, 2017)])
    assert (450, -1228) not in s.index


def test_a_pixel_missing_on_some_days_but_not_all_is_refused(tmp_path):
    days = daymet_days(2017)
    prcp = np.array([day_value(d) + OFFSET for d in days])
    prcp[:, :, 4] = np.nan
    prcp[10, 0, 0] = np.nan
    path = tmp_path / "p.nc"
    write_daymet(path, LAT, LON, days, prcp)
    with pytest.raises(dm.DaymetDiffers, match="some days but not all"):
        dm.read_daymet([path])


def test_reading_in_small_chunks_gives_the_same_series(tmp_path):
    paths = [year_file(tmp_path, 2016), year_file(tmp_path, 2017)]
    a = dm.read_daymet(paths, chunk_days=31)
    b = dm.read_daymet(paths, chunk_days=3)
    assert a.days == b.days and a.index == b.index
    assert np.array_equal(a.values, b.values)


def test_files_with_different_pixel_positions_are_refused(tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(dm.DaymetDiffers, match="lat and lon"):
        dm.read_daymet([year_file(tmp_path, 2016), year_file(other, 2017, lon=LON + 0.001)])


def test_time_must_be_daymets_days_since_1950_at_noon(tmp_path):
    days = daymet_days(2017)
    prcp = np.array([day_value(d) + OFFSET for d in days])
    path = tmp_path / "p.nc"
    write_daymet(path, LAT, LON, days, prcp, time_units="hours since 1950-01-01 00:00:00")
    with pytest.raises(dm.DaymetDiffers, match="time units"):
        dm.read_daymet([path])


def test_the_dropped_days_are_31_december_of_each_leap_year():
    assert dm.dropped_days(date(2014, 10, 1), date(2025, 12, 31)) == [
        date(2016, 12, 31),
        date(2020, 12, 31),
        date(2024, 12, 31),
    ]


def test_the_delivered_days_are_daymets_calendar(tmp_path):
    s = dm.read_daymet([year_file(tmp_path, 2016), year_file(tmp_path, 2017)])
    assert date(2016, 12, 31) not in s.days
    assert date(2016, 2, 29) in s.days
    assert len(s.days) == 730


def window(s, cell, monday, days, gap=1):
    return dm.window_values(s, [cell], [monday], Measure("M", "rain", "sum", days), gap)[0]


def test_the_window_ends_the_day_before_the_week(tmp_path):
    s = dm.read_daymet([year_file(tmp_path, 2017)])
    monday = date(2017, 6, 5)
    want = sum(day_value(monday - timedelta(days=i)) + 1.5 for i in range(1, 15))
    assert window(s, A, monday, 14) == pytest.approx(want)


def test_the_week_late_window_ends_8_days_before_the_week(tmp_path):
    s = dm.read_daymet([year_file(tmp_path, 2017)])
    monday = date(2017, 6, 5)
    want = sum(day_value(monday - timedelta(days=i)) + 1.5 for i in range(8, 22))
    assert window(s, A, monday, 14, gap=8) == pytest.approx(want)


def test_a_window_over_a_dropped_31_december_counts_w_daymet_days(tmp_path):
    # PENDING B-daymet-leap, proposed reading: 14 delivered days, reaching one calendar day further
    # back, here 2016-12-17 to 2017-01-01 less 2016-12-31.
    s = dm.read_daymet([year_file(tmp_path, 2016), year_file(tmp_path, 2017)])
    monday = date(2017, 1, 2)
    calendar = [monday - timedelta(days=i) for i in range(1, 16)]
    used = [d for d in calendar if d != date(2016, 12, 31)]
    assert len(used) == 14
    want = sum(day_value(d) + 1.5 for d in used)
    assert window(s, A, monday, 14) == pytest.approx(want)


def test_a_day_that_was_not_pulled_makes_the_window_missing(tmp_path):
    s = dm.read_daymet([year_file(tmp_path, 2017, skip={date(2017, 6, 1)})])
    assert np.isnan(window(s, A, date(2017, 6, 5), 14))
    assert not np.isnan(window(s, A, date(2017, 6, 26), 14))


def test_a_window_reaching_before_the_first_day_is_missing(tmp_path):
    s = dm.read_daymet([year_file(tmp_path, 2017)])
    assert np.isnan(window(s, A, date(2017, 1, 9), 14))
    assert np.isnan(window(s, (450, -1228), date(2017, 6, 5), 14))
    assert FILL == -9999.0
