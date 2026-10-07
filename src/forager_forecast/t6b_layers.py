"""T6b: T4's soil layer and T5's host-tree layer, one master-grid tile at a time.

docs/dispatch/2026-10-06-t6b-continental-layers.md; rulings D111 to D115 on top of T4's (D74, D80,
D81) and T5's (D84 to D92). Nothing here changes those rules except where a row says so:

- The study area (D111, D113) replaces T4's rectangle and T5's strip: outside it a cell is no data,
  valid fraction 0, flag 0. Which side a cell or a native tree pixel is on follows D115 item 1.
- Water (D112): a TreeMap or SCANFI native pixel whose centre lies on NALCMS water (18) or on a
  pixel NALCMS leaves unmapped (0, or its declared no-data 127) is no data, not no crown. Soil keeps
  ISRIC's own water mask (T4).
- Native pixel positions are placed against each source's full-raster origin (D115 item 5,
  ``regrid.area_weighted_regrid_from_origin``), so a cell's value does not depend on its tile.
- Tiles: tile (i, j) of size n covers cols [n i, n i + n) and rows [n j, n j + n) of the lattice.
- Surrogate scale 1.0 only (D115 item 3); TreeMap plot covers are computed once (D115 item 2).

Every tile file is written to ``<name>.partial`` and renamed, so a file that exists is whole.
"""

import csv
import hashlib
import io
import json
import math
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.transform import Affine, from_origin
from rasterio.windows import Window, from_bounds

from forager_forecast.crown_cover import BANDS, Tree, plot_cover
from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS, GridWindow
from forager_forecast.regrid import area_weighted_regrid_from_origin
from forager_forecast.soilgrids import (
    ATTRIBUTION,
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
from forager_forecast.t4_layer import (
    APPROXIMATE_NOTE,
    BAND_DESCRIPTIONS,
    MIN_VALID_FRACTION,
    _require_homolosine,
)
from forager_forecast.t5_layer import (
    DERIVED_NOTICE,
    FLAG_LEGEND,
    FLAG_NONE,
    FLAG_NOT_AVAILABLE,
    FLAG_SCANFI,
    FLAG_TREEMAP,
    MIN_TOTAL_COVER_PCT,
    OUTSIDE_RASTER,
    SCANFI_BAND_CLASSES,
    SCANFI_CITATION,
    SCANFI_CLASSES,
    SCANFI_CRS_WKT,
    SCANFI_LICENCE,
    SCANFI_TOTAL_LAYER,
    TREE_TABLE_MEMBER,
    TREEMAP_CITATION,
    TREEMAP_CRS,
    _require_crs,
    _to_native,
    native_bounds,
    read_canopy_pct,
    scanfi_url,
)
from forager_forecast.t6b_mask import (
    COUNTRY_NONE,
    SIDE_CA,
    SIDE_NONE,
    SIDE_US,
    cells_in_study,
    read_mask,
    side_rule,
)

RULINGS = ("D74", "D80", "D81", "D84", "D85", "D86", "D87", "D88", "D89", "D90", "D91", "D92",
           "D111", "D112", "D113", "D114", "D115")  # fmt: skip
NALCMS_WATER = 18
NALCMS_UNMAPPED = (0, 127)
NALCMS_CITATION = (
    'Commission for Environmental Cooperation (CEC). 2024. "North American Environmental Atlas - '
    'Land Cover 2020 30m". North American Land Change Monitoring System. Ed. 2.0. CC BY 4.0.'
)
TREE_BANDS = ("total_cover_pct", "valid_fraction", "source", *(f"share_{b}" for b in BANDS))
SURROGATE_SCALE = 1.0


@dataclass(frozen=True)
class Tile:
    i: int
    j: int
    n: int

    @property
    def key(self) -> str:
        return f"{self.n}_{self.i}_{self.j}"

    @property
    def window(self) -> GridWindow:
        s = self.n * CELL_SIZE_M
        return GridWindow(self.i * s, self.j * s, (self.i + 1) * s, (self.j + 1) * s)


def tiles_over(window: GridWindow, n: int) -> list[Tile]:
    """Every tile of size n meeting ``window``, north to south, then west to east."""
    s = n * CELL_SIZE_M
    i0, i1 = math.floor(window.left / s), math.ceil(window.right / s)
    j0, j1 = math.floor(window.bottom / s), math.ceil(window.top / s)
    return [Tile(i, j, n) for j in range(j1 - 1, j0 - 1, -1) for i in range(i0, i1)]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def _write_tif(path: Path, window: GridWindow, bands: dict, dtype: str, tags: dict,
               band_tags: dict | None = None, nodata=None) -> str:  # fmt: skip
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    profile = {
        "driver": "GTiff", "width": window.width, "height": window.height, "count": len(bands),
        "dtype": dtype, "crs": GRID_CRS, "nodata": nodata, "compress": "deflate", "tiled": True,
        "transform": from_origin(window.left, window.top, CELL_SIZE_M, CELL_SIZE_M),
    }  # fmt: skip
    with rasterio.open(partial, "w", **profile) as dst:
        for k, (name, data) in enumerate(bands.items(), start=1):
            dst.write(np.asarray(data).astype(dtype), k)
            dst.set_band_description(k, name)
            if band_tags and name in band_tags:
                dst.update_tags(k, note=band_tags[name])
        dst.update_tags(**tags)
    partial.rename(path)
    return _sha256(path)


# --- Soil ---------------------------------------------------------------------------------------


def _study_box(window: GridWindow, study: np.ndarray) -> GridWindow:
    """The smallest window inside ``window`` holding every study cell of it.

    Soil is regridded over this box only. A 512 km soil tile at the study area's northern edge
    can reach past the pole side of the continent into a gap of SoilGrids' interrupted
    Homolosine, where positions are not defined; no study cell lies there. Each cell's value
    does not depend on the box (D115 item 5), so cropping changes no value.
    """
    rows = np.flatnonzero(study.any(axis=1))
    cols = np.flatnonzero(study.any(axis=0))
    return GridWindow(
        window.left + int(cols[0]) * CELL_SIZE_M,
        window.top - (int(rows[-1]) + 1) * CELL_SIZE_M,
        window.left + (int(cols[-1]) + 1) * CELL_SIZE_M,
        window.top - int(rows[0]) * CELL_SIZE_M,
    )


def soil_tile(tile: Tile, mask_path: Path, native_root: Path, out_dir: Path,
              source_for=vrt_url) -> dict:  # fmt: skip
    """T4's soil pH (D80, D81, D74) for one tile. Native windows are kept under native_root."""
    window = tile.window
    study, _ = cells_in_study(window, *read_mask(mask_path, window))
    if not study.any():
        return {"tile": tile.key, "cells_in_study": 0, "skipped": "no cell in the study area"}
    native_dir = Path(native_root) / tile.key
    request_path = native_dir / "request.json"
    if request_path.exists():
        records = json.loads(request_path.read_text())["layers"]
    else:
        bounds = native_bounds_for(_study_box(window, study))
        if not all(math.isfinite(b) for b in bounds):
            raise ValueError(f"tile {tile.key}: its study cells reach a gap in the Homolosine")
        records = [
            fetch_layer(source_for(d, s), bounds, native_dir / f"{layer_name(d, s)}.tif")
            for d, s in layers()
        ]
        partial = request_path.with_name("request.json.partial")
        partial.write_text(json.dumps({"tile": tile.key, "layers": records}, indent=2) + "\n")
        partial.rename(request_path)
    grid = None
    by_stat: dict[str, dict[str, np.ndarray]] = {s: {} for s in STATISTICS}
    for (depth, stat), record in zip(layers(), records, strict=True):
        path = native_dir / f"{layer_name(depth, stat)}.tif"
        if _sha256(path) != record["sha256"]:
            raise ValueError(f"{path} does not match its request record")
        this = (tuple(record["source_grid"]["transform"]), tuple(record["pixel_window"].values()))
        with rasterio.open(path) as ds:
            if grid is None:
                _require_homolosine(ds.crs, path.name)
                grid = this
            elif this != grid:
                raise ValueError(f"{path.name} is on a different grid from the others")
            by_stat[stat][depth] = ph_from_mapped(ds.read(1), ds.nodata)
    full = Affine(*grid[0])
    col_off, row_off = grid[1][0], grid[1][1]
    native = np.stack([blend_0_30(by_stat[s]) for s in STATISTICS])
    del by_stat
    box = _study_box(window, study)
    sub_values, sub_fraction = area_weighted_regrid_from_origin(
        native, full, col_off, row_off, grid_to_homolosine(), box
    )
    r0 = (window.top - box.top) // CELL_SIZE_M
    c0 = (box.left - window.left) // CELL_SIZE_M
    values = np.full((len(STATISTICS), window.height, window.width), np.nan)
    fraction = np.zeros((len(STATISTICS), window.height, window.width))
    values[:, r0 : r0 + box.height, c0 : c0 + box.width] = sub_values
    fraction[:, r0 : r0 + box.height, c0 : c0 + box.width] = sub_fraction
    values[(fraction < MIN_VALID_FRACTION) | ~study[None]] = np.nan
    fraction[:, ~study] = 0.0
    bands = dict(zip(BAND_DESCRIPTIONS, np.concatenate([values, fraction]), strict=True))
    out = Path(out_dir) / f"soil_{tile.key}.tif"
    sha = _write_tif(
        out, window, bands, "float32",
        tags={
            "depth": "0 to 30 cm, thickness weights 5, 10, 15 (D80)",
            "min_valid_fraction": str(MIN_VALID_FRACTION),
            "study_area": "D111, D113 (cell centre)",
            "regrid": "exact area-weighted, positions from the source's full-raster origin (D115)",
            "attribution": ATTRIBUTION, "rulings": ",".join(RULINGS), "tile": tile.key,
        },
        band_tags={
            "ph_q05_0_30cm_approximate": APPROXIMATE_NOTE.format(q="0.05"),
            "ph_q95_0_30cm_approximate": APPROXIMATE_NOTE.format(q="0.95"),
        },
        nodata=float("nan"),
    )  # fmt: skip
    return {
        "tile": tile.key,
        "file": out.name,
        "sha256": sha,
        "cells_in_study": int(study.sum()),
        "cells_with_mean": int(np.isfinite(values[0]).sum()),
        "cells_below_min_valid_fraction": int(
            (study & (fraction[0] > 0) & (fraction[0] < MIN_VALID_FRACTION)).sum()
        ),
    }


# --- Host trees: inputs computed once -------------------------------------------------------------


def build_plot_table(tree_zip: Path, vat_path: Path, out: Path,
                     member: str = TREE_TABLE_MEMBER) -> dict:  # fmt: skip
    """Every TreeMap plot's cover split at surrogate scale 1.0 (D87 to D91), with CANOPYPCT (D88).

    Columns: tree-list total, the eight bands, CANOPYPCT. A plot with no tree rows has a tree-list
    total of 0 (no split). The same ``plot_cover`` as T5, run once instead of per window.
    """
    trees: dict[int, list[Tree]] = {}
    with zipfile.ZipFile(tree_zip) as z, z.open(member) as f:
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            dia, tpa = row["DIA"], row["TPA_UNADJ"]
            trees.setdefault(int(row["TM_ID"]), []).append(
                Tree(
                    spcd=int(row["SPCD"]),
                    genus=row["SCIENTIFIC_NAME"].split()[0],
                    dbh_in=float("nan") if dia in ("", "NA") else float(dia),
                    tpa=float("nan") if tpa in ("", "NA") else float(tpa),
                    live=row["STATUSCD"] == "1",
                )
            )
    canopy = read_canopy_pct(vat_path)
    ids = np.array(sorted(set(canopy) | set(trees)), dtype="int64")
    table = np.full((len(ids), 2 + len(BANDS)), np.nan)
    counts = {"surrogate_trees": 0, "capped_trees": 0, "nonpositive_width_trees": 0,
              "plots_without_tree_rows": 0, "plots_without_canopypct": 0,
              "unlisted_genus_trees_classed_by_fia_code": 0}  # fmt: skip
    for k, tm in enumerate(ids.tolist()):
        c = plot_cover(
            trees.get(tm, []), surrogate_width_scale=SURROGATE_SCALE,
            classify_unlisted_by_spcd=True,
        )  # fmt: skip
        table[k, 0] = c.total
        table[k, 1 : 1 + len(BANDS)] = [c.by_band[b] for b in BANDS]
        table[k, -1] = canopy.get(tm, np.nan)
        counts["surrogate_trees"] += c.surrogate_trees
        counts["capped_trees"] += c.capped_trees
        counts["nonpositive_width_trees"] += c.nonpositive_width_trees
        counts["unlisted_genus_trees_classed_by_fia_code"] += c.unlisted_genus_trees
        counts["plots_without_tree_rows"] += tm not in trees
        counts["plots_without_canopypct"] += tm not in canopy
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    partial = out.with_name(out.name + ".partial.npz")
    np.savez(partial, ids=ids, table=table)
    partial.rename(out)
    return {"plots": len(ids), **counts, "file": out.name, "sha256": _sha256(out)}


_PLOT_TABLES: dict[str, tuple[np.ndarray, np.ndarray]] = {}


def load_plot_table(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """The plot table, loaded once per process."""
    key = str(Path(path).resolve())
    if key not in _PLOT_TABLES:
        with np.load(path) as z:
            _PLOT_TABLES[key] = (z["ids"], z["table"])
    return _PLOT_TABLES[key]


# --- Host trees: per tile -------------------------------------------------------------------------


def _pixel_lonlat(full: Affine, col_off: int, row_off: int, width: int, height: int, crs):
    """Pixel centres from the full raster's origin: a pixel's position is the same in any tile."""
    xs = full.c + (col_off + np.arange(width) + 0.5) * full.a
    ys = full.f + (row_off + np.arange(height) + 0.5) * full.e
    gx, gy = np.meshgrid(xs, ys)
    lon, lat = Transformer.from_crs(crs, GEOGRAPHIC_CRS, always_xy=True).transform(gx, gy)
    return np.asarray(lon), np.asarray(lat)


def _pixel_side(lon, lat, mask_path: Path) -> np.ndarray:
    """Side of each native pixel by D115 item 1, the polygon read at the cell holding its centre.

    A pixel whose cell is in no polygon (country 0, the sea or a coastline gap) is SIDE_NONE and
    counts for either side; NALCMS decides whether it is water (D112).
    """
    x, y = Transformer.from_crs(GEOGRAPHIC_CRS, GRID_CRS, always_xy=True).transform(lon, lat)
    col = np.floor(np.asarray(x) / CELL_SIZE_M).astype(np.int64)
    row = np.floor(np.asarray(y) / CELL_SIZE_M).astype(np.int64)
    box = GridWindow(
        int(col.min()) * CELL_SIZE_M, int(row.min()) * CELL_SIZE_M,
        (int(col.max()) + 1) * CELL_SIZE_M, (int(row.max()) + 1) * CELL_SIZE_M,
    )  # fmt: skip
    country, _ = read_mask(mask_path, box)
    top_row = box.top // CELL_SIZE_M
    left_col = box.left // CELL_SIZE_M
    pixel_country = country[top_row - 1 - row, col - left_col]
    side = side_rule(lon, lat, pixel_country)
    return np.where((side == SIDE_NONE) & (pixel_country != COUNTRY_NONE), 255, side)


def _own_side(pixel_side: np.ndarray, side: int) -> np.ndarray:
    return (pixel_side == side) | (pixel_side == SIDE_NONE)


def _water(lon, lat, nalcms_tif: Path) -> np.ndarray:
    """True where the pixel centre lies on NALCMS water or on a pixel NALCMS leaves unmapped."""
    with rasterio.open(nalcms_tif) as ds:
        x, y = Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True).transform(lon, lat)
        x, y = np.asarray(x), np.asarray(y)
        t = ds.transform
        col = np.floor((x - t.c) / t.a).astype(np.int64)
        row = np.floor((y - t.f) / t.e).astype(np.int64)
        c0, r0 = int(col.min()), int(row.min())
        win = Window(c0, r0, int(col.max()) - c0 + 1, int(row.max()) - r0 + 1)
        land = ds.read(1, window=win, boundless=True, fill_value=127)
    value = land[row - r0, col - c0]
    return (value == NALCMS_WATER) | np.isin(value, NALCMS_UNMAPPED)


def _regrid_layers(layers_, full: Affine, col_off: int, row_off: int, crs, window: GridWindow):
    names = [n for n, _ in layers_]
    v, f = area_weighted_regrid_from_origin(
        np.stack([a for _, a in layers_]), full, col_off, row_off, _to_native(crs), window
    )
    if not all(np.array_equal(f[0], f[k]) for k in range(1, len(names))):
        raise ValueError("layers of one source must share their no-data pattern")
    return {n: v[k] for k, n in enumerate(names)}, f[0]


def _treemap_part(window, mask_path, treemap_tif, plot_ids, plot_table, nalcms_tif):
    with rasterio.open(treemap_tif) as src:
        _require_crs(src.crs, TREEMAP_CRS, Path(treemap_tif).name)
        raw = from_bounds(*native_bounds(window, TREEMAP_CRS), transform=src.transform)
        c0, r0 = math.floor(raw.col_off), math.floor(raw.row_off)
        c1, r1 = math.ceil(raw.col_off + raw.width), math.ceil(raw.row_off + raw.height)
        win = Window(c0, r0, c1 - c0, r1 - r0)
        plots = src.read(1, window=win, boundless=True, fill_value=OUTSIDE_RASTER)
        if (plots == OUTSIDE_RASTER).any() and src.nodata == OUTSIDE_RASTER:
            raise ValueError("TreeMap's own no-data value collides with OUTSIDE_RASTER")
        full, nodata, crs = src.transform, src.nodata, src.crs
    lon, lat = _pixel_lonlat(full, c0, r0, plots.shape[1], plots.shape[0], crs)
    own = _own_side(_pixel_side(lon, lat, mask_path), SIDE_US)
    water = _water(lon, lat, nalcms_tif)
    del lon, lat
    outside = plots == OUTSIDE_RASTER
    if (outside & own & ~water).any():
        raise ValueError("the TreeMap raster does not cover the US side of this tile")
    forest = (plots != nodata) & ~outside
    pos = np.searchsorted(plot_ids, plots[forest])
    pos_c = np.minimum(pos, len(plot_ids) - 1)
    if (pos >= len(plot_ids)).any() or (plot_ids[pos_c] != plots[forest]).any():
        raise ValueError("a TreeMap plot in this tile has no row in the plot table")
    rows = plot_table[pos_c]
    if np.isnan(rows[:, -1]).any():
        raise ValueError("a TreeMap plot in this tile has no CANOPYPCT")
    tree_total, canopy = rows[:, 0], rows[:, -1]
    has_split = tree_total > 0
    blank = ~own | outside | water

    def layer_of(values):
        layer = np.zeros(plots.shape)
        layer[forest] = values
        layer[blank] = np.nan
        return layer

    with np.errstate(invalid="ignore", divide="ignore"):
        split = [("total", layer_of(np.where(has_split, canopy, np.nan)))]
        for k, band in enumerate(BANDS, start=1):
            split.append(
                (band, layer_of(np.where(has_split, canopy * rows[:, k] / tree_total, np.nan)))
            )
    cover, frac = _regrid_layers([("total", layer_of(canopy))], full, c0, r0, crs, window)
    del rows
    shares, _ = _regrid_layers(split, full, c0, r0, crs, window)
    return cover["total"], frac, shares, int(blank.sum()), int((water & own).sum())


def scanfi_super_window(super_window: GridWindow) -> tuple[float, float, float, float]:
    return native_bounds(super_window, SCANFI_CRS_WKT)


def fetch_scanfi_super(super_window: GridWindow, native_dir: Path, source_for=scanfi_url) -> dict:
    """One windowed read per SCANFI layer for a super-window (D115 item 2), with its record."""
    native_dir = Path(native_dir)
    bounds = scanfi_super_window(super_window)
    records = [
        fetch_layer(source_for(cls, 2025), bounds, native_dir / f"scanfi_{cls}.tif")
        for cls in (*SCANFI_CLASSES, SCANFI_TOTAL_LAYER)
    ]
    body = {
        "dataset": "SCANFI v2 2025, ten species-class crown closures and total crown closure",
        "citation": SCANFI_CITATION, "licence": SCANFI_LICENCE,
        "super_window": asdict(super_window), "native_bounds": list(bounds), "layers": records,
    }  # fmt: skip
    path = native_dir / "scanfi_request.json"
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(body, indent=2) + "\n")
    partial.rename(path)
    return body


def _scanfi_part(window, mask_path, scanfi_dir: Path, nalcms_tif):
    request = json.loads((Path(scanfi_dir) / "scanfi_request.json").read_text())
    by_name = {r["file"]: r for r in request["layers"]}
    bounds = native_bounds(window, SCANFI_CRS_WKT)
    arrays = {}
    grid = None
    for cls in (*SCANFI_CLASSES, SCANFI_TOTAL_LAYER):
        record = by_name[f"scanfi_{cls}.tif"]
        full = Affine(*record["source_grid"]["transform"])
        with rasterio.open(Path(scanfi_dir) / record["file"]) as ds:
            if grid is None:
                _require_crs(ds.crs, SCANFI_CRS_WKT, record["file"])
            raw = from_bounds(*bounds, transform=ds.transform)
            c0, r0 = math.floor(raw.col_off), math.floor(raw.row_off)
            c1, r1 = math.ceil(raw.col_off + raw.width), math.ceil(raw.row_off + raw.height)
            if c0 < 0 or r0 < 0 or c1 > ds.width or r1 > ds.height:
                raise ValueError("this tile reaches past its SCANFI super-window")
            data = ds.read(1, window=Window(c0, r0, c1 - c0, r1 - r0))
            nodata, crs = ds.nodata, ds.crs
        gc = record["pixel_window"]["col_off"] + c0
        gr = record["pixel_window"]["row_off"] + r0
        this = (tuple(full)[:6], gc, gr, data.shape)
        if grid is None:
            grid = this
        elif this != grid:
            raise ValueError(f"scanfi_{cls}.tif is on a different grid from the others")
        if nodata is None:
            raise ValueError(f"scanfi_{cls}.tif declares no no-data value")
        layer = data.astype("float64")
        layer[data == nodata] = 0.0
        arrays[cls] = layer
    full_t = Affine(*grid[0])
    gc, gr, shape = grid[1], grid[2], grid[3]
    lon, lat = _pixel_lonlat(full_t, gc, gr, shape[1], shape[0], crs)
    own = _own_side(_pixel_side(lon, lat, mask_path), SIDE_CA)
    water = _water(lon, lat, nalcms_tif)
    del lon, lat
    blank = ~own | water

    def own_layer(layer):
        layer = layer.copy()
        layer[blank] = np.nan
        return layer

    split = [("total", own_layer(sum(arrays[c] for c in SCANFI_CLASSES)))]
    for band, classes in SCANFI_BAND_CLASSES.items():
        split.append((band, own_layer(sum(arrays[c] for c in classes))))
    cover, frac = _regrid_layers(
        [("total", own_layer(arrays[SCANFI_TOTAL_LAYER]))], full_t, gc, gr, crs, window
    )
    del arrays
    shares, _ = _regrid_layers(split, full_t, gc, gr, crs, window)
    return cover["total"], frac, shares, int(blank.sum()), int((water & own).sum())


def tree_tile(tile: Tile, mask_path: Path, treemap_tif: Path, plot_table_path: Path,
              scanfi_dir: Path | None, nalcms_tif: Path, out_dir: Path) -> dict:  # fmt: skip
    """T5's genus canopy shares (D84 to D92) for one tile, with D111 to D115."""
    window = tile.window
    study, side = cells_in_study(window, *read_mask(mask_path, window))
    if not study.any():
        return {"tile": tile.key, "cells_in_study": 0, "skipped": "no cell in the study area"}
    shape = (window.height, window.width)
    nan = np.full(shape, np.nan)
    canada = side == SIDE_CA
    us_cover, us_frac, us = nan, np.zeros(shape), {b: nan for b in ("total", *BANDS)}
    ca_cover, ca_frac, ca = nan, np.zeros(shape), {b: nan for b in ("total", *BANDS)}
    blanked = {"us_pixels_blank": 0, "us_water_pixels": 0, "ca_pixels_blank": 0,
               "ca_water_pixels": 0}  # fmt: skip
    if (side == SIDE_US).any():
        ids, table = load_plot_table(plot_table_path)
        us_cover, us_frac, us, blanked["us_pixels_blank"], blanked["us_water_pixels"] = (
            _treemap_part(window, mask_path, treemap_tif, ids, table, nalcms_tif)
        )
    if canada.any():
        if scanfi_dir is None:
            raise ValueError(f"tile {tile.key} has Canadian cells but no SCANFI super-window")
        ca_cover, ca_frac, ca, blanked["ca_pixels_blank"], blanked["ca_water_pixels"] = (
            _scanfi_part(window, mask_path, scanfi_dir, nalcms_tif)
        )
        for band in BANDS:
            ca.setdefault(band, nan)

    fraction = np.where(canada, ca_frac, us_frac)
    total = np.where(canada, ca_cover, us_cover)
    valid = study & (fraction >= MIN_VALID_FRACTION)
    defined = valid & (total >= MIN_TOTAL_COVER_PCT)
    side_flag = np.where(canada, FLAG_SCANFI, FLAG_TREEMAP)
    bands = {
        "total_cover_pct": np.where(valid, total, np.nan),
        "valid_fraction": np.where(study, fraction, 0.0),
        "source": np.where(study, side_flag, FLAG_NONE).astype("float64"),
    }
    flags = {}
    with np.errstate(invalid="ignore", divide="ignore"):
        for band in BANDS:
            us_share = us[band] / us["total"]
            if band in SCANFI_BAND_CLASSES:
                share = np.where(canada, ca[band] / ca["total"], us_share)
            else:
                share = np.where(canada, np.nan, us_share)
            has_share = defined & np.isfinite(share)
            flag = np.where(has_share, side_flag, FLAG_NONE)
            if band not in SCANFI_BAND_CLASSES:
                flag = np.where(study & canada, FLAG_NOT_AVAILABLE, flag)
            bands[f"share_{band}"] = np.where(has_share, share, np.nan)
            flags[f"flag_{band}"] = flag.astype("uint8")
    tags = {
        "attribution": f"{TREEMAP_CITATION} | {SCANFI_CITATION} ({SCANFI_LICENCE}) | "
        f"{NALCMS_CITATION}",
        "derived_notice": DERIVED_NOTICE, "rulings": ",".join(RULINGS), "flag_legend": FLAG_LEGEND,
        "min_total_cover_pct": str(MIN_TOTAL_COVER_PCT),
        "min_valid_fraction": str(MIN_VALID_FRACTION),
        "surrogate_width_scale": str(SURROGATE_SCALE), "scanfi_year": "2025",
        "us_total": "TreeMap CANOPYPCT (D88)", "ca_total": "SCANFI v2 total crown closure (D92)",
        "water": "NALCMS 2020 water (18) and unmapped (0, 127) are no data (D112)",
        "study_area": "D111, D113 (cell centre); side D115", "tile": tile.key,
    }  # fmt: skip
    out_dir = Path(out_dir)
    sha_v = _write_tif(out_dir / f"trees_{tile.key}.tif", window, bands, "float32", tags,
                       nodata=float("nan"))  # fmt: skip
    sha_f = _write_tif(out_dir / f"trees_flags_{tile.key}.tif", window, flags, "uint8", tags)
    return {
        "tile": tile.key,
        "files": {f"trees_{tile.key}.tif": sha_v, f"trees_flags_{tile.key}.tif": sha_f},
        "cells_in_study": {
            "us": int((study & ~canada).sum()),
            "canada": int((study & canada).sum()),
        },
        "cells_valid": {"us": int((valid & ~canada).sum()), "canada": int((valid & canada).sum())},
        "cells_with_share": {
            "us": int((defined & ~canada).sum()),
            "canada": int((defined & canada).sum()),
        },
        **blanked,
    }
