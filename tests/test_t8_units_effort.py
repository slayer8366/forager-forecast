"""T8's units (T1's exactly), the lichen attach, and E1 per held-out year. Synthetic data only."""

import hashlib
from datetime import date

import numpy as np
import pytest

from forager_forecast import effort as ef
from forager_forecast.cells import Cell
from forager_forecast.records.occurrence import Record
from forager_forecast.t8 import effort_term as et
from forager_forecast.t8 import units as tu


def record(gbif_id, lat, lon, day, genus=None, class_key=None, observer="ann"):
    return Record(
        gbif_id=gbif_id,
        taxon_key=gbif_id,
        genus_key=genus,
        latitude=lat,
        longitude=lon,
        event_date=day,
        event_time=None,
        coordinate_uncertainty_m=10.0,
        license="CC_BY_4_0",
        dataset_key="d",
        recorded_by=observer,
        class_key=class_key,
    )


def t1_file(tmp_path, units, y, p=None, cells=None, years=None):
    p = np.full(len(units), 0.02) if p is None else p
    cells = [u.split("@")[0] for u in units] if cells is None else cells
    years = (
        [date.fromisoformat(u.split("@")[1]).isocalendar().year for u in units]
        if years is None
        else years
    )
    path = tmp_path / "t1.npz"
    np.savez_compressed(
        path,
        unit=np.array(units),
        cell=np.array(cells),
        year=np.array(years),
        y=np.array(y, dtype=float),
        p=np.array(p, dtype=float),
        land_point=np.array(["own"] * len(units)),
    )
    return path


UNITS = ["470_-1230@2020-09-14", "470_-1230@2020-09-21", "471_-1230@2021-01-04"]


def test_t1_units_read_back_with_cells_weeks_and_years(tmp_path):
    t1 = tu.read_t1_units(t1_file(tmp_path, UNITS, [1, 0, 0]))
    assert len(t1) == 3
    assert t1.cells[2] == Cell(471, -1230)
    assert t1.iso_weeks == [38, 39, 1]
    assert t1.year.tolist() == [2020, 2020, 2021]


def test_a_unit_whose_year_disagrees_with_its_id_is_refused(tmp_path):
    path = t1_file(tmp_path, UNITS, [1, 0, 0], years=[2020, 2020, 2020])
    with pytest.raises(tu.UnitsDiffer, match="disagrees"):
        tu.read_t1_units(path)


def test_the_same_units_pass_and_one_differing_outcome_is_refused(tmp_path):
    t1 = tu.read_t1_units(t1_file(tmp_path, UNITS, [1, 0, 0]))
    recounted = {UNITS[0]: 1.0, UNITS[1]: 0.0, UNITS[2]: 0.0, "999_-1230@2020-09-14": 0.0}
    tu.check_same_units(t1, recounted, expected_extra=1, expected_total=3)
    recounted[UNITS[1]] = 1.0
    with pytest.raises(tu.UnitsDiffer, match="1 outcomes differ"):
        tu.check_same_units(t1, recounted, expected_extra=1, expected_total=3)


def test_one_missing_unit_or_one_extra_is_refused(tmp_path):
    t1 = tu.read_t1_units(t1_file(tmp_path, UNITS, [1, 0, 0]))
    with pytest.raises(tu.UnitsDiffer, match="1 T1 units not recounted"):
        tu.check_same_units(t1, {UNITS[0]: 1.0, UNITS[1]: 0.0}, 0, 3)
    extra = {u: v for u, v in zip(UNITS, [1.0, 0.0, 0.0], strict=True)}
    extra["999_-1230@2020-09-14"] = 0.0
    with pytest.raises(tu.UnitsDiffer, match="1 recounted units beyond"):
        tu.check_same_units(t1, extra, 0, 3)
    with pytest.raises(tu.UnitsDiffer, match="expected 52718"):
        tu.check_same_units(t1, extra, 1, 52718)


def test_recount_builds_t1s_units_and_outcomes():
    survivors = [
        record(1, 47.0, -123.0, date(2020, 9, 15), genus=9623860),
        record(2, 47.0, -123.0, date(2020, 9, 22)),
        record(3, 47.1, -123.0, date(2021, 1, 5)),
        record(4, 47.1, -123.0, date(2015, 1, 1)),  # ISO week 2015-W01 starts in 2014: not a unit
    ]
    assert tu.recount_units(survivors, 9623860) == {
        UNITS[0]: 1.0,
        UNITS[1]: 0.0,
        UNITS[2]: 0.0,
    }


def test_lichens_attach_to_their_unit_as_outcome_and_outings(tmp_path):
    t1 = tu.read_t1_units(t1_file(tmp_path, UNITS, [1, 0, 0]))
    survivors = [
        record(1, 47.0, -123.0, date(2020, 9, 15), class_key=180, observer="a"),
        record(2, 47.0, -123.0, date(2020, 9, 15), class_key=180, observer="a"),
        record(3, 47.0, -123.0, date(2020, 9, 16), class_key=180, observer="a"),
        record(4, 47.0, -123.0, date(2020, 9, 16), class_key=180, observer="b"),
        record(5, 47.0, -123.0, date(2020, 9, 22), class_key=99),  # not a lichen
        record(6, 49.0, -123.0, date(2020, 9, 22), class_key=180),  # in no T1 unit
    ]
    lichens = tu.attach_lichens(t1, survivors)
    assert lichens.positive.tolist() == [1.0, 0.0, 0.0]
    assert lichens.records.tolist() == [4, 0, 0]
    assert lichens.outings.tolist() == [3, 0, 0]
    assert lichens.outside_units == 1


# E1 ----------------------------------------------------------------------------------------


def synthetic_counts(seed=0, scale=1.0):
    """Outings drawn from known parts on 5 cells in two bands, over T6's whole frame."""
    rng = np.random.default_rng(seed)
    cells = [
        Cell(470, -1230),
        Cell(471, -1230),
        Cell(472, -1231),
        Cell(510, -1230),
        Cell(511, -1231),
    ]
    weeks = ef.frame_weeks()
    a = rng.uniform(0.5, 3.0, len(cells))
    yl = rng.uniform(0.5, 2.0, len(ef.YEARS))
    s = 1.0 + 0.8 * np.sin(np.linspace(0, 2 * np.pi, ef.N_SLOTS))
    entries = []
    for c in range(len(cells)):
        for w, week in enumerate(weeks):
            for d in (0, 1):
                m = scale * a[c] * yl[ef.YEARS.index(week.year)] * s[ef.season_slot(week)]
                m *= (0.9, 0.4)[d] * ef.DAYS_PER_TYPE[d]
                v = rng.poisson(m)
                if v:
                    entries.append((c, w, d, float(v)))
    return ef.OutingCounts.from_entries(cells, entries)


CONFIG = ef.Config(10.0, 3)
E_CELLS = [Cell(470, -1230), Cell(510, -1230), Cell(471, -1230)]
E_MONDAYS = [date(2019, 9, 16), date(2020, 9, 14), date(2021, 1, 4)]


def test_the_held_out_years_outings_never_reach_its_own_effort():
    fungi, lichen = synthetic_counts(1), synthetic_counts(2, 0.3)
    before = et.fold_effort(fungi, lichen, 2020, CONFIG, E_CELLS, E_MONDAYS)
    # Double every outing in 2020, in both tables.
    bumped = []
    for counts in (fungi, lichen):
        count = counts.count.copy()
        count[counts.entry_year == ef.YEARS.index(2020)] *= 2.0
        bumped.append(
            ef.OutingCounts.from_entries(
                counts.cells,
                zip(
                    counts.cell.tolist(),
                    counts.week.tolist(),
                    counts.day.tolist(),
                    count.tolist(),
                    strict=True,
                ),
            )
        )
    after = et.fold_effort(bumped[0], bumped[1], 2020, CONFIG, E_CELLS, E_MONDAYS)
    assert after.log_effort[1] == pytest.approx(before.log_effort[1], rel=1e-9)
    # A unit in a training year of another fold does see 2020's outings.
    other = et.fold_effort(fungi, lichen, 2019, CONFIG, E_CELLS, E_MONDAYS)
    other_after = et.fold_effort(bumped[0], bumped[1], 2019, CONFIG, E_CELLS, E_MONDAYS)
    assert other_after.log_effort[1] != pytest.approx(other.log_effort[1], rel=1e-6)


def test_the_held_out_level_is_the_geometric_mean_of_its_neighbours():
    fungi, lichen = synthetic_counts(1), synthetic_counts(2, 0.3)
    fold = et.fold_effort(fungi, lichen, 2020, CONFIG, E_CELLS, E_MONDAYS)
    surface = et.fold_surface(fungi, lichen, 2020, CONFIG)
    y19, y21 = surface.year_level[ef.YEARS.index(2019)], surface.year_level[ef.YEARS.index(2021)]
    assert fold.interpolated_level == pytest.approx(np.sqrt(y19 * y21))
    # The 2020 unit's value is the surface's product at that level; the 2021 unit's at its own.
    weekly = (surface.day_rate * ef.DAYS_PER_TYPE).sum()
    for i, level in ((1, fold.interpolated_level), (2, y21)):
        ci = fungi.cells.index(E_CELLS[i])
        week = date.fromisocalendar(*E_MONDAYS[i].isocalendar()[:2], 1).isocalendar()
        slot = min(week.week, ef.N_SLOTS) - 1
        expect = surface.cell_level[ci] * level * surface.season[fungi.cell_band[ci], slot] * weekly
        assert np.exp(fold.log_effort[i]) == pytest.approx(expect, rel=1e-12)


def test_a_cell_outside_t6s_frame_is_refused():
    fungi, lichen = synthetic_counts(1), synthetic_counts(2, 0.3)
    with pytest.raises(ef.NoEffortValue, match="1 unit cell"):
        et.fold_effort(fungi, lichen, 2020, CONFIG, [Cell(999, -1230)], [E_MONDAYS[0]])


def test_counts_are_refused_when_their_sha256_differs(tmp_path):
    fungi = synthetic_counts(1)
    path = tmp_path / "all_fungi.npz"
    np.savez(
        path,
        lat_tenths=np.array([c.lat_tenths for c in fungi.cells]),
        lon_tenths=np.array([c.lon_tenths for c in fungi.cells]),
        cell=fungi.cell,
        week=fungi.week,
        day=fungi.day,
        count=fungi.count,
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path / "SHA256SUMS").write_text(f"{digest}  all_fungi.npz\n")
    back = et.read_counts(tmp_path, "all_fungi.npz")
    assert back.cells == fungi.cells and np.array_equal(back.count, fungi.count)
    (tmp_path / "SHA256SUMS").write_text(f"{'0' * 64}  all_fungi.npz\n")
    with pytest.raises(et.CountsChanged, match="differs"):
        et.read_counts(tmp_path, "all_fungi.npz")


def test_fold_configurations_are_read_from_t6s_results():
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    chosen = et.chosen_per_fold(repo / "docs/audits/2026-10-06-t6-fit/all_results.json")
    assert chosen[2020] == ef.Config(10.0, 5)
    assert chosen[2021] == ef.Config(10.0, 9)
    assert chosen[2024] == ef.Config(10.0, 3)
    with pytest.raises(ValueError, match="grid"):
        et.parse_config("pull=11,smoothing=3")
