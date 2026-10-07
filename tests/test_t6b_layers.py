"""T6b layers per tile, on synthetic sources in the real projections, through tile entry points.

The Verify's first claim, on a synthetic case: the same cells computed as one tile and as four
smaller tiles agree exactly (no step at a tile edge). Then the mask (D111, D113), the side rule at
the pixel level (D115) and water (D112).
"""

import csv
import io
import math
import zipfile

import numpy as np
import pytest
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin
from test_t5_layer import _write_vat
from test_t6b_mask import _ring, _write_shapefile

from forager_forecast.crown_cover import BANDS
from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS, cell_for_lonlat
from forager_forecast.soilgrids import HOMOLOSINE, layer_name, layers
from forager_forecast.t5_layer import (
    FLAG_NOT_AVAILABLE,
    FLAG_SCANFI,
    FLAG_TREEMAP,
    SCANFI_CLASSES,
    SCANFI_CRS_WKT,
    SCANFI_NOT_AVAILABLE,
    SCANFI_TOTAL_LAYER,
    TREEMAP_CRS,
)
from forager_forecast.t6b_layers import (
    Tile,
    build_plot_table,
    fetch_scanfi_super,
    soil_tile,
    tree_tile,
)
from forager_forecast.t6b_mask import build_mask

NALCMS_CRS = "+proj=laea +lat_0=45 +lon_0=-100 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
TREEMAP_NODATA = -2147483648
N_BIG, N_SMALL = 16, 8
CENTRE = cell_for_lonlat(-121.9, 49.0)
BIG = Tile(CENTRE.col // N_BIG, CENTRE.row // N_BIG, N_BIG)
SMALL = [Tile(2 * BIG.i + di, 2 * BIG.j + dj, N_SMALL) for di in (0, 1) for dj in (0, 1)]


def _lonlat_box(window, pad_deg):
    t = Transformer.from_crs(GRID_CRS, GEOGRAPHIC_CRS, always_xy=True)
    xs = np.linspace(window.left, window.right, 20)
    ys = np.linspace(window.bottom, window.top, 20)
    gx, gy = np.meshgrid(xs, ys)
    lon, lat = t.transform(gx, gy)
    return lon.min() - pad_deg, lat.min() - pad_deg, lon.max() + pad_deg, lat.max() + pad_deg


def _raster_over(crs, box, pixel, path, make, dtype, nodata, snap_origin=(0.0, 0.0)):
    t = Transformer.from_crs(GEOGRAPHIC_CRS, crs, always_xy=True)
    lon = np.linspace(box[0], box[2], 60)
    lat = np.linspace(box[1], box[3], 60)
    gx, gy = np.meshgrid(lon, lat)
    x, y = t.transform(gx, gy)
    ox, oy = snap_origin
    left = ox + math.floor((x.min() - ox) / pixel) * pixel
    top = oy + math.ceil((y.max() - oy) / pixel) * pixel
    width = int(math.ceil((x.max() - left) / pixel))
    height = int(math.ceil((top - y.min()) / pixel))
    transform = from_origin(left, top, pixel, pixel)
    xs = left + (np.arange(width) + 0.5) * pixel
    ys = top - (np.arange(height) + 0.5) * pixel
    px, py = np.meshgrid(xs, ys)
    plon, plat = Transformer.from_crs(crs, GEOGRAPHIC_CRS, always_xy=True).transform(px, py)
    data = make(np.asarray(plon), np.asarray(plat), np.arange(height)[:, None],
                np.arange(width)[None, :])  # fmt: skip
    with rasterio.open(
        path, "w", driver="GTiff", width=width, height=height, count=1, dtype=dtype, crs=crs,
        transform=transform, nodata=nodata,
    ) as dst:  # fmt: skip
        dst.write(np.asarray(data).astype(dtype), 1)


TREES = {
    1: [("202", "Douglas-fir", "Pseudotsuga menziesii", 20.0, 60.0)],
    2: [
        ("263", "western hemlock", "Tsuga heterophylla", 14.0, 40.0),
        ("815", "Oregon white oak", "Quercus garryana", 10.0, 30.0),
    ],
    3: [("263", "western hemlock", "Tsuga heterophylla", 3.0, 300.0)],  # canopy, no split
    4: [
        ("122", "ponderosa pine", "Pinus ponderosa", 16.0, 50.0),
        ("093", "Engelmann spruce", "Picea engelmannii", 12.0, 30.0),
        ("407", "shagbark hickory", "Carya ovata", 11.0, 25.0),  # outside T5's lists (D116)
    ],
}
CANOPY = {1: 70.0, 2: 55.0, 3: 30.0, 4: 45.0}


def _write_tree_zip(path):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["TM_ID", "STATUSCD", "TPA_UNADJ", "SPCD", "SCIENTIFIC_NAME", "DIA"])
    for tm, rows in TREES.items():
        for spcd, _, sci, dia, tpa in rows:
            w.writerow([tm, 1, tpa, int(spcd), sci, dia])
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Data/TreeMap2023_CONUS_Tree_Table.csv", "﻿" + buf.getvalue())


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    d = tmp_path_factory.mktemp("t6b")
    w0, s0, e0, n0 = _lonlat_box(BIG.window, 0.0)
    mid_lon = (w0 + e0) / 2
    # Mask: Washington south of 49 N, British Columbia north; an "Arctic" corner in the north-east.
    _write_shapefile(
        d / "political",
        [[_ring(-123.0, 47.0, -120.0, 49.0)], [_ring(-123.0, 49.0, -120.0, 51.0)]],
        [("COUNTRY", 20), ("STATEABB", 20)],
        [{"COUNTRY": "USA", "STATEABB": "US-WA"}, {"COUNTRY": "CAN", "STATEABB": "CA-BC"}],
    )
    arctic_box = (e0 - 0.25 * (e0 - w0), n0 - 0.2 * (n0 - s0), -120.0, 51.0)
    # The Arctic corner is drawn after the forest region that holds everything, so it wins there.
    _write_shapefile(
        d / "eco",
        [[_ring(-123.0, 47.0, -120.0, 51.0)], [_ring(*arctic_box)]],
        [("LEVEL1", 5), ("NameL1_En", 40)],
        [{"LEVEL1": "7", "NameL1_En": "Marine West Coast Forests"},
         {"LEVEL1": "2", "NameL1_En": "Tundra"}],
    )  # fmt: skip
    pad = BIG.window
    from forager_forecast.grid import GridWindow

    mask_window = GridWindow(pad.left - 4000, pad.bottom - 4000, pad.right + 4000, pad.top + 4000)
    build_mask(d / "political.shp", d / "eco.shp", mask_window, d / "mask.tif", block=13)

    box = _lonlat_box(BIG.window, 0.03)

    # TreeMap: four plots in an irregular pattern, a non-forest patch, a plot with no split.
    def treemap(lon, lat, r, c):
        plots = (1 + ((c // 7) + (r // 5) + (c * r) // 97) % 4).astype("int64")
        plots[(lon > mid_lon) & (lon < mid_lon + 0.004) & (lat < 48.99)] = TREEMAP_NODATA
        return plots

    _raster_over(TREEMAP_CRS, box, 30.0, d / "treemap.tif", treemap, "int32", TREEMAP_NODATA,
                 snap_origin=(15.0, 15.0))  # fmt: skip
    _write_vat(d / "treemap.tif.vat.dbf", CANOPY)
    _write_tree_zip(d / "trees.zip")
    build_plot_table(d / "trees.zip", d / "treemap.tif.vat.dbf", d / "plots.npz")

    rng = np.random.default_rng(20260918)
    for k, cls in enumerate((*SCANFI_CLASSES, SCANFI_TOTAL_LAYER)):

        def scanfi(lon, lat, r, c, k=k):
            base = (rng.integers(0, 12, size=lon.shape) + (r + 3 * c + k) % 9).astype("int64")
            if k == len(SCANFI_CLASSES):
                base = base * 6
            base[(lon < w0 + 0.006) & (lat > 49.003)] = 255  # SCANFI no data: no crown (T5)
            return np.clip(base, 0, 255)

        _raster_over(SCANFI_CRS_WKT, box, 30.0, d / f"scanfi_full_{cls}.tif", scanfi, "uint8",
                     255)  # fmt: skip

    water_us = (mid_lon - 0.012, s0 + 0.004, mid_lon - 0.004, s0 + 0.012)
    water_ca = (mid_lon + 0.002, n0 - 0.015, mid_lon + 0.012, n0 - 0.003)

    def nalcms(lon, lat, r, c, water=True):
        out = np.ones(lon.shape, dtype="int64")
        if water:
            for wb in (water_us, water_ca):
                out[(lon > wb[0]) & (lon < wb[2]) & (lat > wb[1]) & (lat < wb[3])] = 18
        return out

    _raster_over(NALCMS_CRS, box, 30.0, d / "nalcms.tif", nalcms, "uint8", 127)
    _raster_over(NALCMS_CRS, box, 30.0, d / "nalcms_dry.tif",
                 lambda *a: nalcms(*a, water=False), "uint8", 127)  # fmt: skip

    for k, (depth, stat) in enumerate(layers()):

        def soil(lon, lat, r, c, k=k):
            v = (40 + rng.integers(0, 30, size=lon.shape) + k).astype("int64")
            v[(lon > mid_lon) & (lon < mid_lon + 0.01) & (lat > 49.01)] = -32768
            return v

        _raster_over(HOMOLOSINE, box, 250.0, d / f"{layer_name(depth, stat)}.tif", soil,
                     "int16", -32768, snap_origin=(-19949750.0, 8361000.0))  # fmt: skip
    return {"d": d, "water_us": water_us, "water_ca": water_ca, "arctic": arctic_box,
            "mid_lon": mid_lon}  # fmt: skip


def _scanfi_source(world):
    return lambda cls, year: str(world["d"] / f"scanfi_full_{cls}.tif")


def _soil_source(world):
    return lambda depth, stat: str(world["d"] / f"{layer_name(depth, stat)}.tif")


def _trees(world, tiles, out, nalcms="nalcms.tif"):
    d = world["d"]
    super_dir = out / "scanfi_super"
    fetch_scanfi_super(BIG.window, super_dir, source_for=_scanfi_source(world))
    return [
        tree_tile(
            t, d / "mask.tif", d / "treemap.tif", d / "plots.npz", super_dir, d / nalcms, out
        )  # fmt: skip
        for t in tiles
    ]


def _read(path):
    with rasterio.open(path) as ds:
        return ds.read(), ds.transform


def _mosaic(paths_and_tiles, prefix, out):
    big = None
    for t in paths_and_tiles:
        data, tr = _read(out / f"{prefix}_{t.key}.tif")
        if big is None:
            big = np.full((data.shape[0], N_BIG, N_BIG), np.nan if data.dtype.kind == "f" else 0,
                          dtype=data.dtype)  # fmt: skip
        r0 = (BIG.window.top - int(tr.f)) // CELL_SIZE_M
        c0 = (int(tr.c) - BIG.window.left) // CELL_SIZE_M
        big[:, r0 : r0 + N_SMALL, c0 : c0 + N_SMALL] = data
    return big


def test_soil_one_tile_and_four_smaller_tiles_agree_exactly(world, tmp_path):
    d = world["d"]
    one = soil_tile(BIG, d / "mask.tif", tmp_path / "n1", tmp_path / "o1", _soil_source(world))
    four = [soil_tile(t, d / "mask.tif", tmp_path / "n4", tmp_path / "o4", _soil_source(world))
            for t in SMALL]  # fmt: skip
    big, _ = _read(tmp_path / "o1" / f"soil_{BIG.key}.tif")
    mosaic = _mosaic(SMALL, "soil", tmp_path / "o4")
    assert one["cells_with_mean"] > 50
    assert sum(f["cells_with_mean"] for f in four) == one["cells_with_mean"]
    assert np.array_equal(big, mosaic, equal_nan=True)


def test_trees_one_tile_and_four_smaller_tiles_agree_exactly(world, tmp_path):
    one = _trees(world, [BIG], tmp_path / "o1")[0]
    _trees(world, SMALL, tmp_path / "o4")
    for prefix in ("trees", "trees_flags"):
        big, _ = _read(tmp_path / "o1" / f"{prefix}_{BIG.key}.tif")
        assert np.array_equal(big, _mosaic(SMALL, prefix, tmp_path / "o4"), equal_nan=True)
    assert one["cells_with_share"]["us"] > 10 and one["cells_with_share"]["canada"] > 10


def _cells_lonlat():
    w = BIG.window
    xs = w.left + (np.arange(w.width) + 0.5) * CELL_SIZE_M
    ys = w.top - (np.arange(w.height) + 0.5) * CELL_SIZE_M
    gx, gy = np.meshgrid(xs, ys)
    return Transformer.from_crs(GRID_CRS, GEOGRAPHIC_CRS, always_xy=True).transform(gx, gy)


def _inside(lon, lat, box, inset=0.0025):
    return (
        (lon > box[0] + inset)
        & (lon < box[2] - inset)
        & (lat > box[1] + inset)
        & (lat < box[3] - inset)
    )


def test_masked_cells_are_blank_and_sides_and_flags_follow_the_rules(world, tmp_path):
    _trees(world, [BIG], tmp_path)
    values, _ = _read(tmp_path / f"trees_{BIG.key}.tif")
    flags, _ = _read(tmp_path / f"trees_flags_{BIG.key}.tif")
    with rasterio.open(tmp_path / f"trees_{BIG.key}.tif") as ds:
        names = list(ds.descriptions)
    fnames = [f"flag_{b}" for b in BANDS]
    lon, lat = _cells_lonlat()
    arctic = _inside(lon, lat, world["arctic"], inset=0.001)
    assert arctic.any()
    assert np.isnan(values[names.index("total_cover_pct")][arctic]).all()
    assert (values[names.index("valid_fraction")][arctic] == 0).all()
    assert (flags[:, arctic] == 0).all()
    src = values[names.index("source")]
    near_arctic = _inside(lon, lat, world["arctic"], inset=-0.003)
    north = (lat > 49.002) & ~near_arctic
    south = lat < 48.998
    assert (src[north] == FLAG_SCANFI).all() and (src[south] == FLAG_TREEMAP).all()
    for band in SCANFI_NOT_AVAILABLE:
        assert (flags[fnames.index(f"flag_{band}")][north] == FLAG_NOT_AVAILABLE).all()


@pytest.mark.parametrize("which", ["water_us", "water_ca"])
def test_water_is_no_data_not_zero_cover(world, tmp_path, which):
    _trees(world, [BIG], tmp_path / "wet")
    _trees(world, [BIG], tmp_path / "dry", nalcms="nalcms_dry.tif")
    wet, _ = _read(tmp_path / "wet" / f"trees_{BIG.key}.tif")
    dry, _ = _read(tmp_path / "dry" / f"trees_{BIG.key}.tif")
    lon, lat = _cells_lonlat()
    lake = _inside(lon, lat, world[which])
    assert lake.any()
    # Without the water mask these cells carry a cover; with it they are no data (D112), never 0.
    assert np.isfinite(dry[0][lake]).all()
    assert np.isnan(wet[0][lake]).all()
    assert (wet[1][lake] < 0.5).all()
    # Cells away from water are unchanged.
    far = ~_inside(lon, lat, world["water_us"], inset=-0.004) & ~_inside(
        lon, lat, world["water_ca"], inset=-0.004
    )
    assert np.array_equal(wet[:, far], dry[:, far], equal_nan=True)


def test_soil_cells_outside_the_study_area_are_blank(world, tmp_path):
    d = world["d"]
    soil_tile(BIG, d / "mask.tif", tmp_path / "n", tmp_path / "o", _soil_source(world))
    values, _ = _read(tmp_path / "o" / f"soil_{BIG.key}.tif")
    lon, lat = _cells_lonlat()
    arctic = _inside(lon, lat, world["arctic"], inset=0.001)
    assert arctic.any()
    assert np.isnan(values[:3, arctic]).all() and (values[3:, arctic] == 0).all()
    outside_patch = ~_inside(lon, lat, world["arctic"], inset=-0.003) & (lat < 49.0)
    assert np.isfinite(values[0][outside_patch]).any()


def test_the_plot_table_holds_canopypct_and_t5s_split_at_scale_1(world):
    from forager_forecast.crown_cover import Tree, plot_cover
    from forager_forecast.t6b_layers import load_plot_table

    ids, table = load_plot_table(world["d"] / "plots.npz")
    assert ids.tolist() == [1, 2, 3, 4]
    for k, tm in enumerate(ids.tolist()):
        c = plot_cover(
            [Tree(int(s), sci.split()[0], dia, tpa, True) for s, _, sci, dia, tpa in TREES[tm]],
            classify_unlisted_by_spcd=True,
        )
        assert table[k, 0] == c.total
        assert table[k, 1 : 1 + len(BANDS)].tolist() == [c.by_band[b] for b in BANDS]
        assert table[k, -1] == CANOPY[tm]
    assert table[2, 0] == 0.0  # plot 3: only a tree under 5 in, so no split (D88)


# D118: SCANFI read from whole local layer files, one layer regridded at a time.


def _trees_by_layer(world, tiles, out):
    from forager_forecast.t6b_layers import SCANFI_LAYERS, scanfi_layer_tile

    d = world["d"]
    layer_dir = out / "scanfi_layers"
    for layer in SCANFI_LAYERS:
        for t in tiles:
            scanfi_layer_tile(t, d / f"scanfi_full_{layer}.tif", layer, d / "mask.tif",
                              d / "nalcms.tif", layer_dir)  # fmt: skip
    return [
        tree_tile(
            t,
            d / "mask.tif",
            d / "treemap.tif",
            d / "plots.npz",
            None,
            d / "nalcms.tif",
            out,
            scanfi_layer_dir=layer_dir,
        )  # fmt: skip
        for t in tiles
    ]


def test_the_layer_route_matches_the_window_route(world, tmp_path):
    _trees(world, [BIG], tmp_path / "win")
    _trees_by_layer(world, [BIG], tmp_path / "lay")
    for prefix in ("trees", "trees_flags"):
        a, _ = _read(tmp_path / "win" / f"{prefix}_{BIG.key}.tif")
        b, _ = _read(tmp_path / "lay" / f"{prefix}_{BIG.key}.tif")
        assert np.array_equal(np.isnan(a), np.isnan(b)) if a.dtype.kind == "f" else True
        if a.dtype.kind == "f":
            # Sum of per-layer regrids, stored as float32, against the regrid of the sums.
            np.testing.assert_allclose(a, b, rtol=2e-6, atol=1e-6, equal_nan=True)
        else:
            assert np.array_equal(a, b)


def test_the_layer_route_one_tile_and_four_smaller_tiles_agree_exactly(world, tmp_path):
    _trees_by_layer(world, [BIG], tmp_path / "o1")
    _trees_by_layer(world, SMALL, tmp_path / "o4")
    for prefix in ("trees", "trees_flags"):
        big, _ = _read(tmp_path / "o1" / f"{prefix}_{BIG.key}.tif")
        assert np.array_equal(big, _mosaic(SMALL, prefix, tmp_path / "o4"), equal_nan=True)


def test_a_layer_missing_for_a_canadian_tile_is_an_error(world, tmp_path):
    from forager_forecast.t6b_layers import scanfi_layer_tile

    d = world["d"]
    scanfi_layer_tile(BIG, d / "scanfi_full_balsamFir.tif", "balsamFir", d / "mask.tif",
                      d / "nalcms.tif", tmp_path / "layers")  # fmt: skip
    with pytest.raises(FileNotFoundError):
        tree_tile(BIG, d / "mask.tif", d / "treemap.tif", d / "plots.npz", None, d / "nalcms.tif",
                  tmp_path, scanfi_layer_dir=tmp_path / "layers")  # fmt: skip


def test_free_space_is_checked_before_a_whole_layer_download(tmp_path, monkeypatch):
    import shutil

    from forager_forecast.t6b_layers import require_free_space

    monkeypatch.setattr(shutil, "disk_usage", lambda p: shutil._ntuple_diskusage(100, 90, 10))
    with pytest.raises(OSError):
        require_free_space(tmp_path, needed=11)
    require_free_space(tmp_path, needed=10)
