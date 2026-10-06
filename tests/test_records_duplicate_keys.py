"""D27 in full: both duplicate keys counted over the same records, per list and per region.

The tally hooks on Pipeline.on_pass. Its count for each key must equal what a real Pipeline run with
that key as its duplicate step keeps, overall and by the survivors' regions; the survivor is the
lowest gbifID (D65), so the region is the survivor's.
"""

import dataclasses
from collections import Counter
from datetime import date, time

import pytest

from forager_forecast.records import filters as f
from forager_forecast.records.counts import region_of
from forager_forecast.records.duplicate_keys import D27_KEYS, KeyTally
from forager_forecast.records.occurrence import Record


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


RECORDS = [
    # PNW: one taxon, cell and day seen by two observers, and a second record by one of them.
    rec(gbif_id=10, recorded_by="observer_a"),
    rec(gbif_id=11, recorded_by="observer_b"),
    rec(gbif_id=12, recorded_by="observer_a"),
    # PNW: two records with no observer named, same taxon, cell and day.
    rec(gbif_id=13, taxon_key=1, recorded_by=""),
    rec(gbif_id=14, taxon_key=1, recorded_by=""),
    # East: two observers, two taxa.
    rec(gbif_id=20, latitude=42.0, longitude=-77.0, recorded_by="observer_c"),
    rec(gbif_id=21, latitude=42.0, longitude=-77.0, recorded_by="observer_d"),
    rec(gbif_id=22, latitude=42.0, longitude=-77.0, taxon_key=2, recorded_by="observer_c"),
    # Outside both boxes: kept by the R6 list, dropped by the T1 list's box step.
    rec(gbif_id=30, latitude=35.0, longitude=-90.0, recorded_by="observer_e"),
    rec(gbif_id=31, latitude=35.0, longitude=-90.0, recorded_by="observer_f"),
    # Dropped before the duplicate step by both lists (uncertainty), so never tallied.
    rec(gbif_id=40, coordinate_uncertainty_m=5000.0),
]


def with_key(steps: f.Steps, key) -> f.Steps:
    return f.Steps(filters=steps.filters, duplicate=f.DuplicateStep("oracle", key))


BOTH = pytest.mark.parametrize("make_steps", [f.t1_steps, f.r6_audit_steps], ids=["t1", "r6"])


@BOTH
@pytest.mark.parametrize("name", ["event", "observer"])
def test_each_keys_count_equals_a_real_pipeline_run_with_that_key(make_steps, name):
    steps = make_steps()
    tally = KeyTally.for_steps(steps)
    f.Pipeline(steps, on_pass=tally.add).run(RECORDS)
    oracle = f.Pipeline(with_key(steps, D27_KEYS[name])).run(RECORDS)
    assert tally.survivors(name) == len(oracle)
    assert tally.survivors_by_region(name) == Counter(region_of(r) for r in oracle)


def test_the_two_keys_differ_where_d27_says_they_should():
    steps = f.r6_audit_steps()
    tally = KeyTally.for_steps(steps)
    f.Pipeline(steps, on_pass=tally.add).run(RECORDS)
    assert tally.entered == 10
    assert tally.entered_by_region == Counter({"pnw": 5, "east": 3, "outside_t1_boxes": 2})
    assert tally.survivors("event") == 5
    assert tally.survivors("observer") == 8
    assert tally.survivors_by_region("event") == Counter(
        {"pnw": 2, "east": 2, "outside_t1_boxes": 1}
    )
    assert tally.survivors_by_region("observer") == Counter(
        {"pnw": 3, "east": 3, "outside_t1_boxes": 2}
    )
    assert tally.empty_observer_entered == 2


def test_t1_list_tallies_only_what_reaches_its_duplicate_step():
    steps = f.t1_steps()
    tally = KeyTally.for_steps(steps)
    f.Pipeline(steps, on_pass=tally.add).run(RECORDS)
    assert tally.at_stage == "not a default date (first of month at 00:00:00)"
    assert tally.entered == 8
    assert tally.survivors("event") == 4
    assert tally.survivors("observer") == 6


def test_the_tally_names_the_records_region_of_the_lowest_gbif_id():
    """Two records share an event key across a box edge: the survivor's region is counted."""
    steps = f.r6_audit_steps()
    tally = KeyTally.for_steps(steps)
    # 42.0 is in the East box, 41.96 is not; both are the cell 42.0 at 0.1 degree.
    inside = rec(gbif_id=7, latitude=42.0, longitude=-77.0)
    outside = rec(gbif_id=3, latitude=41.96, longitude=-77.0, recorded_by="observer_z")
    f.Pipeline(steps, on_pass=tally.add).run([inside, outside])
    assert tally.survivors_by_region("event") == Counter({"outside_t1_boxes": 1})
