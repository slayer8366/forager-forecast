"""Rolling weather windows and calendar-and-place features (dispatch, "Features").

Every weather feature for a scored date is computed from days strictly before it: a window of w
days covers scored_date - w through scored_date - 1. For the primary design the scored date of a
cell-week is the Monday that starts the ISO week, so no feature sees weather from the week it
scores. For the secondary design the scored date is the record's own date. tests/
test_weather_windows.py holds the leakage test the dispatch asks for.

A missing day inside a window raises MissingWeather. It is never skipped or filled: a window
computed over fewer days than it names would be a different feature under the same name.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from forager_forecast.cell_weeks import CellWeek
from forager_forecast.t1_design import WINDOW_DAYS


@dataclass(frozen=True)
class DailyWeather:
    """One day of the four T1 variables, already reduced to daily values. Soil variables arrive
    hourly from the archive and are averaged over the day
    (see open_meteo.daily_weather_from_archive)."""

    day: date
    temperature_mean_c: float
    precipitation_mm: float
    soil_temperature_mean_c: float
    soil_moisture_mean: float


class MissingWeather(LookupError):
    """A day a window needs is absent from the daily series."""


def window_days(scored_date: date, window: int) -> list[date]:
    """The days a window covers: scored_date - window through scored_date - 1."""
    return [scored_date - timedelta(days=offset) for offset in range(window, 0, -1)]


def window_features(
    daily: Mapping[date, DailyWeather],
    scored_date: date,
    windows: tuple[int, ...] = WINDOW_DAYS,
) -> dict[str, float]:
    """Mean temperature, summed precipitation, mean soil temperature and mean soil moisture over
    each window, from days strictly before scored_date."""
    features: dict[str, float] = {}
    for window in windows:
        days = window_days(scored_date, window)
        missing = [d for d in days if d not in daily]
        if missing:
            raise MissingWeather(
                f"{len(missing)} of {window} days before {scored_date.isoformat()} are missing, "
                f"first {missing[0].isoformat()}"
            )
        rows = [daily[d] for d in days]
        features[f"temperature_mean_{window}d"] = _mean(r.temperature_mean_c for r in rows)
        features[f"precipitation_sum_{window}d"] = sum(r.precipitation_mm for r in rows)
        features[f"soil_temperature_mean_{window}d"] = _mean(
            r.soil_temperature_mean_c for r in rows
        )
        features[f"soil_moisture_mean_{window}d"] = _mean(r.soil_moisture_mean for r in rows)
    return features


def calendar_place_features(
    scored_date: date, latitude: float, longitude: float
) -> dict[str, float]:
    """Day of year as sine and cosine, latitude, longitude. The calendar baseline sees only
    these."""
    day_of_year = scored_date.timetuple().tm_yday
    days_in_year = 366 if _is_leap(scored_date.year) else 365
    angle = 2 * math.pi * (day_of_year - 1) / days_in_year
    return {
        "doy_sin": math.sin(angle),
        "doy_cos": math.cos(angle),
        "latitude": latitude,
        "longitude": longitude,
    }


def scored_date_of(unit: CellWeek) -> date:
    """The Monday that starts the ISO week. Weather from this day onward is never a feature."""
    return unit.week.monday()


def features_for_cell_week(daily: Mapping[date, DailyWeather], unit: CellWeek) -> dict[str, float]:
    """The full model's feature row for one cell-week: calendar and place at the cell centre plus
    the weather windows ending the day before the week starts."""
    scored = scored_date_of(unit)
    row = calendar_place_features(scored, unit.cell.center_latitude, unit.cell.center_longitude)
    row.update(window_features(daily, scored))
    return row


def _mean(values) -> float:
    items = list(values)
    return sum(items) / len(items)


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
