"""Regions, groups and the count table, on synthetic rows."""

from forager_forecast.records import counts as c
from forager_forecast.records import filters as f


def row(
    lat: str, lon: str, genus_key: str = "", year: str = "2024", **extra: str
) -> dict[str, str]:
    base = {
        "decimalLatitude": lat,
        "decimalLongitude": lon,
        "genusKey": genus_key,
        "year": year,
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


def test_region_assignment():
    assert c.region_of(row("47.0", "-123.0")) == "pnw"
    assert c.region_of(row("42.0", "-77.0")) == "east"
    assert c.region_of(row("49.5", "-121.0")) == "pnw", "limits are inclusive"
    assert c.region_of(row("49.51", "-121.0")) == c.REST_OF_NORTH_AMERICA
    assert c.region_of(row("47.0", "-120.99")) == c.REST_OF_NORTH_AMERICA
    assert c.region_of(row("35.0", "-90.0")) == c.REST_OF_NORTH_AMERICA
    assert c.region_of(row("", "")) == c.NO_COORDINATES
    assert c.region_of(row("47.0", "123.0")) == c.REST_OF_NORTH_AMERICA, "east longitude is not pnw"


def test_group_assignment_by_genus_key():
    assert c.group_of(row("47.0", "-123.0", "9623860")) == "cantharellus"
    assert c.group_of(row("47.0", "-123.0", "2542160")) == "laetiporus"
    assert c.group_of(row("47.0", "-123.0", "2525554")) is None
    assert c.group_of(row("47.0", "-123.0", "")) is None


def test_count_table_through_the_pipeline():
    rows = [
        row("47.0", "-123.0", "9623860", "2023"),
        row("47.0", "-123.0", "9623860", "2023", coordinateUncertaintyInMeters="900"),
        row("47.0", "-123.0", "2542160", "2024"),
        row("42.0", "-77.0", "9623860", "2024"),
        row("35.0", "-90.0", "", "2024"),
        row("35.0", "-90.0", "2542160", "2024", informationWithheld="withheld"),
    ]
    table = c.CountTable()
    pipeline = f.Pipeline(on_pass=table.add)
    kept = list(pipeline.run(rows))
    assert len(kept) == 4
    assert table.count("source", "cantharellus", "pnw", "2023") == 2
    assert table.count("coordinate_uncertainty", "cantharellus", "pnw", "2023") == 1
    assert table.count("duplicate_observer_cell_day", "cantharellus", "pnw", "2023") == 1
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
    table.add("source", row("47.0", "-123.0", "9623860", "2023"))
    path = tmp_path / "counts.csv"
    table.write_csv(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "stage,group,region,year,records"
    assert sorted(lines[1:]) == [
        "source,all_fungi,pnw,2023,1",
        "source,cantharellus,pnw,2023,1",
    ]
