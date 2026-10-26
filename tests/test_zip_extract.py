"""Extracting the T6b source zips by their own listings, over small zips made here."""

import hashlib
import zipfile
from pathlib import Path

import pytest

from forager_forecast import zip_extract as zx

SHP = [
    "NA_PoliticalDivisions/data/boundaries_p_2021_v3" + e for e in (".shp", ".dbf", ".shx", ".prj")
]


def make_zip(path: Path, members: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in members.items():
            z.writestr(name, data)
    return path


def test_the_listing_names_every_member_with_its_size_and_crc(tmp_path):
    z = make_zip(tmp_path / "a.zip", {"d/a.txt": b"abc", "b.txt": b"hello"})
    got = {m["name"]: (m["file_size"], m["crc32"]) for m in zx.zip_listing(z)}
    assert got == {
        "d/a.txt": (3, f"{zipfile.crc32(b'abc'):08x}"),
        "b.txt": (5, f"{zipfile.crc32(b'hello'):08x}"),
    }


def test_the_root_puts_the_target_member_at_the_target(tmp_path):
    target = tmp_path / "sources" / "politicalboundaries_shapefile" / SHP[0]
    member, root = zx.root_for_target(SHP, target)
    assert member == SHP[0]
    assert root == tmp_path / "sources" / "politicalboundaries_shapefile"
    # A zip with the folder inside it extracts one level up.
    names = ["politicalboundaries_shapefile/" + n for n in SHP]
    assert zx.root_for_target(names, target)[1] == tmp_path / "sources"


def test_no_member_or_two_members_at_the_target_is_refused(tmp_path):
    target = tmp_path / "s" / "politicalboundaries_shapefile" / SHP[0]
    with pytest.raises(zx.ExtractError, match="0 members"):
        zx.root_for_target(["other/data/boundaries_p_2021_v3.shp"], target)
    with pytest.raises(zx.ExtractError, match="2 members"):
        zx.root_for_target([SHP[0], "politicalboundaries_shapefile/" + SHP[0]], target)


def test_extracting_beside_the_target_writes_every_file_and_records_it(tmp_path):
    members = {n: n.encode() * 1000 for n in SHP} | {"NA_PoliticalDivisions/readme.txt": b"r"}
    z = make_zip(tmp_path / "p.zip", members)
    target = tmp_path / "sources" / "politicalboundaries_shapefile" / SHP[0]
    rec = zx.extract_beside_target(z, target)
    assert target.read_bytes() == members[SHP[0]]
    for name, data in members.items():
        assert (tmp_path / "sources" / "politicalboundaries_shapefile" / name).read_bytes() == data
    assert rec["target_member"] == SHP[0]
    assert sorted(m["name"] for m in rec["listing"]) == sorted(members)
    by = {f["member"]: f for f in rec["files"]}
    assert by[SHP[1]]["sha256"] == hashlib.sha256(members[SHP[1]]).hexdigest()
    assert not list(tmp_path.rglob("*.partial"))


def test_a_member_path_leaving_the_root_is_refused(tmp_path):
    z = make_zip(tmp_path / "bad.zip", {SHP[0]: b"s", "../escape.txt": b"x"})
    target = tmp_path / "sources" / "p" / SHP[0]
    with pytest.raises(zx.ExtractError, match="escape"):
        zx.extract_beside_target(z, target)
    assert not (tmp_path / "sources" / "escape.txt").exists()


def test_a_damaged_member_is_refused_and_not_left_behind(tmp_path):
    payload = b"forest" * 20_000
    z = make_zip(tmp_path / "d.zip", {"Data/TreeMap2023_CONUS.tif": payload})
    info = zipfile.ZipFile(z).getinfo("Data/TreeMap2023_CONUS.tif")
    blob = bytearray(z.read_bytes())
    start = info.header_offset + 30 + len(info.filename) + len(info.extra)
    blob[start + info.compress_size // 2] ^= 0xFF
    z.write_bytes(bytes(blob))
    out = tmp_path / "out"
    with pytest.raises(zx.ExtractError):
        zx.extract_named(z, ["TreeMap2023_CONUS.tif"], out)
    assert not out.exists() or list(out.iterdir()) == []


def test_named_members_come_out_flat_by_file_name(tmp_path):
    members = {
        "Data/TreeMap2023_CONUS.tif": b"tif" * 1000,
        "Data/TreeMap2023_CONUS.tif.vat.dbf": b"dbf" * 10,
        "Data/TreeMap2023_CONUS_Tree_Table.csv": b"csv",
    }
    z = make_zip(tmp_path / "t.zip", members)
    out = tmp_path / "treemap2023"
    rec = zx.extract_named(z, ["TreeMap2023_CONUS.tif", "TreeMap2023_CONUS.tif.vat.dbf"], out)
    assert sorted(p.name for p in out.iterdir()) == [
        "TreeMap2023_CONUS.tif",
        "TreeMap2023_CONUS.tif.vat.dbf",
    ]
    assert (out / "TreeMap2023_CONUS.tif.vat.dbf").read_bytes() == b"dbf" * 10
    assert {f["member"] for f in rec["files"]} == {
        "Data/TreeMap2023_CONUS.tif",
        "Data/TreeMap2023_CONUS.tif.vat.dbf",
    }
    assert len(rec["listing"]) == 3


def test_a_name_with_no_member_or_two_is_refused(tmp_path):
    z = make_zip(tmp_path / "t.zip", {"A/x.tif": b"1", "B/x.tif": b"2"})
    with pytest.raises(zx.ExtractError, match="2 members"):
        zx.extract_named(z, ["x.tif"], tmp_path / "o")
    with pytest.raises(zx.ExtractError, match="0 members"):
        zx.extract_named(z, ["y.tif"], tmp_path / "o")


def test_a_stop_between_members_leaves_no_partial(tmp_path):
    z = make_zip(tmp_path / "t.zip", {"a.bin": b"a" * 100, "b.bin": b"b" * 100})
    with pytest.raises(RuntimeError, match="PAUSE"):
        zx.extract_named(z, ["a.bin", "b.bin"], tmp_path / "o", should_stop=lambda n: "PAUSE file")
    assert not list((tmp_path / "o").glob("*.partial")) if (tmp_path / "o").exists() else True
