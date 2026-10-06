"""SoilGrids 2.0 soil pH (in water): the layers T4 reads, how they are read, and the blend.

Source: ISRIC, https://docs.isric.org/globaldata/soilgrids/ and its FAQ pages, read on 2026-10-06
(docs/audits/2026-10-06-t4-verify-report.md, section 4). Licence CC BY 4.0 (DATA_REGISTER.md:15).

- Depth (D80): 0 to 30 cm, thickness-weighted from 0-5, 5-15 and 15-30 cm (weights 5, 10, 15).
- Statistics (D81): the mean is the value. Q0.05 and Q0.95 are carried, blended the same way, and
  are **approximate**: a weighted mean of quantiles is not a quantile, so the blended pair is not a
  90% interval of the 0 to 30 cm value, only an approximation to its edges.
- Units: SoilGrids maps "pH x 10" with conversion factor 10 (FAQ, "phh2o pH water pH x 10 10").
  The division happens once, here, in ``ph_from_mapped``; everything downstream is in pH.
- Access: the WebDAV VRT for each layer, read through GDAL's /vsicurl/ for a window only, in the
  native Homolosine projection, so the stored subset is the published pixels and is warped once.
"""

import hashlib
import json
import math
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime
from functools import cache
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.windows import Window, from_bounds

from forager_forecast.grid import GEOGRAPHIC_CRS, GRID_CRS, GridWindow

SOILGRIDS_BASE_URL = "https://files.isric.org/soilgrids/latest/data"
PROPERTY = "phh2o"
# ISRIC FAQ: "the Homolosine projection applied to the WGS84 datum", "+proj=igh +datum=WGS84".
HOMOLOSINE = "+proj=igh +datum=WGS84 +no_defs"
NATIVE_PIXEL_M = 250.0
DEPTHS: tuple[tuple[str, int], ...] = (("0-5cm", 5), ("5-15cm", 10), ("15-30cm", 15))
STATISTICS: tuple[str, ...] = ("mean", "Q0.05", "Q0.95")
APPROXIMATE_STATISTICS = frozenset({"Q0.05", "Q0.95"})
MAPPED_UNITS_PER_PH = 10

ATTRIBUTION = (
    "Soil pH: SoilGrids 2.0, ISRIC - World Soil Information, CC BY 4.0. "
    "Poggio, L., de Sousa, L. M., Batjes, N. H., Heuvelink, G. B. M., Kempen, B., Ribeiro, E., "
    "and Rossiter, D.: SoilGrids 2.0: producing soil information for the globe with quantified "
    "spatial uncertainty, SOIL, 7, 217–240, 2021."
)


def layer_name(depth: str, statistic: str) -> str:
    return f"{PROPERTY}_{depth}_{statistic}"


def layers() -> list[tuple[str, str]]:
    return [(depth, stat) for depth, _ in DEPTHS for stat in STATISTICS]


def vrt_url(depth: str, statistic: str, base: str = SOILGRIDS_BASE_URL) -> str:
    return f"{base}/{PROPERTY}/{layer_name(depth, statistic)}.vrt"


def ph_from_mapped(mapped: np.ndarray, nodata: float | None) -> np.ndarray:
    """SoilGrids' integer pH x 10 to pH, with the source's no-data value turned into NaN."""
    if nodata is None:
        raise ValueError("the source declares no no-data value; refusing to guess one")
    ph = np.asarray(mapped, dtype="float64") / MAPPED_UNITS_PER_PH
    ph[np.asarray(mapped) == nodata] = np.nan
    return ph


def blend_0_30(by_depth: Mapping[str, np.ndarray]) -> np.ndarray:
    """Thickness-weighted 0 to 30 cm value (D80). No data at any depth is no data."""
    total = sum(weight for _, weight in DEPTHS)
    out = None
    for depth, weight in DEPTHS:
        term = np.asarray(by_depth[depth], dtype="float64") * weight
        out = term if out is None else out + term
    return out / total


@cache
def grid_to_homolosine():
    """ESRI:102008 x, y to SoilGrids' Homolosine, with no datum step.

    Inverse Albers to NAD83 longitude and latitude, then those values read as WGS84 into the
    Homolosine projection: the same null shift the grid pins (grid.py). Two pure projections,
    so no PROJ operation choice is involved.
    """
    to_lonlat = Transformer.from_crs(GRID_CRS, GEOGRAPHIC_CRS, always_xy=True)
    to_igh = Transformer.from_crs("EPSG:4326", HOMOLOSINE, always_xy=True)

    def transform(xs, ys):
        lon, lat = to_lonlat.transform(xs, ys)
        return to_igh.transform(lon, lat)

    return transform


def native_bounds_for(window: GridWindow, margin_m: float = 2 * NATIVE_PIXEL_M):
    """Homolosine bounds covering every point of ``window``, plus a margin."""
    xs = np.linspace(window.left, window.right, max(window.width // 8, 2) + 1)
    ys = np.linspace(window.bottom, window.top, max(window.height // 8, 2) + 1)
    edge_x = np.concatenate([xs, xs, np.full(len(ys), window.left), np.full(len(ys), window.right)])
    edge_y = np.concatenate([np.full(len(xs), window.bottom), np.full(len(xs), window.top), ys, ys])
    hx, hy = grid_to_homolosine()(edge_x, edge_y)
    return (
        float(np.min(hx)) - margin_m,
        float(np.min(hy)) - margin_m,
        float(np.max(hx)) + margin_m,
        float(np.max(hy)) + margin_m,
    )


def gdal_path(source: str) -> str:
    return f"/vsicurl/{source}" if source.startswith(("http://", "https://")) else source


def _http_headers(url: str) -> dict:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=60) as response:
        return {
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "content_length": response.headers.get("Content-Length"),
        }


def fetch_layer(source: str, bounds, dest: Path) -> dict:
    """Read the window of ``source`` covering ``bounds`` (Homolosine) and store it unchanged.

    Returns the request record for this layer: source, pixel window, the source's grid, its
    no-data value, the HTTP validators when the source is a URL, the time, and the sha256 of the
    file written.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    requested_at = datetime.now(UTC).isoformat(timespec="seconds")
    http = _http_headers(source) if source.startswith(("http://", "https://")) else None
    with rasterio.open(gdal_path(source)) as src:
        raw = from_bounds(*bounds, transform=src.transform)
        col0 = math.floor(raw.col_off)
        row0 = math.floor(raw.row_off)
        col1 = math.ceil(raw.col_off + raw.width)
        row1 = math.ceil(raw.row_off + raw.height)
        if col0 < 0 or row0 < 0 or col1 > src.width or row1 > src.height:
            raise ValueError(f"bounds {bounds} reach outside the source raster")
        window = Window(col0, row0, col1 - col0, row1 - row0)
        data = src.read(1, window=window)
        profile = {
            "driver": "GTiff",
            "width": window.width,
            "height": window.height,
            "count": 1,
            "dtype": data.dtype.name,
            "crs": src.crs,
            "transform": src.window_transform(window),
            "nodata": src.nodata,
            "compress": "deflate",
        }
        source_grid = {
            "crs_wkt": src.crs.to_wkt(),
            "transform": list(src.transform)[:6],
            "width": src.width,
            "height": src.height,
            "dtype": src.dtypes[0],
        }
        nodata = src.nodata
    with rasterio.open(dest, "w", **profile) as dst:
        dst.write(data, 1)
        dst.update_tags(source=source, requested_at=requested_at)
    return {
        "source": source,
        "requested_at": requested_at,
        "account": "anonymous",
        "http": http,
        "bounds_requested": list(bounds),
        "pixel_window": {
            "col_off": col0,
            "row_off": row0,
            "width": col1 - col0,
            "height": row1 - row0,
        },
        "source_grid": source_grid,
        "nodata": nodata,
        "file": dest.name,
        "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
    }


def write_request(records: list[dict], extra: dict, path: Path) -> None:
    body = {**extra, "attribution": ATTRIBUTION, "layers": records}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n")


def parse_checksums(text: str) -> dict[str, str]:
    """ISRIC's checksum.sha256.txt (``<sha256>  <file name>`` per line) as {name: sha256}."""
    out = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest.lower()):
            raise ValueError(f"not a sha256 line: {line!r}")
        out[name.strip()] = digest.lower()
    return out


def verify_sha256(path: Path, checksums: Mapping[str, str], name: str) -> dict:
    """Compare a downloaded file with ISRIC's published sha256. Raises on a mismatch.

    ISRIC publishes checksums for the VRT and OVR files only, not for the GeoTIFF tiles the
    window is read from; a name with no published checksum is reported as such, never as a pass.
    """
    actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    expected = checksums.get(name)
    if expected is None:
        return {
            "file": name,
            "sha256": actual,
            "published": None,
            "verdict": "no published checksum",
        }
    if actual != expected:
        raise ValueError(f"{name}: sha256 {actual} does not match ISRIC's {expected}")
    return {"file": name, "sha256": actual, "published": expected, "verdict": "match"}
