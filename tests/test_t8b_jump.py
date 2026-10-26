"""Plan section 3's reading rule for the 2024-25 jump, on made-up totals only. No iNaturalist or
GBIF total is queried anywhere in this step."""

import pytest
from t8b_files import rule_all, unrule_all

from forager_forecast.t8b import design
from forager_forecast.t8b import jump_reporting as jr

T = jr.Totals


def steady():
    return {2023: T(1000, 900, 800, 700), 2024: T(2000, 1800, 1600, 1400)}


@pytest.mark.parametrize(
    "before, after, moved",
    [
        ((30, 100), (41, 100), True),
        ((30, 100), (39, 100), False),
        ((30, 100), (19, 100), True),
        ((30, 100), (21, 100), False),
        ((30, 100), (40, 100), False),  # exactly a third up is not "more than a third"
        ((30, 100), (20, 100), False),  # nor exactly a third down
        ((3, 10), (400, 1000), False),  # shares are compared exactly, not as floats
    ],
)
def test_a_share_moves_when_it_changes_by_more_than_a_third_of_itself(before, after, moved):
    assert jr.share_moved(before, after) is moved


def test_the_rule_refuses_while_its_readings_are_open(monkeypatch):
    unrule_all(monkeypatch)
    with pytest.raises(design.NotRuled):
        jr.read_rule(steady(), steady())


def test_chanterelle_accuracy_share_moving_alone_reads_partly_reporting(monkeypatch):
    rule_all(monkeypatch, "count")
    ch = {2023: T(100, 90, 50, 70), 2024: T(300, 280, 250, 210)}  # 0.50 -> 0.83
    out = jr.read_rule(ch, steady())
    assert out["label"] == design.PARTLY_REPORTING
    assert out["accuracy"]["chanterelle_moved"] and not out["accuracy"]["fungi_moved"]


def test_chanterelle_licence_share_moving_alone_reads_partly_reporting(monkeypatch):
    rule_all(monkeypatch, "count")
    ch = {2023: T(100, 90, 80, 70), 2024: T(300, 280, 240, 90)}  # licence 0.70 -> 0.30
    out = jr.read_rule(ch, steady())
    assert out["label"] == design.PARTLY_REPORTING
    assert out["licence"]["chanterelle_moved"]


def test_a_move_shared_by_all_fungi_stays_undetermined(monkeypatch):
    rule_all(monkeypatch, "count")
    ch = {2023: T(100, 90, 50, 70), 2024: T(300, 280, 250, 210)}
    fungi = {2023: T(1000, 900, 500, 700), 2024: T(2000, 1800, 1700, 1400)}  # 0.50 -> 0.85
    assert jr.read_rule(ch, fungi)["label"] == design.UNDETERMINED


def test_nothing_moving_stays_undetermined(monkeypatch):
    rule_all(monkeypatch, "count")
    assert jr.read_rule(steady(), steady())["label"] == design.UNDETERMINED


def test_a_year_with_no_records_has_no_share_and_stays_undetermined(monkeypatch):
    rule_all(monkeypatch, "count")
    ch = {2023: T(0, 0, 0, 0), 2024: T(300, 280, 250, 210)}
    out = jr.read_rule(ch, steady())
    assert out["label"] == design.UNDETERMINED
    assert "no records" in out["reason"]


def test_totals_that_do_not_nest_are_refused():
    with pytest.raises(ValueError, match="nest"):
        T(100, 90, 95, 70)
    with pytest.raises(ValueError, match="nest"):
        T(100, 90, 80, 170)
