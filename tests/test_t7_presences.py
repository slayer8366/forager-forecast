"""T7 item 6: presences through R6, the box, the join; thinning; M3 (b) weights. Synthetic only."""

from datetime import date

import numpy as np
import pytest

from forager_forecast.cells import cell_for
from forager_forecast.grid import cell_for_lonlat
from forager_forecast.records.occurrence import Record
from forager_forecast.t4_layer import LonLatBox
from forager_forecast.t7.membership import (
    IN_GROUP,
    MAIN_RUN,
    MYCORRHIZAL_GROUP,
    NOT_LISTED,
    Join,
    ListRow,
    load_list,
    write_list,
)
from forager_forecast.t7.names import TaxonNames
from forager_forecast.t7.presences import (
    OUTSIDE_BOX,
    POOLED,
    Presence,
    R6Violation,
    genus_weights,
    select_presences,
    thin,
)

BOX = LonLatBox(south=40.0, north=49.0, west=-125.0, east=-111.0)


def _join(tmp_path):
    path = tmp_path / "list.tsv"
    sha = write_list(path, [
        ListRow("Alphamyces", None, "Alphaceae", "ectomycorrhizal", "clear", "hand", "x"),
        ListRow("Betamyces", None, "Alphaceae", "ectomycorrhizal", "clear", "hand", "x"),
    ])  # fmt: skip
    return Join(load_list(path, sha), sha, MYCORRHIZAL_GROUP, MAIN_RUN)


def _rec(gid, lat=45.5, lon=-122.5, unc=10.0, day=date(2020, 10, 1), who="a", withheld=""):
    return Record(gbif_id=gid, taxon_key=gid, genus_key=None, latitude=lat, longitude=lon,
                  event_date=day, event_time=None, coordinate_uncertainty_m=unc,
                  license="CC_BY_4_0", recorded_by=who, information_withheld=withheld)  # fmt: skip


def _n(genus):
    return TaxonNames(genus, "Alphaceae", "", "SPECIES")


def test_records_pass_r6_the_box_and_the_join_and_every_drop_is_counted(tmp_path):
    named = [
        (_rec(1), _n("Alphamyces")),
        (_rec(2, unc=300.0), _n("Alphamyces")),  # R6: above 250 m
        (_rec(3, unc=None), _n("Alphamyces")),  # R6: no stated uncertainty
        (_rec(4, withheld="coordinates generalised"), _n("Alphamyces")),  # obscured
        (_rec(5, lat=50.5), _n("Alphamyces")),  # outside the box
        (_rec(6), _n("Zetamyces")),  # not listed
        (_rec(7, who="b"), _n("Betamyces")),
    ]
    presences, counts = select_presences(named, _join(tmp_path), BOX)
    assert [p.gbif_id for p in presences] == [1, 7]
    p = presences[0]
    cell = cell_for_lonlat(-122.5, 45.5)
    weather = cell_for(45.5, -122.5)
    assert (p.genus, p.cell_id, p.lat_tenths, p.lon_tenths, p.year) == (
        "Alphamyces",
        cell.id,
        weather.lat_tenths,
        weather.lon_tenths,
        2020,
    )
    assert counts.outcomes[OUTSIDE_BOX] == 1
    assert counts.outcomes[NOT_LISTED] == 1 and counts.outcomes[IN_GROUP] == 2
    steps = {s["step"]: s["dropped"] for s in counts.as_dict()["r6_steps"]}
    assert steps["coordinate_uncertainty"] == 2 and steps["user_obscured"] == 1
    assert all(q.uncertainty_m <= 250 for q in presences)


def test_a_record_above_250_m_reaching_the_table_stops_the_run(tmp_path, monkeypatch):
    import forager_forecast.t7.presences as module

    def steps():
        from forager_forecast.records.filters import FilterStep, Steps, r6_audit_steps

        real = r6_audit_steps()
        return Steps(filters=(FilterStep("lax", lambda _r: False),), duplicate=real.duplicate)

    monkeypatch.setattr(module, "r6_audit_steps", steps)
    with pytest.raises(R6Violation):
        select_presences([(_rec(2, unc=900.0), _n("Alphamyces"))], _join(tmp_path), BOX)


def _p(gid, genus, cell):
    return Presence(gid, genus, cell, 455, -1225, 2020, 10.0, "CC_BY_4_0")


def test_thinning_keeps_one_presence_per_genus_and_cell_the_lowest_gbif_id():
    kept = thin([_p(9, "A", 1), _p(3, "A", 1), _p(4, "B", 1), _p(5, "A", 2)])
    assert sorted((p.gbif_id, p.genus, p.cell_id) for p in kept) == [
        (3, "A", 1), (4, "B", 1), (5, "A", 2)]  # fmt: skip


def test_each_genus_at_the_minimum_weighs_one_and_the_small_genera_weigh_one_together():
    ps = [_p(i, "Big", i) for i in range(6)] + [_p(10 + i, "Mid", i) for i in range(3)]
    ps += [_p(20, "Tiny", 1), _p(21, "Rare", 2)]
    gw = genus_weights(ps, min_presences=3)
    w = dict(zip([p.gbif_id for p in ps], gw.weights.tolist(), strict=True))
    assert w[0] == pytest.approx(1 / 6) and w[10] == pytest.approx(1 / 3)
    assert w[20] == pytest.approx(1 / 2) and w[21] == pytest.approx(1 / 2)
    assert gw.unit_of == {"Big": "Big", "Mid": "Mid", "Tiny": POOLED, "Rare": POOLED}
    assert gw.presences_per_unit == {"Big": 6, "Mid": 3, POOLED: 2}
    assert np.isclose(gw.weights.sum(), 3.0)
