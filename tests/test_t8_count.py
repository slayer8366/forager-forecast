"""T8's count end to end on a synthetic D26-shaped zip: T1's units reproduced exactly, lichens
attached, J5's genus keys resolved from the zip, the jump check run; and every refusal. No real
records are read."""

import hashlib
import json
import zipfile
from datetime import date

import numpy as np
import pytest

from forager_forecast.records.occurrence import COLUMNS_READ
from forager_forecast.t1_design import CANTHARELLUS_GENUS_KEY
from forager_forecast.t8 import count as tc
from forager_forecast.t8 import design
from forager_forecast.t8 import jump as jp
from forager_forecast.t8 import units as tu

COLUMNS = list(COLUMNS_READ) + ["classKey", "speciesKey", "taxonRank", "genus", "kingdom"]
GENUS_KEY = {name: 1000 + i for i, name in enumerate(jp.PROPOSED_GENERA)}


def row(gid, lat, lon, day, genus_key="", genus="", class_key="", species_key="", rank="",
        license="CC_BY_4_0", observer="ann", uncertainty="10", taxon=None):  # fmt: skip
    values = {
        "gbifID": str(gid),
        "acceptedTaxonKey": str(taxon if taxon is not None else gid),
        "genusKey": str(genus_key),
        "decimalLatitude": str(lat),
        "decimalLongitude": str(lon),
        "coordinateUncertaintyInMeters": uncertainty,
        "eventDate": day,
        "license": license,
        "datasetKey": "inat",
        "recordedBy": observer,
        "informationWithheld": "",
        "dataGeneralizations": "",
        "classKey": str(class_key),
        "speciesKey": str(species_key),
        "taxonRank": rank,
        "genus": genus,
        "kingdom": "Fungi",
    }
    return "\t".join(values[c] for c in COLUMNS)


def rows():
    canth = CANTHARELLUS_GENUS_KEY
    out = [
        # Cell 470_-1230, 2020-W38: a chanterelle (to species) and a lichen, two outings of it.
        row(1, 47.0, -123.0, "2020-09-14", canth, "Cantharellus", 50, 111, "SPECIES"),
        row(2, 47.0, -123.0, "2020-09-15", "", "", 180, observer="bo"),
        row(3, 47.01, -123.0, "2020-09-16", "", "", 180, observer="cy"),
        # Same cell, 2020-W39: another fungus only (an eligible negative unit).
        row(4, 47.0, -123.0, "2020-09-21", 77, "Mycena", 50),
        # Cell 455_-1220, 2021-W01: a genus-rank chanterelle (no speciesKey), and a Boletus.
        row(5, 45.5, -122.0, "2021-01-05", canth, "Cantharellus", 50, "", "GENUS"),
        row(6, 45.5, -122.0, "2021-01-06", GENUS_KEY["Boletus"], "Boletus", 50),
        # Outside the PNW box (the east box's longitude): never counted.
        row(7, 45.0, -80.0, "2020-09-14", canth, "Cantharellus", 50),
        # Uncertainty 3,000 m: only the 5,000 m list keeps it (a unit of its own there).
        row(8, 44.0, -122.5, "2019-06-03", 77, "Mycena", 50, uncertainty="3000"),
        # Not CC: the commercial-safe list drops it.
        row(9, 43.0, -123.5, "2018-10-01", 77, "Mycena", 50, license="CC_BY_NC_4_0"),
    ]
    # The rest of J5's names appear once each, outside the box, so each resolves to one key.
    for i, name in enumerate(jp.PROPOSED_GENERA[1:]):
        out.append(row(100 + i, 40.0, -80.0, "2020-09-14", GENUS_KEY[name], name, 50))
    return out


def write_zip(path, lines):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("occurrence.txt", "\t".join(COLUMNS) + "\n" + "\n".join(lines) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_t1(fits, stem, recounted, sea_dropped=0, flip=None):
    units = sorted(recounted)
    y = np.array([recounted[u] for u in units])
    if flip is not None:
        y[units.index(flip)] = 1.0 - y[units.index(flip)]
    years = [date.fromisoformat(u.split("@")[1]).isocalendar().year for u in units]
    np.savez_compressed(
        fits / f"{stem}.npz",
        unit=np.array(units),
        cell=np.array([u.split("@")[0] for u in units]),
        year=np.array(years),
        y=y,
        p=np.full(len(units), 0.05),
        land_point=np.array(["own"] * len(units)),
    )
    (fits / f"{stem}.json").write_text(
        json.dumps(
            {
                "weather_units_dropped": {
                    "units_before": len(units) + sea_dropped,
                    "kept_land_point_own": len(units),
                    "kept_land_point_neighbour_RECORD_822": 0,
                }
            }
        )
    )
    return units


@pytest.fixture
def world(tmp_path, monkeypatch):
    """A zip, T1 unit files reproducing T1's own recount, and every reading marked ruled."""
    monkeypatch.setattr(design, "RULED", {p: "test" for p in design.PENDING})
    zip_path = tmp_path / "d26.zip"
    sha = write_zip(zip_path, rows())
    fits = tmp_path / "fits"
    fits.mkdir()
    box = tc.read_box(zip_path, jp.PROPOSED_GENERA)
    lists = {}
    for name, (stem, _total) in design.T1_LISTS.items():
        steps, keep = tc.list_steps(name)
        from forager_forecast.records.filters import Pipeline

        survivors = Pipeline(steps).run(r for r in box.records if keep(r))
        recounted = tu.recount_units(survivors, CANTHARELLUS_GENUS_KEY)
        lists[name] = (stem, len(write_t1(fits, stem, recounted)))
    monkeypatch.setattr(design, "T1_LISTS", lists)
    return zip_path, sha, fits, tmp_path / "out"


def test_the_count_reproduces_t1s_units_and_attaches_lichens(world):
    zip_path, sha, fits, out = world
    summary = tc.run_count(zip_path, sha, fits, out)
    assert summary["records_in_pnw_box"] == 8
    assert {n: s["units"] for n, s in summary["lists"].items()} == {
        "t1_1000m": 4,
        "t1_5000m": 5,
        "t1_1000m_cc": 3,
    }
    assert all(s["units_identical_to_t1"] for s in summary["lists"].values())
    lichen = np.load(out / "lichen_t1_1000m.npz")
    by_unit = dict(zip(lichen["unit"].tolist(), lichen["lichen_y"].tolist(), strict=True))
    assert by_unit == {
        "430_-1235@2018-10-01": 0.0,
        "455_-1220@2021-01-04": 0.0,
        "470_-1230@2020-09-14": 1.0,
        "470_-1230@2020-09-21": 0.0,
    }
    outings = dict(zip(lichen["unit"].tolist(), lichen["lichen_outings"].tolist(), strict=True))
    assert outings["470_-1230@2020-09-14"] == 2
    assert summary["j5_genus_keys"] == GENUS_KEY


def test_the_jump_check_reads_j5_by_unit_year_and_j6_by_the_rule(world):
    zip_path, sha, fits, out = world
    summary = tc.run_count(zip_path, sha, fits, out)
    tallies = summary["jump"]["tallies"]
    assert tallies["cantharellus_by_year"] == {"2018": 0, "2020": 1, "2021": 1}
    assert tallies["species_share_by_year"] == {"2018": "nan", "2020": 1.0, "2021": 0.0}
    # The Boletus record is in T1 unit 455_-1220@2021-01-04, 2021's only unit.
    assert tallies["genus_rate_by_year"]["Boletus"] == {"2018": 0.0, "2020": 0.0, "2021": 1.0}
    assert summary["jump"]["label"] in (jp.REPORTING_LED, jp.SURGE_CONSISTENT, jp.UNDETERMINED)
    by_rank = tc.run_count(zip_path, sha, fits, out, species_rule="taxonRank")
    assert by_rank["jump"]["tallies"]["species_share_by_year"]["2021"] == 0.0


def test_one_differing_outcome_in_t1s_file_refuses_the_count(world):
    zip_path, sha, fits, out = world
    stem = design.T1_LISTS["t1_1000m"][0]
    recounted = {u: y for u, y in zip(*_units(fits, stem), strict=True)}
    write_t1(fits, stem, recounted, flip="470_-1230@2020-09-21")
    with pytest.raises(tu.UnitsDiffer, match="1 outcomes differ"):
        tc.run_count(zip_path, sha, fits, out)


def test_a_unit_t1_did_not_drop_for_weather_refuses_the_count(world):
    zip_path, sha, fits, out = world
    stem = design.T1_LISTS["t1_1000m"][0]
    units, y = _units(fits, stem)
    recounted = dict(zip(units[1:], y[1:], strict=True))  # one unit missing, no sea drop recorded
    write_t1(fits, stem, recounted)
    with pytest.raises(tu.UnitsDiffer, match="beyond T1's"):
        tc.run_count(zip_path, sha, fits, out)


def test_a_differing_zip_checksum_refuses_before_any_row_is_read(world):
    zip_path, _sha, fits, out = world
    with pytest.raises(tc.CountRefused, match="sha256"):
        tc.run_count(zip_path, "0" * 64, fits, out)
    assert not out.exists()


def test_the_count_refuses_while_a_reading_is_open(world, monkeypatch):
    zip_path, sha, fits, out = world
    monkeypatch.setattr(design, "RULED", {})
    with pytest.raises(design.NotRuled, match="count"):
        tc.run_count(zip_path, sha, fits, out)


def test_a_j5_name_with_two_genus_keys_is_refused():
    seen = {name: {GENUS_KEY[name]} for name in jp.PROPOSED_GENERA}
    seen["Boletus"] = {1000, 2000}
    with pytest.raises(tc.CountRefused, match="Boletus"):
        tc.resolve_genus_keys(seen)


def test_a_zip_without_species_columns_is_refused(tmp_path):
    path = tmp_path / "bare.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("occurrence.txt", "\t".join(COLUMNS_READ) + "\n" + "\t".join(["1"] * 12) + "\n")
    with pytest.raises(tc.CountRefused, match="speciesKey"):
        tc.read_box(path, jp.PROPOSED_GENERA)


def test_the_5000_m_list_changes_only_the_uncertainty_step():
    base, _ = tc.list_steps("t1_1000m")
    wide, _ = tc.list_steps("t1_5000m")
    changed = [(a.name, b.name) for a, b in zip(base.filters, wide.filters, strict=True)
               if a.name != b.name]  # fmt: skip
    assert changed == [(tc.UNCERTAINTY_STEP, "coordinate uncertainty present and at most 5,000 m")]


def _units(fits, stem):
    z = np.load(fits / f"{stem}.npz")
    return z["unit"].tolist(), z["y"].tolist()
