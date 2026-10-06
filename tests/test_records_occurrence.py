"""The one Record type and its DWCA row loader (D42, D66).

Rows are synthetic and shaped like GBIF Darwin Core Archive occurrence.txt rows: Darwin Core field
names, text values.
"""

import io
from datetime import date, time

import pytest

from forager_forecast.records import occurrence as o


def row(**overrides: str) -> dict[str, str]:
    base = {
        "gbifID": "11",
        "acceptedTaxonKey": "5249462",
        "genusKey": "9623860",
        "decimalLatitude": "47.05",
        "decimalLongitude": "-123.05",
        "coordinateUncertaintyInMeters": "8",
        "eventDate": "2024-09-14T10:15:00",
        "license": "CC_BY_NC_4_0",
        "datasetKey": "50c9509d-22c7-4a22-a47d-8c48425ef4a7",
        "recordedBy": "observer_a",
        "informationWithheld": "",
        "dataGeneralizations": "",
    }
    base.update(overrides)
    return base


def test_record_from_row_reads_every_field():
    assert o.record_from_row(row()) == o.Record(
        gbif_id=11,
        taxon_key=5249462,
        genus_key=9623860,
        latitude=47.05,
        longitude=-123.05,
        event_date=date(2024, 9, 14),
        event_time=time(10, 15),
        coordinate_uncertainty_m=8.0,
        license="CC_BY_NC_4_0",
        dataset_key="50c9509d-22c7-4a22-a47d-8c48425ef4a7",
        recorded_by="observer_a",
        information_withheld="",
        data_generalizations="",
    )


def test_taxon_is_the_accepted_taxon_key_not_the_taxon_key():
    # D27: "the record's accepted GBIF taxon key". T1's first loader read taxonKey.
    record = o.record_from_row(row(taxonKey="9999999", acceptedTaxonKey="5249462"))
    assert record.taxon_key == 5249462


def test_optional_fields_load_as_absent():
    record = o.record_from_row(row(genusKey="", coordinateUncertaintyInMeters="", license=""))
    assert record.genus_key is None
    assert record.coordinate_uncertainty_m is None
    assert record.license == ""
    assert (
        o.record_from_row(row(coordinateUncertaintyInMeters="NaN")).coordinate_uncertainty_m is None
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2024-09-14", (date(2024, 9, 14), None)),
        ("2024-09-14T10:30:00", (date(2024, 9, 14), time(10, 30))),
        ("2024-09-14T10:30:00Z", (date(2024, 9, 14), time(10, 30))),
        ("2024-09-01T00:00:00-08:00", (date(2024, 9, 1), time(0, 0))),
        ("2024-09-01T00:00", (date(2024, 9, 1), time(0, 0))),
        ("2024-09-01/2024-09-01", (date(2024, 9, 1), None)),
        ("2024-09-14T08:00/2024-09-14T17:00", (date(2024, 9, 14), time(8, 0))),
    ],
)
def test_parse_event_reads_days_clock_times_and_same_day_ranges(text, expected):
    assert o.parse_event(text) == expected


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"eventDate": ""}, "eventDate empty"),
        ({"eventDate": "2024-09"}, "eventDate does not name a calendar day"),
        ({"eventDate": "2024"}, "eventDate does not name a calendar day"),
        ({"eventDate": "2024-09-01/2024-09-30"}, "eventDate spans more than one day"),
        ({"eventDate": "2024-09-14T25:00:00"}, "eventDate clock time is not readable"),
        ({"decimalLatitude": ""}, "coordinates missing or not numbers"),
        ({"decimalLongitude": "west"}, "coordinates missing or not numbers"),
        ({"decimalLatitude": "95.0"}, "coordinates out of range"),
        ({"decimalLongitude": "-181.0"}, "coordinates out of range"),
        ({"gbifID": "x"}, "gbifID not an integer"),
        ({"acceptedTaxonKey": ""}, "acceptedTaxonKey empty or not an integer"),
    ],
)
def test_a_row_that_cannot_be_typed_is_refused_with_its_reason(overrides, reason):
    with pytest.raises(o.UnloadableRow) as excinfo:
        o.record_from_row(row(**overrides))
    assert excinfo.value.reason == reason


def test_loader_counts_what_it_cannot_load_and_yields_the_rest():
    # D66: rows that cannot be typed go to a counted stage. A row with no coordinates is one of
    # them, so it can no longer share a duplicate key with other such rows.
    rows = [
        row(gbifID="1"),
        row(gbifID="2", eventDate="2024-09"),
        row(gbifID="3", decimalLatitude="", decimalLongitude=""),
        row(gbifID="4", decimalLatitude="", decimalLongitude=""),
        row(gbifID="5"),
    ]
    loader = o.OccurrenceLoader()
    loaded = list(loader.load(rows))
    assert [r.gbif_id for r in loaded] == [1, 5]
    assert loader.rows_read == 5
    assert dict(loader.unloadable) == {
        "eventDate does not name a calendar day": 1,
        "coordinates missing or not numbers": 2,
    }
    assert loader.rows_read == len(loaded) + sum(loader.unloadable.values())


def test_missing_columns_names_what_a_header_lacks():
    assert o.missing_columns(list(o.COLUMNS_READ)) == []
    assert "acceptedTaxonKey" in o.COLUMNS_READ
    assert o.missing_columns(["gbifID"]) == [c for c in o.COLUMNS_READ if c != "gbifID"]


def test_read_occurrence_rows_streams_tab_rows_without_quoting(tmp_path):
    text = 'gbifID\trecordedBy\toccurrenceRemarks\n1\tsomeone\tsaid "very soggy"\n2\telse\t\n'
    path = tmp_path / "occurrence.txt"
    path.write_text(text, encoding="utf-8")
    from_stream = list(o.read_occurrence_rows(io.StringIO(text, newline="")))
    assert from_stream == list(o.read_occurrence_table(path))
    assert from_stream == [
        {"gbifID": "1", "recordedBy": "someone", "occurrenceRemarks": 'said "very soggy"'},
        {"gbifID": "2", "recordedBy": "else", "occurrenceRemarks": ""},
    ]
