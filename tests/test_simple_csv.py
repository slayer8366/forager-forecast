"""The SIMPLE_CSV row loader, on synthetic rows shaped like GBIF's documented format."""

import io
from datetime import date, time

import pytest

from forager_forecast.records import Record
from forager_forecast.simple_csv import (
    COLUMNS_READ,
    UnloadableRow,
    is_cantharellus,
    missing_columns,
    parse_event,
    read_rows,
    record_from_row,
)
from forager_forecast.t1_design import CANTHARELLUS_GENUS_KEY


def row(**overrides: str) -> dict[str, str]:
    base = {
        "gbifID": "5006980885",
        "datasetKey": "50c9509d-22c7-4a22-a47d-8c48425ef4a7",
        "kingdom": "Fungi",
        "genus": "Cantharellus",
        "taxonKey": "8290244",
        "decimalLatitude": "47.8184800926",
        "decimalLongitude": "-122.2805825552",
        "coordinateUncertaintyInMeters": "26775",
        "eventDate": "2025-10-04T11:52:00",
        "license": "CC_BY_NC_4_0",
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2020-09-15", (date(2020, 9, 15), None)),
        ("2020-09-15T10:30:00", (date(2020, 9, 15), time(10, 30, 0))),
        ("2020-09-15T10:30", (date(2020, 9, 15), time(10, 30, 0))),
        ("2020-09-15T10:30:00Z", (date(2020, 9, 15), time(10, 30, 0))),
        ("2020-09-15T10:30:00-07:00", (date(2020, 9, 15), time(10, 30, 0))),
        ("2020-09-01T00:00:00", (date(2020, 9, 1), time(0, 0, 0))),
        ("2020-09-15T10:00:00/2020-09-15T12:00:00", (date(2020, 9, 15), time(10, 0, 0))),
        ("2020-09-15/2020-09-15", (date(2020, 9, 15), None)),
    ],
)
def test_parse_event_reads_days_clock_times_and_same_day_ranges(text, expected):
    assert parse_event(text) == expected


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("", "eventDate empty"),
        ("2020-09", "eventDate does not name a calendar day"),
        ("2020", "eventDate does not name a calendar day"),
        ("2020-09-15/2020-09-16", "eventDate spans more than one day"),
        ("2020-09-01/2020-09-30", "eventDate spans more than one day"),
        ("2020-09-15T25:00:00", "eventDate clock time is not readable"),
        ("2020-09-15/2020-09-16/2020-09-17", "eventDate is not a day or a range"),
    ],
)
def test_parse_event_refuses_anything_that_is_not_one_day(text, reason):
    with pytest.raises(UnloadableRow) as excinfo:
        parse_event(text)
    assert excinfo.value.reason == reason


def test_parse_event_never_returns_an_aware_time():
    assert parse_event("2020-09-01T00:00:00+02:00")[1] == time(0, 0, 0)


def test_record_from_row_reads_every_field():
    record = record_from_row(row())
    assert record == Record(
        gbif_id=5006980885,
        taxon_key=8290244,
        genus_key=CANTHARELLUS_GENUS_KEY,
        latitude=47.8184800926,
        longitude=-122.2805825552,
        event_date=date(2025, 10, 4),
        event_time=time(11, 52, 0),
        coordinate_uncertainty_m=26775.0,
        license="CC_BY_NC_4_0",
    )
    assert is_cantharellus(record)


def test_genus_key_is_filled_only_for_fungal_cantharellus():
    assert record_from_row(row(genus="Laetiporus")).genus_key is None
    assert record_from_row(row(genus="")).genus_key is None
    assert record_from_row(row(kingdom="Animalia")).genus_key is None
    assert not is_cantharellus(record_from_row(row(genus="Craterellus")))


def test_missing_uncertainty_and_empty_license_load_as_none_and_empty():
    record = record_from_row(row(coordinateUncertaintyInMeters="", license=""))
    assert record.coordinate_uncertainty_m is None
    assert record.license == ""
    assert (
        record_from_row(row(coordinateUncertaintyInMeters="NaN")).coordinate_uncertainty_m is None
    )


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"gbifID": ""}, "gbifID not an integer"),
        ({"taxonKey": ""}, "taxonKey empty or not an integer"),
        ({"decimalLatitude": ""}, "coordinates missing or not numbers"),
        ({"decimalLongitude": "nan"}, "coordinates missing or not numbers"),
        ({"eventDate": "2025-10"}, "eventDate does not name a calendar day"),
        ({"eventDate": "2025-10-04/2025-10-05"}, "eventDate spans more than one day"),
    ],
)
def test_unloadable_rows_name_their_reason_and_the_row(overrides, reason):
    with pytest.raises(UnloadableRow) as excinfo:
        record_from_row(row(**overrides))
    assert excinfo.value.reason == reason
    if "gbifID" not in overrides:
        assert excinfo.value.gbif_id == "5006980885"


def test_read_rows_is_tab_separated_and_ignores_quote_characters():
    header = "\t".join(COLUMNS_READ)
    values = row()
    values["genus"] = 'Cantharellus "chanterelle'
    line = "\t".join(values[column] for column in COLUMNS_READ)
    rows = list(read_rows(io.StringIO(f"{header}\n{line}\n")))
    assert len(rows) == 1
    assert rows[0]["genus"] == 'Cantharellus "chanterelle'
    assert rows[0]["license"] == "CC_BY_NC_4_0"


def test_missing_columns_names_what_the_file_lacks():
    assert missing_columns(list(COLUMNS_READ)) == []
    assert missing_columns(["gbifID", "kingdom"]) == [
        column for column in COLUMNS_READ if column not in ("gbifID", "kingdom")
    ]
    assert missing_columns(None) == list(COLUMNS_READ)
