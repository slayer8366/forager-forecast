"""Regions, groups and the count table, on synthetic rows run through the loader and pipeline."""

from forager_forecast.records import counts as c
from forager_forecast.records import filters as f
from forager_forecast.records.occurrence import OccurrenceLoader, record_from_row

TAXON_BY_GENUS = {"9623860": "5249462", "2542160": "2542161", "": "8000001"}


def row(
    lat: str, lon: str, genus_key: str = "", year: str = "2024", gbif_id: str = "1", **extra: str
) -> dict[str, str]:
    base = {
        "gbifID": gbif_id,
        "acceptedTaxonKey": TAXON_BY_GENUS[genus_key],
        "decimalLatitude": lat,
        "decimalLongitude": lon,
        "genusKey": genus_key,
        "coordinateUncertaintyInMeters": "5",
        "informationWithheld": "",
        "dataGeneralizations": "",
        "eventDate": f"{year}-09-14T10:00:00",
        "recordedBy": "someone",
    }
    base.update(extra)
    return base


def test_boxes_are_the_t1_limits():
    by_name = {b.name: b for b in c.T1_BOXES}
    assert (by_name["pnw"].lat_min, by_name["pnw"].lat_max) == (42.0, 49.5)
    assert (by_name["pnw"].lon_min, by_name["pnw"].lon_max) == (-125.0, -121.0)
    assert (by_name["east"].lat_min, by_name["east"].lat_max) == (38.0, 46.0)
    assert (by_name["east"].lon_min, by_name["east"].lon_max) == (-84.0, -70.0)


def region(lat: str, lon: str) -> str:
    return c.region_of(record_from_row(row(lat, lon)))


def test_region_assignment():
    assert region("47.0", "-123.0") == "pnw"
    assert region("42.0", "-77.0") == "east"
    assert region("49.5", "-121.0") == "pnw", "limits are inclusive"
    assert region("49.51", "-121.0") == c.REST_OF_NORTH_AMERICA
    assert region("47.0", "-120.99") == c.REST_OF_NORTH_AMERICA
    assert region("35.0", "-90.0") == c.REST_OF_NORTH_AMERICA
    assert region("47.0", "123.0") == c.REST_OF_NORTH_AMERICA, "east longitude is not pnw"


def test_group_assignment_by_genus_key():
    def group(genus_key: str) -> str | None:
        return c.group_of(record_from_row(row("47.0", "-123.0", genus_key)))

    assert group("9623860") == "cantharellus"
    assert group("2542160") == "laetiporus"
    assert group("") is None


def test_year_is_the_event_year():
    assert c.year_of(record_from_row(row("47.0", "-123.0", year="2019"))) == "2019"


def test_count_table_through_the_loader_and_pipeline():
    rows = [
        row("47.0", "-123.0", "9623860", "2023", "1"),
        row("47.0", "-123.0", "9623860", "2023", "2", coordinateUncertaintyInMeters="900"),
        row("47.0", "-123.0", "2542160", "2024", "3"),
        row("42.0", "-77.0", "9623860", "2024", "4"),
        row("35.0", "-90.0", "", "2024", "5"),
        row("35.0", "-90.0", "2542160", "2024", "6", informationWithheld="withheld"),
        row("", "", "9623860", "2024", "7"),
    ]
    loader = OccurrenceLoader()
    table = c.CountTable()
    pipeline = f.Pipeline(f.r6_audit_steps(), on_pass=table.add)
    kept = pipeline.run(loader.load(rows))
    assert [r.gbif_id for r in kept] == [1, 3, 4, 5]
    assert dict(loader.unloadable) == {"coordinates missing or not numbers": 1}
    assert table.count("source", "cantharellus", "pnw", "2023") == 2
    assert table.count("coordinate_uncertainty", "cantharellus", "pnw", "2023") == 1
    assert table.count("duplicate_taxon_observer_cell_day", "cantharellus", "pnw", "2023") == 1
    assert table.count("source", "all_fungi", "rest_of_north_america", "2024") == 2
    assert table.count("user_obscured", "all_fungi", "rest_of_north_america", "2024") == 1
    assert table.count("user_obscured", "laetiporus", "rest_of_north_america", "2024") == 0
    assert table.count("source", "laetiporus", "pnw", "2024") == 1
    assert table.count("source", "cantharellus", "east", "2024") == 1
    final = pipeline.counts[-1].step
    assert (
        sum(n for stage, group, _, _, n in table.rows() if stage == final and group == "all_fungi")
        == 4
    )


def test_count_table_csv_has_the_five_columns(tmp_path):
    table = c.CountTable()
    table.add("source", record_from_row(row("47.0", "-123.0", "9623860", "2023")))
    path = tmp_path / "counts.csv"
    table.write_csv(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "stage,group,region,year,records"
    assert sorted(lines[1:]) == [
        "source,all_fungi,pnw,2023,1",
        "source,cantharellus,pnw,2023,1",
    ]
