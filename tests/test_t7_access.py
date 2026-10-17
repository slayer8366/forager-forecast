"""T7 part B: distances to synthetic lines with known answers, keying, and the trail rules."""

import numpy as np
import pytest
import shapely

from forager_forecast.grid import CELL_SIZE_M, GridWindow
from forager_forecast.t6b_mask import cell_lonlat
from forager_forecast.t7.access import (
    block_distances,
    cell_centres,
    combine,
    keep_road_class,
    keep_trail,
    nearest_distance,
)


def _line(*xy):
    return shapely.linestrings(np.array(xy, dtype=float))


def test_distance_perpendicular_beyond_an_end_on_the_line_and_the_nearer_of_two():
    a = _line((0, 0), (1000, 0))
    b = _line((0, 700), (1000, 700))
    x = np.array([500.0, 1300.0, 250.0, 500.0])
    y = np.array([300.0, -400.0, 0.0, 600.0])
    d = nearest_distance(np.array([a, b]), x, y)
    assert d.tolist() == pytest.approx([300.0, 500.0, 0.0, 100.0])


def test_a_multiline_counts_as_its_nearest_part():
    m = shapely.multilinestrings([_line((0, 0), (0, 10)), _line((100, 0), (100, 10))])
    assert nearest_distance(np.array([m]), np.array([90.0]), np.array([5.0])).tolist() == [10.0]


def test_no_lines_gives_nan_not_a_number_made_up():
    d = nearest_distance(np.array([], dtype=object), np.array([1.0, 2.0]), np.array([0.0, 0.0]))
    assert np.isnan(d).all()


def test_cell_centres_are_the_grid_convention():
    w = GridWindow(-1_000_000, 500_000, -1_000_000 + 3 * CELL_SIZE_M, 500_000 + 2 * CELL_SIZE_M)
    x, y = cell_centres(w)
    assert x.shape == (2, 3)
    assert x[0].tolist() == [-999_875.0, -999_625.0, -999_375.0]
    assert y[:, 0].tolist() == [500_375.0, 500_125.0]
    # the same centres t6b_mask.cell_lonlat (the keying used by T7) projects
    lon, lat = cell_lonlat(w)
    from pyproj import Transformer

    from forager_forecast.grid import GEOGRAPHIC_CRS, GRID_CRS

    gx, gy = Transformer.from_crs(GEOGRAPHIC_CRS, GRID_CRS, always_xy=True).transform(lon, lat)
    assert np.allclose(gx, x, atol=1e-4) and np.allclose(gy, y, atol=1e-4)


def test_block_distances_are_exact_when_the_nearest_line_is_far_outside_the_first_radius():
    w = GridWindow(0, 0, 4 * CELL_SIZE_M, 4 * CELL_SIZE_M)
    far = _line((0, 50_000), (1000, 50_000))  # 49 km north of the block
    near = _line((-300, -300), (-300, 2000))  # beside the block's west edge
    lines = np.array([far, near])
    calls = []

    def read(bbox):
        calls.append(bbox)
        return lines[shapely.intersects(lines, shapely.box(*bbox))]

    inside = np.ones((4, 4), dtype=bool)
    inside[0, 0] = False
    d = block_distances(read, w, inside, start_radius=1000.0)
    x, y = cell_centres(w)
    truth = nearest_distance(lines, x.ravel(), y.ravel()).reshape(4, 4)
    assert np.isnan(d[0, 0])
    assert np.allclose(d[inside], truth[inside])
    # only lines (west) within reach: the first bbox is the block widened by the start radius
    assert calls[0] == (-1000.0, -1000.0, 2000.0, 2000.0)

    only_far = np.array([far])
    d2 = block_distances(lambda b: only_far[shapely.intersects(only_far, shapely.box(*b))],
                         w, np.ones((4, 4), bool), start_radius=1000.0)  # fmt: skip
    assert d2[3, 0] == pytest.approx(50_000 - 125.0)  # bottom-left centre (125, 125)
    assert d2[0, 3] == pytest.approx(50_000 - 875.0)  # top-right centre (875, 875)


def test_block_distances_give_nan_when_no_line_exists_within_the_largest_radius():
    w = GridWindow(0, 0, 2 * CELL_SIZE_M, 2 * CELL_SIZE_M)
    d = block_distances(lambda b: np.array([], dtype=object), w, np.ones((2, 2), bool),
                        start_radius=1000.0, max_radius=5000.0)  # fmt: skip
    assert np.isnan(d).all()


def test_combine_takes_the_nearer_and_masks_unpublished_trail_cells():
    road = np.array([[100.0, 900.0], [50.0, np.nan]])
    trail = np.array([[300.0, 200.0], [10.0, 40.0]])
    unpublished = np.array([[False, False], [True, False]])
    t, a = combine(road, trail, unpublished)
    assert t[0].tolist() == [300.0, 200.0] and np.isnan(t[1, 0]) and t[1, 1] == 40.0
    assert a[0].tolist() == [100.0, 200.0]
    assert np.isnan(a[1, 0])  # never filled from the road alone where trails are unpublished
    assert np.isnan(a[1, 1])  # no road value: the combined band is not the trail alone
    assert road[1, 0] == 50.0  # the road band is untouched


def test_only_federal_trail_sources_are_kept():
    src = np.array(["U.S. Forest Service", "Bureau of Land Management", "National Park Service",
                    "U.S. Fish and Wildlife Service", "Continental Divide Trail Coalition",
                    "Utah Automated Geographic Reference Center (AGRC)", None, ""],
                   dtype=object)  # fmt: skip
    assert keep_trail(src).tolist() == [True, True, True, True, False, False, False, False]


def test_ferries_and_tunnels_are_not_roads_and_every_other_class_is():
    assert keep_road_class([1, 2, 3, 4, 5, 6, 7, 8, None]).tolist() == [
        True, True, True, True, True, True, False, False, False]  # fmt: skip
