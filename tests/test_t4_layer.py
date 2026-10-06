"""T4 end to end on synthetic SoilGrids-shaped sources: fetch, master grid, archive."""

import hashlib
import json
import math

import numpy as np
import pytest
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin

from forager_forecast.grid import GridWindow
from forager_forecast.soilgrids import HOMOLOSINE, layer_name, layers, native_bounds_for
from forager_forecast.t4_layer import (
    MIN_VALID_FRACTION,
    WESTERN_WASHINGTON,
    LonLatBox,
    box_mask,
    build_archive,
    build_master,
    fetch_natives,
    master_window,
)
from forager_forecast.tiles import Z9_PIXEL_M, decode_tile, read_archive

SMALL_BOX = LonLatBox(south=47.0, north=47.12, west=-122.3, east=-122.12)
# pH x 10 per depth and statistic: blended mean (5*60 + 10*55 + 15*50) / 30 / 10 = 5.3333...
MAPPED = {
    "mean": {"0-5cm": 60, "5-15cm": 55, "15-30cm": 50},
    "Q0.05": {"0-5cm": 50, "5-15cm": 45, "15-30cm": 40},
    "Q0.95": {"0-5cm": 70, "5-15cm": 65, "15-30cm": 60},
}
NODATA = -32768


def test_western_washington_is_the_d82_rectangle():
    box = WESTERN_WASHINGTON
    assert (box.south, box.north, box.west, box.east) == (45.5, 49.0, -125.0, -121.0)


def test_the_master_window_covers_the_box_and_the_mask_follows_the_rectangle():
    window = master_window(SMALL_BOX)
    mask = box_mask(window, SMALL_BOX)
    to_lonlat = Transformer.from_crs("ESRI:102008", "EPSG:4269", always_xy=True)
    for r, c in [(0, 0), (0, window.width - 1), (window.height // 2, window.width // 2)]:
        x = window.left + (c + 0.5) * 250
        y = window.top - (r + 0.5) * 250
        lon, lat = to_lonlat.transform(x, y)
        inside = (
            SMALL_BOX.south <= lat <= SMALL_BOX.north and SMALL_BOX.west <= lon <= SMALL_BOX.east
        )
        assert mask[r, c] == inside
    assert mask[window.height // 2, window.width // 2]
    # The rectangle in longitude and latitude is not a rectangle in Albers: some corners are out.
    assert not mask.all()
    to_grid = Transformer.from_crs("EPSG:4269", "ESRI:102008", always_xy=True)
    for lon in (SMALL_BOX.west, SMALL_BOX.east):
        for lat in (SMALL_BOX.south, SMALL_BOX.north):
            x, y = to_grid.transform(lon, lat)
            assert window.left <= x <= window.right and window.bottom <= y <= window.top


def _write_sources(tmp_path, window, hole_depth="15-30cm"):
    left, bottom, right, top = native_bounds_for(window, margin_m=2_000.0)
    x0 = math.floor(left / 250) * 250 - 37.0  # deliberately off the master lattice
    y0 = math.ceil(top / 250) * 250 + 61.0
    width = math.ceil((right - x0) / 250) + 2
    height = math.ceil((y0 - bottom) / 250) + 2
    paths = {}
    for depth, stat in layers():
        values = np.full((height, width), MAPPED[stat][depth], dtype="int16")
        if depth == hole_depth:
            values[:, : width // 3] = NODATA  # a no-data block in one depth only
        path = tmp_path / "isric" / f"{layer_name(depth, stat)}.tif"
        path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=width,
            height=height,
            count=1,
            dtype="int16",
            crs=HOMOLOSINE,
            transform=from_origin(x0, y0, 250.0, 250.0),
            nodata=NODATA,
        ) as dst:
            dst.write(values, 1)
        paths[(depth, stat)] = str(path)
    return paths, x0, width


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("t4")
    window = master_window(SMALL_BOX)
    sources, x0, width = _write_sources(tmp_path, window)
    native_dir = tmp_path / "native"
    request = fetch_natives(native_dir, SMALL_BOX, source_for=lambda d, s: sources[(d, s)])
    master = tmp_path / "master.tif"
    summary = build_master(native_dir, master, SMALL_BOX)
    header, metadata = build_archive(master, tmp_path / "archive")
    return {
        "tmp": tmp_path,
        "window": window,
        "request": request,
        "native_dir": native_dir,
        "master": master,
        "summary": summary,
        "header": header,
        "metadata": metadata,
        "hole_edge_x": x0 + (width // 3) * 250.0,
    }


def test_the_request_record_lists_nine_layers_with_hashes_of_the_files_kept(built):
    body = json.loads(built["request"].read_text())
    assert len(body["layers"]) == 9
    assert body["extent"] == {"south": 47.0, "north": 47.12, "west": -122.3, "east": -122.12}
    for record in body["layers"]:
        path = built["native_dir"] / record["file"]
        assert record["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert "Poggio" in body["attribution"]


def test_the_master_grid_is_on_the_lattice_and_carries_the_blended_values(built):
    window = built["window"]
    with rasterio.open(built["master"]) as ds:
        assert ds.crs.to_string() in ("ESRI:102008",) or "Albers" in ds.crs.to_wkt()
        assert ds.res == (250.0, 250.0)
        assert ds.transform.c % 250 == 0 and ds.transform.f % 250 == 0
        assert (ds.transform.c, ds.transform.f) == (window.left, window.top)
        assert ds.descriptions == (
            "ph_mean_0_30cm",
            "ph_q05_0_30cm_approximate",
            "ph_q95_0_30cm_approximate",
            "valid_fraction_mean",
            "valid_fraction_q05",
            "valid_fraction_q95",
        )
        mean, q05, q95, frac = ds.read(1), ds.read(2), ds.read(3), ds.read(4)
        tags = ds.tags()
        assert "approximate" in ds.tags(2)["note"] and "approximate" in ds.tags(3)["note"]
    assert "D80" in tags["depth"] and float(tags["min_valid_fraction"]) == MIN_VALID_FRACTION
    mask = box_mask(window, SMALL_BOX)
    full = mask & (frac == 1.0)
    assert full.sum() > 100
    np.testing.assert_allclose(mean[full], (5 * 6.0 + 10 * 5.5 + 15 * 5.0) / 30, rtol=1e-6)
    np.testing.assert_allclose(q05[full], (5 * 5.0 + 10 * 4.5 + 15 * 4.0) / 30, rtol=1e-6)
    np.testing.assert_allclose(q95[full], (5 * 7.0 + 10 * 6.5 + 15 * 6.0) / 30, rtol=1e-6)
    assert np.isnan(mean[~mask]).all()


def test_a_cell_mostly_over_no_data_becomes_no_data_and_keeps_its_fraction(built):
    with rasterio.open(built["master"]) as ds:
        mean, frac = ds.read(1), ds.read(4)
    mask = box_mask(built["window"], SMALL_BOX)
    hole = mask & (frac == 0.0)
    sliver = mask & (frac > 0.0) & (frac < MIN_VALID_FRACTION)
    kept = mask & (frac >= MIN_VALID_FRACTION) & (frac < 1.0)
    assert hole.any() and sliver.any() and kept.any()
    assert np.isnan(mean[hole]).all() and np.isnan(mean[sliver]).all()
    np.testing.assert_allclose(mean[kept], 5.3333333, rtol=1e-6)
    assert built["summary"]["cells_below_min_valid_fraction"] == int(
        (mask & (frac < MIN_VALID_FRACTION) & (frac > 0)).sum()
    )


def test_the_archive_is_zoom_9_and_reads_back_the_master_value(built):
    header, metadata = built["header"], built["metadata"]
    assert header["max_zoom"] == 9 and header["tile_type"] == "PNG"
    assert "approximate" in metadata["forager_forecast_range_bands"]
    assert "not in this archive" in metadata["forager_forecast_range_bands"]
    assert "Poggio" in metadata["attribution"]
    assert "floor(pH * 10 + 0.5)" in metadata["forager_forecast_encoding"]
    text = json.dumps(metadata).lower()
    for forbidden in ("fruiting probability", "probability of finding", "chance of finding"):
        assert forbidden not in text  # D58
    assert "chance" not in text and "%" not in text  # R8: this raster carries no chance wording

    _, _, get_tile = read_archive(built["tmp"] / "archive" / "soil-ph-0-30cm.pmtiles")
    lon, lat = -122.16, 47.06  # inside the box, east of the no-data block
    mx, my = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform(lon, lat)
    half = math.pi * 6378137
    px = math.floor((mx + half) / Z9_PIXEL_M)
    py = math.floor((half - my) / Z9_PIXEL_M)
    grey, alpha = decode_tile(get_tile(9, px // 256, py // 256))
    assert alpha[py % 256, px % 256] == 255
    assert grey[py % 256, px % 256] == 53


def test_the_regrid_time_is_reported(built):
    assert built["summary"]["regrid_seconds"] >= 0
    assert built["summary"]["cells"] == built["window"].width * built["window"].height


def test_a_native_file_from_a_different_grid_is_refused(tmp_path):
    window = master_window(SMALL_BOX)
    sources, _, _ = _write_sources(tmp_path, window)
    native_dir = tmp_path / "native"
    fetch_natives(native_dir, SMALL_BOX, source_for=lambda d, s: sources[(d, s)])
    odd = native_dir / f"{layer_name('5-15cm', 'Q0.95')}.tif"
    with rasterio.open(odd, "r+") as ds:
        t = ds.transform
        ds.transform = from_origin(t.c + 10.0, t.f, 250.0, 250.0)
    with pytest.raises(ValueError, match="grid"):
        build_master(native_dir, tmp_path / "m.tif", SMALL_BOX)


def test_window_type():
    assert isinstance(master_window(SMALL_BOX), GridWindow)
