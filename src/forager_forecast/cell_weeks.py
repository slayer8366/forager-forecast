"""The primary design's unit and label (dispatch, "Primary design").

Unit: weather cell x ISO week. Eligible: cell-weeks with at least one fungal record of any
kind. Positive: eligible, with at least one record of the target group. Negative: eligible, with
none. This matches the fixed meaning of sighting chance (START_HERE.md, Fixed terms; D12, D13).

Each eligible cell-week is emitted exactly once, with one label, so a unit can never be both a
positive and a negative. tests/test_cell_weeks.py holds the test the dispatch asks for.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from forager_forecast.cells import Cell, IsoWeek, cell_for, iso_week_of
from forager_forecast.records.t1_record import Record


@dataclass(frozen=True, order=True)
class CellWeek:
    cell: Cell
    week: IsoWeek

    @property
    def id(self) -> str:
        return f"{self.cell.id}@{self.week.id}"


@dataclass(frozen=True)
class LabelledCellWeek:
    unit: CellWeek
    positive: bool
    record_count: int
    target_count: int


def cell_week_of(record: Record) -> CellWeek:
    return CellWeek(
        cell=cell_for(record.latitude, record.longitude),
        week=iso_week_of(record.event_date),
    )


def label_cell_weeks(records: Iterable[Record], target_genus_key: int) -> list[LabelledCellWeek]:
    """One row per eligible cell-week, sorted, labelled positive if any record in it belongs to
    the target genus."""
    record_counts: dict[CellWeek, int] = {}
    target_counts: dict[CellWeek, int] = {}
    for record in records:
        unit = cell_week_of(record)
        record_counts[unit] = record_counts.get(unit, 0) + 1
        if record.genus_key == target_genus_key:
            target_counts[unit] = target_counts.get(unit, 0) + 1
    return [
        LabelledCellWeek(
            unit=unit,
            positive=target_counts.get(unit, 0) > 0,
            record_count=record_counts[unit],
            target_count=target_counts.get(unit, 0),
        )
        for unit in sorted(record_counts)
    ]


def positive_units(labelled: Iterable[LabelledCellWeek]) -> set[CellWeek]:
    return {row.unit for row in labelled if row.positive}


def negative_units(labelled: Iterable[LabelledCellWeek]) -> set[CellWeek]:
    return {row.unit for row in labelled if not row.positive}
