"""The license table through the loader and pipeline."""

from forager_forecast.records import counts as c
from forager_forecast.records import filters as f
from forager_forecast.records.licenses import EMPTY, LicenseTable, fan_out
from forager_forecast.records.occurrence import OccurrenceLoader, record_from_row

INAT = "50c9509d-22c7-4a22-a47d-8c48425ef4a7"
MUSHROOM_OBSERVER = "d714382d-5890-4234-ae81-696eeb53658a"
TAXON_BY_GENUS = {"9623860": "5249462", "2542160": "2542161", "": "8000001"}


def row(genus_key: str = "", **extra: str) -> dict[str, str]:
    base = {
        "gbifID": "1",
        "acceptedTaxonKey": TAXON_BY_GENUS[genus_key],
        "datasetKey": INAT,
        "license": "CC_BY_NC_4_0",
        "decimalLatitude": "47.0",
        "decimalLongitude": "-123.0",
        "genusKey": genus_key,
        "coordinateUncertaintyInMeters": "5",
        "informationWithheld": "",
        "dataGeneralizations": "",
        "eventDate": "2024-09-14T10:00:00",
        "recordedBy": "someone",
    }
    base.update(extra)
    return base


def test_license_table_counts_every_stage_by_group_license_and_publisher():
    rows = [
        row("9623860", gbifID="1"),
        row("9623860", gbifID="2", coordinateUncertaintyInMeters="900"),
        row(
            "2542160",
            gbifID="3",
            license="CC_BY_4_0",
            datasetKey=MUSHROOM_OBSERVER,
            recordedBy="observer_b",
        ),
        row("", gbifID="4", license="", datasetKey="", recordedBy="observer_c"),
        row("9623860", gbifID="5", recordedBy="observer_d"),
    ]
    # Rows 1 and 5 share taxon, cell and day; distinct observers keep both under the observer key.
    licenses = LicenseTable()
    pipeline = f.Pipeline(f.r6_audit_steps(), on_pass=licenses.add)
    survivors = pipeline.run(OccurrenceLoader().load(rows))
    assert [r.gbif_id for r in survivors] == [1, 3, 4, 5]
    final = "duplicate_taxon_observer_cell_day"
    assert licenses.count("source", "all_fungi", "CC_BY_NC_4_0", INAT) == 3
    assert licenses.count("source", "cantharellus", "CC_BY_NC_4_0", INAT) == 3
    assert licenses.count("source", "laetiporus", "CC_BY_4_0", MUSHROOM_OBSERVER) == 1
    assert licenses.count("source", "all_fungi", EMPTY, EMPTY) == 1
    assert licenses.count("coordinate_uncertainty", "cantharellus", "CC_BY_NC_4_0", INAT) == 2
    assert licenses.count(final, "cantharellus", "CC_BY_NC_4_0", INAT) == 2
    assert licenses.count(final, "all_fungi", "CC_BY_NC_4_0", INAT) == 2
    assert licenses.count(final, "all_fungi", "CC_BY_4_0", MUSHROOM_OBSERVER) == 1
    assert licenses.count(final, "laetiporus", "CC_BY_NC_4_0", INAT) == 0


def test_license_rows_are_sorted_and_written_as_csv(tmp_path):
    licenses = LicenseTable()
    licenses.add("source", record_from_row(row("2542160", license="CC0_1_0")))
    licenses.add("source", record_from_row(row("9623860")))
    path = tmp_path / "licenses.csv"
    licenses.write_csv(path)
    assert path.read_text(encoding="utf-8").splitlines() == [
        "stage,group,license,datasetKey,records",
        f"source,all_fungi,CC0_1_0,{INAT},1",
        f"source,all_fungi,CC_BY_NC_4_0,{INAT},1",
        f"source,cantharellus,CC_BY_NC_4_0,{INAT},1",
        f"source,laetiporus,CC0_1_0,{INAT},1",
    ]


def test_fan_out_feeds_both_tables_from_one_pipeline():
    table = c.CountTable()
    licenses = LicenseTable()
    pipeline = f.Pipeline(f.r6_audit_steps(), on_pass=fan_out(table.add, licenses.add))
    rows = [row("9623860", gbifID="1"), row("2542160", gbifID="2", license="CC_BY_4_0")]
    pipeline.run(OccurrenceLoader().load(rows))
    assert table.count("source", "all_fungi", "pnw", "2024") == 2
    assert licenses.count("source", "all_fungi", "CC_BY_4_0", INAT) == 1
    assert licenses.count("source", "all_fungi", "CC_BY_NC_4_0", INAT) == 1
