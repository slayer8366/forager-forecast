"""T7 items 2 and 4: level III codes per cell, and genus and family names beside each Record."""

from pathlib import Path

import numpy as np
from test_t6b_mask import _cell_lonlat, _ring, _window, _write_shapefile

from forager_forecast.grid import GridWindow
from forager_forecast.records.occurrence import COLUMNS_READ, OccurrenceLoader
from forager_forecast.t7.ecoregions import burn_level3, read_level3
from forager_forecast.t7.names import (
    NAME_COLUMNS,
    TaxonNames,
    load_named,
    missing_name_columns,
    names_from_row,
)

HEADER = Path(__file__).parent / "fixtures" / "d26_occurrence_header.tsv"


def _level3_file(tmp_path):
    stem = tmp_path / "l3"
    _write_shapefile(
        stem,
        [
            [_ring(-122.0, 45.0, -121.0, 46.0)],
            [_ring(-121.0, 45.0, -120.0, 46.0)],
            [_ring(-122.0, 46.0, -120.0, 47.0)],
        ],  # fmt: skip
        [("LEVEL1", 5), ("LEVEL3", 10), ("NameL3_En", 40)],
        [
            {"LEVEL1": "7", "LEVEL3": "7.1.8", "NameL3_En": "Coast Range"},
            {"LEVEL1": "6", "LEVEL3": "6.2.7", "NameL3_En": "Cascades"},
            {"LEVEL1": "6", "LEVEL3": "6.2.15", "NameL3_En": "Idaho Batholith"},
        ],
    )
    return stem.with_suffix(".shp")


def test_level3_codes_are_burned_by_cell_centre_and_numbered_in_sorted_order(tmp_path):
    table, polygons = read_level3(_level3_file(tmp_path))
    assert [(t.code, t.level3, t.level1) for t in table] == [
        (1, "6.2.15", "6"), (2, "6.2.7", "6"), (3, "7.1.8", "7"),
    ]  # fmt: skip
    window = _window(-122.5, 44.5, -119.5, 47.5)
    codes = burn_level3(polygons, window)
    assert codes.dtype == np.uint16 and codes.shape == (window.height, window.width)
    lon, lat = _cell_lonlat(window)
    inside = (lat > 45.02) & (lat < 45.98)
    assert (codes[inside & (lon > -121.98) & (lon < -121.02)] == 3).all()
    assert (codes[inside & (lon > -120.98) & (lon < -120.02)] == 2).all()
    assert (codes[(lat > 46.02) & (lat < 46.98) & (lon > -121.98) & (lon < -120.02)] == 1).all()
    assert (codes[(lat < 44.98) | (lat > 47.02) | (lon < -122.02) | (lon > -119.98)] == 0).all()


def test_level3_burns_by_centre_not_by_touch():
    """A square from 300 m to 800 m east of a window's edge holds the centres at 375 and 625 m
    only; the cell from 750 m to 1,000 m touches it but its centre (875 m) is outside."""
    window = GridWindow(0, 0, 1000, 250)
    ring = np.array([[300.0, -50.0], [300.0, 300.0], [800.0, 300.0], [800.0, -50.0],
                     [300.0, -50.0]])  # fmt: skip
    codes = burn_level3([(5, [ring])], window)
    assert codes.tolist() == [[0, 5, 5, 0]]


def test_the_d26_header_carries_every_name_column_and_every_loader_column():
    header = HEADER.read_text(encoding="utf-8").rstrip("\n").split("\t")
    assert len(header) == 230
    assert missing_name_columns(header) == []
    assert all(c in header for c in COLUMNS_READ)
    assert missing_name_columns([c for c in header if c != "family"]) == ["family"]
    assert NAME_COLUMNS == ("genus", "family", "order", "taxonRank")


def _row(gbif_id, genus, family, rank="SPECIES", lat="45.5"):
    return {
        "gbifID": str(gbif_id), "acceptedTaxonKey": "11", "genusKey": "22",
        "decimalLatitude": lat, "decimalLongitude": "-122.5",
        "coordinateUncertaintyInMeters": "10", "eventDate": "2020-10-01", "license": "CC_BY_4_0",
        "datasetKey": "d", "recordedBy": "someone", "informationWithheld": "",
        "dataGeneralizations": "", "genus": genus, "family": family, "order": "Agaricales",
        "taxonRank": rank,
    }  # fmt: skip


def test_names_ride_beside_each_record_and_unloadable_rows_are_counted_by_the_loader():
    loader = OccurrenceLoader()
    rows = [
        _row(1, " Alphamyces ", "Alphaceae"),
        _row(2, "", "Alphaceae", rank="FAMILY"),
        _row(3, "Betamyces", "Betaceae", lat=""),  # no coordinates: the loader refuses it
    ]
    out = list(load_named(rows, loader))
    assert [(r.gbif_id, n) for r, n in out] == [
        (1, TaxonNames("Alphamyces", "Alphaceae", "Agaricales", "SPECIES")),
        (2, TaxonNames("", "Alphaceae", "Agaricales", "FAMILY")),
    ]
    assert loader.rows_read == 3
    assert loader.unloadable == {"coordinates missing or not numbers": 1}
    assert names_from_row({"genus": "X"}) == TaxonNames("X", "", "", "")
