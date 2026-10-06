"""T5: host trees as a genus share of canopy, with a source flag, across the BC-Washington border.

Dispatch docs/dispatch/2026-10-06-t5-host-trees.md, Amendment 1, rulings D83 to D87, plan in
docs/audits/2026-10-06-t5-verify-report.md.

- US side: TreeMap 2023 (D84). Each 30 m pixel is an imputed FIA plot; the plot's canopy cover and
  its split by genus come from its tree list (crown_cover.py, D87).
- Canadian side: SCANFI v2 crown closure per species class, year 2025. Shares are taken against
  the sum of its ten classes. SCANFI cannot supply Tsuga, Picea, Abies, Pinus or Quercus (D85):
  those are flagged not available there, never filled.
- Which side a master cell is on: its centre's latitude, 49 N and above is Canada. Each side's
  native pixels on the other side are no data, so a cell straddling the line is averaged from its
  own side only and D74's half-area rule applies.
- Within a side, a native pixel with no data is no crown (TreeMap's non-forest, SCANFI's 255),
  so total cover is a cell's canopy over all its own-side area. A share is defined only where that
  total is at least 10% (the verify report, section 4).
- Every derived raster carries both sources' citations and says it is derived (D84).
"""

import csv
import hashlib
import io
import json
import math
import struct
import zipfile
from dataclasses import asdict
from pathlib import Path

import numpy as np
import rasterio
from pyproj import CRS, Transformer
from rasterio.transform import from_origin
from rasterio.windows import Window, from_bounds

from forager_forecast.crown_cover import BANDS, Tree, plot_cover
from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS, GridWindow
from forager_forecast.regrid import area_weighted_regrid
from forager_forecast.soilgrids import fetch_layer
from forager_forecast.t4_layer import MIN_VALID_FRACTION, LonLatBox, box_mask, master_window

__all__ = ["master_window"]

# The strip: the D82 rectangle's land border (49 N, 122.76 W to 121.0 W) and about 33 km either
# side, extended north into British Columbia (verify report, section 4).
STRIP = LonLatBox(south=48.70, north=49.30, west=-122.80, east=-120.95)
BORDER_LATITUDE = 49.0
MIN_TOTAL_COVER_PCT = 10.0
SURROGATE_SCALES = (0.7, 1.0, 1.3)

FLAG_NONE = 0
FLAG_TREEMAP = 1
FLAG_SCANFI = 2
FLAG_NOT_AVAILABLE = 3
FLAG_LEGEND = (
    "0 no value (outside the strip, under half the cell's area from its own side, or under 10% "
    "canopy cover); 1 TreeMap 2023 (US); 2 SCANFI v2 (Canada); 3 Canada, genus not available "
    "in SCANFI (D85)"
)

TREEMAP_CRS = "EPSG:5070"
TREE_TABLE_MEMBER = "Data/TreeMap2023_CONUS_Tree_Table.csv"
TREEMAP_CITATION = (
    "Zimmer, Scott N.; Houtman, Rachel M.; Leatherman, Lila S. T.; Shaw, John D.; Housman, Ian W.; "
    "Shrestha, Abhinav; Borja Arboleda, Maria O.; Grenfell, Isaac C.; Finney, Mark A.; Riley, "
    "Karin L. 2026. TreeMap 2023 CONUS: A tree-level model of the forests of the conterminous "
    "United States circa 2023. Fort Collins, CO: Forest Service Research Data Archive. "
    "https://doi.org/10.2737/RDS-2026-0038"
)
TREEMAP_TERMS = {
    "use": "These data were collected using funding from the U.S. Government and can be used "
    "without additional permissions or fees.",
    "licence": "Formally, Archive-published datasets are released under the Creative Commons "
    "CC-BY license structure.",
    "redistribution": "The Data User agrees to not re-distribute a modified version of the data "
    "publication and represent it as the original data publication.",
    "sources": [
        "https://www.fs.usda.gov/rds/archive/catalog/RDS-2026-0038",
        "https://www.fs.usda.gov/rds/archive/dataUseInfo",
        "https://www.fs.usda.gov/rds/archive/datauseinfo/open",
    ],
}
DERIVED_NOTICE = (
    "Derived data, not the original data publication: genus shares of canopy cover computed by "
    "forager-forecast (T5, D84, D87) from TreeMap 2023 CONUS (RDS-2026-0038) and SCANFI v2. "
    "Neither source's authors produced or reviewed these values."
)

SCANFI_BASE_URL = "https://ftp.maps.canada.ca/pub/nrcan_rncan/Forests_Foret/SCANFI/v2"
SCANFI_YEAR = 2025
SCANFI_CRS_WKT = (
    "+proj=lcc +lat_0=0 +lon_0=-95 +lat_1=49 +lat_2=77 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"  # noqa: E501
)
SCANFI_CITATION = (
    "Guindon L., Correia D.L.P, Manka F. and Smiley B. 2026. SCANFI v2: Spatialized CAnadian "
    "National Forest Inventory data product v2. Natural Resources Canada, Canadian Forest "
    "Service, Laurentian Forestry Centre, Quebec, Canada. "
    "https://doi.org/10.23687/07653869-f303-46c2-a04e-9ab479b73cbf"
)
SCANFI_LICENCE = "Open Government Licence - Canada"
SCANFI_CLASSES = (
    "balsamFir", "blackSpruce", "broadleaf", "douglasFir", "jackPine", "lodgepolePine",
    "otherConiferous", "ponderosaPine", "tamarack", "whiteRedPine",
)  # fmt: skip
SCANFI_BAND_CLASSES = {
    "Pseudotsuga": ("douglasFir",),
    "conifer": tuple(c for c in SCANFI_CLASSES if c != "broadleaf"),
    "broadleaf": ("broadleaf",),
}
SCANFI_NOT_AVAILABLE = tuple(b for b in BANDS if b not in SCANFI_BAND_CLASSES)

RULINGS = ("D83", "D84", "D85", "D86", "D87", "D74")


def scanfi_url(cls: str, year: int, base: str = SCANFI_BASE_URL) -> str:
    return f"{base}/SCANFI_spsCC_{cls}_{year}_v2_20260119.tif"


def _to_native(crs):
    """ESRI:102008 to a NAD83 projection through NAD83 longitude and latitude, no datum step."""
    to_lonlat = Transformer.from_crs(GRID_CRS, GEOGRAPHIC_CRS, always_xy=True)
    to_crs = Transformer.from_crs(GEOGRAPHIC_CRS, crs, always_xy=True)

    def transform(xs, ys):
        lon, lat = to_lonlat.transform(xs, ys)
        return to_crs.transform(lon, lat)

    return transform


def native_bounds(window: GridWindow, crs, margin_m: float = 300.0):
    xs = np.linspace(window.left, window.right, max(window.width // 8, 2) + 1)
    ys = np.linspace(window.bottom, window.top, max(window.height // 8, 2) + 1)
    ex = np.concatenate([xs, xs, np.full(len(ys), window.left), np.full(len(ys), window.right)])
    ey = np.concatenate([np.full(len(xs), window.bottom), np.full(len(xs), window.top), ys, ys])
    nx, ny = _to_native(crs)(ex, ey)
    return (
        float(np.min(nx)) - margin_m,
        float(np.min(ny)) - margin_m,
        float(np.max(nx)) + margin_m,
        float(np.max(ny)) + margin_m,
    )


def _require_crs(actual, expected, name: str) -> None:
    probe_lon = np.array([-122.8, -120.95, -121.9, -96.0])
    probe_lat = np.array([48.7, 49.3, 49.0, 45.0])
    a = Transformer.from_crs(GEOGRAPHIC_CRS, CRS.from_user_input(expected), always_xy=True)
    b = Transformer.from_crs(GEOGRAPHIC_CRS, CRS.from_wkt(actual.to_wkt()), always_xy=True)
    ax, ay = a.transform(probe_lon, probe_lat)
    bx, by = b.transform(probe_lon, probe_lat)
    if not (np.allclose(ax, bx, atol=1e-3) and np.allclose(ay, by, atol=1e-3)):
        raise ValueError(f"{name} is not in the expected projection")


def _pixel_latitudes(transform, width, height, crs) -> np.ndarray:
    xs = transform.c + (np.arange(width) + 0.5) * transform.a
    ys = transform.f + (np.arange(height) + 0.5) * transform.e
    gx, gy = np.meshgrid(xs, ys)
    _, lat = Transformer.from_crs(crs, GEOGRAPHIC_CRS, always_xy=True).transform(gx, gy)
    return np.asarray(lat)


def _cell_latitudes(window: GridWindow) -> np.ndarray:
    xs = window.left + (np.arange(window.width) + 0.5) * CELL_SIZE_M
    ys = window.top - (np.arange(window.height) + 0.5) * CELL_SIZE_M
    gx, gy = np.meshgrid(xs, ys)
    _, lat = Transformer.from_crs(GRID_CRS, GEOGRAPHIC_CRS, always_xy=True).transform(gx, gy)
    return np.asarray(lat)


def _number(text: str) -> float:
    return float("nan") if text in ("", "NA") else float(text)


# Pixels of the cut window that lie beyond the TreeMap raster itself. The raster ends a little north
# of 49 N (its top edge in EPSG:5070 is 3,177,435 m), short of the strip's north edge; those pixels
# are on the Canadian side and are no data there. One on the US side is an error.
OUTSIDE_RASTER = -1


def _cut_window(source: Path, bounds, dest: Path) -> dict:
    """Like soilgrids.fetch_layer for a local raster, but pixels beyond it read OUTSIDE_RASTER."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(source) as src:
        raw = from_bounds(*bounds, transform=src.transform)
        col0, row0 = math.floor(raw.col_off), math.floor(raw.row_off)
        col1 = math.ceil(raw.col_off + raw.width)
        row1 = math.ceil(raw.row_off + raw.height)
        window = Window(col0, row0, col1 - col0, row1 - row0)
        data = src.read(1, window=window, boundless=True, fill_value=OUTSIDE_RASTER)
        if (data == OUTSIDE_RASTER).any() and src.nodata == OUTSIDE_RASTER:
            raise ValueError("the raster's own no-data value collides with OUTSIDE_RASTER")
        profile = {
            "driver": "GTiff", "width": window.width, "height": window.height, "count": 1,
            "dtype": data.dtype.name, "crs": src.crs, "transform": src.window_transform(window),
            "nodata": src.nodata, "compress": "deflate",
        }  # fmt: skip
        record = {
            "source": str(source),
            "bounds_requested": list(bounds),
            "pixel_window": {"col_off": col0, "row_off": row0, "width": col1 - col0,
                             "height": row1 - row0},
            "source_grid": {"crs_wkt": src.crs.to_wkt(), "transform": list(src.transform)[:6],
                            "width": src.width, "height": src.height},
            "nodata": src.nodata,
            "outside_raster_value": OUTSIDE_RASTER,
            "outside_raster_pixels": int((data == OUTSIDE_RASTER).sum()),
        }  # fmt: skip
    lat = _pixel_latitudes(profile["transform"], window.width, window.height, profile["crs"])
    if ((data == OUTSIDE_RASTER) & (lat < BORDER_LATITUDE)).any():
        raise ValueError("the TreeMap raster does not cover the US side of the window")
    with rasterio.open(dest, "w", **profile) as dst:
        dst.write(data, 1)
    record["file"] = dest.name
    record["sha256"] = hashlib.sha256(dest.read_bytes()).hexdigest()
    return record


US_TOTALS = ("treemap_canopy", "tree_list")
US_TOTAL_TAGS = {
    "treemap_canopy": "treemap_canopy (D88): TreeMap CANOPYPCT, live canopy cover (percent) from "
    "the Forest Vegetation Simulator; genus cover = CANOPYPCT x the tree-list genus share (D87)",
    "tree_list": "tree_list (D87 as first built): Crookston and Stage cover from Bechtold 2004 "
    "crown widths, trees of 5.0 in and up",
}


def read_dbf_columns(path: Path, names: tuple[str, ...]) -> dict[str, list[str]]:
    """Named columns of a dBase III table (a raster attribute table), as stripped strings."""
    with open(path, "rb") as f:
        head = f.read(32)
        count, header_len, record_len = struct.unpack("<IHH", head[4:12])
        fields = []
        while True:
            d = f.read(32)
            if not d or d[0] == 0x0D:
                break
            fields.append((d[:11].split(b"\0")[0].decode("ascii"), d[16]))
        missing = [n for n in names if n not in {name for name, _ in fields}]
        if missing:
            raise ValueError(f"{path.name} has no field {missing}")
        f.seek(header_len)
        out: dict[str, list[str]] = {n: [] for n in names}
        for _ in range(count):
            record = f.read(record_len)
            pos = 1
            for name, size in fields:
                if name in out:
                    out[name].append(record[pos : pos + size].decode("ascii").strip())
                pos += size
    return out


def read_canopy_pct(vat_path: Path) -> dict[int, float]:
    """TreeMap's CANOPYPCT by raster value (TM_ID), from the raster attribute table (D88)."""
    cols = read_dbf_columns(Path(vat_path), ("Value", "CANOPYPCT"))
    return {
        int(float(v)): float(c) for v, c in zip(cols["Value"], cols["CANOPYPCT"], strict=True) if c
    }


def cut_treemap(
    native_dir: Path,
    box: LonLatBox,
    treemap_tif: Path,
    tree_zip: Path,
    member: str = TREE_TABLE_MEMBER,
) -> Path:
    """The TreeMap window over ``box`` and its plots' covers. Returns the request record's path."""
    native_dir = Path(native_dir)
    window = master_window(box)
    record = _cut_window(
        Path(treemap_tif), native_bounds(window, TREEMAP_CRS), native_dir / "treemap_plots.tif"
    )
    with rasterio.open(native_dir / "treemap_plots.tif") as ds:
        plots = ds.read(1)
        nodata = ds.nodata
    ids = {int(v) for v in np.unique(plots[(plots != nodata) & (plots != OUTSIDE_RASTER)])}

    trees: dict[int, list[Tree]] = {i: [] for i in ids}
    with zipfile.ZipFile(tree_zip) as z, z.open(member) as f:
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            tm = int(row["TM_ID"])
            if tm in trees:
                trees[tm].append(
                    Tree(
                        spcd=int(row["SPCD"]),
                        genus=row["SCIENTIFIC_NAME"].split()[0],
                        dbh_in=_number(row["DIA"]),
                        tpa=_number(row["TPA_UNADJ"]),
                        live=row["STATUSCD"] == "1",
                    )
                )
    vat_path = Path(str(treemap_tif) + ".vat.dbf")
    canopy = read_canopy_pct(vat_path)
    lacking = sorted(i for i in ids if i not in canopy)
    if lacking:
        raise ValueError(
            f"{len(lacking)} plots in the window have no CANOPYPCT, e.g. {lacking[:5]}"
        )
    surrogates: dict[int, int] = {}
    surrogate_trees = 0
    without_split = 0
    with open(native_dir / "treemap_plot_covers.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["TM_ID", "surrogate_width_scale", "total", *BANDS, "treemap_canopy_pct"])
        for tm in sorted(trees):
            for scale in SURROGATE_SCALES:
                c = plot_cover(trees[tm], surrogate_width_scale=scale)
                w.writerow(
                    [tm, scale, repr(c.total), *(repr(c.by_band[b]) for b in BANDS), canopy[tm]]
                )
                if scale == 1.0:
                    without_split += c.total == 0
                    surrogates.update(c.surrogate_species)
                    surrogate_trees += c.surrogate_trees
    sidecar = Path(str(tree_zip) + ".sha256")
    zip_sha = sidecar.read_text().split()[0] if sidecar.exists() else None
    request = {
        "dataset": "TreeMap 2023 CONUS (Forest Service Research Data Archive, RDS-2026-0038)",
        "citation": TREEMAP_CITATION,
        "terms": TREEMAP_TERMS,
        "derived_notice": DERIVED_NOTICE,
        "zip": Path(tree_zip).name,
        "zip_sha256": zip_sha,
        "tree_table_member": member,
        "raster_window": record,
        "plots_in_window": len(ids),
        "plots_without_tree_rows": sum(1 for t in trees.values() if not t),
        "plots_without_split": int(without_split),
        "attribute_table": vat_path.name,
        "attribute_table_sha256": hashlib.sha256(vat_path.read_bytes()).hexdigest(),
        "surrogate_trees": surrogate_trees,
        "surrogate_species": {str(k): v for k, v in sorted(surrogates.items())},
        "extent": asdict(box),
        "master_window": asdict(window),
        "rulings": list(RULINGS),
    }
    path = native_dir / "treemap_request.json"
    path.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n")
    return path


def fetch_scanfi(native_dir: Path, box: LonLatBox, year: int = SCANFI_YEAR, source_for=scanfi_url):
    """One windowed read per SCANFI class. Returns the request record's path."""
    native_dir = Path(native_dir)
    window = master_window(box)
    bounds = native_bounds(window, SCANFI_CRS_WKT)
    records = [
        fetch_layer(source_for(cls, year), bounds, native_dir / f"scanfi_{cls}.tif")
        for cls in SCANFI_CLASSES
    ]
    request = {
        "dataset": "SCANFI v2, species crown closure (%)",
        "citation": SCANFI_CITATION,
        "licence": SCANFI_LICENCE,
        "licence_source": "https://open.canada.ca/data/en/dataset/07653869-f303-46c2-a04e-9ab479b73cbf",
        "year": year,
        "classes": list(SCANFI_CLASSES),
        "extent": asdict(box),
        "master_window": asdict(window),
        "native_bounds": list(bounds),
        "layers": records,
        "rulings": list(RULINGS),
    }
    path = native_dir / "scanfi_request.json"
    path.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n")
    return path


def _plot_cover_table(native_dir: Path, scale: float) -> tuple[np.ndarray, np.ndarray]:
    if scale not in SURROGATE_SCALES:
        raise ValueError(f"surrogate width scale {scale} was not computed; use {SURROGATE_SCALES}")
    ids, values = [], []
    with open(native_dir / "treemap_plot_covers.csv") as f:
        for row in csv.DictReader(f):
            if float(row["surrogate_width_scale"]) == scale:
                ids.append(int(row["TM_ID"]))
                values.append(
                    [
                        float(row["total"]),
                        *(float(row[b]) for b in BANDS),
                        float(row["treemap_canopy_pct"]),
                    ]
                )
    order = np.argsort(ids)
    return np.asarray(ids)[order], np.asarray(values)[order]


def _treemap_layers(native_dir: Path, scale: float, us_total: str):
    """(cover layers, split layers). Cover gives the cell's total; split gives the shares.

    ``tree_list``: both are the tree-list cover (D87 as first built). ``treemap_canopy`` (D88):
    the cover is TreeMap's CANOPYPCT; a genus's cover is CANOPYPCT x its tree-list share, and a
    plot whose tree list has no crown (only trees under 5 in) has canopy but no split, so its
    pixels are left out of the shares rather than counted as no genus.
    """
    if us_total not in US_TOTALS:
        raise ValueError(f"us_total must be one of {US_TOTALS}")
    ids, table = _plot_cover_table(native_dir, scale)
    with rasterio.open(native_dir / "treemap_plots.tif") as ds:
        _require_crs(ds.crs, TREEMAP_CRS, "treemap_plots.tif")
        plots = ds.read(1)
        nodata = ds.nodata
        transform, crs = ds.transform, ds.crs
    own_side = _pixel_latitudes(transform, plots.shape[1], plots.shape[0], crs) < BORDER_LATITUDE
    outside = plots == OUTSIDE_RASTER
    forest = (plots != nodata) & ~outside
    pos = np.searchsorted(ids, plots[forest])
    if (pos >= len(ids)).any() or (ids[np.minimum(pos, len(ids) - 1)] != plots[forest]).any():
        raise ValueError("a TreeMap plot in the window has no row in the plot cover table")
    rows = table[pos]
    tree_total = rows[:, 0]
    if us_total == "tree_list":
        cover = tree_total
        split = {name: rows[:, k] for k, name in enumerate(("total", *BANDS))}
    else:
        canopy = rows[:, -1]
        cover = canopy
        has_split = tree_total > 0
        with np.errstate(invalid="ignore", divide="ignore"):
            split = {"total": np.where(has_split, canopy, np.nan)}
            for k, name in enumerate(BANDS, start=1):
                split[name] = np.where(has_split, canopy * rows[:, k] / tree_total, np.nan)

    def layer_of(values):
        layer = np.zeros(plots.shape)
        layer[forest] = values
        layer[~own_side | outside] = np.nan
        return layer

    cover_layers = [("total", layer_of(cover), transform)]
    split_layers = [(name, layer_of(v), transform) for name, v in split.items()]
    return cover_layers, split_layers


def _scanfi_layers(native_dir: Path):
    arrays = {}
    grid = None
    for cls in SCANFI_CLASSES:
        with rasterio.open(native_dir / f"scanfi_{cls}.tif") as ds:
            this = (tuple(ds.transform)[:6], ds.width, ds.height)
            if grid is None:
                _require_crs(ds.crs, SCANFI_CRS_WKT, f"scanfi_{cls}.tif")
                grid, transform, crs = this, ds.transform, ds.crs
            elif this != grid:
                raise ValueError(f"scanfi_{cls}.tif is on a different grid from the others")
            data = ds.read(1).astype("float64")
            if ds.nodata is None:
                raise ValueError(f"scanfi_{cls}.tif declares no no-data value")
            data[ds.read(1) == ds.nodata] = 0.0
            arrays[cls] = data
    shape = arrays[SCANFI_CLASSES[0]].shape
    own_side = _pixel_latitudes(transform, shape[1], shape[0], crs) >= BORDER_LATITUDE
    total = sum(arrays.values())
    layers = {"total": total}
    for band, classes in SCANFI_BAND_CLASSES.items():
        layers[band] = sum(arrays[c] for c in classes)
    for name, layer in layers.items():
        layer = layer.copy()
        layer[~own_side] = np.nan
        yield name, layer, transform


def _regrid(layers, crs, window):
    """All of one source's layers in one regrid, so the footprint geometry is computed once."""
    names, arrays, transform = [], [], None
    for name, layer, this in layers:
        if transform is not None and this != transform:
            raise ValueError("layers of one source must share a grid")
        names.append(name)
        arrays.append(layer)
        transform = this
    v, f = area_weighted_regrid(np.stack(arrays), transform, _to_native(crs), window)
    if not all(np.array_equal(f[0], f[k]) for k in range(1, len(names))):
        raise ValueError("layers of one source must share their no-data pattern")
    return {name: v[k] for k, name in enumerate(names)}, f[0]


def build_master(
    native_dir: Path,
    out_dir: Path,
    box: LonLatBox,
    surrogate_width_scale: float = 1.0,
    us_total: str = "treemap_canopy",
) -> dict:
    native_dir, out_dir = Path(native_dir), Path(out_dir)
    window = master_window(box)
    in_box = box_mask(window, box)
    canada = _cell_latitudes(window) >= BORDER_LATITUDE

    cover_layers, split_layers = _treemap_layers(native_dir, surrogate_width_scale, us_total)
    us_cover, us_frac = _regrid(cover_layers, TREEMAP_CRS, window)
    us, _ = _regrid(split_layers, TREEMAP_CRS, window)
    ca, ca_frac = _regrid(_scanfi_layers(native_dir), SCANFI_CRS_WKT, window)

    fraction = np.where(canada, ca_frac, us_frac)
    total = np.where(canada, ca["total"], us_cover["total"])
    valid = in_box & (fraction >= MIN_VALID_FRACTION)
    defined = valid & (total >= MIN_TOTAL_COVER_PCT)
    side_flag = np.where(canada, FLAG_SCANFI, FLAG_TREEMAP)

    bands = {
        "total_cover_pct": np.where(valid, total, np.nan),
        "valid_fraction": np.where(in_box, fraction, 0.0),
        "source": np.where(in_box, side_flag, FLAG_NONE).astype("float64"),
    }
    flags = {}
    with np.errstate(invalid="ignore", divide="ignore"):
        for band in BANDS:
            us_share = us[band] / us["total"]
            if band in SCANFI_BAND_CLASSES:
                share = np.where(canada, ca[band] / ca["total"], us_share)
            else:
                share = np.where(canada, np.nan, us_share)
            # A cell with cover but no split (D88: canopy from plots whose tree list has no crown)
            # has no share and no source flag.
            has_share = defined & np.isfinite(share)
            flag = np.where(has_share, side_flag, FLAG_NONE)
            if band not in SCANFI_BAND_CLASSES:
                flag = np.where(in_box & canada, FLAG_NOT_AVAILABLE, flag)
            bands[f"share_{band}"] = np.where(has_share, share, np.nan)
            flags[f"flag_{band}"] = flag.astype("uint8")

    with open(native_dir / "treemap_request.json") as f:
        tm_request = json.load(f)
    with open(native_dir / "scanfi_request.json") as f:
        sc_request = json.load(f)
    tags = {
        "attribution": f"{TREEMAP_CITATION} | {SCANFI_CITATION} ({SCANFI_LICENCE})",
        "derived_notice": DERIVED_NOTICE,
        "rulings": ",".join(RULINGS),
        "flag_legend": FLAG_LEGEND,
        "not_available_in_scanfi": ",".join(SCANFI_NOT_AVAILABLE),
        "min_total_cover_pct": str(MIN_TOTAL_COVER_PCT),
        "min_valid_fraction": str(MIN_VALID_FRACTION),
        "surrogate_width_scale": str(surrogate_width_scale),
        "scanfi_year": str(sc_request["year"]),
        "share_definition": "genus crown cover / total crown cover on the cell's own side (D87)",
        "us_total": US_TOTAL_TAGS[us_total],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    transform = from_origin(window.left, window.top, CELL_SIZE_M, CELL_SIZE_M)
    profile = {
        "driver": "GTiff",
        "width": window.width,
        "height": window.height,
        "crs": GRID_CRS,
        "transform": transform,
        "compress": "deflate",
    }
    with rasterio.open(
        out_dir / "host_trees_strip.tif", "w", count=len(bands), dtype="float32",
        nodata=float("nan"), **profile,
    ) as dst:  # fmt: skip
        for i, (name, data) in enumerate(bands.items(), start=1):
            dst.write(data.astype("float32"), i)
            dst.set_band_description(i, name)
        dst.update_tags(**tags)
    with rasterio.open(
        out_dir / "host_trees_strip_flags.tif", "w", count=len(flags), dtype="uint8", **profile
    ) as dst:
        for i, (name, data) in enumerate(flags.items(), start=1):
            dst.write(data, i)
            dst.set_band_description(i, name)
        dst.update_tags(**tags)

    summary = {
        "master_window": asdict(window),
        "cells_in_box": {
            "us": int((in_box & ~canada).sum()),
            "canada": int((in_box & canada).sum()),
        },
        "cells_valid": {"us": int((valid & ~canada).sum()), "canada": int((valid & canada).sum())},
        "cells_with_share": {
            "us": int((defined & ~canada).sum()),
            "canada": int((defined & canada).sum()),
        },
        "surrogate_width_scale": surrogate_width_scale,
        "surrogate_species": tm_request["surrogate_species"],
        "surrogate_trees": tm_request["surrogate_trees"],
        "plots_in_window": tm_request["plots_in_window"],
        "plots_without_tree_rows": tm_request["plots_without_tree_rows"],
        "plots_without_split": tm_request["plots_without_split"],
        "us_total": us_total,
        "scanfi_year": sc_request["year"],
        "mean_share_where_defined": {
            band: {
                side: (
                    None
                    if not (m := defined & sel & np.isfinite(bands[f"share_{band}"])).any()
                    else float(np.mean(bands[f"share_{band}"][m]))
                )
                for side, sel in (("us", ~canada), ("canada", canada))
            }
            for band in BANDS
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if not math.isfinite(float(np.nanmax(bands["valid_fraction"]))):
        raise AssertionError("valid fraction is not finite")
    return summary
