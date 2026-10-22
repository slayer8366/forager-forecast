"""T8's ecoregion assignment on synthetic polygons in the CEC plane."""

import numpy as np

from forager_forecast.cells import Cell
from forager_forecast.t8 import ecoregions as eco


def square(cx, cy, half):
    return np.array(
        [[cx - half, cy - half], [cx - half, cy + half], [cx + half, cy + half],
         [cx + half, cy - half], [cx - half, cy - half]]
    )  # fmt: skip


CELLS = [Cell(470, -1230), Cell(455, -1220), Cell(430, -1240)]


def test_centres_fall_in_their_polygon_holes_are_honoured_and_misses_are_none():
    pts = eco.project_centres(CELLS)
    a = (pts[0, 0], pts[0, 1])
    polygons = [
        ("6.2.7", [square(*a, 20_000)]),
        # A ring around the second centre with a hole over it: not inside.
        ("7.1.8", [square(pts[1, 0], pts[1, 1], 20_000), square(pts[1, 0], pts[1, 1], 5_000)]),
    ]
    codes, shared = eco.assign(CELLS, polygons)
    assert codes == ["6.2.7", eco.NO_BLOCK, eco.NO_BLOCK]
    assert shared == 0


def test_a_centre_claimed_twice_takes_the_lower_code_and_is_counted():
    pts = eco.project_centres(CELLS[:1])
    ring = square(pts[0, 0], pts[0, 1], 10_000)
    codes, shared = eco.assign(CELLS[:1], [("7.1.8", [ring]), ("6.2.7", [ring])])
    assert codes == ["6.2.7"]
    assert shared == 1


def test_projection_puts_the_box_west_of_the_plane_origin():
    pts = eco.project_centres(CELLS)
    assert (pts[:, 0] < 0).all()  # the plane's origin is 100 W
