"""Units: the weather cells on the two climate grids, and the ISO week.

The weather cell that defines sighting chance is the 0.1 degree cell (D19, D21): ERA5-Land, whose
points sit at multiples of 0.1 degree. ERA5 precipitation comes on a 0.25 degree grid whose points
sit at multiples of 0.25 degree. Both grids use longitudes in -180 to 180, as the delivered files
show (D51; docs/audits/2026-09-22-grid-positions-d51-report.md:13, :105).

A coordinate belongs to the nearest grid point (D46). Where it lies exactly halfway between two
points it goes to the one toward +infinity on that axis, north on latitude and east on longitude,
as both sources did at every probed exact tie (D63; grid positions part 2 report). "Exactly
halfway" is read on the decimal value GBIF reports, not on the binary double (D64). Decimal
arithmetic on repr(value), the shortest text that round-trips the float, is what makes the tie
exact; float arithmetic and Python's round() (halves to even) would both miss it.

D64 records one place where this rule and Open-Meteo part: for 47.05, -123.05 the archive returned
-123.1 on 2026-09-18, and the rule gives -123.0.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_FLOOR, Decimal

GRID_STEP_DEGREES = Decimal("0.1")
QUARTER_GRID_STEP_DEGREES = Decimal("0.25")
_HALF = Decimal("0.5")


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


@dataclass(frozen=True, order=True)
class QuarterCell:
    """One 0.25 degree ERA5 cell, named by its centre in quarters of a degree."""

    lat_quarters: int
    lon_quarters: int

    @property
    def center_latitude(self) -> float:
        return self.lat_quarters / 4

    @property
    def center_longitude(self) -> float:
        return self.lon_quarters / 4

    @property
    def id(self) -> str:
        return f"q{self.lat_quarters}_{self.lon_quarters}"


def _nearest_index(value: float, step: Decimal) -> int:
    """The index of the nearest multiple of step, exact halves toward +infinity (D63, D64)."""
    scaled = Decimal(repr(value)) / step
    return int((scaled + _HALF).to_integral_value(rounding=ROUND_FLOOR))


def _check_range(latitude: float, longitude: float) -> None:
    if not -90.0 <= latitude <= 90.0:
        raise ValueError(f"latitude {latitude!r} is outside -90 to 90")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError(f"longitude {longitude!r} is outside -180 to 180")


def cell_for(latitude: float, longitude: float) -> Cell:
    """The 0.1 degree ERA5-Land cell whose centre is nearest to the coordinate."""
    _check_range(latitude, longitude)
    return Cell(
        lat_tenths=_nearest_index(latitude, GRID_STEP_DEGREES),
        lon_tenths=_nearest_index(longitude, GRID_STEP_DEGREES),
    )


def quarter_cell_for(latitude: float, longitude: float) -> QuarterCell:
    """The 0.25 degree ERA5 cell whose centre is nearest to the coordinate."""
    _check_range(latitude, longitude)
    return QuarterCell(
        lat_quarters=_nearest_index(latitude, QUARTER_GRID_STEP_DEGREES),
        lon_quarters=_nearest_index(longitude, QUARTER_GRID_STEP_DEGREES),
    )


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
