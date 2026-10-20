"""T8's units: T1's own cell-weeks, exactly (plan section 3; D133 (1)), and the lichen outcome.

T1's units are read from the npz T1 wrote with its held-out calendar predictions
(`fits/primary_t1_1000m_calendar.npz`: unit, cell, year, y, p, land_point; scripts/pnw_t1_fit.py).
A unit id is "<cell id>@<Monday>", the cell id "<lat tenths>_<lon tenths>", and `year` the ISO year
(the fold year).

The run refuses to start if its units or outcomes differ from T1's by one (`check_same_units`):
the units recounted from D26's zip under T1's steps must hold every T1 unit with the same outcome,
and may hold more only by exactly the number T1 dropped for want of weather (sea cells).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np

from forager_forecast.cell_weeks import cell_week_of, label_cell_weeks
from forager_forecast.cells import Cell, iso_week_of
from forager_forecast.effort import observer_of
from forager_forecast.records.occurrence import Record
from forager_forecast.t8.design import LICHEN_CLASS_KEY


class UnitsDiffer(RuntimeError):
    """T8's units or outcomes are not T1's."""


@dataclass(frozen=True)
class T1Units:
    unit: np.ndarray  # str
    cell: np.ndarray  # str, cell id
    year: np.ndarray  # int, ISO year
    y: np.ndarray  # float 0/1, Cantharellus positive
    p: np.ndarray  # float, T1's held-out calendar prediction
    land_point: np.ndarray  # str, "own" or "neighbour"

    def __len__(self) -> int:
        return len(self.unit)

    @property
    def cells(self) -> list[Cell]:
        return [parse_cell(c) for c in self.cell]

    @property
    def mondays(self) -> list[date]:
        return [date.fromisoformat(u.split("@", 1)[1]) for u in self.unit]

    @property
    def iso_weeks(self) -> list[int]:
        return [iso_week_of(d).week for d in self.mondays]


def parse_cell(cell_id: str) -> Cell:
    lat, lon = cell_id.split("_")
    return Cell(int(lat), int(lon))


def unit_id(cell: Cell, monday: date) -> str:
    return f"{cell.id}@{monday.isoformat()}"


def read_t1_units(path: Path) -> T1Units:
    z = np.load(path, allow_pickle=False)
    units = T1Units(
        unit=z["unit"].astype(str),
        cell=z["cell"].astype(str),
        year=z["year"].astype(int),
        y=z["y"].astype(float),
        p=z["p"].astype(float),
        land_point=z["land_point"].astype(str),
    )
    validate_t1_units(units)
    return units


def validate_t1_units(units: T1Units) -> None:
    """The npz is internally consistent: ids unique, cell and ISO year agree with the id, outcomes
    0 or 1, predictions finite probabilities."""
    n = len(units)
    for name in ("cell", "year", "y", "p", "land_point"):
        if len(getattr(units, name)) != n:
            raise UnitsDiffer(f"T1's {name} has {len(getattr(units, name))} entries for {n} units")
    if len(set(units.unit.tolist())) != n:
        raise UnitsDiffer("T1's unit ids repeat")
    for u, c, y in zip(units.unit, units.cell, units.year, strict=True):
        cell_id, monday = u.split("@", 1)
        d = date.fromisoformat(monday)
        if cell_id != c or d.weekday() != 0 or iso_week_of(d).year != y:
            raise UnitsDiffer(f"unit {u} disagrees with its cell {c} or year {y}")
    if not np.isin(units.y, (0.0, 1.0)).all():
        raise UnitsDiffer("T1's outcomes are not all 0 or 1")
    if not (np.isfinite(units.p).all() and (units.p > 0).all() and (units.p < 1).all()):
        raise UnitsDiffer("T1's predictions are not all probabilities strictly inside 0 to 1")


def check_same_units(
    t1: T1Units, recounted: dict[str, float], expected_extra: int, expected_total: int
) -> None:
    """Refuses unless T1's units and outcomes are reproduced exactly, with extras only by the
    number T1 dropped for want of weather."""
    if len(t1) != expected_total:
        raise UnitsDiffer(f"T1's file holds {len(t1)} units, expected {expected_total}")
    missing = [u for u in t1.unit if u not in recounted]
    differ = [u for u, y in zip(t1.unit, t1.y, strict=True) if u in recounted and recounted[u] != y]
    extra = len(set(recounted) - set(t1.unit.tolist()))
    problems = []
    if missing:
        problems.append(f"{len(missing)} T1 units not recounted (first {missing[0]})")
    if differ:
        problems.append(f"{len(differ)} outcomes differ (first {differ[0]})")
    if extra != expected_extra:
        problems.append(f"{extra} recounted units beyond T1's, expected {expected_extra}")
    if problems:
        raise UnitsDiffer("; ".join(problems))


@dataclass(frozen=True)
class LichenAttach:
    positive: np.ndarray  # float 0/1 per T1 unit
    outings: np.ndarray  # int: distinct (observer, day) among the unit's lichen records
    records: np.ndarray  # int: lichen records in the unit
    outside_units: int  # lichen records in no T1 unit (sea units, or outside T1's weeks)


def attach_lichens(t1: T1Units, survivors: Iterable[Record]) -> LichenAttach:
    """The lichen outcome per T1 unit (design.PENDING L-outcome, proposed reading): a unit is
    positive if a record of class 180 survived T1's steps in it."""
    index = {u: i for i, u in enumerate(t1.unit.tolist())}
    records = np.zeros(len(t1), dtype=np.int64)
    outings: dict[int, set] = defaultdict(set)
    outside = 0
    for r in survivors:
        if r.class_key != LICHEN_CLASS_KEY:
            continue
        cw = cell_week_of(r)
        i = index.get(unit_id(cw.cell, cw.week.monday()))
        if i is None:
            outside += 1
            continue
        records[i] += 1
        outings[i].add((observer_of(r), r.event_date))
    n_outings = np.zeros(len(t1), dtype=np.int64)
    for i, s in outings.items():
        n_outings[i] = len(s)
    return LichenAttach((records > 0).astype(float), n_outings, records, outside)


# T1's primary design (scripts/pnw_t1_fit.py `primary_units`): only ISO weeks wholly inside these.
FIRST_DAY = date(2015, 1, 1)
LAST_DAY = date(2025, 12, 31)


def recount_units(survivors: Iterable[Record], target_genus_key: int) -> dict[str, float]:
    """T1's eligible cell-weeks and their outcomes, recounted from T1's survivors, as
    scripts/pnw_t1_fit.py builds them, before T1's weather drop."""
    out: dict[str, float] = {}
    for row in label_cell_weeks(survivors, target_genus_key):
        monday = row.unit.week.monday()
        if monday >= FIRST_DAY and date.fromordinal(monday.toordinal() + 6) <= LAST_DAY:
            out[unit_id(row.unit.cell, monday)] = 1.0 if row.positive else 0.0
    return out
