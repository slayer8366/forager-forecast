"""T5 end to end on synthetic TreeMap- and SCANFI-shaped sources: cut, fetch, master grid."""

import csv
import io
import json
import math
import struct
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin

from forager_forecast.crown_cover import BANDS, Tree, plot_cover
from forager_forecast.grid import cell_for_lonlat
from forager_forecast.t4_layer import LonLatBox
from forager_forecast.t5_layer import (
    FLAG_NONE,
    FLAG_NOT_AVAILABLE,
    FLAG_SCANFI,
    FLAG_TREEMAP,
    MIN_TOTAL_COVER_PCT,
    SCANFI_CLASSES,
    SCANFI_CRS_WKT,
    SCANFI_NOT_AVAILABLE,
    STRIP,
    TREEMAP_CITATION,
    TREEMAP_CRS,
    build_master,
    cut_treemap,
    fetch_scanfi,
    master_window,
    scanfi_url,
)

SMALL = LonLatBox(south=48.96, north=49.04, west=-121.95, east=-121.85)
TREEMAP_NODATA = -2147483648

TREES = {
    1: [("202", "Douglas-fir", "Pseudotsuga menziesii", 20.0, 60.0)],
    2: [
        ("263", "western hemlock", "Tsuga heterophylla", 14.0, 40.0),
        ("815", "Oregon white oak", "Quercus garryana", 10.0, 30.0),
        ("542", "Oregon ash", "Fraxinus latifolia", 12.0, 10.0),
    ],
    # Only trees under 5 in: TreeMap publishes canopy for it, but the tree list cannot split it.
    3: [("263", "western hemlock", "Tsuga heterophylla", 3.0, 300.0)],
    9: [("202", "Douglas-fir", "Pseudotsuga menziesii", 20.0, 60.0)],  # not in the raster
}
# TreeMap's own CANOPYPCT per plot (D88), as the raster attribute table carries it.
CANOPY = {1: 70.0, 2: 55.0, 3: 30.0, 9: 80.0}
SCANFI_VALUES = {"douglasFir": 30, "otherConiferous": 30, "broadleaf": 20}


def _covers(plot, scale=1.0):
    return plot_cover(
        [Tree(int(s), sci.split()[0], d, tpa, True) for s, _, sci, d, tpa in TREES[plot]],
        surrogate_width_scale=scale,
    )


def _grid_lonlat(transform, width, height, crs):
    xs = transform.c + (np.arange(width) + 0.5) * transform.a
    ys = transform.f + (np.arange(height) + 0.5) * transform.e
    gx, gy = np.meshgrid(xs, ys)
    return Transformer.from_crs(crs, "EPSG:4269", always_xy=True).transform(gx, gy)


def _bounds_in(crs, box, margin):
    t = Transformer.from_crs("EPSG:4269", crs, always_xy=True)
    lon = np.linspace(box.west, box.east, 50)
    lat = np.linspace(box.south, box.north, 50)
    gx, gy = np.meshgrid(lon, lat)
    x, y = t.transform(gx, gy)
    return x.min() - margin, y.min() - margin, x.max() + margin, y.max() + margin


def _write_treemap(path, top_lat=49.015):
    # Like the real raster, it ends a little north of 49 N, short of the strip's north edge.
    left, bottom, right, _ = _bounds_in(TREEMAP_CRS, SMALL, 3000)
    _, top = Transformer.from_crs("EPSG:4269", TREEMAP_CRS, always_xy=True).transform(
        -121.90, top_lat
    )
    left, top = math.floor(left / 30) * 30, math.floor(top / 30) * 30
    width, height = int((right - left) // 30) + 1, int((top - bottom) // 30) + 1
    transform = from_origin(left, top, 30, 30)
    lon, lat = _grid_lonlat(transform, width, height, TREEMAP_CRS)
    plots = np.where(lon < -121.90, 1, 2).astype("int32")
    plots[lat >= 49.0] = 2  # north of the border: a different plot, which no cell may read
    plots[(lat >= 48.975) & (lat < 48.985) & (lon < -121.915)] = 3
    plots[lat < 48.975] = TREEMAP_NODATA  # non-forest on the US side
    with rasterio.open(
        path, "w", driver="GTiff", width=width, height=height, count=1, dtype="int32",
        crs=TREEMAP_CRS, transform=transform, nodata=TREEMAP_NODATA,
    ) as dst:  # fmt: skip
        dst.write(plots, 1)
    _write_vat(Path(str(path) + ".vat.dbf"), {k: v for k, v in CANOPY.items() if k != 9})


def _write_vat(path, canopy):
    """A dBase III attribute table shaped like TreeMap's: numeric Value and CANOPYPCT fields."""
    fields = [("Value", 20, 11), ("Count", 20, 0), ("CANOPYPCT", 19, 14)]
    rlen = 1 + sum(f[1] for f in fields)
    hlen = 32 + 32 * len(fields) + 1
    out = bytearray(struct.pack("<B3BIHH20x", 3, 126, 10, 6, len(canopy), hlen, rlen))
    for name, size, dec in fields:
        out += struct.pack("<11sc4xBB14x", name.encode(), b"N", size, dec)
    out += b"\r"
    for value, pct in canopy.items():
        out += (
            b" "
            + f"{value:.11f}".rjust(20).encode()
            + b"1".rjust(20)
            + f"{pct:.14f}".rjust(19).encode()
        )
    out += b"\x1a"
    path.write_bytes(bytes(out))


def _write_tree_zip(path):
    buf = io.StringIO()
    w = csv.writer(buf, quoting=csv.QUOTE_NONNUMERIC)
    w.writerow(
        ["TM_ID", "PLT_CN", "STATUSCD", "TPA_UNADJ", "SPCD", "COMMON_NAME", "SCIENTIFIC_NAME",
         "SPECIES_SYMBOL", "DIA", "HT", "ACTUALHT", "CR", "SUBP", "TREE", "AGENTCD"]
    )  # fmt: skip
    for tm, rows in TREES.items():
        for i, (spcd, common, sci, dia, tpa) in enumerate(rows):
            w.writerow(
                [tm, 1000 + tm, 1, tpa, int(spcd), common, sci, "X", dia, 50, 50, 40, 1, i, "NA"]
            )
        # A dead tree and a sapling in every plot: both carry no crown.
        w.writerow(
            [
                tm,
                1000 + tm,
                2,
                6.0,
                202,
                "Douglas-fir",
                "Pseudotsuga menziesii",
                "X",
                30,
                1,
                1,
                1,
                1,
                98,
                10,
            ]
        )
        w.writerow(
            [
                tm,
                1000 + tm,
                1,
                75.0,
                263,
                "western hemlock",
                "Tsuga heterophylla",
                "X",
                3.0,
                1,
                1,
                1,
                1,
                99,
                "NA",
            ]
        )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Data/TreeMap2023_CONUS_Tree_Table.csv", "﻿" + buf.getvalue())
    path.with_name(path.name + ".sha256").write_text(f"{'ab' * 32}  {path.name}\n")


def _write_scanfi(directory):
    left, bottom, right, top = _bounds_in(SCANFI_CRS_WKT, SMALL, 3000)
    left, top = math.floor(left / 30) * 30, math.ceil(top / 30) * 30
    width, height = int((right - left) // 30) + 1, int((top - bottom) // 30) + 1
    transform = from_origin(left, top, 30, 30)
    lon, lat = _grid_lonlat(transform, width, height, SCANFI_CRS_WKT)
    for cls in SCANFI_CLASSES:
        data = np.full((height, width), SCANFI_VALUES.get(cls, 0), dtype="uint8")
        data[(lat > 49.03) & (lon > -121.87)] = 255  # no data in one Canadian corner
        low = {"douglasFir": 3, "otherConiferous": 2, "broadleaf": 1}.get(cls, 0)
        data[(lat > 49.03) & (lon < -121.93)] = low  # 6% cover in the opposite corner
        with rasterio.open(
            directory / f"{cls}.tif", "w", driver="GTiff", width=width, height=height, count=1,
            dtype="uint8", crs=SCANFI_CRS_WKT, transform=transform, nodata=255,
        ) as dst:  # fmt: skip
            dst.write(data, 1)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    root = tmp_path_factory.mktemp("t5")
    src = root / "sources"
    src.mkdir()
    _write_treemap(src / "TreeMap2023_CONUS.tif")
    _write_tree_zip(src / "RDS-2026-0038.zip")
    _write_scanfi(src)
    native = root / "native"
    tm_request = cut_treemap(
        native, SMALL, src / "TreeMap2023_CONUS.tif", src / "RDS-2026-0038.zip"
    )
    sc_request = fetch_scanfi(native, SMALL, source_for=lambda cls, year: str(src / f"{cls}.tif"))
    out = root / "out"
    summary = build_master(native, out, SMALL)
    build_master(native, root / "wider", SMALL, surrogate_width_scale=1.3)
    build_master(native, root / "tree_list", SMALL, us_total="tree_list")
    return {
        "native": native, "out": out, "summary": summary, "wider": root / "wider",
        "tree_list": root / "tree_list",
        "tm_request": tm_request, "sc_request": sc_request,
    }  # fmt: skip


def _read(path):
    with rasterio.open(path) as ds:
        return {d: ds.read(i + 1) for i, d in enumerate(ds.descriptions)}, ds.tags(), ds.transform


def _at(bands, transform, lon, lat):
    cell = cell_for_lonlat(lon, lat)
    col = int(round((cell.col * 250 - transform.c) / 250))
    row = int(round((transform.f - (cell.row + 1) * 250) / 250))
    return {k: v[row, col] for k, v in bands.items()}


def test_the_strip_is_the_planned_one():
    assert (STRIP.south, STRIP.north, STRIP.west, STRIP.east) == (48.70, 49.30, -122.80, -120.95)
    assert MIN_TOTAL_COVER_PCT == 10.0
    assert set(SCANFI_NOT_AVAILABLE) == {"Tsuga", "Picea", "Abies", "Pinus", "Quercus"}
    assert scanfi_url("douglasFir", 2025).endswith("SCANFI_spsCC_douglasFir_2025_v2_20260119.tif")


def test_us_cells_carry_treemap_crown_shares(built):
    bands, _, transform = _read(built["out"] / "host_trees_strip.tif")
    flags, _, _ = _read(built["out"] / "host_trees_strip_flags.tif")
    west = _at(bands, transform, -121.93, 48.99)
    assert west["source"] == FLAG_TREEMAP
    assert west["total_cover_pct"] == pytest.approx(CANOPY[1])  # TreeMap's own canopy (D88)
    assert west["share_Pseudotsuga"] == pytest.approx(1.0)
    assert west["share_conifer"] == pytest.approx(1.0)
    assert west["share_Tsuga"] == pytest.approx(0.0)
    east = _at(bands, transform, -121.87, 48.99)
    c = _covers(2)
    for band in ("Tsuga", "Quercus", "conifer", "broadleaf"):
        assert east[f"share_{band}"] == pytest.approx(c.by_band[band] / c.total, rel=1e-5)
    f = _at(flags, transform, -121.87, 48.99)
    assert all(f[f"flag_{b}"] == FLAG_TREEMAP for b in BANDS)


def test_us_total_cover_is_treemaps_canopy_and_genus_cover_is_canopy_times_the_split(built):
    bands, tags, transform = _read(built["out"] / "host_trees_strip.tif")
    east = _at(bands, transform, -121.87, 48.99)
    assert east["total_cover_pct"] == pytest.approx(CANOPY[2])
    c = _covers(2)
    # The shares are the tree-list split, unchanged by the new total.
    assert east["share_Tsuga"] == pytest.approx(c.by_band["Tsuga"] / c.total, rel=1e-5)
    assert tags["us_total"].startswith("treemap_canopy")


def test_the_first_builds_tree_list_total_is_still_reproducible(built):
    bands, tags, transform = _read(built["tree_list"] / "host_trees_strip.tif")
    west = _at(bands, transform, -121.93, 48.99)
    assert west["total_cover_pct"] == pytest.approx(_covers(1).total, rel=1e-5)
    assert west["share_Pseudotsuga"] == pytest.approx(1.0)
    assert tags["us_total"].startswith("tree_list")


def test_canopy_the_tree_list_cannot_split_counts_as_cover_but_gives_no_share(built):
    bands, _, transform = _read(built["out"] / "host_trees_strip.tif")
    flags, _, _ = _read(built["out"] / "host_trees_strip_flags.tif")
    cell = _at(bands, transform, -121.935, 48.98)
    assert cell["total_cover_pct"] == pytest.approx(CANOPY[3])
    for band in BANDS:
        assert np.isnan(cell[f"share_{band}"])
    assert _at(flags, transform, -121.935, 48.98)["flag_Tsuga"] == FLAG_NONE
    assert built["summary"]["plots_without_split"] == 1


def test_a_plot_missing_from_the_attribute_table_is_an_error(tmp_path):
    _write_treemap(tmp_path / "TreeMap2023_CONUS.tif")
    _write_vat(Path(str(tmp_path / "TreeMap2023_CONUS.tif") + ".vat.dbf"), {1: 70.0})
    _write_tree_zip(tmp_path / "RDS-2026-0038.zip")
    with pytest.raises(ValueError, match="CANOPYPCT"):
        cut_treemap(
            tmp_path / "native", SMALL, tmp_path / "TreeMap2023_CONUS.tif",
            tmp_path / "RDS-2026-0038.zip",
        )  # fmt: skip


def test_canadian_cells_carry_scanfi_shares_and_flag_what_it_cannot_supply(built):
    bands, _, transform = _read(built["out"] / "host_trees_strip.tif")
    flags, _, _ = _read(built["out"] / "host_trees_strip_flags.tif")
    # TreeMap has plot 1 (pure Douglas-fir) here too; the Canadian side must not read it.
    cell = _at(bands, transform, -121.93, 49.02)
    assert cell["source"] == FLAG_SCANFI
    assert cell["total_cover_pct"] == pytest.approx(80.0)
    assert cell["share_Pseudotsuga"] == pytest.approx(30 / 80)
    assert cell["share_conifer"] == pytest.approx(60 / 80)
    assert cell["share_broadleaf"] == pytest.approx(20 / 80)
    f = _at(flags, transform, -121.93, 49.02)
    for genus in SCANFI_NOT_AVAILABLE:
        assert np.isnan(cell[f"share_{genus}"])
        assert f[f"flag_{genus}"] == FLAG_NOT_AVAILABLE
    for band in ("Pseudotsuga", "conifer", "broadleaf"):
        assert f[f"flag_{band}"] == FLAG_SCANFI


def test_cells_below_ten_percent_cover_or_outside_the_box_have_no_share(built):
    bands, _, transform = _read(built["out"] / "host_trees_strip.tif")
    flags, _, _ = _read(built["out"] / "host_trees_strip_flags.tif")
    # US non-forest: cover 0, so no share.
    bare = _at(bands, transform, -121.90, 48.965)
    assert bare["total_cover_pct"] == pytest.approx(0.0)
    assert np.isnan(bare["share_Pseudotsuga"])
    assert _at(flags, transform, -121.90, 48.965)["flag_Pseudotsuga"] == FLAG_NONE
    # SCANFI no data in the north-east corner counts as no crown.
    corner = _at(bands, transform, -121.855, 49.038)
    assert corner["total_cover_pct"] < MIN_TOTAL_COVER_PCT
    assert np.isnan(corner["share_conifer"])
    # Some cover, but under 10%: still no share.
    sparse = _at(bands, transform, -121.945, 49.038)
    assert sparse["total_cover_pct"] == pytest.approx(6.0)
    assert np.isnan(sparse["share_Pseudotsuga"])
    assert _at(flags, transform, -121.945, 49.038)["flag_Pseudotsuga"] == FLAG_NONE
    # Outside the box altogether: the Albers window's corners lie outside the rectangle.
    window = master_window(SMALL)
    assert bands["source"].shape == (window.height, window.width)
    assert (bands["source"] == 0).any()
    assert np.isnan(bands["total_cover_pct"][bands["source"] == 0]).all()


def test_a_straddling_cell_uses_its_own_side_and_the_half_area_rule(built):
    bands, _, transform = _read(built["out"] / "host_trees_strip.tif")
    vf = bands["valid_fraction"]
    src = bands["source"]
    inside = src > 0
    assert (vf[inside] <= 1.0 + 1e-9).all()
    # Some cells straddle 49 N: their own side covers only part of them.
    assert ((vf > 0.5) & (vf < 1.0) & inside).any()
    assert np.isnan(bands["share_conifer"][inside & (vf < 0.5)]).all()
    lat = _cell_lat(bands["source"].shape, transform)
    # A cell whose centre is at or just north of 49 N is Canadian.
    assert (src[inside & (lat >= 49.0) & (lat < 49.01)] == FLAG_SCANFI).all()
    assert (inside & (lat >= 49.0) & (lat < 49.01)).any()
    # A US cell straddling the line reads only its US part: in the west that is pure plot 1
    # (Douglas-fir), although the raster north of 49 N holds plot 2 there.
    west_straddle = inside & (lat < 49.0) & (lat > 48.998) & (vf < 1.0) & (vf > 0.5)
    lon = _cell_lon(bands["source"].shape, transform)
    west_straddle &= lon < -121.91
    assert west_straddle.any()
    assert np.allclose(bands["share_Pseudotsuga"][west_straddle], 1.0)


def _cell_centres(shape, transform):
    h, w = shape
    xs = transform.c + (np.arange(w) + 0.5) * 250
    ys = transform.f - (np.arange(h) + 0.5) * 250
    gx, gy = np.meshgrid(xs, ys)
    return Transformer.from_crs("ESRI:102008", "EPSG:4269", always_xy=True).transform(gx, gy)


def _cell_lat(shape, transform):
    return _cell_centres(shape, transform)[1]


def _cell_lon(shape, transform):
    return _cell_centres(shape, transform)[0]


def test_surrogate_widths_move_only_the_plot_with_a_surrogate(built):
    base, _, transform = _read(built["out"] / "host_trees_strip.tif")
    wide, _, _ = _read(built["wider"] / "host_trees_strip.tif")
    e0 = _at(base, transform, -121.87, 48.99)
    e1 = _at(wide, transform, -121.87, 48.99)
    assert e1["share_broadleaf"] > e0["share_broadleaf"]
    c = _covers(2, 1.3)
    assert e1["share_broadleaf"] == pytest.approx(c.by_band["broadleaf"] / c.total, rel=1e-5)
    w0 = _at(base, transform, -121.93, 48.99)
    w1 = _at(wide, transform, -121.93, 48.99)
    assert w1["share_Pseudotsuga"] == w0["share_Pseudotsuga"]
    assert built["summary"]["surrogate_species"] == {"542": 746}


def test_the_treemap_raster_may_end_north_of_the_border_but_not_south_of_it(built, tmp_path):
    # The fixture's raster stops at about 49.015 N and the build above succeeded; its Canadian
    # cells read SCANFI only (test_canadian_cells_...). A raster ending south of 49 N leaves US
    # cells unknown, which must be an error, not no crown.
    _write_treemap(tmp_path / "short.tif", top_lat=48.99)
    _write_tree_zip(tmp_path / "RDS-2026-0038.zip")
    with pytest.raises(ValueError, match="does not cover"):
        cut_treemap(
            tmp_path / "native", SMALL, tmp_path / "short.tif", tmp_path / "RDS-2026-0038.zip"
        )


def test_plot_covers_are_computed_only_for_plots_in_the_window(built):
    with open(built["native"] / "treemap_plot_covers.csv") as f:
        ids = {row["TM_ID"] for row in csv.DictReader(f)}
    assert ids == {"1", "2", "3"}


def test_request_records_carry_the_sources_terms_and_attribution(built):
    tm = json.loads(built["tm_request"].read_text())
    assert tm["citation"] == TREEMAP_CITATION
    assert "doi.org/10.2737/RDS-2026-0038" in tm["citation"]
    assert tm["zip_sha256"] == "ab" * 32
    assert "not the original" in tm["derived_notice"]
    sc = json.loads(built["sc_request"].read_text())
    assert sc["licence"] == "Open Government Licence - Canada"
    assert sc["year"] == 2025
    assert len(sc["layers"]) == len(SCANFI_CLASSES) == 10
    _, tags, _ = _read(built["out"] / "host_trees_strip.tif")
    assert TREEMAP_CITATION in tags["attribution"]
    assert "SCANFI" in tags["attribution"]
    assert "Derived data, not the original" in tags["derived_notice"]
    assert tags["rulings"].split(",") == ["D83", "D84", "D85", "D86", "D87", "D74"]
