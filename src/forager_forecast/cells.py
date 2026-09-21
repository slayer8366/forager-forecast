"""Units: the 0.1 degree weather cell and the ISO week (T1 dispatch, "Verify first" item 3).

The weather cell that defines sighting chance is the 0.1 degree cell (D19, D21). A coordinate
maps to the cell whose centre is the nearest 0.1 degree grid point, halves rounded away from
zero. That is the rule Open-Meteo's archive was observed to apply on 2026-09-18: requests at
47.049, -123.049 came back from grid point 47.0, -123.0 and requests at 47.05, -123.05 from
47.1, -123.1 (T1 completion report, "Verify first" item 3). Decimal arithmetic is used so that
the rule is exact at the halves, where float rounding and Python's round() (halves to even)
would both disagree with the API.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

GRID_STEP_DEGREES = Decimal("0.1")


@dataclass(frozen=True, order=True)
class Cell:
    """One 0.1 degree cell, named by its centre in tenths of a degree."""

    lat_tenths: int
    lon_tenths: int

    @property
    def center_latitude(self) -> float:
        return self.lat_tenths / 10

    @property
    def center_longitude(self) -> float:
        return self.lon_tenths / 10

    @property
    def id(self) -> str:
        return f"{self.lat_tenths}_{self.lon_tenths}"


def _tenths(value: float) -> int:
    scaled = Decimal(repr(value)) / GRID_STEP_DEGREES
    return int(scaled.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def cell_for(latitude: float, longitude: float) -> Cell:
    """The 0.1 degree cell whose centre is nearest to the coordinate."""
    if not -90.0 <= latitude <= 90.0:
        raise ValueError(f"latitude {latitude!r} is outside -90 to 90")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError(f"longitude {longitude!r} is outside -180 to 180")
    return Cell(lat_tenths=_tenths(latitude), lon_tenths=_tenths(longitude))


@dataclass(frozen=True, order=True)
class IsoWeek:
    """An ISO 8601 week. Weeks start on Monday; week 1 holds the year's first Thursday."""

    year: int
    week: int

    @property
    def id(self) -> str:
        return f"{self.year}-W{self.week:02d}"

    def monday(self) -> date:
        return date.fromisocalendar(self.year, self.week, 1)


def iso_week_of(day: date) -> IsoWeek:
    calendar = day.isocalendar()
    return IsoWeek(year=calendar.year, week=calendar.week)
