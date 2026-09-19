"""The dispatch's second test: a positive cell-week never also appears as a negative."""

from datetime import date, time

from forager_forecast.cell_weeks import (
    CellWeek,
    cell_week_of,
    label_cell_weeks,
    negative_units,
    positive_units,
)
from forager_forecast.cells import Cell, IsoWeek
from forager_forecast.records import Record
from forager_forecast.t1_design import CANTHARELLUS_GENUS_KEY

OTHER_GENUS = 2534945  # any other fungal genus key; only inequality matters here


def record(gbif_id, genus, lat, lon, day):
    return Record(
        gbif_id=gbif_id,
        taxon_key=genus * 10 + 1,
        genus_key=genus,
        latitude=lat,
        longitude=lon,
        event_date=day,
        event_time=time(12, 0),
        coordinate_uncertainty_m=25.0,
    )


# A tiny synthetic fixture. Cell 47.0,-123.0 in ISO week 2024-W36 gets both a Cantharellus record
# and an unrelated one, so that a naive design that emits "one row per record" would put the
# same cell-week in both classes. The same cell a week later has only an unrelated record. A
# second cell in W36 has only a Cantharellus record. A third cell has records in two weeks.
FIXTURE = [
    record(1, CANTHARELLUS_GENUS_KEY, 47.0, -123.0, date(2024, 9, 3)),
    record(2, OTHER_GENUS, 47.04, -123.04, date(2024, 9, 5)),
    record(3, OTHER_GENUS, 47.0, -123.0, date(2024, 9, 12)),
    record(4, CANTHARELLUS_GENUS_KEY, 42.0, -77.0, date(2024, 9, 2)),
    record(5, OTHER_GENUS, 46.5, -122.5, date(2024, 9, 8)),
    record(6, OTHER_GENUS, 46.5, -122.5, date(2024, 9, 9)),
    record(7, CANTHARELLUS_GENUS_KEY, 46.5, -122.5, date(2024, 9, 9)),
]


def test_a_positive_cell_week_never_also_appears_as_a_negative():
    labelled = label_cell_weeks(FIXTURE, CANTHARELLUS_GENUS_KEY)
    positives = positive_units(labelled)
    negatives = negative_units(labelled)
    assert positives, "the fixture has positives"
    assert negatives, "the fixture has negatives"
    assert positives.isdisjoint(negatives), sorted(u.id for u in positives & negatives)
    # and every eligible unit is emitted exactly once
    units = [row.unit for row in labelled]
    assert len(units) == len(set(units))
    assert set(units) == {cell_week_of(r) for r in FIXTURE}


def test_labels_and_counts_match_the_fixture():
    labelled = {row.unit: row for row in label_cell_weeks(FIXTURE, CANTHARELLUS_GENUS_KEY)}
    w36 = IsoWeek(2024, 36)
    w37 = IsoWeek(2024, 37)
    mixed = labelled[CellWeek(Cell(470, -1230), w36)]
    assert (mixed.positive, mixed.record_count, mixed.target_count) == (True, 2, 1)
    unrelated_only = labelled[CellWeek(Cell(470, -1230), w37)]
    assert (unrelated_only.positive, unrelated_only.record_count, unrelated_only.target_count) == (
        False,
        1,
        0,
    )
    target_only = labelled[CellWeek(Cell(420, -770), w36)]
    assert (target_only.positive, target_only.record_count, target_only.target_count) == (
        True,
        1,
        1,
    )
    # 2024-09-08 is a Sunday (W36); the 9th is Monday of W37.
    assert labelled[CellWeek(Cell(465, -1225), w36)].positive is False
    assert labelled[CellWeek(Cell(465, -1225), w37)].positive is True
    assert len(labelled) == 5


def test_no_records_means_no_units():
    assert label_cell_weeks([], CANTHARELLUS_GENUS_KEY) == []
