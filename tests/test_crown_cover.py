"""Crown width, crown area and plot canopy cover from a tree list (D87).

Sources: Bechtold 2004 (WJAF 19(4):245-251), Equation 3 and Table 3; Crookston and Stage 1999
(RMRS-GTR-24), equations 1 and 2. docs/audits/2026-10-06-t5-verify-report.md, section 2.
"""

import math

import pytest

from forager_forecast.crown_cover import (
    BECHTOLD_2004_EQ3,
    MIN_DBH_IN,
    Tree,
    UnknownGenus,
    crown_width_for,
    plot_cover,
)


def tree(spcd, genus, dbh, tpa=6.018046, live=True):
    return Tree(spcd=spcd, genus=genus, dbh_in=dbh, tpa=tpa, live=live)


def test_table_3_coefficients_reproduce_hand_values():
    # Douglas-fir: 5.7753 + 1.0639 D - 0.0109 D^2
    width, used = crown_width_for(202, "Pseudotsuga", 20.0)
    assert width == pytest.approx(5.7753 + 1.0639 * 20 - 0.0109 * 400)
    assert used == 202
    # Pacific silver fir has no quadratic term.
    assert crown_width_for(11, "Abies", 10.0)[0] == pytest.approx(7.3037 + 0.5909 * 10)
    # Oregon white oak has the largest quadratic term in the table.
    assert crown_width_for(815, "Quercus", 10.0)[0] == pytest.approx(-1.3160 + 29.311 - 8.66)
    # Western hemlock and mountain hemlock, the strip's main hosts after Douglas-fir.
    assert crown_width_for(263, "Tsuga", 12.0)[0] == pytest.approx(
        5.0036 + 1.1808 * 12 - 0.0107 * 144
    )
    assert crown_width_for(264, "Tsuga", 12.0)[0] == pytest.approx(3.2343 + 0.6927 * 12)


def test_the_table_has_the_papers_53_species():
    assert len(BECHTOLD_2004_EQ3) == 53


def test_a_species_missing_from_the_table_takes_its_genus_mate_with_most_observations():
    # Alaska yellow-cedar (42) is not in Table 3; Port-Orford cedar (41) is its only genus mate.
    width, used = crown_width_for(42, "Chamaecyparis", 10.0)
    assert used == 41
    assert width == pytest.approx(2.3625 + 0.9974 * 10)
    # Subalpine larch (72) takes western larch (73).
    assert crown_width_for(72, "Larix", 10.0)[1] == 73
    # Black cottonwood (747) takes quaking aspen (746, n = 1383), not narrowleaf cottonwood
    # (749, n = 44).
    assert crown_width_for(747, "Populus", 10.0)[1] == 746
    # An unlisted maple takes bigleaf maple, not a woodland maple whose D is root-collar diameter.
    assert crown_width_for(324, "Acer", 10.0)[1] == 312


def test_woodland_species_are_never_surrogates():
    # Every Table 3 juniper is a woodland species (D is root-collar diameter), so an unlisted
    # juniper takes the softwood default, not a juniper.
    assert crown_width_for(68, "Juniperus", 10.0)[1] == 202


def test_a_species_with_no_genus_mate_takes_its_class_default():
    assert crown_width_for(542, "Fraxinus", 10.0)[1] == 746  # hardwood: quaking aspen
    assert crown_width_for(231, "Taxus", 10.0)[1] == 202  # softwood: Douglas-fir


def test_an_unknown_genus_is_refused_rather_than_guessed():
    with pytest.raises(UnknownGenus):
        crown_width_for(9999, "Notagenus", 10.0)


def test_plot_cover_follows_crookston_and_stage_equations_1_and_2():
    # One Douglas-fir, D = 20 in, TPA 6.018046.
    width = 5.7753 + 1.0639 * 20 - 0.0109 * 400
    area = math.pi * (width / 2) ** 2
    c_prime = 100 * 6.018046 * area / 43560
    expected = 100 * (1 - math.exp(-0.01 * c_prime))
    cover = plot_cover([tree(202, "Pseudotsuga", 20.0)])
    assert cover.total == pytest.approx(expected)
    assert cover.by_band["Pseudotsuga"] == pytest.approx(expected)
    assert cover.by_band["conifer"] == pytest.approx(expected)
    assert cover.by_band["broadleaf"] == 0.0
    assert cover.by_band["Tsuga"] == 0.0


def test_genus_covers_split_the_overlap_corrected_total_by_crown_area():
    trees = [
        tree(202, "Pseudotsuga", 20.0),
        tree(263, "Tsuga", 14.0, tpa=12.0),
        tree(815, "Quercus", 9.0, tpa=30.0),
        tree(351, "Alnus", 8.0, tpa=20.0),
    ]
    cover = plot_cover(trees)
    pa = {}
    for t in trees:
        w = crown_width_for(t.spcd, t.genus, t.dbh_in)[0]
        pa[t.genus] = t.tpa * math.pi * (w / 2) ** 2
    total_pa = sum(pa.values())
    for genus in ("Pseudotsuga", "Tsuga", "Quercus"):
        assert cover.by_band[genus] == pytest.approx(cover.total * pa[genus] / total_pa)
    assert cover.by_band["conifer"] == pytest.approx(
        cover.total * (pa["Pseudotsuga"] + pa["Tsuga"]) / total_pa
    )
    assert cover.by_band["broadleaf"] == pytest.approx(
        cover.total * (pa["Quercus"] + pa["Alnus"]) / total_pa
    )
    assert cover.by_band["conifer"] + cover.by_band["broadleaf"] == pytest.approx(cover.total)


def test_dead_trees_and_trees_under_5_inches_carry_no_crown():
    assert MIN_DBH_IN == 5.0
    cover = plot_cover([tree(202, "Pseudotsuga", 4.9), tree(263, "Tsuga", 20.0, live=False)])
    assert cover.total == 0.0
    assert cover.by_band["Pseudotsuga"] == 0.0
    edge = plot_cover([tree(202, "Pseudotsuga", 5.0)])
    assert edge.total > 0


def test_surrogates_are_counted_and_their_widths_can_be_scaled():
    trees = [tree(202, "Pseudotsuga", 20.0), tree(542, "Fraxinus", 12.0, tpa=20.0)]
    base = plot_cover(trees)
    assert base.surrogate_trees == 1
    assert base.surrogate_species == {542: 746}
    wider = plot_cover(trees, surrogate_width_scale=1.3)
    narrower = plot_cover(trees, surrogate_width_scale=0.7)
    # Only the ash's crown changes, so the broadleaf share moves with the scale.
    assert narrower.by_band["broadleaf"] / narrower.total < base.by_band["broadleaf"] / base.total
    assert wider.by_band["broadleaf"] / wider.total > base.by_band["broadleaf"] / base.total


def test_a_diameter_beyond_the_fitted_range_takes_the_width_at_the_largest_fitted_diameter():
    # D91 (Amendment 3, F2 of the T5 review). Western redcedar's quadratic crosses zero near 74 in,
    # and the strip held 28 redcedars beyond that, which the first build dropped. Bechtold's
    # Table 1 fitted redcedar up to 62.0 in.
    capped, used = crown_width_for(242, "Thuja", 80.0)
    at_max, _ = crown_width_for(242, "Thuja", 62.0)
    assert used == 242
    assert capped == pytest.approx(at_max)
    assert capped > 0
    cover = plot_cover([tree(242, "Thuja", 80.0, tpa=6.0)])
    assert cover.total > 0
    assert cover.capped_trees == 1
    assert cover.nonpositive_width_trees == 0
    # Douglas-fir was fitted to 68.7 in.
    assert crown_width_for(202, "Pseudotsuga", 120.0)[0] == pytest.approx(
        crown_width_for(202, "Pseudotsuga", 68.7)[0]
    )
    # Inside the range nothing changes, and nothing is counted.
    inside = plot_cover([tree(242, "Thuja", 40.0)])
    assert inside.capped_trees == 0


def test_a_surrogate_is_capped_at_its_coefficients_species_range():
    # Oregon ash takes quaking aspen's coefficients, fitted to 19.9 in.
    assert crown_width_for(542, "Fraxinus", 30.0)[0] == pytest.approx(
        crown_width_for(746, "Populus", 19.9)[0]
    )


def test_a_non_positive_width_is_counted_not_dropped_silently(monkeypatch):
    from forager_forecast import crown_cover

    monkeypatch.setitem(crown_cover.BECHTOLD_2004_EQ3, 202, (-50.0, 0.0, 0.0))
    cover = plot_cover([tree(202, "Pseudotsuga", 20.0), tree(263, "Tsuga", 20.0)])
    assert cover.nonpositive_width_trees == 1
    assert cover.by_band["Pseudotsuga"] == 0.0
    assert cover.by_band["Tsuga"] == pytest.approx(cover.total)


# D116 (T6b, Forager RECORD -615): genera outside T5's lists are classed by FIA species code.


def test_an_unlisted_genus_is_classed_by_its_fia_code_when_t6b_asks():
    from forager_forecast.crown_cover import Tree, plot_cover

    hickory = Tree(spcd=407, genus="Carya", dbh_in=12.0, tpa=20.0, live=True)
    cypress = Tree(spcd=221, genus="Taxodium", dbh_in=12.0, tpa=20.0, live=True)
    fir = Tree(spcd=202, genus="Pseudotsuga", dbh_in=12.0, tpa=20.0, live=True)
    c = plot_cover([hickory, cypress, fir], classify_unlisted_by_spcd=True)
    # Each of the three takes the same crown (Douglas-fir's width for the two unlisted ones'
    # class defaults: hickory gets quaking aspen's, cypress Douglas-fir's), so compare by class.
    only_fir = plot_cover([fir])
    assert c.by_band["Pseudotsuga"] < c.total
    assert c.by_band["broadleaf"] > 0  # the hickory
    assert c.by_band["conifer"] > c.by_band["Pseudotsuga"]  # the cypress joins the conifers
    assert abs(c.by_band["conifer"] + c.by_band["broadleaf"] - c.total) < 1e-9
    # Never a host: no host band takes either unlisted tree.
    hosts = ("Tsuga", "Picea", "Abies", "Pinus", "Quercus")
    assert all(c.by_band[h] == 0 for h in hosts)
    assert c.unlisted_genus_trees == 2
    assert only_fir.unlisted_genus_trees == 0


def test_the_fia_code_split_is_at_300():
    from forager_forecast.crown_cover import is_conifer

    assert is_conifer("Notagenus", spcd=299) is True
    assert is_conifer("Notagenus", spcd=300) is False
    with pytest.raises(UnknownGenus):  # T5's refusal stands without a code
        is_conifer("Notagenus")
