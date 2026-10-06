"""The one filter pipeline for GBIF occurrence records, every step counted (D32, D65, D66).

D32 asked for one module in place of T1's list filters (records/t1_record.py) and T2's R6 stream
(this file before the follow-up task). Every step either pipeline applied is here once, as one
implementation; the two step lists differ only where the documents that fix them differ:

- t1_steps(): T1's calendar design. Inside a T1 box, years 2015 to 2025, not user-obscured,
  coordinate uncertainty at most 1,000 m (T1 dispatch; D33's headline), the date kept as given
  (D97, D98), one record per taxon, cell and day (D27's event key).
- r6_audit_steps(): T2's audit of SPEC.md R6. Not user-obscured, uncertainty at most 250 m (R6),
  the date kept as given (D97, D98), one record per taxon, observer, cell and day (D27's
  observer-duplicate key).

Decided by D65: the user-obscured step is in both lists (T1's SIMPLE_CSV download could not carry
it), the default-date rule is T1's on the parsed date and time, and the record that survives a
duplicate is the one with the lowest gbifID. The duplicate cell is the nearest 0.1 degree point
with exact ties toward +infinity (cells.cell_for; D46, D63, D64); T2's floor is retired (D46).

Records reach the pipeline already typed by records/occurrence.py, whose loader counts the rows it
cannot type (D66). The pipeline reads records and never changes them.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Hashable, Iterable
from dataclasses import dataclass, field
from datetime import time

from forager_forecast.cells import cell_for
from forager_forecast.records.occurrence import Record
from forager_forecast.t1_design import (
    FIRST_YEAR,
    LAST_YEAR,
    MAX_COORDINATE_UNCERTAINTY_M,
    box_of,
)

SOURCE_STAGE = "source"

# SPEC.md R6: "coordinate uncertainty above 250 m" never reaches habitat training.
R6_MAX_COORDINATE_UNCERTAINTY_M = 250.0


# Filter steps. Each returns True to say "this record does not flow on".


def outside_t1_boxes(record: Record) -> bool:
    """Outside both T1 boxes. The download predicate selects the boxes; this re-checks the rows
    received and makes the count visible."""
    return box_of(record.latitude, record.longitude) is None


def outside_t1_years(record: Record) -> bool:
    return not FIRST_YEAR <= record.event_date.year <= LAST_YEAR


def is_user_obscured(record: Record) -> bool:
    """True when the publisher says the coordinates were withheld or generalised.

    On GBIF an obscured iNaturalist record carries informationWithheld "Coordinate uncertainty
    increased to NNNNNm at the request of the observer" and an uncertainty most often of 26 to
    29 km, with values past 67 km (T2 report, spot checks of 2026-09-18; D31). dataGeneralizations
    was empty on every sampled record; it is read anyway because Darwin Core defines it for exactly
    this purpose. Any non-empty text in either counts.
    """
    return bool(record.information_withheld.strip()) or bool(record.data_generalizations.strip())


@dataclass(frozen=True)
class UncertaintyAbove:
    """True when the uncertainty radius is missing or above limit_m. Exactly limit_m passes."""

    limit_m: float

    def __call__(self, record: Record) -> bool:
        value = record.coordinate_uncertainty_m
        return value is None or value > self.limit_m


def drops_no_dated_record(record: Record) -> bool:
    """The date step under D97 and D98: every record the loader could date is kept.

    The owner ruled on D28's final rule in the Forager planner session: "Keep the 1st
    (Recommended)" (Forager RECORD -601; D97), so a date-only record on the 1st is kept like any
    other day, and, after the midnight count (docs/audits/2026-10-06-d28-midnight/, commit
    394c6c1), "Drop the check, keep them (Recommended)" (RECORD -605; D98), so a record stamped
    00:00:00 on the 1st is kept too. Records whose eventDate names no single day never get this
    far: the loader counts them as unloadable (D66). The step stays in both lists, dropping
    nothing, so every run's step counts show the ruling, and so the D28 tools can still swap a
    candidate rule into this position (date_step_position). Rejected: removing the step, which
    would hide the ruling from the counts and leave those tools without a place to put a rule.
    """
    return False


def is_default_date(record: Record) -> bool:
    """The first of a month at 00:00:00, or on the first with no time at all.

    The provisional rule (T1 completion report; D28 kept it provisionally; D65 made it the rule for
    both lists), retired from both lists by D97 and D98 (drops_no_dated_record). Kept as the
    "drop all" candidate rule the D28 tables measured (records/date_quality.py, DROP_ALL).
    """
    if record.event_date.day != 1:
        return False
    return record.event_time is None or record.event_time == time(0, 0, 0)


# Duplicate keys (D27). The cell is the D46/D63 nearest 0.1 degree point.


def event_key(record: Record) -> Hashable:
    """Taxon, cell and day: D27's event key, for T1's modelling tables."""
    cell = cell_for(record.latitude, record.longitude)
    return (record.taxon_key, cell.lat_tenths, cell.lon_tenths, record.event_date)


def observer_key(record: Record) -> Hashable:
    """Taxon, observer, cell and day: D27's observer-duplicate key, for T2's audit counts."""
    cell = cell_for(record.latitude, record.longitude)
    return (
        record.taxon_key,
        record.recorded_by.strip(),
        cell.lat_tenths,
        cell.lon_tenths,
        record.event_date,
    )


@dataclass(frozen=True)
class FilterStep:
    name: str
    drops: Callable[[Record], bool]


@dataclass(frozen=True)
class DuplicateStep:
    """Keeps one record per key: the one with the lowest gbifID (D65)."""

    name: str
    key: Callable[[Record], Hashable]


@dataclass(frozen=True)
class Steps:
    """A step list: filters in order, then the duplicate step, which always runs last."""

    filters: tuple[FilterStep, ...]
    duplicate: DuplicateStep

    def __post_init__(self) -> None:
        names = self.names()
        if len(set(names)) != len(names):
            raise ValueError(f"step names repeat: {names}")

    def names(self) -> tuple[str, ...]:
        return (*(step.name for step in self.filters), self.duplicate.name)


def t1_steps() -> Steps:
    return Steps(
        filters=(
            FilterStep("inside a T1 box", outside_t1_boxes),
            FilterStep("year 2015 to 2025", outside_t1_years),
            FilterStep("not user-obscured", is_user_obscured),
            FilterStep(
                "coordinate uncertainty present and at most 1,000 m",
                UncertaintyAbove(MAX_COORDINATE_UNCERTAINTY_M),
            ),
            FilterStep("date kept as given (D97, D98)", drops_no_dated_record),
        ),
        duplicate=DuplicateStep("one record per taxon, cell and day", event_key),
    )


def r6_audit_steps() -> Steps:
    return Steps(
        filters=(
            FilterStep("user_obscured", is_user_obscured),
            FilterStep("coordinate_uncertainty", UncertaintyAbove(R6_MAX_COORDINATE_UNCERTAINTY_M)),
            FilterStep("date_kept_as_given", drops_no_dated_record),
        ),
        duplicate=DuplicateStep("duplicate_taxon_observer_cell_day", observer_key),
    )


DATE_STEP_RULES: tuple[Callable[[Record], bool], ...] = (drops_no_dated_record, is_default_date)


def date_step_position(steps: Steps) -> int:
    """Where a step list's date step is: the one filter applying the ruled or provisional rule."""
    positions = [i for i, step in enumerate(steps.filters) if step.drops in DATE_STEP_RULES]
    if len(positions) != 1:
        raise ValueError(f"no default-date step to replace (found {len(positions)})")
    return positions[0]


@dataclass
class StepCount:
    step: str
    before: int = 0
    dropped: int = 0

    @property
    def after(self) -> int:
        return self.before - self.dropped


def _digest(key: Hashable) -> bytes:
    # 16 bytes per distinct key rather than the key itself, so 1.4 million keys stay small.
    return hashlib.blake2b(repr(key).encode("utf-8"), digest_size=16).digest()


@dataclass
class Pipeline:
    """Runs a step list over records once and counts what each step drops.

    The filters see each record as it streams in. The duplicate step can only name its survivors
    once every record has been seen, since the lowest gbifID per key is not known before then, so
    run() returns the survivors as a list in gbifID order. on_pass(stage, record) is called with
    "source" for every record, after each filter it clears, and finally with the duplicate step's
    name for each survivor. Read counts after run() returns.
    """

    steps: Steps
    on_pass: Callable[[str, Record], None] | None = None
    counts: list[StepCount] = field(init=False)
    source_count: int = field(init=False, default=0)
    _ran: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.counts = [StepCount(name) for name in self.steps.names()]

    def _pass(self, stage: str, record: Record) -> None:
        if self.on_pass is not None:
            self.on_pass(stage, record)

    def run(self, records: Iterable[Record]) -> list[Record]:
        if self._ran:
            raise RuntimeError("a Pipeline runs once; make a new one for another run")
        self._ran = True
        filter_counts = self.counts[:-1]
        duplicate_count = self.counts[-1]
        kept: dict[bytes, Record] = {}
        for record in records:
            self.source_count += 1
            self._pass(SOURCE_STAGE, record)
            for step, count in zip(self.steps.filters, filter_counts, strict=True):
                count.before += 1
                if step.drops(record):
                    count.dropped += 1
                    break
                self._pass(step.name, record)
            else:
                duplicate_count.before += 1
                key = _digest(self.steps.duplicate.key(record))
                current = kept.get(key)
                if current is None or record.gbif_id < current.gbif_id:
                    kept[key] = record
        survivors = sorted(kept.values(), key=lambda r: r.gbif_id)
        duplicate_count.dropped = duplicate_count.before - len(survivors)
        for record in survivors:
            self._pass(self.steps.duplicate.name, record)
        return survivors
