"""apply_t1_filters_observed sees the source and every step, and agrees with apply_t1_filters."""

from datetime import date, time

from forager_forecast.records.t1_record import (
    SOURCE_STAGE,
    T1_FILTER_STEPS,
    Record,
    apply_t1_filters,
    apply_t1_filters_observed,
)
from forager_forecast.t1_design import CANTHARELLUS_GENUS_KEY


def record(gbif_id, lat=47.0, lon=-123.0, day=date(2020, 9, 15), at=time(10, 30), unc=30.0):
    return Record(
        gbif_id=gbif_id,
        taxon_key=1,
        genus_key=CANTHARELLUS_GENUS_KEY,
        latitude=lat,
        longitude=lon,
        event_date=day,
        event_time=at,
        coordinate_uncertainty_m=unc,
    )


def fixture():
    return [
        record(1),
        record(2, lat=44.0, lon=-100.0),  # outside both boxes
        record(3, day=date(2014, 6, 1)),  # before 2015
        record(4, unc=5000.0),  # too uncertain
        record(5, day=date(2020, 9, 1), at=time(0, 0)),  # default date
        record(6),  # duplicate of 1: same taxon, cell and day
        record(7, day=date(2020, 9, 16)),
    ]


def test_observe_is_called_for_the_source_and_once_per_step_with_the_survivors():
    seen = []
    filtered = apply_t1_filters_observed(
        fixture(), lambda stage, rows: seen.append((stage, len(rows)))
    )
    assert [stage for stage, _ in seen] == [SOURCE_STAGE, *[name for name, _ in T1_FILTER_STEPS]]
    assert seen == [
        (SOURCE_STAGE, 7),
        ("inside a T1 box", 6),
        ("year 2015 to 2025", 5),
        ("coordinate uncertainty present and at most 1,000 m", 4),
        ("not a default date (first of month at 00:00:00)", 3),
        ("one record per taxon, cell and day", 2),
    ]
    assert [step.after for step in filtered.steps] == [n for _, n in seen[1:]]
    assert [r.gbif_id for r in filtered.records] == [1, 7]


def test_the_observed_run_and_the_plain_run_agree():
    assert apply_t1_filters_observed(fixture(), lambda *_: None) == apply_t1_filters(fixture())
