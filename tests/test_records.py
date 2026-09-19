from datetime import date, time

from forager_forecast.records import (
    Record,
    apply_t1_filters,
    drop_default_dates,
    drop_uncertain_coordinates,
    is_default_date,
    keep_inside_boxes,
    keep_one_per_taxon_cell_day,
    keep_years,
)
from forager_forecast.t1_design import CANTHARELLUS_GENUS_KEY


def record(
    gbif_id, lat=47.0, lon=-123.0, day=date(2020, 9, 15), at=time(10, 30), unc=30.0, taxon=1
):
    return Record(
        gbif_id=gbif_id,
        taxon_key=taxon,
        genus_key=CANTHARELLUS_GENUS_KEY,
        latitude=lat,
        longitude=lon,
        event_date=day,
        event_time=at,
        coordinate_uncertainty_m=unc,
    )


def test_box_filter_keeps_both_boxes_and_drops_the_rest():
    inside_pnw = record(1, 47.0, -123.0)
    inside_east = record(2, 42.0, -77.0)
    between = record(3, 44.0, -100.0)
    on_edge = record(4, 42.0, -125.0)
    assert keep_inside_boxes([inside_pnw, inside_east, between, on_edge]) == [
        inside_pnw,
        inside_east,
        on_edge,
    ]


def test_year_filter_is_inclusive_at_both_ends():
    kept = keep_years(
        [
            record(1, day=date(2014, 12, 31)),
            record(2, day=date(2015, 1, 1)),
            record(3, day=date(2025, 12, 31)),
            record(4, day=date(2026, 1, 1)),
        ]
    )
    assert [r.gbif_id for r in kept] == [2, 3]


def test_uncertainty_filter_drops_missing_and_above_1000_m_and_keeps_1000_m():
    kept = drop_uncertain_coordinates(
        [record(1, unc=None), record(2, unc=1000.1), record(3, unc=1000.0), record(4, unc=28000.0)]
    )
    assert [r.gbif_id for r in kept] == [3]


def test_default_date_rule():
    assert is_default_date(date(2020, 9, 1), time(0, 0, 0))
    assert is_default_date(date(2020, 9, 1), None)
    assert not is_default_date(date(2020, 9, 1), time(0, 0, 1))
    assert not is_default_date(date(2020, 9, 2), time(0, 0, 0))
    assert not is_default_date(date(2020, 9, 2), None)


def test_default_date_filter():
    kept = drop_default_dates([record(1, day=date(2020, 9, 1), at=time(0, 0)), record(2)])
    assert [r.gbif_id for r in kept] == [2]


def test_one_record_per_taxon_cell_day_keeps_the_lowest_id_regardless_of_order():
    same_cell_a = record(20, 47.04, -123.04)
    same_cell_b = record(10, 46.96, -122.96)
    other_cell = record(30, 47.1, -123.0)
    other_day = record(40, day=date(2020, 9, 16))
    other_taxon = record(50, taxon=2)
    kept = keep_one_per_taxon_cell_day(
        [same_cell_a, other_cell, same_cell_b, other_day, other_taxon]
    )
    assert [r.gbif_id for r in kept] == [10, 30, 40, 50]


def test_apply_t1_filters_counts_every_step():
    records = [
        record(1),
        record(2, lat=44.0, lon=-100.0),
        record(3, day=date(2014, 6, 1)),
        record(4, unc=None),
        record(5, day=date(2020, 9, 1), at=time(0, 0)),
        record(6, lat=47.04, lon=-123.04),
    ]
    result = apply_t1_filters(records)
    assert [(s.name, s.before, s.after) for s in result.steps] == [
        ("inside a T1 box", 6, 5),
        ("year 2015 to 2025", 5, 4),
        ("coordinate uncertainty present and at most 1,000 m", 4, 3),
        ("not a default date (first of month at 00:00:00)", 3, 2),
        ("one record per taxon, cell and day", 2, 1),
    ]
    assert [r.gbif_id for r in result.records] == [1]
    assert sum(s.dropped for s in result.steps) == 5
