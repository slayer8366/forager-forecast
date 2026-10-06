"""T4: SoilGrids pH for western Washington on the master grid, then to a zoom-9 PMTiles archive.

docs/dispatch/2026-10-06-t4-master-grid.md. Rulings: D80 (0 to 30 cm, thickness-weighted), D81
(mean as the value; Q0.05 and Q0.95 carried on the master grid, approximate, not in the archive),
D82 (the area is a longitude-latitude rectangle, 45.5 to 49.0 N, 121.0 to 125.0 W).

Steps, each a function so tests reach them through the same entry points the script uses:

1. ``fetch_natives``: one windowed read per layer (3 depths x 3 statistics) in SoilGrids' native
   Homolosine, stored unchanged, with the request record written beside them.
2. ``build_master``: pH x 10 to pH, the 0 to 30 cm blend per statistic, then the one warp, an exact
   area-weighted regrid onto the master grid (regrid.py). A cell whose valid area is under
   ``MIN_VALID_FRACTION`` becomes no data; every cell's valid fraction is kept as its own band.
   Cells whose centre lies outside the rectangle are no data.
3. ``build_archive``: nearest to zoom-9 Web Mercator, one grey byte per pixel, PMTiles.
"""

import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

from forager_forecast.grid import (
    CELL_SIZE_M,
    GEOGRAPHIC_CRS,
    GRID_CRS,
    GridWindow,
    lonlat_transformer,
    window_for_bounds,
)
from forager_forecast.regrid import area_weighted_regrid
from forager_forecast.soilgrids import (
    ATTRIBUTION,
    DEPTHS,
    STATISTICS,
    blend_0_30,
    fetch_layer,
    grid_to_homolosine,
    layer_name,
    layers,
    native_bounds_for,
    ph_from_mapped,
    vrt_url,
    write_request,
)
from forager_forecast.tiles import (
    encode_ph_byte,
    master_to_mercator_nearest,
    mercator_window_for,
    write_archive,
)


@dataclass(frozen=True)
class LonLatBox:
    """A longitude-latitude rectangle, edges inclusive, WGS84 read as NAD83 (grid.py)."""

    south: float
    north: float
    west: float
    east: float

    def contains(self, lon, lat):
        lon = np.asarray(lon)
        lat = np.asarray(lat)
        return (lat >= self.south) & (lat <= self.north) & (lon >= self.west) & (lon <= self.east)


# D82, the owner's "Simple rectangle (Recommended)".
WESTERN_WASHINGTON = LonLatBox(south=45.5, north=49.0, west=-125.0, east=-121.0)

# Below this share of valid area a master cell is no data: a cell averaged from a sliver of soil
# beside water or town should not pass as a full one. Chosen by the builder on 2026-10-06 at the
# planner's request (condition 2); every cell's fraction is kept, so a later layer can choose
# differently without a refetch.
MIN_VALID_FRACTION = 0.5

BAND_DESCRIPTIONS = (
    "ph_mean_0_30cm",
    "ph_q05_0_30cm_approximate",
    "ph_q95_0_30cm_approximate",
    "valid_fraction_mean",
    "valid_fraction_q05",
    "valid_fraction_q95",
)
APPROXIMATE_NOTE = (
    "approximate: SoilGrids Q{q} pH blended 0 to 30 cm with thickness weights 5, 10, 15 "
    "(D80, D81). "
    "A weighted mean of quantiles is not a quantile, so this is not the 0 to 30 cm value's "
    "{q} quantile, only an approximation to it."
)
ARCHIVE_NAME = "soil-ph-0-30cm"


def master_window(box: LonLatBox) -> GridWindow:
    """The master-grid window, snapped to the lattice, covering the whole rectangle."""
    n = 400
    lons = np.linspace(box.west, box.east, n + 1)
    lats = np.linspace(box.south, box.north, n + 1)
    edge_lon = np.concatenate([lons, lons, np.full(n + 1, box.west), np.full(n + 1, box.east)])
    edge_lat = np.concatenate([np.full(n + 1, box.south), np.full(n + 1, box.north), lats, lats])
    x, y = lonlat_transformer().transform(edge_lon, edge_lat)
    return window_for_bounds(float(np.min(x)), float(np.min(y)), float(np.max(x)), float(np.max(y)))


def box_mask(window: GridWindow, box: LonLatBox) -> np.ndarray:
    """True for cells whose centre lies inside the rectangle."""
    to_lonlat = Transformer.from_crs(GRID_CRS, GEOGRAPHIC_CRS, always_xy=True)
    xs = window.left + (np.arange(window.width) + 0.5) * CELL_SIZE_M
    ys = window.top - (np.arange(window.height) + 0.5) * CELL_SIZE_M
    gx, gy = np.meshgrid(xs, ys)
    lon, lat = to_lonlat.transform(gx.ravel(), gy.ravel())
    return box.contains(lon, lat).reshape(window.height, window.width)


def fetch_natives(
    native_dir: Path,
    box: LonLatBox,
    source_for: Callable[[str, str], str] = vrt_url,
) -> Path:
    """One windowed read per layer. Returns the path of the request record written beside them."""
    native_dir = Path(native_dir)
    window = master_window(box)
    bounds = native_bounds_for(window)
    records = [
        fetch_layer(source_for(depth, stat), bounds, native_dir / f"{layer_name(depth, stat)}.tif")
        for depth, stat in layers()
    ]
    request_path = native_dir / "request.json"
    write_request(
        records,
        {
            "dataset": "SoilGrids 2.0, ISRIC - World Soil Information",
            "licence": "CC BY 4.0",
            "property": "phh2o (pH in water, mapped as pH x 10)",
            "depths": [d for d, _ in DEPTHS],
            "statistics": list(STATISTICS),
            "extent": asdict(box),
            "master_window": asdict(window),
            "native_bounds_homolosine": list(bounds),
            "rulings": ["D80", "D81", "D82"],
            "dispatch": "docs/dispatch/2026-10-06-t4-master-grid.md",
        },
        request_path,
    )
    return request_path


def _read_native(native_dir: Path):
    grid = None
    by_stat: dict[str, dict[str, np.ndarray]] = {stat: {} for stat in STATISTICS}
    transform = None
    for depth, stat in layers():
        with rasterio.open(native_dir / f"{layer_name(depth, stat)}.tif") as ds:
            this = (ds.crs.to_wkt(), tuple(ds.transform)[:6], ds.width, ds.height)
            if grid is None:
                grid, transform = this, ds.transform
            elif this != grid:
                raise ValueError(
                    f"{layer_name(depth, stat)} is on a different grid from the others"
                )
            by_stat[stat][depth] = ph_from_mapped(ds.read(1), ds.nodata)
    return by_stat, transform


def build_master(native_dir: Path, master_path: Path, box: LonLatBox) -> dict:
    """The blended layers regridded onto the master grid, written as a 6-band GeoTIFF."""
    native_dir, master_path = Path(native_dir), Path(master_path)
    by_stat, transform = _read_native(native_dir)
    native = np.stack([blend_0_30(by_stat[stat]) for stat in STATISTICS])
    window = master_window(box)

    started = time.perf_counter()
    values, fraction = area_weighted_regrid(native, transform, grid_to_homolosine(), window)
    regrid_seconds = time.perf_counter() - started

    mask = box_mask(window, box)
    sliver = (fraction < MIN_VALID_FRACTION) & (fraction > 0)
    values[(fraction < MIN_VALID_FRACTION) | ~mask[None]] = np.nan
    fraction[:, ~mask] = 0.0

    master_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "width": window.width,
        "height": window.height,
        "count": 6,
        "dtype": "float32",
        "crs": GRID_CRS,
        "transform": rasterio.transform.from_origin(
            window.left, window.top, CELL_SIZE_M, CELL_SIZE_M
        ),
        "nodata": float("nan"),
        "compress": "deflate",
        "tiled": True,
    }
    with rasterio.open(master_path, "w", **profile) as dst:
        dst.write(np.concatenate([values, fraction]).astype("float32"))
        for i, name in enumerate(BAND_DESCRIPTIONS, start=1):
            dst.set_band_description(i, name)
        dst.update_tags(1, note="SoilGrids mean pH blended 0 to 30 cm (D80, D81)")
        dst.update_tags(2, note=APPROXIMATE_NOTE.format(q="0.05"))
        dst.update_tags(3, note=APPROXIMATE_NOTE.format(q="0.95"))
        dst.update_tags(
            grid="ESRI:102008, 250 m, lattice origin (0, 0), cell id "
            "((row + 32768) << 16) | (col + 32768); src/forager_forecast/grid.py",
            depth="0 to 30 cm, thickness weights 5, 10, 15 over 0-5, 5-15, 15-30 cm (D80)",
            extent=json.dumps(asdict(box)) + " (D82)",
            min_valid_fraction=str(MIN_VALID_FRACTION),
            regrid="exact area-weighted, valid pixels only (src/forager_forecast/regrid.py)",
            attribution=ATTRIBUTION,
        )
    return {
        "cells": window.width * window.height,
        "cells_in_extent": int(mask.sum()),
        "cells_with_mean": int(np.isfinite(values[0]).sum()),
        "cells_below_min_valid_fraction": int((sliver[0] & mask).sum()),
        "regrid_seconds": regrid_seconds,
        "window": asdict(window),
    }


def archive_metadata(box: LonLatBox) -> dict[str, str]:
    return {
        "name": ARCHIVE_NAME,
        "description": (
            "Soil pH (in water), 0 to 30 cm, thickness-weighted mean of SoilGrids 2.0 0-5, 5-15 "
            "and 15-30 cm layers (D80), on the 250 m master grid (ESRI:102008) and shown at "
            "zoom 9 in Web Mercator."
        ),
        "attribution": ATTRIBUTION,
        "forager_forecast_encoding": (
            "grey byte = floor(pH * 10 + 0.5), so pH = grey / 10; alpha 0 = no data"
        ),
        "forager_forecast_range_bands": (
            "Q0.05 and Q0.95 pH, blended 0 to 30 cm the same way, are approximate (a weighted mean "
            "of quantiles is not a quantile). They exist on the master grid only and are not in "
            "this archive (D81)."
        ),
        "forager_forecast_master_grid": (
            "ESRI:102008, 250 m cells, lattice origin (0, 0), cell id "
            "((row + 32768) << 16) | (col + 32768)"
        ),
        "forager_forecast_extent": (
            f"{box.south} to {box.north} N, {-box.east} to {-box.west} W (D82)"
        ),
        "forager_forecast_min_valid_fraction": str(MIN_VALID_FRACTION),
    }


def build_archive(master_path: Path, out_dir: Path, box: LonLatBox | None = None):
    """The master grid's mean band to a zoom-9 PMTiles archive. Returns (header, metadata)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(master_path) as ds:
        mean = ds.read(1).astype("float64")
        t = ds.transform
        window = GridWindow(
            int(t.c),
            int(t.f - ds.height * CELL_SIZE_M),
            int(t.c + ds.width * CELL_SIZE_M),
            int(t.f),
        )
        extent = json.loads(ds.tags()["extent"].removesuffix(" (D82)"))
    box = box or LonLatBox(**extent)
    merc = mercator_window_for(window)
    grey, alpha = encode_ph_byte(master_to_mercator_nearest(mean, window, merc))
    return write_archive(
        grey,
        alpha,
        merc,
        out_dir / f"{ARCHIVE_NAME}.mbtiles",
        out_dir / f"{ARCHIVE_NAME}.pmtiles",
        archive_metadata(box),
    )
