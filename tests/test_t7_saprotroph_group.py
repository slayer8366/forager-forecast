"""T7 part C: the saprotroph comparison group's rule (D146; Forager RECORD -1164, -1167): the
mushroom-forming genera whose FungalTraits primary lifestyle is litter or soil saprotroph, not
unspecified saprotroph; genera with "ectomycorrhizal" in their secondary lifestyle or lifestyle
comment out; genera with a secondary lifestyle in a side run only; no genus shared with the
mycorrhizal group. Synthetic rows, then the committed export (D143)."""

import importlib.util
from pathlib import Path

import pytest

from forager_forecast.t7 import fungaltraits as ft
from forager_forecast.t7.fungaltraits import GenusTraits, saprotroph_genera
from forager_forecast.t7.membership import (
    IN_GROUP,
    MAIN_RUN,
    MYCORRHIZAL_GROUP,
    Join,
    ListRow,
    MembershipList,
    ectomycorrhizal_overlap,
)
from forager_forecast.t7.names import TaxonNames

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "t7_v9_counts.py"
# Forager RECORD -1167 item 2, verbatim list
THE_NINE = {"Hyaloscypha", "Peziza", "Entoloma", "Hydropus", "Sistotrema", "Ceratorhiza",
            "Epulorhiza", "Tulasnella", "Clavariadelphus"}  # fmt: skip


def _t(genus, primary, secondary="", comment="", fruit="agaricoid", family="Fam"):
    return GenusTraits(family, genus, primary, secondary, comment, fruit)


SYNTHETIC = [
    _t("Litter", "litter_saprotroph"),
    _t("Soil", "soil_saprotroph", fruit="gasteroid"),
    _t("LitterSecond", "litter_saprotroph", secondary="plant_pathogen"),
    _t("SoilComment", "soil_saprotroph", comment="also on dung"),
    _t("EcmSecond", "litter_saprotroph", secondary="ectomycorrhizal"),
    _t("EcmComment", "soil_saprotroph", comment="possibly Ectomycorrhizal"),
    _t("Unspecified", "unspecified_saprotroph"),
    _t("Flat", "litter_saprotroph", fruit="perithecium_(hymenium_hidden,_narrow_opening)"),
    _t("NoFruit", "soil_saprotroph", fruit=""),
    _t("Wood", "wood_saprotroph"),
    _t("Ecm", "ectomycorrhizal"),
]


def test_the_rule_takes_litter_and_soil_mushroom_formers_and_splits_main_from_side():
    g = saprotroph_genera(SYNTHETIC)
    assert g.main == ("Litter", "Soil", "SoilComment")
    assert g.side_only == ("LitterSecond",)
    assert g.excluded_ectomycorrhizal == ("EcmComment", "EcmSecond")


def test_unspecified_saprotroph_and_non_mushroom_formers_are_out():
    g = saprotroph_genera(SYNTHETIC)
    every = set(g.main) | set(g.side_only) | set(g.excluded_ectomycorrhizal)
    assert not every & {"Unspecified", "Flat", "NoFruit", "Wood", "Ecm"}


def test_a_qualifying_genus_on_two_rows_is_refused_not_resolved():
    rows = [*SYNTHETIC, _t("Litter", "plant_pathogen")]
    with pytest.raises(ValueError, match="Litter"):
        saprotroph_genera(rows)
    # a genus on two rows neither of which qualifies is no business of the rule
    saprotroph_genera([*SYNTHETIC, _t("Wood", "plant_pathogen")])


@pytest.fixture(scope="module")
def export_traits():
    return ft.read_traits_export()


def test_on_the_committed_export_the_nine_are_out_and_669_genera_meet_d146(export_traits):
    g = saprotroph_genera(export_traits)
    assert set(g.excluded_ectomycorrhizal) == THE_NINE
    assert len(g.main) + len(g.side_only) + len(g.excluded_ectomycorrhizal) == 669
    by = {t.genus: t for t in export_traits}
    assert all(not by[x].secondary for x in g.main)
    assert all(by[x].secondary for x in g.side_only)
    assert all(by[x].primary in ft.SAPROTROPH_LIFESTYLES for x in g.main + g.side_only)


def _members(rows):
    return MembershipList({r.genus: r for r in rows}, "sha")


def test_the_overlap_check_names_any_genus_the_list_classes_ectomycorrhizal():
    rows = [ListRow("A", None, "F", "ectomycorrhizal", "clear", "s", ""),
            ListRow("B", None, "F", "ectomycorrhizal", "mixed", "s", ""),
            ListRow("C", None, "F", "other", "clear", "s", "")]  # fmt: skip
    assert ectomycorrhizal_overlap(["A", "B", "C", "D"], _members(rows)) == {
        "A": "clear", "B": "mixed"}  # fmt: skip
    assert ectomycorrhizal_overlap(["C", "D"], _members(rows)) == {}


def test_on_the_committed_export_the_group_shares_no_genus_with_the_mycorrhizal_group(
    export_traits,
):
    members = _members(ft.to_list_rows(export_traits, "s"))
    g = saprotroph_genera(export_traits)
    assert ectomycorrhizal_overlap(g.main + g.side_only, members) == {}
    assert len(ectomycorrhizal_overlap(g.excluded_ectomycorrhizal, members)) == 9


@pytest.fixture(scope="module")
def counts():
    spec = importlib.util.spec_from_file_location("t7_v9_counts", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_count_runs_the_group_by_genus_through_the_v9_join(counts):
    g = ft.SaprotrophGenera(("Litter", "Soil"), ("LitterSecond",), ("EcmSecond",))
    runs = counts.saprotroph_runs(g)
    assert list(runs) == ["saprotroph_main", "saprotroph_side"]
    (main, main_run), (side, _) = runs["saprotroph_main"], runs["saprotroph_side"]
    assert main.genera == ("Litter", "Soil") and main.lifestyle is None and main_run == MAIN_RUN
    assert side.genera == ("Litter", "LitterSecond", "Soil")
    members = _members([ListRow("Litter", None, "Fam", "other", "clear", "s", "")])
    j = Join(members, "sha", main, MAIN_RUN)
    assert j.outcome(TaxonNames("Litter", "Fam", "Agaricales", "SPECIES")) == IN_GROUP
    assert not j.joins(TaxonNames("LitterSecond", "Fam", "Agaricales", "SPECIES"))
    assert not j.joins(TaxonNames("EcmSecond", "Fam", "Agaricales", "SPECIES"))
    # D144 rule 2: records named only to family stay out
    assert not j.joins(TaxonNames("", "Fam", "Agaricales", "FAMILY"))
    assert MYCORRHIZAL_GROUP.lifestyle == "ectomycorrhizal"
