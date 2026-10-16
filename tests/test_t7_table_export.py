"""D143: the committed FungalTraits export, lossless against the workbook, and the list from it.

The synthetic tests use made-up cells. The tests on the committed export read
``reference/fungaltraits-2020/``; the cell-by-cell check against the workbook needs the workbook,
which stays outside the repository, and is skipped (with its reason printed) where it is absent.
"""

import gzip
import json

import pytest
from t7_synthetic import write_xlsx

from forager_forecast.t7 import fungaltraits as ft
from forager_forecast.t7.membership import file_sha256, load_list
from forager_forecast.t7.table_export import (
    compare_export,
    export_file_name,
    export_sheet,
    export_workbook,
    gzip_deterministic,
    read_csv_gz,
)
from forager_forecast.t7.xlsx import sheet_names

PROVENANCE = ft.EXPORT_DIR / "provenance.json"
needs_workbook = pytest.mark.skipif(
    not ft.table_path().exists(), reason=f"workbook not present at {ft.table_path()}"
)


def _book(tmp_path, sheets):
    path = tmp_path / "w.xlsx"
    write_xlsx(path, sheets)
    return path


def test_an_export_round_trips_every_cell_with_quotes_commas_newlines_and_gaps(tmp_path):
    sheets = {
        "one": [["h1", "h2", "h3", ""], ['a "quoted", text', "", "line\nbreak", ""],
                ["", "", "", "far"], [" lead and trail ", "ü ñ é", "", ""]],
        "two words": [["z"]],
    }  # fmt: skip
    book = _book(tmp_path, sheets)
    assert sheet_names(book) == ["one", "two words"]
    exports = export_workbook(book, tmp_path / "out")
    assert [e.file_name for e in exports] == ["one.csv.gz", "two_words.csv.gz"]
    got = read_csv_gz(tmp_path / "out" / "one.csv.gz")
    assert got == sheets["one"]
    for e in exports:
        c = compare_export(book, e.sheet, tmp_path / "out" / e.file_name)
        assert c.mismatches == [] and c.formulas == 0
    c = compare_export(book, "one", tmp_path / "out" / "one.csv.gz")
    assert (c.stored_rows, c.cells_compared, c.non_empty_cells) == (4, 16, 8)


def test_the_comparison_finds_one_edited_cell_a_dropped_row_and_an_extra_column(tmp_path):
    """Positive controls: the check that proves the real export lossless can fail."""
    book = _book(tmp_path, {"s": [["a", "b"], ["c", "d"], ["e", "f"]]})
    out = tmp_path / "s.csv.gz"
    export_sheet(book, "s", out)
    assert compare_export(book, "s", out).mismatches == []

    def write(rows):
        text = "".join(",".join(r) + "\n" for r in rows)
        out.write_bytes(gzip_deterministic(text.encode()))

    write([["a", "b"], ["c", "D"], ["e", "f"]])
    assert compare_export(book, "s", out).mismatches == ["row 2 column 2: sheet 'd', export 'D'"]
    write([["a", "b"], ["c", "d"]])
    assert any("2 rows" in m for m in compare_export(book, "s", out).mismatches)
    write([["a", "b", ""], ["c", "d", ""], ["e", "f", "x"]])
    assert any("3 fields" in m for m in compare_export(book, "s", out).mismatches)


def test_the_export_bytes_are_deterministic(tmp_path):
    book = _book(tmp_path, {"s": [["a", "b"], ["c", "d"]]})
    first = export_sheet(book, "s", tmp_path / "1.csv.gz")
    second = export_sheet(book, "s", tmp_path / "2.csv.gz")
    assert first.gz_sha256 == second.gz_sha256
    header = (tmp_path / "1.csv.gz").read_bytes()[:10]
    assert header[4:8] == b"\0\0\0\0"  # mtime 0
    assert header[3] & 0x08 == 0  # no file name stored
    assert export_file_name("trait states") == "trait_states.csv.gz"


def test_the_committed_export_matches_its_provenance_and_the_recorded_hashes():
    prov = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    assert prov["source"]["sha256"] == ft.SOURCE.sha256
    assert prov["source"]["size_bytes"] == ft.SOURCE.size == 1_243_643
    assert prov["source"]["md5"] == ft.SOURCE.md5
    assert prov["source"]["record_handle"] == "2263/80202"
    assert prov["source"]["fetched_utc"] == "2026-10-16T02:03:46Z"
    assert "10.1007/s13225-020-00466-2" in prov["citation"]
    assert prov["consent"]["words_verbatim"] == (
        "Hi Brandon! I support such initiatives where science can contribute to public "
        "knowledge, so it is fine by me. Best Sergei"
    )
    by_name = {e["file_name"]: e for e in prov["exports"]}
    assert set(by_name) == {"data.csv.gz", "trait_states.csv.gz"}
    expected = {"data.csv.gz": ft.EXPORT_DATA_SHA256,
                "trait_states.csv.gz": ft.EXPORT_TRAIT_STATES_SHA256}  # fmt: skip
    for name, sha in expected.items():
        path = ft.EXPORT_DIR / name
        assert file_sha256(path) == sha == by_name[name]["gz_sha256"], name
        assert path.stat().st_size == by_name[name]["gz_size"] < 1_048_576, name
        raw = gzip.decompress(path.read_bytes())
        assert len(raw) == by_name[name]["csv_size"], name
        rows = read_csv_gz(path)
        assert len(rows) == by_name[name]["rows"], name
        assert {len(r) for r in rows} == {by_name[name]["columns"]}, name
    assert all(c["mismatches"] == 0 for c in prov["check"])


@needs_workbook
def test_the_committed_export_matches_every_cell_of_the_workbook():
    """The losslessness proof (D143): every sheet, every row, every column, through the xlsx
    reader, against the committed export; and a fresh export gives the committed bytes."""
    workbook = ft.table_path()
    assert file_sha256(workbook) == ft.SOURCE.sha256
    prov = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    sheets = sheet_names(workbook)
    assert sheets == [e["sheet"] for e in prov["exports"]] == ["data", "trait states"]
    for e in prov["exports"]:
        c = compare_export(workbook, e["sheet"], ft.EXPORT_DIR / e["file_name"])
        assert c.mismatches == [], e["sheet"]
        assert c.cells_compared == e["rows"] * e["columns"], e["sheet"]
        assert c.stored_rows == e["rows"] and c.formulas == 0, e["sheet"]
    counts = {c["sheet"]: c["non_empty_cells"] for c in prov["check"]}
    assert counts == {"data": 124_176, "trait states": 251}


@needs_workbook
def test_a_fresh_export_of_the_workbook_gives_the_committed_bytes(tmp_path):
    for e in export_workbook(ft.table_path(), tmp_path):
        committed = ft.EXPORT_DIR / e.file_name
        assert (tmp_path / e.file_name).read_bytes() == committed.read_bytes(), e.file_name


def test_the_normalised_list_written_from_the_committed_export_has_the_recorded_sha256(tmp_path):
    out = tmp_path / "list.tsv"
    sha = ft.convert_export(out)
    assert sha == ft.NORMALISED_LIST_SHA256
    members = load_list(out, ft.NORMALISED_LIST_SHA256)
    assert len(members.rows) == 10_765
    assert {r.source_id for r in members.rows.values()} == {ft.export_source_id()}


@needs_workbook
def test_the_workbook_and_the_export_give_the_same_list_rows_but_for_source_id(tmp_path):
    via_book = ft.to_list_rows(ft.read_traits(ft.table_path()), "x")
    via_export = ft.to_list_rows(ft.read_traits_export(), "x")
    assert via_book == via_export
    assert len(via_export) == 10_765


def test_the_adapter_refuses_an_export_that_is_not_the_recorded_one(tmp_path):
    other = tmp_path / "data.csv.gz"
    other.write_bytes(gzip_deterministic(b"GENUS\nx\n"))
    with pytest.raises(ft.SourceMismatch):
        ft.read_traits_export(other)
