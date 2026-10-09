import math

import numpy as np
import pytest
from pyproj import Transformer

from forager_forecast.grid import GRID_CRS, GridWindow
from forager_forecast.tiles import (
    MAX_ZOOM,
    MIN_ZOOM,
    Z9_PIXEL_M,
    MercatorWindow,
    decode_tile,
    encode_ph_byte,
    master_to_mercator_nearest,
    mercator_window_for,
    read_archive,
    write_archive,
)


def test_zoom_9_pixel_size_is_the_web_mercator_one():
    assert MAX_ZOOM == 9
    assert Z9_PIXEL_M == pytest.approx(2 * math.pi * 6378137 / 256 / 2**9)
    # SPEC.md:48: "At 45 N that is about 216 m per pixel".
    assert Z9_PIXEL_M * math.cos(math.radians(45)) == pytest.approx(216.2, abs=0.05)


def test_the_mercator_window_sits_on_zoom_9_tile_edges_and_covers_the_master_window():
    window = GridWindow(-1_850_000, 1_150_000, -1_830_000, 1_170_000)
    merc = mercator_window_for(window)
    half = math.pi * 6378137
    tile = 256 * Z9_PIXEL_M
    assert (merc.left + half) / tile == pytest.approx(round((merc.left + half) / tile))
    assert (half - merc.top) / tile == pytest.approx(round((half - merc.top) / tile))
    assert merc.width % 256 == 0 and merc.height % 256 == 0
    to_merc = Transformer.from_crs(GRID_CRS, "EPSG:3857", always_xy=True)
    xs, ys = np.meshgrid(
        np.linspace(window.left, window.right, 9), np.linspace(window.bottom, window.top, 9)
    )
    mx, my = to_merc.transform(xs.ravel(), ys.ravel())
    assert merc.left <= mx.min() and merc.right >= mx.max()
    assert merc.bottom <= my.min() and merc.top >= my.max()


def test_each_mercator_pixel_takes_the_master_cell_under_its_centre():
    window = GridWindow(-1_860_000, 1_140_000, -1_820_000, 1_180_000)
    rows, cols = window.height, window.width
    values = (np.arange(rows * cols, dtype="float64").reshape(rows, cols)) / 7.0
    merc = mercator_window_for(window)
    out = master_to_mercator_nearest(values, window, merc)
    assert out.shape == (merc.height, merc.width)
    # Independent path: pixel centre -> ESRI:102008 directly through pyproj, then floor.
    to_grid = Transformer.from_crs("EPSG:3857", "ESRI:102008", always_xy=True)
    rng = np.random.default_rng(0)
    checked = 0
    for r, c in zip(
        rng.integers(0, merc.height, 2000), rng.integers(0, merc.width, 2000), strict=True
    ):
        x = merc.left + (c + 0.5) * Z9_PIXEL_M
        y = merc.top - (r + 0.5) * Z9_PIXEL_M
        gx, gy = to_grid.transform(x, y)
        col = math.floor((gx - window.left) / 250)
        row = math.floor((window.top - gy) / 250)
        if 0 <= row < rows and 0 <= col < cols:
            assert out[r, c] == values[row, col]
            checked += 1
        else:
            assert np.isnan(out[r, c])
    assert checked > 100


def test_encoding_rounds_ph_times_ten_half_up_and_marks_no_data_transparent():
    grey, alpha = encode_ph_byte(np.array([[5.36, 5.34, np.nan], [0.0, 14.0, 4.56]]))
    np.testing.assert_array_equal(grey, [[54, 53, 0], [0, 140, 46]])
    np.testing.assert_array_equal(alpha, [[255, 255, 0], [255, 255, 255]])
    assert grey.dtype == np.uint8 and alpha.dtype == np.uint8


def test_an_exact_half_rounds_up_as_the_archive_metadata_states():
    # Added by the T4 reviewer (D18), docs/audits/2026-10-06-t4-review.md. The test above is named
    # "half up" but holds no exact half, so round-half-to-even passed it. 4.25 and 5.25 are exact
    # in binary (x 10 = 42.5, 52.5): half up gives 43 and 53, half to even 42 and 52. On the real
    # master grid, 2,065 zoom-9 pixels sit on an exact half.
    grey, _ = encode_ph_byte(np.array([4.25, 5.25, 5.75]))
    np.testing.assert_array_equal(grey, [43, 53, 58])


def test_values_that_cannot_be_a_ph_are_refused_not_clipped():
    with pytest.raises(ValueError):
        encode_ph_byte(np.array([30.0]))
    with pytest.raises(ValueError):
        encode_ph_byte(np.array([-0.2]))


def test_the_archive_has_max_zoom_9_and_carries_the_values_and_metadata(tmp_path):
    # Two by two zoom-9 tiles over western Washington, values coded by position.
    half = math.pi * 6378137
    tile = 256 * Z9_PIXEL_M
    merc = MercatorWindow(left=-half + 80 * tile, top=half - 178 * tile, width=512, height=512)
    grey = (np.arange(512 * 512).reshape(512, 512) % 140 + 1).astype("uint8")
    alpha = np.full((512, 512), 255, "uint8")
    alpha[:, :40] = 0
    meta = {"attribution": "test attribution", "pixel_scale": "0.1"}
    header, metadata = write_archive(
        grey, alpha, merc, tmp_path / "t.mbtiles", tmp_path / "t.pmtiles", meta
    )
    assert header["max_zoom"] == MAX_ZOOM == 9
    assert header["min_zoom"] == MIN_ZOOM
    assert header["tile_type"] == "PNG"
    assert metadata["attribution"] == "test attribution"
    assert metadata["pixel_scale"] == "0.1"
    assert metadata["maxzoom"] == "9"

    reread_header, reread_meta, get_tile = read_archive(tmp_path / "t.pmtiles")
    assert reread_header == header
    g, a = decode_tile(get_tile(9, 80, 178))
    np.testing.assert_array_equal(a, alpha[:256, :256])
    np.testing.assert_array_equal(g[a == 255], grey[:256, :256][a == 255])
    g, a = decode_tile(get_tile(9, 81, 179))
    np.testing.assert_array_equal(g, grey[256:, 256:])


def test_the_percent_encoding_rounds_to_half_points_and_makes_no_data_transparent():
    from forager_forecast.tiles import encode_percent_byte

    grey, alpha = encode_percent_byte(np.array([0.0, 0.24, 0.25, 37.6, 100.0, np.nan, 100.0000001]))
    assert grey.tolist() == [0, 0, 1, 75, 200, 0, 200]
    assert alpha.tolist() == [255, 255, 255, 255, 255, 0, 255]
    with pytest.raises(ValueError, match="not a percentage"):
        encode_percent_byte(np.array([100.5]))
    with pytest.raises(ValueError, match="not a percentage"):
        encode_percent_byte(np.array([-0.5]))
