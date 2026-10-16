"""T7 item 5: the normalised membership list, its sha256, the join, and the FungalTraits adapter.

Every genus and family name here is made up. No row of any published list is in this file.
"""

import hashlib

import pytest
from t7_synthetic import write_xlsx

from forager_forecast.t7 import fungaltraits as ft
from forager_forecast.t7.membership import (
    COLUMNS,
    COMPARISON_GROUP,
    FAMILY_ONLY_OUT,
    FAMILY_ONLY_SIDE,
    IN_GROUP,
    MAIN_RUN,
    MYCORRHIZAL_GROUP,
    NO_NAME,
    NOT_IN_GROUP,
    NOT_LISTED,
    SIDE_ONLY,
    SIDE_RUN,
    Join,
    ListRow,
    MembershipListError,
    load_list,
    write_list,
)
from forager_forecast.t7.names import TaxonNames
from forager_forecast.t7.xlsx import column_index, read_table


def _names(genus, family="", rank="SPECIES"):
    return TaxonNames(genus, family, "", rank)


def _hand_list(tmp_path):
    rows = [
        ListRow("Alphamyces", 101, "Alphaceae", "ectomycorrhizal", "clear", "hand", "made up"),
        ListRow("Betamyces", None, "Alphaceae", "ectomycorrhizal", "mixed", "hand", "made up"),
        ListRow("Gammamyces", None, "Gammaceae", "wood_rot", "clear", "hand", "made up"),
        ListRow("Deltamyces", None, "Gammaceae", "ectomycorrhizal", "clear", "hand", "made up"),
        ListRow("Laetiporus", None, "Fomitopsidaceae", "wood_rot", "clear", "hand", "made up"),
    ]
    path = tmp_path / "hand.tsv"
    return path, write_list(path, rows)


def test_the_list_is_refused_unless_its_sha256_is_the_recorded_one(tmp_path):
    path, sha = _hand_list(tmp_path)
    assert sha == hashlib.sha256(path.read_bytes()).hexdigest()
    members = load_list(path, sha)
    assert members.fingerprint == sha and set(members.rows) >= {"Alphamyces", "Laetiporus"}
    assert path.read_text(encoding="utf-8").splitlines()[0].split("\t") == list(COLUMNS)
    with pytest.raises(MembershipListError, match="sha256"):
        load_list(path, "0" * 64)
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(MembershipListError, match="sha256"):
        load_list(path, sha)


def test_a_malformed_list_is_refused(tmp_path):
    bad = tmp_path / "bad.tsv"
    bad.write_text("\t".join(COLUMNS) + "\nA\t\t\tlichen\tclear\ts\tn\n", encoding="utf-8")
    with pytest.raises(MembershipListError, match="lifestyle"):
        load_list(bad, hashlib.sha256(bad.read_bytes()).hexdigest())
    dup = tmp_path / "dup.tsv"
    line = "A\t\t\tother\tclear\ts\tn\n"
    dup.write_text("\t".join(COLUMNS) + "\n" + line + line, encoding="utf-8")
    with pytest.raises(MembershipListError, match="twice"):
        load_list(dup, hashlib.sha256(dup.read_bytes()).hexdigest())


def test_the_join_refuses_a_list_with_another_fingerprint(tmp_path):
    path, sha = _hand_list(tmp_path)
    with pytest.raises(MembershipListError, match="fingerprint"):
        Join(load_list(path, sha), "f" * 64, MYCORRHIZAL_GROUP, MAIN_RUN)


def test_main_and_side_runs_join_listed_unlisted_unclear_and_family_only_records(tmp_path):
    path, sha = _hand_list(tmp_path)
    members = load_list(path, sha)
    main = Join(members, sha, MYCORRHIZAL_GROUP, MAIN_RUN)
    side = Join(members, sha, MYCORRHIZAL_GROUP, SIDE_RUN)
    cases = {
        "listed clear": (_names("Alphamyces", "Alphaceae"), IN_GROUP, IN_GROUP),
        "listed mixed": (_names("Betamyces", "Alphaceae"), SIDE_ONLY, IN_GROUP),
        "listed other lifestyle": (_names("Gammamyces", "Gammaceae"), NOT_IN_GROUP, NOT_IN_GROUP),
        "unlisted": (_names("Zetamyces", "Alphaceae"), NOT_LISTED, NOT_LISTED),
        "family wholly in group": (_names("", "Alphaceae", "FAMILY"), FAMILY_ONLY_SIDE, IN_GROUP),
        "family mixed": (_names("", "Gammaceae", "FAMILY"), FAMILY_ONLY_OUT, FAMILY_ONLY_OUT),
        "no names": (_names("", ""), NO_NAME, NO_NAME),
    }
    for label, (names, in_main, in_side) in cases.items():
        assert main.outcome(names) == in_main, label
        assert side.outcome(names) == in_side, label
        assert main.joins(names) == (in_main == IN_GROUP), label
        assert side.joins(names) == (in_side == IN_GROUP), label


def test_the_comparison_group_joins_by_genus_name(tmp_path):
    path, sha = _hand_list(tmp_path)
    comparison = Join(load_list(path, sha), sha, COMPARISON_GROUP, MAIN_RUN)
    assert comparison.joins(_names("Laetiporus"))
    assert not comparison.joins(_names("Alphamyces"))
    assert not comparison.joins(_names("", "Fomitopsidaceae", "FAMILY"))


def _workbook(tmp_path):
    header = ["jrk_template", "Phylum", "Class", "Order", "Family", "GENUS", "COMMENT on genus",
              "primary_lifestyle", "Secondary_lifestyle", "Comment_on_lifestyle_template",
              "Fruitbody_type_template"]  # fmt: skip

    def row(fam, genus, primary, secondary="", comment="", fruit="agaricoid"):
        return ["", "P", "C", "O", fam, genus, "", primary, secondary, comment, fruit]

    rows = [
        header,
        row("Alphaceae", "Alphamyces", "ectomycorrhizal"),
        row("Alphaceae", "Betamyces", "ectomycorrhizal", secondary="soil_saprotroph"),
        row("Alphaceae", "Epsilomyces", "ectomycorrhizal", comment="some species saprotrophic"),
        row("Alphaceae", "Etamyces", "ectomycorrhizal", fruit="zygosporangium"),
        row("Gammaceae", "Gammamyces", "wood_saprotroph", fruit="polyporoid"),
        row("Gammaceae", "Thetamyces", "litter_saprotroph", secondary="ectomycorrhizal"),
        row("Gammaceae", "Iotamyces", ""),
        row("Gammaceae", "Kappamyces", "plant_pathogen"),
        row("Lambdaceae", "Mumyces", "ectomycorrhizal"),
        row("Lambdaceae", "Mumyces", "litter_saprotroph"),
    ]
    path = tmp_path / "traits.xlsx"
    write_xlsx(path, {"data": rows, "trait states": [["Guild"], ["ectomycorrhizal"]]})
    return path


def test_the_xlsx_reader_reads_shared_strings_numbers_and_gaps(tmp_path):
    path = tmp_path / "w.xlsx"
    write_xlsx(path, {"one": [["a", "b", "c"], ["x", "", "3"]], "two": [["z"]]})
    header, rows = read_table(path, "one")
    assert header == ["a", "b", "c"]
    assert list(rows) == [{"a": "x", "b": "", "c": "3"}]
    assert column_index("A1") == 0 and column_index("AB7") == 27


def test_the_adapter_refuses_a_table_that_is_not_the_recorded_one(tmp_path):
    path = _workbook(tmp_path)
    with pytest.raises(ft.SourceMismatch):
        ft.read_traits(path)  # the recorded sha256 is the real table's, not this fixture's
    assert ft.table_path({}) == ft.DEFAULT_PATH
    assert ft.table_path({ft.PATH_ENV: str(path)}) == path


def test_the_adapter_classifies_under_the_proposed_rule_and_writes_the_normalised_list(tmp_path):
    path = _workbook(tmp_path)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    rows = {r.genus: r for r in ft.to_list_rows(ft.read_traits(path, sha), "fixture")}
    got = {g: (r.lifestyle, r.certainty) for g, r in rows.items()}
    assert got == {
        "Alphamyces": ("ectomycorrhizal", "clear"),
        "Betamyces": ("ectomycorrhizal", "mixed"),
        "Epsilomyces": ("ectomycorrhizal", "mixed"),
        "Etamyces": ("ectomycorrhizal", "uncertain"),
        "Gammamyces": ("wood_rot", "clear"),
        "Thetamyces": ("ectomycorrhizal", "mixed"),
        "Iotamyces": ("other", "uncertain"),
        "Kappamyces": ("other", "clear"),
        "Mumyces": ("ectomycorrhizal", "uncertain"),
    }
    assert all(r.note for r in rows.values()) and rows["Alphamyces"].family == "Alphaceae"
    out = tmp_path / "list.tsv"
    out_sha = ft.convert(path, out, sha)
    members = load_list(out, out_sha)
    assert set(members.rows) == set(got)


def test_a_hand_made_list_and_an_adapter_made_list_drive_the_same_join_unchanged(tmp_path):
    """The planner's requirement: a second list in the normalised format drives the join with
    no change to the join, and gives the same answers where the two lists agree."""
    hand_path, hand_sha = _hand_list(tmp_path)
    book = _workbook(tmp_path)
    book_sha = hashlib.sha256(book.read_bytes()).hexdigest()
    adapted = tmp_path / "adapted.tsv"
    adapted_sha = ft.convert(book, adapted, book_sha)
    joins = [
        Join(load_list(hand_path, hand_sha), hand_sha, MYCORRHIZAL_GROUP, MAIN_RUN),
        Join(load_list(adapted, adapted_sha), adapted_sha, MYCORRHIZAL_GROUP, MAIN_RUN),
    ]
    for names in (_names("Alphamyces"), _names("Betamyces"), _names("Gammamyces"),
                  _names("Zetamyces")):  # fmt: skip
        assert joins[0].outcome(names) == joins[1].outcome(names), names
