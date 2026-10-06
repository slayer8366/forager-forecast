"""The one filter pipeline (D32, D65, D66): each step, both step lists, and the counting.

Records are built directly as the one Record type; tests/test_records_occurrence.py covers the
loader that builds them from rows, and tests/test_records_counts.py runs rows through both.
"""

import dataclasses
from datetime import date, time

import pytest

from forager_forecast.records import filters as f
from forager_forecast.records.occurrence import Record

OBSCURED_TEXT = "Coordinate uncertainty increased to 26775m at the request of the observer"


def rec(**overrides) -> Record:
    base = Record(
        gbif_id=1,
        taxon_key=5249462,
        genus_key=9623860,
        latitude=47.02,
        longitude=-123.02,
        event_date=date(2024, 9, 14),
        event_time=time(10, 15),
        coordinate_uncertainty_m=8.0,
        recorded_by="observer_a",
    )
    return dataclasses.replace(base, **overrides)


def run(steps: f.Steps, records: list[Record]) -> tuple[f.Pipeline, list[Record]]:
    pipeline = f.Pipeline(steps)
    return pipeline, pipeline.run(records)


def dropped_by(steps: f.Steps, record: Record) -> str | None:
    """The name of the step that drops this record alone, or None when it survives."""
    pipeline, kept = run(steps, [record])
    for count in pipeline.counts:
        if count.dropped:
            return count.step
    assert kept == [record]
    return None


BOTH = pytest.mark.parametrize("steps", [f.t1_steps(), f.r6_audit_steps()], ids=["t1", "r6"])


# Step names and order


def test_t1_step_list_is_the_t1_dispatch_order_with_the_obscured_step_added():
    assert f.t1_steps().names() == (
        "inside a T1 box",
        "year 2015 to 2025",
        "not user-obscured",
        "coordinate uncertainty present and at most 1,000 m",
        "not a default date (first of month at 00:00:00)",
        "one record per taxon, cell and day",
    )


def test_r6_audit_step_list_is_the_t2_dispatch_order_with_the_d44_key_name():
    assert f.r6_audit_steps().names() == (
        "user_obscured",
        "coordinate_uncertainty",
        "default_first_of_month_date",
        "duplicate_taxon_observer_cell_day",
    )


# Box and years (T1 list only)


@pytest.mark.parametrize(
    ("latitude", "longitude", "dropped"),
    [(47.0, -123.0, False), (42.0, -77.0, False), (35.0, -90.0, True), (49.51, -121.0, True)],
)
def test_t1_keeps_only_records_inside_a_box(latitude, longitude, dropped):
    step = dropped_by(f.t1_steps(), rec(latitude=latitude, longitude=longitude))
    assert (step == "inside a T1 box") is dropped


@pytest.mark.parametrize(
    ("year", "dropped"), [(2014, True), (2015, False), (2025, False), (2026, True)]
)
def test_t1_keeps_years_2015_to_2025(year, dropped):
    step = dropped_by(f.t1_steps(), rec(event_date=date(year, 9, 14)))
    assert (step == "year 2015 to 2025") is dropped


def test_r6_audit_has_no_box_or_year_step():
    assert dropped_by(f.r6_audit_steps(), rec(latitude=35.0, longitude=-90.0)) is None
    assert dropped_by(f.r6_audit_steps(), rec(event_date=date(2012, 9, 14))) is None


# User-obscured (both lists, D65)


@BOTH
def test_information_withheld_drops_a_record_even_with_a_small_uncertainty(steps):
    # D65: in both lists. The 23 such records on T2's download had uncertainty of 1,000 m or less,
    # which T1's uncertainty step alone would have let through.
    record = rec(information_withheld=OBSCURED_TEXT, coordinate_uncertainty_m=30.0)
    assert dropped_by(steps, record) == steps.names()[-4]


@BOTH
def test_data_generalizations_drops_a_record(steps):
    record = rec(data_generalizations="coordinates rounded to 0.1 degree")
    assert dropped_by(steps, record) == steps.names()[-4]


@BOTH
def test_blank_withheld_text_is_not_obscured(steps):
    assert dropped_by(steps, rec(information_withheld="   ")) is None


# Coordinate uncertainty: one implementation, the limit each list's document sets


@pytest.mark.parametrize(
    ("uncertainty", "dropped"),
    [(8.0, False), (1000.0, False), (1000.5, True), (5000.0, True), (None, True)],
)
def test_t1_uncertainty_limit_is_1000_m(uncertainty, dropped):
    step = dropped_by(f.t1_steps(), rec(coordinate_uncertainty_m=uncertainty))
    assert (step == "coordinate uncertainty present and at most 1,000 m") is dropped


@pytest.mark.parametrize(
    ("uncertainty", "dropped"),
    [(8.0, False), (250.0, False), (250.5, True), (26775.0, True), (None, True)],
)
def test_r6_uncertainty_limit_is_250_m(uncertainty, dropped):
    step = dropped_by(f.r6_audit_steps(), rec(coordinate_uncertainty_m=uncertainty))
    assert (step == "coordinate_uncertainty") is dropped


# Default first-of-month date: T1's rule on the parsed date and time, both lists (D65)


@BOTH
@pytest.mark.parametrize(
    ("day", "clock", "dropped"),
    [
        (date(2024, 9, 1), None, True),
        (date(2024, 9, 1), time(0, 0), True),
        (date(2024, 9, 1), time(13, 24, 27), False),
        (date(2024, 9, 14), None, False),
        (date(2024, 9, 14), time(0, 0), False),
    ],
)
def test_first_of_month_without_a_real_time_is_dropped(steps, day, clock, dropped):
    step = dropped_by(steps, rec(event_date=day, event_time=clock))
    assert (step == steps.names()[-2]) is dropped


# Duplicates: two keys (D27), the D46/D63 cell, the lowest gbifID survives (D65)


def test_event_key_is_taxon_cell_and_day_without_the_observer():
    _, kept = run(f.t1_steps(), [rec(gbif_id=1), rec(gbif_id=2, recorded_by="observer_b")])
    assert [r.gbif_id for r in kept] == [1]


def test_observer_key_keeps_two_observers_of_one_taxon_cell_and_day():
    _, kept = run(f.r6_audit_steps(), [rec(gbif_id=1), rec(gbif_id=2, recorded_by="observer_b")])
    assert [r.gbif_id for r in kept] == [1, 2]


@BOTH
@pytest.mark.parametrize(
    "change",
    [
        {"taxon_key": 2542160},
        {"latitude": 47.16},
        {"longitude": -122.94},
        {"event_date": date(2024, 9, 15)},
    ],
)
def test_a_different_taxon_cell_or_day_is_kept(steps, change):
    _, kept = run(steps, [rec(gbif_id=1), rec(gbif_id=2, **change)])
    assert len(kept) == 2


@BOTH
def test_the_lowest_gbif_id_survives_whatever_the_input_order(steps):
    records = [rec(gbif_id=30, license="C"), rec(gbif_id=10, license="A"), rec(gbif_id=20)]
    _, forward = run(steps, records)
    _, backward = run(steps, list(reversed(records)))
    assert [r.gbif_id for r in forward] == [10]
    assert forward == backward


@BOTH
def test_duplicate_cell_is_the_nearest_point_not_the_floor(steps):
    # D46 retires T2's floor. 47.08 and 47.12 share the nearest 0.1 degree point, 47.1; the floor
    # put them in 47.0 and 47.1.
    _, kept = run(steps, [rec(gbif_id=1, latitude=47.08), rec(gbif_id=2, latitude=47.12)])
    assert [r.gbif_id for r in kept] == [1]


@BOTH
def test_duplicate_cell_sends_an_exact_longitude_tie_east(steps):
    # D63 and D64: -123.05 goes to -123.0, the same point as -122.98. The floor and the old
    # away-from-zero rule both put it at -123.1.
    _, kept = run(steps, [rec(gbif_id=1, longitude=-123.05), rec(gbif_id=2, longitude=-122.98)])
    assert [r.gbif_id for r in kept] == [1]


# The pipeline


def fixture() -> list[Record]:
    return [
        rec(gbif_id=1),
        rec(gbif_id=2, information_withheld=OBSCURED_TEXT, coordinate_uncertainty_m=26775.0),
        rec(gbif_id=3, coordinate_uncertainty_m=300.0),
        rec(gbif_id=4, coordinate_uncertainty_m=None),
        rec(gbif_id=5, event_date=date(2024, 9, 1), event_time=None),
        rec(gbif_id=6, event_time=time(18, 0)),
        rec(gbif_id=7, recorded_by="observer_b"),
    ]


def test_pipeline_counts_every_step_and_the_counts_chain():
    pipeline, kept = run(f.r6_audit_steps(), fixture())
    assert [r.gbif_id for r in kept] == [1, 7]
    assert pipeline.source_count == 7
    assert [(c.step, c.before, c.dropped) for c in pipeline.counts] == [
        ("user_obscured", 7, 1),
        ("coordinate_uncertainty", 6, 2),
        ("default_first_of_month_date", 4, 1),
        ("duplicate_taxon_observer_cell_day", 3, 1),
    ]
    for earlier, later in zip(pipeline.counts[:-1], pipeline.counts[1:], strict=True):
        assert later.before == earlier.after
    assert pipeline.counts[-1].after == len(kept)


def test_t1_list_over_the_same_records():
    pipeline, kept = run(f.t1_steps(), fixture())
    assert [r.gbif_id for r in kept] == [1]
    assert [c.dropped for c in pipeline.counts] == [0, 0, 1, 1, 1, 3]


def test_a_record_is_counted_under_the_first_step_that_drops_it():
    record = rec(
        information_withheld=OBSCURED_TEXT,
        coordinate_uncertainty_m=26775.0,
        event_date=date(2024, 9, 1),
        event_time=None,
    )
    pipeline, kept = run(f.r6_audit_steps(), [record])
    assert kept == []
    assert [c.dropped for c in pipeline.counts] == [1, 0, 0, 0]


def test_on_pass_sees_source_then_each_cleared_stage_and_the_duplicate_stage_last():
    seen: list[tuple[str, int]] = []
    pipeline = f.Pipeline(f.r6_audit_steps(), on_pass=lambda s, r: seen.append((s, r.gbif_id)))
    pipeline.run([rec(gbif_id=9), rec(gbif_id=3, coordinate_uncertainty_m=300.0), rec(gbif_id=4)])
    assert seen == [
        ("source", 9),
        ("user_obscured", 9),
        ("coordinate_uncertainty", 9),
        ("default_first_of_month_date", 9),
        ("source", 3),
        ("user_obscured", 3),
        ("source", 4),
        ("user_obscured", 4),
        ("coordinate_uncertainty", 4),
        ("default_first_of_month_date", 4),
        # Only once every record is seen is the lowest gbifID per key known.
        ("duplicate_taxon_observer_cell_day", 4),
    ]


def test_survivors_are_the_input_objects_in_gbif_id_order():
    records = [rec(gbif_id=7, recorded_by="b"), rec(gbif_id=2)]
    _, kept = run(f.r6_audit_steps(), records)
    assert [r.gbif_id for r in kept] == [2, 7]
    assert all(any(k is r for r in records) for k in kept)


def test_a_second_pipeline_does_not_remember_the_first():
    assert len(f.Pipeline(f.r6_audit_steps()).run([rec()])) == 1
    assert len(f.Pipeline(f.r6_audit_steps()).run([rec()])) == 1


def test_a_pipeline_runs_once():
    pipeline = f.Pipeline(f.r6_audit_steps())
    pipeline.run([rec()])
    with pytest.raises(RuntimeError):
        pipeline.run([rec()])


def test_repeated_step_names_are_refused():
    with pytest.raises(ValueError):
        f.Steps(
            filters=(f.FilterStep("x", lambda r: False), f.FilterStep("x", lambda r: False)),
            duplicate=f.DuplicateStep("y", f.event_key),
        )
