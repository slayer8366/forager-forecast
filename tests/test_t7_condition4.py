"""P10b condition 4 as ruled (Forager RECORD -1187): each specimen scored by the map's mean over
its stated uncertainty circle; background matched to the specimens' road-distance mix and scored
the same way at the same radii; the whole box carries the verdict, the interior beside it.
Synthetic data only."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from forager_forecast.grid import GridCell, GridWindow
from forager_forecast.t7 import condition4 as c4
from forager_forecast.t7 import metrics as mt

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "t7_fit.py"
W = GridWindow(0, 0, 250 * 9, 250 * 9)  # 9 by 9 cells


def centre(r, c, window=W):
    return window.left + (c + 0.5) * 250, window.top - (r + 0.5) * 250


@pytest.fixture(scope="module")
def t7_fit():
    spec = importlib.util.spec_from_file_location("t7_fit_c4", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_road_bands_are_the_fixed_edges():
    got = c4.road_band(np.array([0.0, 49.9, 50.0, 260.0, 1999.0, 6000.0]))
    assert got.tolist() == [0, 0, 1, 3, 5, 7]
    with pytest.raises(ValueError):
        c4.road_band(np.array([np.nan]))


def test_circle_mean_averages_the_cells_whose_centres_lie_within_the_radius():
    raster = np.arange(81, dtype=np.float32).reshape(9, 9)
    x, y = centre(4, 4)
    assert c4.circle_mean(raster, W, x, y, 100.0) == 40.0  # own cell only
    assert c4.circle_mean(raster, W, x, y, 250.0) == pytest.approx(np.mean([40, 31, 49, 39, 41]))
    assert c4.circle_mean(raster, W, x, y, 360.0) == pytest.approx(raster[3:6, 3:6].mean())
    with_gap = raster.copy()
    with_gap[3, 4] = np.nan  # a masked neighbour is left out, never filled
    assert c4.circle_mean(with_gap, W, x, y, 250.0) == pytest.approx(np.mean([40, 49, 39, 41]))
    # an off-centre point: the eastern neighbour's centre is 130 m away
    assert c4.circle_mean(raster, W, x + 120, y, 130.0) == pytest.approx(np.mean([40, 41]))


def test_circle_mean_always_includes_the_points_own_cell():
    raster = np.arange(81, dtype=np.float32).reshape(9, 9)
    x, y = centre(4, 4)
    assert c4.circle_mean(raster, W, x + 124, y + 124, 10.0) == 40.0


def test_background_matches_the_specimens_road_mix_and_carries_their_radii():
    bands = np.array([0, 0, 3])
    radii = np.array([100.0, 200.0, 900.0])
    pool = np.arange(1000, 1100)
    pool_bands = pool % 4
    cells, r = c4.matched_background(bands, radii, pool, pool_bands, per_specimen=3, seed=1)
    assert len(cells) == 9 and len(r) == 9
    assert np.isin(cells, pool).all()
    got_bands = pool_bands[np.searchsorted(pool, cells)]
    assert sorted(got_bands.tolist()) == [0] * 6 + [3] * 3
    assert sorted(r.tolist()) == [100.0] * 3 + [200.0] * 3 + [900.0] * 3
    assert (got_bands[r == 900.0] == 3).all() and (got_bands[r < 900.0] == 0).all()
    assert len(set(cells.tolist())) == 9  # no cell drawn twice
    again, _ = c4.matched_background(bands, radii, pool, pool_bands, per_specimen=3, seed=1)
    assert (again == cells).all()
    with pytest.raises(ValueError, match="band"):
        c4.matched_background(np.array([3] * 10), np.ones(10), pool, pool_bands, per_specimen=3)


def test_auc_above_half_is_the_auc_minus_one_half_with_a_block_interval():
    rng = np.random.default_rng(2)
    n = 600
    y = (rng.random(n) < 0.2).astype(int)
    s = rng.normal(0, 1, n) + 0.8 * y
    blocks = rng.integers(0, 9, n)
    got = mt.auc_above_half(s, y, blocks, resamples=60)
    want = mt.clustered_auc_difference(s, np.zeros(n), y, np.ones(n), blocks, resamples=60)
    assert got.point == pytest.approx(mt.weighted_auc(s, y, np.ones(n)) - 0.5, abs=1e-12)
    assert (got.point, got.low, got.high) == pytest.approx((want.point, want.low, want.high))


def _scene(seed=4):
    """A 40 by 40 map rising to the east; specimens on the east half, a few on masked cells."""
    w = GridWindow(0, 0, 250 * 40, 250 * 40)
    rr, cc = np.mgrid[0:40, 0:40]
    raster = cc.astype(np.float32) / 40
    raster[:, :3] = np.nan  # masked cells
    # real packed master-grid ids, sorted as the table holds them
    pairs = zip(rr.ravel(), cc.ravel(), strict=True)
    ids = np.array([GridCell(col=int(c), row=39 - int(r)).id for r, c in pairs])
    order = np.argsort(ids)
    cell_id = ids[order]
    access = ((rr * 37 + cc * 11) % 3000 * 1.0).ravel()[order]
    level3 = ((rr // 5) * 8 + cc // 5).ravel()[order]  # 64 blocks
    scorable = np.isfinite(raster).ravel()[order]
    rng = np.random.default_rng(seed)
    spec_rc = [(int(r), int(c)) for r, c in zip(rng.integers(0, 40, 60), rng.integers(25, 40, 60),
                                               strict=True)]  # fmt: skip
    spec_rc += [(5, 1), (6, 2)]  # on masked cells: not scorable
    xs, ys = zip(*[(w.left + (c + 0.5) * 250, w.top - (r + 0.5) * 250) for r, c in spec_rc],
                 strict=True)  # fmt: skip
    spec_cell = np.array([GridCell(col=c, row=39 - r).id for r, c in spec_rc])
    radii = rng.choice([200.0, 600.0, 1000.0], len(spec_rc))
    interior = np.array([r < 20 for r, _ in spec_rc])
    return dict(raster=raster, window=w, spec_x=np.array(xs), spec_y=np.array(ys),
                spec_cell=spec_cell, spec_radius=radii, spec_interior=interior, cell_id=cell_id,
                access=access, level3=level3, scorable=scorable)  # fmt: skip


def test_condition_4_scores_specimens_against_matched_background_whole_box_and_interior():
    sc = _scene()
    got = c4.score_condition_4(**sc, per_specimen=5, seed=3, resamples=40)
    box, inner = got["whole_box"], got["interior_no_verdict"]
    assert box["specimens_in"] == 62 and box["specimens_not_scorable"] == 2
    assert box["specimens_scored"] == 60 and box["background"] == 300
    n_inner = int(sc["spec_interior"][:60].sum())
    assert inner["specimens_scored"] == n_inner and inner["background"] == 5 * n_inner
    assert isinstance(box["difference"], mt.Difference)
    assert box["difference"].point > 0.2  # specimens sit east, where the map is high
    assert box["background_road_bands"] == box["specimen_road_bands_times_per_specimen"]


def test_p10b_takes_condition_4_when_computed(t7_fit):
    ok, bad = mt.Difference(0.01, 0.005, 0.02, 1000), mt.Difference(0.01, -0.005, 0.02, 1000)
    got = t7_fit.p10b_figures(ok, ok, ok, "computed", p10_passes=False, condition_4=ok)
    assert got["verdict"] == "pass"
    assert got["conditions"]["4_independent_data"]["status"] == "computed"
    assert got["conditions"]["4_independent_data"]["low"] == 0.005
    got = t7_fit.p10b_figures(ok, ok, ok, "computed", p10_passes=False, condition_4=bad)
    assert got["verdict"] == "fail"
