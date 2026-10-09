"""From a finished master-grid raster to a zoom-9 PMTiles archive (D6, D8, SPEC.md:48).

- The warp to Web Mercator is the only reprojection of a finished raster (D8). It is nearest, done
  here with pyproj rather than GDAL's warper: each zoom-9 pixel takes the master cell under its
  centre, so a value read from a tile is the master grid's value. Zoom 9 is about 208 m per pixel
  at 47 N, so this upsamples by about 1.2; smoothing is the map client's job. GDAL's warper was
  not used because its approximate transformer moved about 2.5% of nearest lookups to a
  neighbouring pixel in the verify-stage probe (docs/audits/2026-10-06-t4-verify/).
- Tiles hold one grey byte, ``floor(pH * 10 + 0.5)``, and an alpha byte that is 0 for no data
  (R5: masked cells are transparent). Overview zooms below 9 are GDAL ``average``; they are for
  display and nothing is checked against them.
- GDAL 3.12 writes raster MBTiles but not raster PMTiles, so the MBTiles is converted with the
  pinned ``pmtiles`` package.
"""

import math
import sqlite3
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from pmtiles.convert import mbtiles_to_pmtiles
from pmtiles.reader import MmapSource, Reader
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from forager_forecast.grid import CELL_SIZE_M, GridWindow, lonlat_transformer

MAX_ZOOM = 9
MIN_ZOOM = 5
TILE_PX = 256
_HALF_WORLD_M = math.pi * 6378137.0
Z9_PIXEL_M = 2 * _HALF_WORLD_M / TILE_PX / 2**MAX_ZOOM
_TILE_M = TILE_PX * Z9_PIXEL_M


@dataclass(frozen=True)
class MercatorWindow:
    """A block of zoom-9 pixels in EPSG:3857, aligned to tile edges."""

    left: float
    top: float
    width: int
    height: int

    @property
    def right(self) -> float:
        return self.left + self.width * Z9_PIXEL_M

    @property
    def bottom(self) -> float:
        return self.top - self.height * Z9_PIXEL_M


def mercator_window_for(window: GridWindow) -> MercatorWindow:
    """The tile-aligned zoom-9 block covering a master-grid window."""
    to_merc = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    to_lonlat = Transformer.from_crs("ESRI:102008", "EPSG:4269", always_xy=True)
    n = 64
    xs = np.linspace(window.left, window.right, n + 1)
    ys = np.linspace(window.bottom, window.top, n + 1)
    ex = np.concatenate([xs, xs, np.full(n + 1, window.left), np.full(n + 1, window.right)])
    ey = np.concatenate([np.full(n + 1, window.bottom), np.full(n + 1, window.top), ys, ys])
    lon, lat = to_lonlat.transform(ex, ey)
    mx, my = to_merc.transform(lon, lat)
    tx0 = math.floor((mx.min() + _HALF_WORLD_M) / _TILE_M)
    tx1 = math.ceil((mx.max() + _HALF_WORLD_M) / _TILE_M)
    ty0 = math.floor((_HALF_WORLD_M - my.max()) / _TILE_M)
    ty1 = math.ceil((_HALF_WORLD_M - my.min()) / _TILE_M)
    return MercatorWindow(
        left=-_HALF_WORLD_M + tx0 * _TILE_M,
        top=_HALF_WORLD_M - ty0 * _TILE_M,
        width=(tx1 - tx0) * TILE_PX,
        height=(ty1 - ty0) * TILE_PX,
    )


def master_to_mercator_nearest(
    values: np.ndarray, window: GridWindow, merc: MercatorWindow
) -> np.ndarray:
    """Each zoom-9 pixel takes the master cell under its centre; NaN outside the window."""
    to_lonlat = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    out = np.full((merc.height, merc.width), np.nan)
    xs = merc.left + (np.arange(merc.width) + 0.5) * Z9_PIXEL_M
    for r0 in range(0, merc.height, 256):
        r1 = min(r0 + 256, merc.height)
        ys = merc.top - (np.arange(r0, r1) + 0.5) * Z9_PIXEL_M
        mx, my = np.meshgrid(xs, ys)
        lon, lat = to_lonlat.transform(mx.ravel(), my.ravel())
        gx, gy = lonlat_transformer().transform(lon, lat)
        col = np.floor((np.asarray(gx) - window.left) / CELL_SIZE_M).astype(np.int64)
        row = np.floor((window.top - np.asarray(gy)) / CELL_SIZE_M).astype(np.int64)
        inside = (col >= 0) & (col < window.width) & (row >= 0) & (row < window.height)
        block = np.full(col.shape, np.nan)
        block[inside] = values[row[inside], col[inside]]
        out[r0:r1] = block.reshape(r1 - r0, merc.width)
    return out


def encode_ph_byte(ph: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(grey, alpha): grey is floor(pH * 10 + 0.5), alpha 0 where pH is NaN."""
    ph = np.asarray(ph, dtype="float64")
    valid = np.isfinite(ph)
    scaled = np.floor(np.where(valid, ph, 0.0) * 10 + 0.5)
    if (scaled[valid] < 0).any() or (scaled[valid] > 255).any():
        raise ValueError("a value outside 0 to 25.5 cannot be a pH and does not fit a byte")
    grey = np.where(valid, scaled, 0).astype("uint8")
    alpha = np.where(valid, 255, 0).astype("uint8")
    return grey, alpha


PERCENT_STEPS = 2  # grey byte steps per percentage point: 0.5 points, 0 to 100 -> 0 to 200


def encode_percent_byte(percent: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(grey, alpha) for a tree layer in percent (canopy cover, or a share times 100): grey is
    floor(percent * 2 + 0.5), alpha 0 where the value is NaN (no data, masked or pending)."""
    percent = np.asarray(percent, dtype="float64")
    valid = np.isfinite(percent)
    if (percent[valid] < -1e-6).any() or (percent[valid] > 100 + 1e-6).any():
        raise ValueError("a value outside 0 to 100 is not a percentage")
    scaled = np.floor(np.clip(np.where(valid, percent, 0.0), 0.0, 100.0) * PERCENT_STEPS + 0.5)
    grey = np.where(valid, scaled, 0).astype("uint8")
    alpha = np.where(valid, 255, 0).astype("uint8")
    return grey, alpha


def _normalise_header(header: Mapping) -> dict:
    out = dict(header)
    for key in ("tile_type", "tile_compression", "internal_compression"):
        if key in out and hasattr(out[key], "name"):
            out[key] = out[key].name
    return out


def read_archive(path: Path) -> tuple[dict, dict, Callable[[int, int, int], bytes | None]]:
    """(header, metadata, get_tile) of a PMTiles archive, opened read-only."""
    path = Path(path)
    with open(path, "rb") as f:
        reader = Reader(MmapSource(f))
        header = _normalise_header(reader.header())
        metadata = reader.metadata()

    def get_tile(z: int, x: int, y: int) -> bytes | None:
        with open(path, "rb") as f:
            return Reader(MmapSource(f)).get(z, x, y)

    return header, metadata, get_tile


def decode_tile(data: bytes | None) -> tuple[np.ndarray, np.ndarray]:
    """(grey, alpha) of one PNG tile."""
    if data is None:
        raise ValueError("no tile at that address")
    with MemoryFile(data) as mem, mem.open() as ds:
        bands = ds.read()
    if bands.shape[0] == 1:  # GDAL writes a fully opaque tile without its alpha band
        return bands[0], np.full(bands[0].shape, 255, dtype="uint8")
    if bands.shape[0] == 2:
        return bands[0], bands[1]
    if bands.shape[0] == 4:
        return bands[0], bands[3]
    raise ValueError(f"unexpected tile with {bands.shape[0]} bands")


def write_archive(
    grey: np.ndarray,
    alpha: np.ndarray,
    merc: MercatorWindow,
    mbtiles_path: Path,
    pmtiles_path: Path,
    metadata: Mapping[str, str],
) -> tuple[dict, dict]:
    """Write grey+alpha zoom-9 tiles with overviews to MIN_ZOOM, then convert to PMTiles."""
    mbtiles_path, pmtiles_path = Path(mbtiles_path), Path(pmtiles_path)
    for p in (mbtiles_path, pmtiles_path):
        if p.exists():
            p.unlink()
    profile = {
        "driver": "MBTiles",
        "width": merc.width,
        "height": merc.height,
        "count": 2,
        "dtype": "uint8",
        "crs": "EPSG:3857",
        "transform": from_origin(merc.left, merc.top, Z9_PIXEL_M, Z9_PIXEL_M),
    }
    with rasterio.open(
        mbtiles_path, "w", **profile, TILE_FORMAT="PNG", RESAMPLING="NEAREST"
    ) as dst:
        dst.write(grey, 1)
        dst.write(alpha, 2)
        factors = [2**k for k in range(1, MAX_ZOOM - MIN_ZOOM + 1)]
        dst.build_overviews(factors, Resampling.average)
    with sqlite3.connect(mbtiles_path) as con:
        for name, value in metadata.items():
            con.execute("DELETE FROM metadata WHERE name = ?", (name,))
            con.execute("INSERT INTO metadata (name, value) VALUES (?, ?)", (name, str(value)))
        zooms = con.execute("SELECT MIN(zoom_level), MAX(zoom_level) FROM tiles").fetchone()
        con.execute("UPDATE metadata SET value = ? WHERE name = 'minzoom'", (str(zooms[0]),))
        con.execute("UPDATE metadata SET value = ? WHERE name = 'maxzoom'", (str(zooms[1]),))
    mbtiles_to_pmtiles(str(mbtiles_path), str(pmtiles_path), None)
    header, meta, _ = read_archive(pmtiles_path)
    return header, meta


# --- Static z/x/y tiles (the site's test area, owner's "A: Pre-cut tiles, go live", RECORD -786) --
#
# Every zoom, not only zoom 9, takes the master cell under each pixel's centre (nearest), so no
# overview blends a value with a sentinel (review F5): a pixel is a value, no data or a sentinel.


def lonlat_to_tile(lon: float, lat: float, z: int) -> tuple[float, float]:
    """Fractional slippy-map tile coordinates (x east, y south) of a point at zoom z."""
    n = 2**z
    s = math.sin(math.radians(lat))
    return (lon + 180.0) / 360.0 * n, (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n


def tile_range(west: float, south: float, east: float, north: float, z: int):
    """(x0, x1, y0, y1), inclusive, of the tiles meeting the box: the same tiles MapLibre asks
    for when a source declares these bounds (floor of the west and north edges, ceil - 1 of the
    east and south edges)."""
    xw, yn = lonlat_to_tile(west, north, z)
    xe, ys = lonlat_to_tile(east, south, z)
    return math.floor(xw), math.ceil(xe) - 1, math.floor(yn), math.ceil(ys) - 1


def tile_values(values: np.ndarray, window: GridWindow, z: int, x: int, y: int) -> np.ndarray:
    """One 256 x 256 tile: each pixel takes the master cell under its centre; NaN outside."""
    size = 2 * _HALF_WORLD_M / 2**z
    px = size / TILE_PX
    left = -_HALF_WORLD_M + x * size
    top = _HALF_WORLD_M - y * size
    xs = left + (np.arange(TILE_PX) + 0.5) * px
    ys = top - (np.arange(TILE_PX) + 0.5) * px
    mx, my = np.meshgrid(xs, ys)
    lon, lat = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True).transform(
        mx.ravel(), my.ravel()
    )
    gx, gy = lonlat_transformer().transform(lon, lat)
    col = np.floor((np.asarray(gx) - window.left) / CELL_SIZE_M).astype(np.int64)
    row = np.floor((window.top - np.asarray(gy)) / CELL_SIZE_M).astype(np.int64)
    inside = (col >= 0) & (col < window.width) & (row >= 0) & (row < window.height)
    out = np.full(col.shape, np.nan)
    out[inside] = values[row[inside], col[inside]]
    return out.reshape(TILE_PX, TILE_PX)


def png_grey_alpha(grey: np.ndarray, alpha: np.ndarray) -> bytes:
    """A two-band (grey, alpha) PNG."""
    with MemoryFile() as mem:
        with mem.open(driver="PNG", width=grey.shape[1], height=grey.shape[0], count=2,
                      dtype="uint8") as dst:  # fmt: skip
            dst.write(grey, 1)
            dst.write(alpha, 2)
        return mem.read()
