"""The exact area-weighted regrid onto the master grid, on cases with a known answer."""

import numpy as np
import pytest
from rasterio.crs import CRS
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject

from forager_forecast.grid import GRID_CRS, GridWindow
from forager_forecast.regrid import area_weighted_regrid, polygon_square_overlap


def _identity(xs, ys):
    return xs, ys


def _shifted(dx, dy):
    def to_native(xs, ys):
        return xs + dx, ys + dy

    return to_native


def test_overlap_of_a_unit_square_with_itself_and_with_a_shifted_copy():
    square = np.array([[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]])
    assert polygon_square_overlap(square)[0] == pytest.approx(1.0)
    shifted = square + np.array([0.4, 0.3])
    assert polygon_square_overlap(shifted)[0] == pytest.approx(0.6 * 0.7)
    outside = square + np.array([1.5, 0.0])
    assert polygon_square_overlap(outside)[0] == 0.0


def test_overlap_of_a_rotated_square_is_exact():
    # A square of area 1 rotated 45 degrees about the target square's centre. Each of its four
    # corners pokes past an edge of the target by d = sqrt(0.5) - 0.5, cutting off a triangle of
    # area d * d, so the overlap is 1 - 4 d^2.
    c = 0.5
    h = np.sqrt(0.5)
    diamond = np.array([[[c, c - h], [c + h, c], [c, c + h], [c - h, c]]])
    corner_leg = h - 0.5  # each corner of the diamond pokes out by this much past the square
    expected = 1.0 - 4 * corner_leg**2
    assert polygon_square_overlap(diamond)[0] == pytest.approx(expected, abs=1e-12)


def test_a_uniform_field_returns_its_value_exactly():
    native = np.full((1, 40, 40), 6.3, dtype="float64")
    transform = from_origin(-73.0, 10_000.0 + 41.0, 250.0, 250.0)
    window = GridWindow(0, 2_500, 2_500, 7_500)
    values, valid = area_weighted_regrid(native, transform, _identity, window)
    assert values.shape == (1, window.height, window.width)
    # Exact up to floating-point rounding of sum(w * 6.3) / sum(w).
    np.testing.assert_allclose(values, 6.3, rtol=1e-14, atol=0)
    np.testing.assert_allclose(valid, 1.0, atol=1e-12)


def test_a_half_and_half_split_returns_the_area_weighted_mean():
    # Native pixels 250 m, offset 100 m east of the lattice: a master cell covers 150 m of one
    # native column and 100 m of the next. Left column 4.0, right column 8.0, alternating.
    native = np.zeros((1, 20, 20))
    native[0, :, 0::2] = 4.0
    native[0, :, 1::2] = 8.0
    transform = from_origin(100.0, 5_000.0, 250.0, 250.0)
    window = GridWindow(250, 1_000, 2_250, 4_000)
    values, valid = area_weighted_regrid(native, transform, _identity, window)
    # Master cell [250, 500) overlaps native col 0 ([100, 350), 4.0) for 100 m and col 1
    # ([350, 600), 8.0) for 150 m: (100 * 4 + 150 * 8) / 250 = 6.4. The next cell flips: 5.6.
    np.testing.assert_allclose(values[0, :, 0], 6.4)
    np.testing.assert_allclose(values[0, :, 1], 5.6)
    np.testing.assert_allclose(valid, 1.0)


def test_a_cell_partly_over_no_data_uses_valid_pixels_only_and_reports_the_fraction():
    native = np.full((1, 20, 20), 5.0)
    native[0, :, 1::2] = np.nan  # every second native column is no data
    native[0, :, 0::2] = 7.0
    transform = from_origin(100.0, 5_000.0, 250.0, 250.0)
    window = GridWindow(250, 1_000, 2_250, 4_000)
    values, valid = area_weighted_regrid(native, transform, _identity, window)
    # Cell [250, 500): 100 m of valid col 0 (7.0), 150 m of no-data col 1.
    np.testing.assert_allclose(values[0, :, 0], 7.0)
    np.testing.assert_allclose(valid[0, :, 0], 0.4)
    # Cell [500, 750): 100 m no data (col 1), 150 m valid col 2.
    np.testing.assert_allclose(valid[0, :, 1], 0.6)


def test_a_cell_with_no_valid_pixel_is_no_data_with_fraction_zero():
    native = np.full((1, 10, 10), np.nan)
    values, valid = area_weighted_regrid(
        native, from_origin(0.0, 2_500.0, 250.0, 250.0), _identity, GridWindow(0, 0, 1_000, 1_000)
    )
    assert np.isnan(values).all()
    np.testing.assert_array_equal(valid, 0.0)


def test_a_master_cell_beyond_the_native_raster_is_an_error_not_a_silent_gap():
    native = np.ones((1, 4, 4))
    with pytest.raises(ValueError, match="native raster does not cover"):
        area_weighted_regrid(
            native,
            from_origin(0.0, 1_000.0, 250.0, 250.0),
            _identity,
            GridWindow(0, 0, 2_000, 1_000),
        )


def test_the_pure_shift_case_agrees_with_gdal_average_to_1e_6():
    # The verify-stage probe found GDAL's average exact when the grids differ only by a shift.
    rng = np.random.default_rng(3)
    src = (rng.integers(40, 80, (60, 60)) / 10).astype("float32")
    src_transform = from_origin(0.0, 15_000.0, 250.0, 250.0)
    window = GridWindow(250, 1_000, 12_750, 14_750)  # shifted by whole cells, then...
    to_native = _shifted(-100.0, 70.0)  # ...the native grid sits 100 m east, 70 m south
    values, _ = area_weighted_regrid(src[None].astype("float64"), src_transform, to_native, window)

    gdal_dst = np.full((window.height, window.width), np.nan, dtype="float32")
    shifted_dst_transform = from_origin(window.left - 100.0, window.top + 70.0, 250.0, 250.0)
    crs = CRS.from_string(GRID_CRS)
    reproject(
        src,
        gdal_dst,
        src_transform=src_transform,
        src_crs=crs,
        dst_transform=shifted_dst_transform,
        dst_crs=crs,
        resampling=Resampling.average,
        src_nodata=np.nan,
        dst_nodata=np.nan,
    )
    np.testing.assert_allclose(values[0], gdal_dst, atol=1e-6)


def test_several_bands_share_the_geometry_but_not_the_validity():
    native = np.stack([np.full((10, 10), 5.0), np.full((10, 10), 9.0)])
    native[1, :, :5] = np.nan
    values, valid = area_weighted_regrid(
        native, from_origin(0.0, 2_500.0, 250.0, 250.0), _identity, GridWindow(0, 0, 2_500, 2_500)
    )
    np.testing.assert_allclose(values[0], 5.0)
    assert np.isnan(values[1, :, :5]).all()
    np.testing.assert_allclose(values[1, :, 5:], 9.0)
    np.testing.assert_allclose(valid[0], 1.0)
    np.testing.assert_allclose(valid[1, :, :5], 0.0)
