"""T6b: the study-area mask (D111, D113) and which side of the border a cell is on (D115).

- Lines: CEC North American Atlas, Political Boundaries 2021 (D113), and CEC Terrestrial
  Ecoregions v2, level I "Tundra" (LEVEL1 2) and "Arctic Cordillera" (LEVEL1 1) (D111). Both are
  shapefiles in Lambert azimuthal equal-area on a sphere of radius 6,370,997 m (their .prj). Their
  coordinates go to longitude and latitude on that sphere by a pure inverse projection, and those
  values are then read as NAD83, as everything else on the master grid is (grid.py): a null datum
  step, which at 1:10M is far below the lines' own accuracy.
- Burned by cell centre (GDAL's default rasterize rule), as T4's rectangle and T5's strip were.
  Rings are burned even-odd, so a lake drawn as a hole is out and an island in it is back in. Only
  rings whose bounding box meets a block are passed, which changes nothing: a closed ring that
  does not contain a point crosses any line to it an even number of times.
- The mask raster has two bands: the country code of the cell centre, and 1 where the centre is in
  the Arctic (D111). In the study area: 48 conterminous states and DC, or Canada; and not Arctic.
- Side (D115 item 1): T5's rule, centre at 49 N or north is Canada, inside the band where the border
  is the 49th parallel (122.80 W to 95.15 W, 48.0 to 50.0 N); elsewhere the country polygon.
"""

import struct
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.windows import Window

from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS, GridWindow
from forager_forecast.t5_layer import read_dbf_columns

CEC_LAEA = "+proj=laea +lat_0=45 +lon_0=-100 +x_0=0 +y_0=0 +R=6370997 +units=m +no_defs"
_CEC_LONLAT = "+proj=longlat +R=6370997 +no_defs"

COUNTRY_NONE = 0
COUNTRY_US48 = 1
COUNTRY_CAN = 2
COUNTRY_US_OTHER = 3  # Alaska, Hawaii, Puerto Rico, US Virgin Islands (D31, D86, D113)
COUNTRY_MEX = 4
COUNTRY_LEGEND = (
    "country: 0 none, 1 US 48 states and DC, 2 Canada, 3 Alaska Hawaii Puerto Rico USVI, "
    "4 Mexico (D113)"
)
US_MASKED_STATES = frozenset({"US-AK", "US-HI", "US-PR", "US-VI"})
ARCTIC_LEVEL1 = frozenset({"1", "2"})  # "Arctic Cordillera", "Tundra" (D111, read from the file)

SIDE_NONE = 0
SIDE_US = 1
SIDE_CA = 2
BAND_WEST, BAND_EAST = -122.80, -95.15
BAND_SOUTH, BAND_NORTH = 48.0, 50.0
BORDER_LATITUDE = 49.0


def read_shapefile(shp: Path) -> list[list[np.ndarray]]:
    """Each record's rings, as (N, 2) arrays of the file's own coordinates. Polygons only."""
    out: list[list[np.ndarray]] = []
    with open(shp, "rb") as f:
        header = f.read(100)
        if struct.unpack(">i", header[:4])[0] != 9994:
            raise ValueError(f"{shp} is not a shapefile")
        while head := f.read(8):
            _, words = struct.unpack(">2i", head)
            content = f.read(2 * words)
            shape_type = struct.unpack("<i", content[:4])[0]
            if shape_type == 0:
                out.append([])
                continue
            if shape_type != 5:
                raise ValueError(f"{shp}: shape type {shape_type} is not a polygon")
            nparts, npoints = struct.unpack("<2i", content[36:44])
            parts = list(struct.unpack(f"<{nparts}i", content[44 : 44 + 4 * nparts]))
            start = 44 + 4 * nparts
            pts = np.frombuffer(content[start : start + 16 * npoints], dtype="<f8").reshape(-1, 2)
            out.append([pts[a:b] for a, b in zip(parts, [*parts[1:], npoints], strict=True)])
    return out


def _to_grid(rings: list[np.ndarray]) -> list[np.ndarray]:
    inverse = Transformer.from_crs(CEC_LAEA, _CEC_LONLAT, always_xy=True)
    forward = Transformer.from_crs(GEOGRAPHIC_CRS, GRID_CRS, always_xy=True)
    projected = []
    for ring in rings:
        lon, lat = inverse.transform(ring[:, 0], ring[:, 1])
        x, y = forward.transform(lon, lat)
        projected.append(np.column_stack([x, y]))
    return projected


def political_rings(shp: Path) -> list[tuple[int, list[np.ndarray]]]:
    """(country code, rings on the master grid) for every polygon in the political file."""
    cols = read_dbf_columns(Path(shp).with_suffix(".dbf"), ("COUNTRY", "STATEABB"))
    out = []
    for rings, country, state in zip(
        read_shapefile(shp), cols["COUNTRY"], cols["STATEABB"], strict=True
    ):
        if country == "USA":
            code = COUNTRY_US_OTHER if state in US_MASKED_STATES else COUNTRY_US48
        elif country == "CAN":
            code = COUNTRY_CAN
        elif country == "MEX":
            code = COUNTRY_MEX
        else:
            raise ValueError(f"unknown country {country!r} in {shp}")
        out.append((code, _to_grid(rings)))
    return out


def arctic_rings(shp: Path) -> list[list[np.ndarray]]:
    cols = read_dbf_columns(Path(shp).with_suffix(".dbf"), ("LEVEL1",))
    return [
        _to_grid(rings)
        for rings, level1 in zip(read_shapefile(shp), cols["LEVEL1"], strict=True)
        if level1 in ARCTIC_LEVEL1
    ]


def _burn(polygons, window: GridWindow) -> np.ndarray:
    """polygons: (value, rings). Later polygons overwrite earlier ones on shared edges."""
    left, bottom, right, top = window.left, window.bottom, window.right, window.top
    shapes = []
    for value, rings in polygons:
        kept = [
            r.tolist()
            for r in rings
            if r[:, 0].max() >= left and r[:, 0].min() <= right
            and r[:, 1].max() >= bottom and r[:, 1].min() <= top
        ]  # fmt: skip
        if kept:
            shapes.append(({"type": "Polygon", "coordinates": kept}, value))
    if not shapes:
        return np.zeros((window.height, window.width), dtype="uint8")
    return rasterize(
        shapes,
        out_shape=(window.height, window.width),
        transform=from_origin(left, top, CELL_SIZE_M, CELL_SIZE_M),
        fill=0,
        dtype="uint8",
    )


def build_mask(political_shp: Path, ecoregions_shp: Path, window: GridWindow, out: Path,
               block: int = 2048) -> dict:  # fmt: skip
    """Write the two-band mask over ``window`` block by block. Returns cell counts per code."""
    countries = political_rings(political_shp)
    arctic = [(1, rings) for rings in arctic_rings(ecoregions_shp)]
    profile = {
        "driver": "GTiff", "width": window.width, "height": window.height, "count": 2,
        "dtype": "uint8", "crs": GRID_CRS, "nodata": None, "compress": "deflate", "tiled": True,
        "transform": from_origin(window.left, window.top, CELL_SIZE_M, CELL_SIZE_M),
    }  # fmt: skip
    counts = {"country": {}, "arctic": 0}
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    partial = out.with_name(out.name + ".partial")
    with rasterio.open(partial, "w", **profile) as dst:
        for r0 in range(0, window.height, block):
            for c0 in range(0, window.width, block):
                h = min(block, window.height - r0)
                w = min(block, window.width - c0)
                sub = GridWindow(
                    window.left + c0 * CELL_SIZE_M,
                    window.top - (r0 + h) * CELL_SIZE_M,
                    window.left + (c0 + w) * CELL_SIZE_M,
                    window.top - r0 * CELL_SIZE_M,
                )
                country = _burn(countries, sub)
                arc = _burn(arctic, sub)
                dst.write(country, 1, window=Window(c0, r0, w, h))
                dst.write(arc, 2, window=Window(c0, r0, w, h))
                for code, n in zip(*np.unique(country, return_counts=True), strict=True):
                    counts["country"][int(code)] = counts["country"].get(int(code), 0) + int(n)
                counts["arctic"] += int(arc.sum())
        dst.set_band_description(1, COUNTRY_LEGEND)
        dst.set_band_description(2, "arctic: 1 in CEC level I Tundra or Arctic Cordillera (D111)")
    partial.rename(out)
    return counts


def read_mask(path: Path, window: GridWindow) -> tuple[np.ndarray, np.ndarray]:
    """(country, arctic) for ``window``; cells outside the mask raster read as none."""
    with rasterio.open(path) as ds:
        t = ds.transform
        col0 = (window.left - int(t.c)) // CELL_SIZE_M
        row0 = (int(t.f) - window.top) // CELL_SIZE_M
        win = Window(col0, row0, window.width, window.height)
        country = ds.read(1, window=win, boundless=True, fill_value=COUNTRY_NONE)
        arctic = ds.read(2, window=win, boundless=True, fill_value=0)
    return country, arctic


def cell_lonlat(window: GridWindow) -> tuple[np.ndarray, np.ndarray]:
    xs = window.left + (np.arange(window.width) + 0.5) * CELL_SIZE_M
    ys = window.top - (np.arange(window.height) + 0.5) * CELL_SIZE_M
    gx, gy = np.meshgrid(xs, ys)
    lon, lat = Transformer.from_crs(GRID_CRS, GEOGRAPHIC_CRS, always_xy=True).transform(gx, gy)
    return np.asarray(lon), np.asarray(lat)


def side_rule(lon: np.ndarray, lat: np.ndarray, country: np.ndarray) -> np.ndarray:
    """SIDE_US, SIDE_CA or SIDE_NONE per point (D115 item 1)."""
    in_band = (lon >= BAND_WEST) & (lon <= BAND_EAST) & (lat >= BAND_SOUTH) & (lat <= BAND_NORTH)
    by_line = np.where(lat >= BORDER_LATITUDE, SIDE_CA, SIDE_US)
    by_polygon = np.select(
        [country == COUNTRY_US48, country == COUNTRY_CAN], [SIDE_US, SIDE_CA], SIDE_NONE
    )
    return np.where(in_band, by_line, by_polygon).astype("uint8")


def cells_in_study(window: GridWindow, country: np.ndarray, arctic: np.ndarray):
    """(in study area, side) per cell. In: centre in the 48 states and DC or Canada, not Arctic."""
    lon, lat = cell_lonlat(window)
    study = ((country == COUNTRY_US48) | (country == COUNTRY_CAN)) & (arctic == 0)
    side = side_rule(lon, lat, country)
    return study, np.where(study, side, SIDE_NONE).astype("uint8")
