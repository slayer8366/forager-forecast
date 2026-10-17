"""T7 item 7: the tile reader applies P4 and records why each cell is out. Synthetic tiles only."""

import math

import numpy as np
import pytest
from pyproj import Transformer
from t7_synthetic import write_raster

from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS
from forager_forecast.t4_layer import LonLatBox
from forager_forecast.t6b_hosts import BAND_LAYOUT
from forager_forecast.t6b_layers import TREE_BANDS, Tile
from forager_forecast.t6b_mask import COUNTRY_CAN, COUNTRY_NONE, COUNTRY_US48, ECO_OTHER
from forager_forecast.t7.keying import weather_cells_for_window
from forager_forecast.t7.predictors import (
    ACCESS_BANDS,
    ACCESS_MAIN_BANDS,
    ACCESS_SIDE_BANDS,
    CODE_CANADA,
    CODE_IN,
    CODE_NO_SHARES,
    CODE_NO_SOIL,
    CODE_OUTSIDE,
    CODE_WATER,
    FEATURES,
    LayoutMismatch,
    PendingCell,
    read_tile,
)

N = 4
BOX = LonLatBox(south=40.0, north=49.0, west=-125.0, east=-111.0)
SHARE_BANDS = [b for b in TREE_BANDS if b.startswith("share_")]


def _tile():
    x, y = Transformer.from_crs(GEOGRAPHIC_CRS, GRID_CRS, always_xy=True).transform(-122.0, 45.5)
    s = N * CELL_SIZE_M
    return Tile(math.floor(x / s), math.floor(y / s), N)


def _layers(tmp_path, pending_at=None, layout=BAND_LAYOUT):
    tile = _tile()
    w = tile.window
    shape = (N, N)
    total = np.full(shape, 60.0)
    valid = np.ones(shape)
    source = np.ones(shape)
    shares = {b: np.full(shape, 0.1) for b in SHARE_BANDS}
    shares["share_Pinus"][:] = 0.005  # under the 0.01 floor (D137)
    total[0, 2], valid[0, 2] = np.nan, 0.0  # all water: code 6
    total[0, 3], valid[0, 3] = np.nan, 0.3  # under half valid: code 4
    total[1, 0] = 5.0  # canopy under 10%: code 4
    for b in SHARE_BANDS:
        for rc in ((0, 2), (0, 3), (1, 0)):
            shares[b][rc] = np.nan
    if pending_at is not None:
        source[pending_at] = 4.0
    bands = {"total_cover_pct": total, "valid_fraction": valid, "source": source, **shares}
    assert list(bands) == list(TREE_BANDS)
    tags = {"band_layout": layout, "attribution": "TREEMAP CITE | SCANFI CITE (OGL) | NALCMS CITE"}
    tree = tmp_path / f"trees_{tile.key}.tif"
    flags = tmp_path / f"trees_flags_{tile.key}.tif"
    write_raster(tree, w, bands, tags=tags, nodata=float("nan"))
    write_raster(flags, w, {f"flag_{b[6:]}": np.ones(shape) for b in SHARE_BANDS}, "uint8",
                 tags=tags)  # fmt: skip
    ph = np.full(shape, 5.5)
    ph[1, 1] = np.nan  # no soil pH: code 5
    soil = tmp_path / "soil.tif"
    write_raster(soil, w, {"ph_mean_0_30cm": ph, "valid_fraction_mean": np.ones(shape)},
                 tags={"attribution": "SOILGRIDS CITE"}, nodata=float("nan"))  # fmt: skip
    country = np.full(shape, COUNTRY_US48)
    country[0, 0] = COUNTRY_NONE  # outside the study area: code 0
    country[0, 1] = COUNTRY_CAN  # Canada by polygon (outside the 49 N band): code 3
    mask = tmp_path / "mask.tif"
    write_raster(mask, w, {"country": country, "eco": np.full(shape, ECO_OTHER)}, "uint8")
    ring = np.array([[w.left - 10, w.bottom - 10], [w.left - 10, w.top + 10],
                     [w.right + 10, w.top + 10], [w.right + 10, w.bottom - 10],
                     [w.left - 10, w.bottom - 10]], dtype=float)  # fmt: skip
    return tile, tree, flags, soil, mask, [(7, [ring])]


def test_each_cell_gets_its_code_and_only_eligible_cells_carry_values(tmp_path):
    tile, tree, flags, soil, mask, polygons = _layers(tmp_path)
    cells = read_tile(tile, tree, flags, soil, mask, BOX, polygons)
    code = cells.code
    assert code[0, 0] == CODE_OUTSIDE and code[0, 1] == CODE_CANADA
    assert code[0, 2] == CODE_WATER and code[0, 3] == CODE_NO_SHARES
    assert code[1, 0] == CODE_NO_SHARES and code[1, 1] == CODE_NO_SOIL
    eligible = np.argwhere(code == CODE_IN)
    assert len(eligible) == 10 and cells.code_counts() == {0: 1, 1: 10, 3: 1, 4: 2, 5: 1, 6: 1}
    assert cells.features.shape == (10, len(FEATURES))
    assert list(zip(cells.rows.tolist(), cells.cols.tolist(), strict=True)) == [
        tuple(rc) for rc in eligible.tolist()
    ]
    f = dict(zip(FEATURES, cells.features[0], strict=True))
    assert f["share_Pinus"] == 0.0  # floored
    assert f["share_Pseudotsuga"] == pytest.approx(0.1) and f["ph_mean_0_30cm"] == 5.5
    assert f["total_cover_pct"] == 60.0
    assert not any(n.startswith(("share_Fagus", "share_Carya")) for n in FEATURES)
    win = tile.window
    lat_t, lon_t = weather_cells_for_window(win)
    assert cells.lat_tenths.tolist() == lat_t[code == CODE_IN].tolist()
    assert cells.lon_tenths.tolist() == lon_t[code == CODE_IN].tolist()
    assert set(cells.level3.tolist()) == {7}
    r, c = eligible[0]
    assert cells.cell_id[0] == win.cell_of_pixel(int(r), int(c)).id
    assert cells.tree_attribution.startswith("TREEMAP CITE")
    assert cells.soil_attribution == "SOILGRIDS CITE"
    assert cells.canadian_values_read is False


def test_a_pending_study_cell_stops_the_run(tmp_path):
    tile, tree, flags, soil, mask, polygons = _layers(tmp_path, pending_at=(2, 2))
    with pytest.raises(PendingCell):
        read_tile(tile, tree, flags, soil, mask, BOX, polygons)


def test_a_pending_cell_outside_the_study_area_does_not(tmp_path):
    tile, tree, flags, soil, mask, polygons = _layers(tmp_path, pending_at=(0, 0))
    assert read_tile(tile, tree, flags, soil, mask, BOX, polygons).code[0, 0] == CODE_OUTSIDE


def test_a_tile_of_another_band_layout_is_refused(tmp_path):
    tile, tree, flags, soil, mask, polygons = _layers(tmp_path, layout="t6b-bands-000000000000")
    with pytest.raises(LayoutMismatch):
        read_tile(tile, tree, flags, soil, mask, BOX, polygons)


def test_cells_outside_the_box_are_code_0(tmp_path):
    tile, tree, flags, soil, mask, polygons = _layers(tmp_path)
    east = LonLatBox(south=40.0, north=49.0, west=-110.0, east=-100.0)
    cells = read_tile(tile, tree, flags, soil, mask, east, polygons)
    assert (cells.code == CODE_OUTSIDE).all() and len(cells.cell_id) == 0


def _access(tmp_path, tile):
    from t7_synthetic import write_raster as wr

    w = tile.window
    vals = {b: np.arange(N * N, dtype=float).reshape(N, N) * (k + 1) + 0.5
            for k, b in enumerate(ACCESS_BANDS)}  # fmt: skip
    vals["dist_trail_m"][2, 2] = np.nan  # a trails-not-published cell stays NaN, never filled
    path = tmp_path / "access.tif"
    wr(path, w, vals, nodata=float("nan"))
    return path, vals


def test_access_bands_are_off_by_default_and_change_nothing_else(tmp_path):
    tile, tree, flags, soil, mask, polygons = _layers(tmp_path)
    base = read_tile(tile, tree, flags, soil, mask, BOX, polygons)
    assert base.access.shape == (10, 0) and base.access_bands == ()
    assert set(ACCESS_BANDS).isdisjoint(FEATURES)
    path, vals = _access(tmp_path, tile)
    on = read_tile(tile, tree, flags, soil, mask, BOX, polygons, access_path=path,
                   access_bands=ACCESS_BANDS)  # fmt: skip
    assert np.array_equal(on.features, base.features) and np.array_equal(on.code, base.code)
    assert on.access_bands == ACCESS_BANDS and on.access.shape == (10, 3)
    for k, b in enumerate(ACCESS_BANDS):
        assert on.access[:, k].tolist() == pytest.approx(
            vals[b][on.rows, on.cols].tolist(), nan_ok=True)
    k = list(on.rows * N + on.cols).index(2 * N + 2)
    assert np.isnan(on.access[k, 1])


def test_the_main_access_band_is_roads_and_the_others_are_named_side_bands():
    assert ACCESS_MAIN_BANDS == ("dist_road_m",)
    assert ACCESS_SIDE_BANDS == ("dist_trail_m", "dist_any_m")


def test_an_access_band_the_file_lacks_or_no_file_is_refused(tmp_path):
    tile, tree, flags, soil, mask, polygons = _layers(tmp_path)
    path, _ = _access(tmp_path, tile)
    with pytest.raises(LayoutMismatch):
        read_tile(tile, tree, flags, soil, mask, BOX, polygons, access_path=path,
                  access_bands=("dist_rail_m",))  # fmt: skip
    with pytest.raises(ValueError):
        read_tile(tile, tree, flags, soil, mask, BOX, polygons, access_bands=("dist_road_m",))
