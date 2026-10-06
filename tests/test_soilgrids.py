import hashlib
import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from forager_forecast.grid import GridWindow, lonlat_transformer
from forager_forecast.soilgrids import (
    ATTRIBUTION,
    DEPTHS,
    HOMOLOSINE,
    STATISTICS,
    blend_0_30,
    fetch_layer,
    grid_to_homolosine,
    layer_name,
    layers,
    native_bounds_for,
    ph_from_mapped,
    vrt_url,
)


def test_the_layers_are_three_depths_by_three_statistics_named_as_isric_names_them():
    # D80: 0-5, 5-15, 15-30 cm. D81: mean, Q0.05, Q0.95. ISRIC's naming, read on 2026-10-06:
    # "property_depthInterval_quantile", e.g. cfvo_5-15cm_Q0.5; folder listing phh2o_0-5cm_Q0.05.
    assert [d for d, _ in DEPTHS] == ["0-5cm", "5-15cm", "15-30cm"]
    assert [w for _, w in DEPTHS] == [5, 10, 15]
    assert STATISTICS == ("mean", "Q0.05", "Q0.95")
    assert layer_name("0-5cm", "Q0.05") == "phh2o_0-5cm_Q0.05"
    assert len(layers()) == 9
    assert vrt_url("15-30cm", "mean") == (
        "https://files.isric.org/soilgrids/latest/data/phh2o/phh2o_15-30cm_mean.vrt"
    )


def test_mapped_values_divide_by_ten_once_and_no_data_becomes_nan():
    mapped = np.array([[65, 50], [-32768, 0]], dtype="int16")
    ph = ph_from_mapped(mapped, nodata=-32768)
    assert ph.dtype == np.float64
    np.testing.assert_allclose(ph[0], [6.5, 5.0])
    assert np.isnan(ph[1, 0])
    assert ph[1, 1] == 0.0


def test_a_missing_no_data_value_is_refused_not_guessed():
    with pytest.raises(ValueError, match="no-data"):
        ph_from_mapped(np.zeros((2, 2), dtype="int16"), nodata=None)


def test_the_blend_is_thickness_weighted_and_no_data_in_any_depth_is_no_data():
    a = np.array([6.0, 6.0, np.nan])
    b = np.array([5.0, 5.0, 5.0])
    c = np.array([4.0, np.nan, 4.0])
    blended = blend_0_30({"0-5cm": a, "5-15cm": b, "15-30cm": c})
    assert blended[0] == pytest.approx((5 * 6.0 + 10 * 5.0 + 15 * 4.0) / 30)
    assert np.isnan(blended[1]) and np.isnan(blended[2])
    with pytest.raises(KeyError):
        blend_0_30({"0-5cm": a, "5-15cm": b})


def test_grid_to_homolosine_pins_the_same_null_datum_step_as_the_grid():
    from pyproj import Transformer

    lon, lat = -122.3321, 47.6062
    x, y = lonlat_transformer().transform(lon, lat)
    hx, hy = grid_to_homolosine()(np.array([x]), np.array([y]))
    ex, ey = Transformer.from_crs("EPSG:4326", HOMOLOSINE, always_xy=True).transform(lon, lat)
    assert abs(hx[0] - ex) < 1e-3 and abs(hy[0] - ey) < 1e-3


def test_native_bounds_cover_the_whole_window_with_a_margin():
    window = GridWindow(-1_850_000, 1_150_000, -1_840_000, 1_160_000)
    left, bottom, right, top = native_bounds_for(window, margin_m=500.0)
    to_h = grid_to_homolosine()
    xs = np.linspace(window.left, window.right, 41)
    ys = np.linspace(window.bottom, window.top, 41)
    gx, gy = np.meshgrid(xs, ys)
    hx, hy = to_h(gx.ravel(), gy.ravel())
    assert left <= hx.min() - 500 and right >= hx.max() + 500
    assert bottom <= hy.min() - 500 and top >= hy.max() + 500


def _homolosine_source(path, origin_x, origin_y, values, nodata=-32768):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=values.shape[1],
        height=values.shape[0],
        count=1,
        dtype="int16",
        crs=HOMOLOSINE,
        transform=from_origin(origin_x, origin_y, 250.0, 250.0),
        nodata=nodata,
    ) as dst:
        dst.write(values, 1)


def test_fetch_layer_keeps_the_native_pixels_and_records_the_request(tmp_path):
    values = (np.arange(40 * 30).reshape(40, 30) % 90 + 10).astype("int16")
    source = tmp_path / "phh2o_0-5cm_mean.tif"
    _homolosine_source(source, -13_000_000.0, 5_300_000.0, values)
    dest = tmp_path / "out" / "phh2o_0-5cm_mean.tif"
    # Bounds inside the source, not on its pixel edges, so the window must round outward.
    record = fetch_layer(
        str(source), (-12_998_100.0, 5_292_600.0, -12_995_900.0, 5_297_400.0), dest
    )
    with rasterio.open(dest) as out:
        got = out.read(1)
        assert out.nodata == -32768
        assert out.crs == rasterio.crs.CRS.from_string(HOMOLOSINE)
        col_off = round((out.transform.c - -13_000_000.0) / 250)
        row_off = round((5_300_000.0 - out.transform.f) / 250)
        assert out.transform.c <= -12_998_100.0 and out.transform.f >= 5_297_400.0
    np.testing.assert_array_equal(
        got, values[row_off : row_off + got.shape[0], col_off : col_off + got.shape[1]]
    )
    assert record["source"] == str(source)
    assert record["pixel_window"] == {
        "col_off": col_off,
        "row_off": row_off,
        "width": got.shape[1],
        "height": got.shape[0],
    }
    assert record["sha256"] == hashlib.sha256(dest.read_bytes()).hexdigest()
    assert record["nodata"] == -32768
    assert record["http"] is None  # a local source has no ETag to record
    json.dumps(record)


def test_fetch_layer_refuses_bounds_outside_the_source(tmp_path):
    source = tmp_path / "s.tif"
    _homolosine_source(source, -13_000_000.0, 5_300_000.0, np.ones((10, 10), dtype="int16"))
    with pytest.raises(ValueError, match="outside"):
        fetch_layer(
            str(source),
            (-12_000_000.0, 5_290_000.0, -11_990_000.0, 5_295_000.0),
            tmp_path / "o.tif",
        )


def test_attribution_is_isrics_citation_and_licence_verbatim():
    assert (
        "Poggio, L., de Sousa, L. M., Batjes, N. H., Heuvelink, G. B. M., Kempen, B., Ribeiro, "
        "E., and Rossiter, D.: SoilGrids 2.0: producing soil information for the globe with "
        "quantified spatial uncertainty, SOIL, 7, 217–240, 2021" in ATTRIBUTION
    )
    assert "CC BY 4.0" in ATTRIBUTION
