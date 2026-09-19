"""Occurrence records and the T1 filters (dispatch, "Then build", "Filters").

Each filter is its own function that takes a sequence and returns a list, so the count before
and after every step can be reported, as "Verify first" item 1 asks. Nothing here reads a file:
the GBIF download that would feed this has not been requested (T1 completion report).
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, time

from forager_forecast.cells import cell_for
from forager_forecast.t1_design import (
    FIRST_YEAR,
    LAST_YEAR,
    MAX_COORDINATE_UNCERTAINTY_M,
    box_of,
)


@dataclass(frozen=True)
class Record:
    """One occurrence, as the fields T1 needs from a GBIF download row."""

    gbif_id: int
    taxon_key: int
    genus_key: int | None
    latitude: float
    longitude: float
    event_date: date
    event_time: time | None
    coordinate_uncertainty_m: float | None


@dataclass(frozen=True)
class FilterStep:
    name: str
    before: int
    after: int

    @property
    def dropped(self) -> int:
        return self.before - self.after


@dataclass(frozen=True)
class Filtered:
    records: tuple[Record, ...]
    steps: tuple[FilterStep, ...]


def keep_inside_boxes(records: Iterable[Record]) -> list[Record]:
    """Records inside one of the T1 boxes. The download predicate selects the same boxes; this
    step re-checks it on the rows received and makes the count visible."""
    return [r for r in records if box_of(r.latitude, r.longitude) is not None]


def keep_years(records: Iterable[Record]) -> list[Record]:
    return [r for r in records if FIRST_YEAR <= r.event_date.year <= LAST_YEAR]


def drop_uncertain_coordinates(records: Iterable[Record]) -> list[Record]:
    """Drop coordinate uncertainty above 1,000 m or missing. Obscured iNaturalist points carry
    an uncertainty of tens of kilometres, so this removes them too (dispatch, "Filters")."""
    return [
        r
        for r in records
        if r.coordinate_uncertainty_m is not None
        and r.coordinate_uncertainty_m <= MAX_COORDINATE_UNCERTAINTY_M
    ]


def is_default_date(event_date: date, event_time: time | None) -> bool:
    """The first of a month at 00:00:00. A record whose date carries no time at all is treated
    the same way, because a date-only value on the first of a month is what a defaulted date
    looks like once the clock part has been dropped (decision recorded in the T1 completion
    report; the dispatch names only "first of month at 00:00:00")."""
    if event_date.day != 1:
        return False
    return event_time is None or event_time == time(0, 0, 0)


def drop_default_dates(records: Iterable[Record]) -> list[Record]:
    return [r for r in records if not is_default_date(r.event_date, r.event_time)]


def keep_one_per_taxon_cell_day(records: Iterable[Record]) -> list[Record]:
    """Keep one record per taxon, cell and day: the one with the lowest gbif_id, so the result
    does not depend on input order."""
    kept: dict[tuple[int, int, int, date], Record] = {}
    for record in records:
        cell = cell_for(record.latitude, record.longitude)
        key = (record.taxon_key, cell.lat_tenths, cell.lon_tenths, record.event_date)
        current = kept.get(key)
        if current is None or record.gbif_id < current.gbif_id:
            kept[key] = record
    return sorted(kept.values(), key=lambda r: r.gbif_id)


def apply_t1_filters(records: Sequence[Record]) -> Filtered:
    """The dispatch's filters, in order, with a count after each."""
    steps: list[FilterStep] = []
    current = list(records)
    for name, step in (
        ("inside a T1 box", keep_inside_boxes),
        ("year 2015 to 2025", keep_years),
        ("coordinate uncertainty present and at most 1,000 m", drop_uncertain_coordinates),
        ("not a default date (first of month at 00:00:00)", drop_default_dates),
        ("one record per taxon, cell and day", keep_one_per_taxon_cell_day),
    ):
        before = len(current)
        current = step(current)
        steps.append(FilterStep(name=name, before=before, after=len(current)))
    return Filtered(records=tuple(current), steps=tuple(steps))
