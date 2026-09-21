"""Requests to Open-Meteo's historical archive for one weather cell (D19, D21, T1 amendment 2).

Every request pins models=era5_seamless. The endpoint default is never used, in code or in
tests: it blends in a third product from 2017 onward (T0b completion report; D19). Temperature
and soil come from ERA5-Land at 0.1 degree, precipitation from ERA5 at 0.25 degree.

Two further parameters were verified live on 2026-09-18 and are pinned for the same reason,
that the unit is the cell and not a point (T1 completion report, "Verify first" item 3):

- elevation=nan turns off Open-Meteo's per-point downscaling, which otherwise adjusts
  temperature to a 90 m elevation model at the requested coordinate. Without it two points in
  one cell return different temperatures (8.7 and 7.4 C on 2024-11-01 at 47.0,-123.0 and
  47.04,-123.04); with it both return the cell's own value (8.2 C at elevation 151 m).
- cell_selection=nearest returns the cell the coordinate falls in. The default ("land")
  substitutes a nearby land cell for a coordinate over water, so a request for a cell on Puget
  Sound came back as its neighbour.

Nothing here performs a network call. The URL builder and the parser are pure so they can be
tested on fixtures; the pull itself waits on the record download and on the rate-limit question
in the T1 completion report.
"""

import math
from datetime import date, datetime
from urllib.parse import urlencode

from forager_forecast.cells import Cell
from forager_forecast.weather_windows import DailyWeather

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
MODEL = "era5_seamless"
DAILY_VARIABLES: tuple[str, ...] = ("temperature_2m_mean", "precipitation_sum")
HOURLY_VARIABLES: tuple[str, ...] = ("soil_temperature_0_to_7cm", "soil_moisture_0_to_7cm")

# Open-Meteo's own weighting of a request against its rate limits (https://open-meteo.com/en/
# pricing, "How is one API call defined?", read 2026-09-18): one call covers one location, up to
# 10 variables and up to 14 days; longer or wider requests count fractionally. The page's
# examples: 14 days with 15 variables is 1.5 calls, 28 days with 15 variables is 3.0 calls.
CALL_UNIT_DAYS = 14
CALL_UNIT_VARIABLES = 10


class ArchiveGap(ValueError):
    """The archive answered with a null where the four T1 variables should be fully populated."""


def archive_request_url(cell: Cell, start: date, end: date) -> str:
    """The archive request for one cell over an inclusive date range."""
    if end < start:
        raise ValueError(f"end {end.isoformat()} is before start {start.isoformat()}")
    query = {
        "latitude": f"{cell.center_latitude:.1f}",
        "longitude": f"{cell.center_longitude:.1f}",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(DAILY_VARIABLES),
        "hourly": ",".join(HOURLY_VARIABLES),
        "models": MODEL,
        "elevation": "nan",
        "cell_selection": "nearest",
        "timezone": "UTC",
    }
    return f"{ARCHIVE_URL}?{urlencode(query)}"


def api_call_units(days: int, variables: int, locations: int = 1) -> float:
    """How many of Open-Meteo's rate-limit units a request costs, by the pricing page's rule."""
    if days < 1 or variables < 1 or locations < 1:
        raise ValueError("days, variables and locations must each be at least 1")
    return locations * max(1.0, days / CALL_UNIT_DAYS) * max(1.0, variables / CALL_UNIT_VARIABLES)


def daily_weather_from_archive(payload: dict) -> dict[date, DailyWeather]:
    """Parse one cell's archive response into daily rows. Hourly soil values are averaged per
    day. Any null raises ArchiveGap naming the variable and the day: T0b and T1 saw the four
    variables fully populated under era5_seamless, so a null is a fault to report, not a value to
    fill."""
    if payload.get("error"):
        raise ArchiveGap(f"archive answered with an error: {payload.get('reason', '?')}")
    daily = payload["daily"]
    hourly = payload["hourly"]
    days = [date.fromisoformat(d) for d in daily["time"]]
    hourly_days = [datetime.fromisoformat(t).date() for t in hourly["time"]]
    soil_t: dict[date, list[float]] = {d: [] for d in days}
    soil_m: dict[date, list[float]] = {d: [] for d in days}
    for day, temperature, moisture in zip(
        hourly_days,
        hourly["soil_temperature_0_to_7cm"],
        hourly["soil_moisture_0_to_7cm"],
        strict=True,
    ):
        _require(temperature, "soil_temperature_0_to_7cm", day)
        _require(moisture, "soil_moisture_0_to_7cm", day)
        soil_t[day].append(temperature)
        soil_m[day].append(moisture)
    rows: dict[date, DailyWeather] = {}
    for day, temperature, precipitation in zip(
        days, daily["temperature_2m_mean"], daily["precipitation_sum"], strict=True
    ):
        _require(temperature, "temperature_2m_mean", day)
        _require(precipitation, "precipitation_sum", day)
        if len(soil_t[day]) != 24:
            raise ArchiveGap(f"{len(soil_t[day])} hourly soil values for {day.isoformat()}, not 24")
        rows[day] = DailyWeather(
            day=day,
            temperature_mean_c=temperature,
            precipitation_mm=precipitation,
            soil_temperature_mean_c=sum(soil_t[day]) / 24,
            soil_moisture_mean=sum(soil_m[day]) / 24,
        )
    return rows


def _require(value: float | None, variable: str, day: date) -> None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        raise ArchiveGap(f"{variable} is null on {day.isoformat()}")
