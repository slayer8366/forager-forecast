"""The PNW render (RECORD -772): tiles put together, US halves read, labels and sources carried."""

import numpy as np
import rasterio
from rasterio.transform import from_origin

from forager_forecast.grid import CELL_SIZE_M, GRID_CRS, GridWindow
from forager_forecast.pnw import (
    DATA_LICENCE,
    LABEL,
    SOURCES,
    TILE_MISSING,
    TILE_US_HALF,
    TILE_WHOLE,
    LegendEntry,
    assemble,
    png_bytes,
    ramp,
    svg_image,
    tree_file_for,
)
from forager_forecast.t6b_layers import Tile

N = 4


def _tile_file(path, tile, value):
    w = tile.window
    with rasterio.open(path, "w", driver="GTiff", width=N, height=N, count=2, dtype="float32",
                       crs=GRID_CRS, transform=from_origin(w.left, w.top, CELL_SIZE_M,
                                                           CELL_SIZE_M)) as dst:  # fmt: skip
        dst.write(np.full((N, N), value, "float32"), 1)
        dst.write(np.arange(N * N, dtype="float32").reshape(N, N), 2)
        dst.set_band_description(1, "a")
        dst.set_band_description(2, "b")


def test_tiles_are_put_together_whole_first_then_us_half_and_a_missing_tile_is_flagged(tmp_path):
    whole, half = tmp_path / "trees", tmp_path / "trees" / "trees_us_half"
    half.mkdir(parents=True)
    t1, t2, t3 = Tile(0, 0, N), Tile(1, 0, N), Tile(0, 1, N)
    _tile_file(whole / f"trees_{t1.key}.tif", t1, 1.0)
    _tile_file(half / f"trees_us_half_{t2.key}.tif", t2, 2.0)
    _tile_file(whole / f"trees_{t2.key}.tif", t2, 3.0)  # whole wins over the US half
    _tile_file(half / f"trees_us_half_{t3.key}.tif", t3, 4.0)
    assert tree_file_for(whole, half, t1.key)[1] == TILE_WHOLE
    assert tree_file_for(whole, half, t3.key)[1] == TILE_US_HALF
    assert tree_file_for(whole, half, Tile(1, 1, N).key) == (None, TILE_MISSING)
    s = N * CELL_SIZE_M
    window = GridWindow(s // 2, s // 2, 2 * s - s // 2 + s // 2, 2 * s)  # straddles all four
    values, missing = assemble(window, N, lambda k: tree_file_for(whole, half, k)[0], "a")
    assert values.shape == (window.height, window.width)
    # rows north to south: 4 rows of tiles j=1, then 2 of j=0; 2 columns of i=0, then 4 of i=1
    assert set(np.unique(values[:4, :2])) == {4.0}
    assert np.isnan(values[:4, 2:]).all() and missing[:4, 2:].all() and missing.sum() == 16
    assert set(np.unique(values[4:, :2])) == {1.0}
    assert set(np.unique(values[4:, 2:])) == {3.0}
    b, _ = assemble(window, N, lambda k: tree_file_for(whole, half, k)[0], "b")
    assert b[-1, 0] == 1 * N + 2  # tile (0, 0), its row 1 from the top, column 2


def test_the_ramp_is_transparent_for_no_data_and_clips_its_ends():
    rgba = ramp(np.array([np.nan, -1.0, 0.0, 1.0, 2.0]), 0.0, 1.0)
    assert rgba[0, 3] == 0 and (rgba[1:, 3] == 255).all()
    assert rgba[1].tolist() == rgba[2].tolist() == [68, 1, 84, 255]
    assert rgba[3].tolist() == rgba[4].tolist() == [253, 231, 37, 255]


def test_the_image_carries_the_label_every_source_and_the_data_licence():
    png = png_bytes(ramp(np.array([[0.0, 1.0]]), 0.0, 1.0))
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    svg = svg_image(png, 2, 1, "Douglas-fir & co", "sub", (0.0, 100.0, "%"),
                    [LegendEntry((190, 190, 190, 255), "Canada: pending")], SOURCES["trees"],
                    [[(0, 0), (1, 1)]], [("Seattle", 1.0, 0.5)])  # fmt: skip
    assert LABEL in svg and "Douglas-fir &amp; co" in svg and "Seattle" in svg
    flat = " ".join(svg.split())
    import html

    for s in [*SOURCES["trees"], DATA_LICENCE]:
        words = html.escape(s).split()
        assert all(w in flat for w in words), s
    assert "TreeMap 2023" in svg and "CC BY-NC 4.0" in svg and "Not a forecast" in svg


def test_the_blocked_box_mask_equals_the_whole_one():
    from forager_forecast.pnw import PNW_BOX, in_box
    from forager_forecast.t4_layer import box_mask

    s = CELL_SIZE_M
    # a window across the box's north-west corner (125 W, 49 N), 300 x 200 cells
    from pyproj import Transformer

    x, y = Transformer.from_crs("EPSG:4269", GRID_CRS, always_xy=True).transform(-125.0, 49.0)
    left, top = int(x // s - 150) * s, int(y // s + 100) * s
    window = GridWindow(left, top - 200 * s, left + 300 * s, top)
    whole = box_mask(window, PNW_BOX)
    assert whole.any() and not whole.all()
    assert np.array_equal(in_box(window, rows_per_block=37), whole)
