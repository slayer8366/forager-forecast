"""The license table through the pipeline, and the stream reader beside the file reader."""

import io

from forager_forecast.records import counts as c
from forager_forecast.records import filters as f
from forager_forecast.records.licenses import EMPTY, LicenseTable, fan_out

INAT = "50c9509d-22c7-4a22-a47d-8c48425ef4a7"
MUSHROOM_OBSERVER = "d714382d-5890-4234-ae81-696eeb53658a"


def row(genus_key: str = "", **extra: str) -> dict[str, str]:
    base = {
        "gbifID": "1",
        "datasetKey": INAT,
        "license": "CC_BY_NC_4_0",
        "decimalLatitude": "47.0",
        "decimalLongitude": "-123.0",
        "genusKey": genus_key,
        "year": "2024",
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
    # Distinct observers on rows 3 to 5: the duplicate step keys on observer, cell and day
    # without the taxon (T2 review, check 3), so a shared observer would drop them.
    licenses = LicenseTable()
    pipeline = f.Pipeline(on_pass=licenses.add)
    survivors = list(pipeline.run(rows))
    assert [r["gbifID"] for r in survivors] == ["1", "3", "4", "5"]
    assert licenses.count("source", "all_fungi", "CC_BY_NC_4_0", INAT) == 3
    assert licenses.count("source", "cantharellus", "CC_BY_NC_4_0", INAT) == 3
    assert licenses.count("source", "laetiporus", "CC_BY_4_0", MUSHROOM_OBSERVER) == 1
    assert licenses.count("source", "all_fungi", EMPTY, EMPTY) == 1
    assert licenses.count("coordinate_uncertainty", "cantharellus", "CC_BY_NC_4_0", INAT) == 2
    assert licenses.count("duplicate_observer_cell_day", "cantharellus", "CC_BY_NC_4_0", INAT) == 2
    assert licenses.count("duplicate_observer_cell_day", "all_fungi", "CC_BY_NC_4_0", INAT) == 2
    assert (
        licenses.count("duplicate_observer_cell_day", "all_fungi", "CC_BY_4_0", MUSHROOM_OBSERVER)
        == 1
    )
    assert licenses.count("duplicate_observer_cell_day", "laetiporus", "CC_BY_NC_4_0", INAT) == 0


def test_license_rows_are_sorted_and_written_as_csv(tmp_path):
    licenses = LicenseTable()
    licenses.add("source", row("2542160", license="CC0_1_0"))
    licenses.add("source", row("9623860"))
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
    pipeline = f.Pipeline(on_pass=fan_out(table.add, licenses.add))
    list(pipeline.run([row("9623860"), row("2542160", license="CC_BY_4_0")]))
    assert table.count("source", "all_fungi", "pnw", "2024") == 2
    assert licenses.count("source", "all_fungi", "CC_BY_4_0", INAT) == 1
    assert licenses.count("source", "all_fungi", "CC_BY_NC_4_0", INAT) == 1


def test_stream_reader_and_file_reader_agree(tmp_path):
    text = 'gbifID\tlocality\tlicense\n1\tsay "here"\tCC0_1_0\n2\t\tCC_BY_4_0\n'
    path = tmp_path / "occurrence.txt"
    path.write_text(text, encoding="utf-8")
    from_stream = list(f.read_occurrence_rows(io.StringIO(text, newline="")))
    from_file = list(f.read_occurrence_table(path))
    assert from_stream == from_file
    assert from_stream[0] == {"gbifID": "1", "locality": 'say "here"', "license": "CC0_1_0"}
    assert from_stream[1]["locality"] == ""
