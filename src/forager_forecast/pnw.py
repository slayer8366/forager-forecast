"""The Pacific Northwest render for the owner's meeting (Forager RECORD -772 to -777).

Model inputs only: T6b's soil pH and host-tree layers over the box 40 to 49 N, 111 to 125 W, put
together from the finished tiles, drawn as labelled images and as PMTiles for a browsable map. It
is not a forecast and has not been reviewed (D18); every output says so. Nothing here changes a
tile, the mask or a rule: it reads finished tiles and writes new files elsewhere.

- A tree tile is read from its whole file when one exists, else from its US-half file (D119),
  whose Canadian cells are pending. A tile with neither is "not computed yet", counted, and shown
  as such, never as no trees.
- Cells outside the box are blank. Masked and no-data cells are transparent.
"""

import base64
import html
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window

from forager_forecast.grid import CELL_SIZE_M, GridWindow
from forager_forecast.soilgrids import ATTRIBUTION as SOILGRIDS_ATTRIBUTION
from forager_forecast.t4_layer import LonLatBox, box_mask, master_window
from forager_forecast.t5_layer import DERIVED_NOTICE, TREEMAP_CITATION
from forager_forecast.t6b_layers import NALCMS_CITATION, tiles_over, us_half_names

PNW_BOX = LonLatBox(south=40.0, north=49.0, west=-125.0, east=-111.0)
LABEL = "Model inputs (soil, host trees). Not a forecast. Not yet reviewed."
CEC_POLITICAL_CITATION = (
    'Commission for Environmental Cooperation (CEC). 2022. "North American Environmental Atlas - '
    'Political Boundaries". Ed. 3.0. CC BY 4.0.'
)
CEC_ECOREGIONS_CITATION = (
    'Commission for Environmental Cooperation (CEC). "North American Environmental Atlas - '
    'Terrestrial Ecoregions, level III". Ed. 2.0. CC BY 4.0.'
)
DATA_LICENCE = (
    "Layers compiled by forager-forecast are published under CC BY-NC 4.0 (D110); each source "
    "keeps its own licence."
)
SOURCES = {
    "soil": [SOILGRIDS_ATTRIBUTION, CEC_POLITICAL_CITATION, CEC_ECOREGIONS_CITATION],
    "trees": [
        f"Host trees (US): {TREEMAP_CITATION}. Terms: CC BY (Forest Service Research Data "
        "Archive).",
        DERIVED_NOTICE,
        f"Water mask: {NALCMS_CITATION}",
        CEC_POLITICAL_CITATION,
        CEC_ECOREGIONS_CITATION,
    ],
}

TILE_WHOLE = "whole"
TILE_US_HALF = "us_half"
TILE_MISSING = "not computed yet"


def pnw_window() -> GridWindow:
    return master_window(PNW_BOX)


def tree_file_for(tiles_dir: Path, us_half_dir: Path, key: str) -> tuple[Path | None, str]:
    """The file a tree tile is read from: whole, else US half (D119), else none."""
    whole = Path(tiles_dir) / f"trees_{key}.tif"
    if whole.exists():
        return whole, TILE_WHOLE
    half = Path(us_half_dir) / us_half_names(key)[0]
    if half.exists():
        return half, TILE_US_HALF
    return None, TILE_MISSING


def assemble(
    window: GridWindow, n: int, file_for: Callable[[str], Path | None], band: str
) -> tuple[np.ndarray, np.ndarray]:
    """(values, missing) of one band over ``window`` from tiles of size n. ``missing`` is True
    where the tile covering a cell has no file (value NaN there)."""
    values = np.full((window.height, window.width), np.nan, dtype="float32")
    missing = np.zeros((window.height, window.width), dtype=bool)
    for tile in tiles_over(window, n):
        tw = tile.window
        left, right = max(tw.left, window.left), min(tw.right, window.right)
        bottom, top = max(tw.bottom, window.bottom), min(tw.top, window.top)
        if left >= right or bottom >= top:
            continue
        r0, r1 = (window.top - top) // CELL_SIZE_M, (window.top - bottom) // CELL_SIZE_M
        c0, c1 = (left - window.left) // CELL_SIZE_M, (right - window.left) // CELL_SIZE_M
        path = file_for(tile.key)
        if path is None:
            missing[r0:r1, c0:c1] = True
            continue
        with rasterio.open(path) as ds:
            names = list(ds.descriptions)
            if band not in names:
                raise ValueError(f"{path} has no band {band!r}")
            win = Window(
                (left - tw.left) // CELL_SIZE_M, (tw.top - top) // CELL_SIZE_M,
                (right - left) // CELL_SIZE_M, (top - bottom) // CELL_SIZE_M,
            )  # fmt: skip
            values[r0:r1, c0:c1] = ds.read(names.index(band) + 1, window=win)
    return values, missing


def tile_states(window: GridWindow, n: int, state_for: Callable[[str], str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for tile in tiles_over(window, n):
        s = state_for(tile.key)
        out[s] = out.get(s, 0) + 1
    return out


def in_box(window: GridWindow) -> np.ndarray:
    return box_mask(window, PNW_BOX)


# --- Colour ---------------------------------------------------------------------------------------

# Viridis at nine stops (matplotlib's published table, sampled at 0, 1/8, ..., 1): perceptually
# even and readable in grey and by most colour-blind viewers.
VIRIDIS = (
    (68, 1, 84), (71, 44, 122), (59, 81, 139), (44, 113, 142), (33, 144, 141),
    (39, 173, 129), (92, 200, 99), (170, 220, 50), (253, 231, 37),
)  # fmt: skip
PENDING_RGBA = (190, 190, 190, 255)  # Canadian cells waiting for SCANFI
MISSING_RGBA = (120, 120, 120, 255)  # US cells whose tile is not computed yet


def ramp(values: np.ndarray, vmin: float, vmax: float, stops=VIRIDIS) -> np.ndarray:
    """RGBA uint8: values clipped to [vmin, vmax] along the stops; NaN transparent."""
    v = np.asarray(values, dtype="float64")
    valid = np.isfinite(v)
    t = np.clip((np.where(valid, v, vmin) - vmin) / (vmax - vmin), 0.0, 1.0) * (len(stops) - 1)
    k = np.minimum(np.floor(t).astype(int), len(stops) - 2)
    f = (t - k)[..., None]
    s = np.asarray(stops, dtype="float64")
    rgb = s[k] * (1 - f) + s[k + 1] * f
    out = np.zeros((*v.shape, 4), dtype="uint8")
    out[..., :3] = np.round(rgb).astype("uint8")
    out[..., 3] = np.where(valid, 255, 0)
    return out


def paint(rgba: np.ndarray, where: np.ndarray, colour: tuple[int, int, int, int]) -> np.ndarray:
    out = rgba.copy()
    out[where] = colour
    return out


def png_bytes(rgba: np.ndarray) -> bytes:
    """An RGBA PNG of the array, rows north to south."""
    from rasterio.io import MemoryFile

    h, w, _ = rgba.shape
    with MemoryFile() as mem:
        with mem.open(driver="PNG", width=w, height=h, count=4, dtype="uint8") as dst:
            dst.write(np.moveaxis(rgba, -1, 0))
        return mem.read()


# --- The labelled image ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LegendEntry:
    colour: tuple[int, int, int, int]
    text: str


def svg_image(
    png: bytes,
    width: int,
    height: int,
    title: str,
    subtitle: str,
    scale: tuple[float, float, str],
    extra_legend: list[LegendEntry],
    sources: list[str],
    lines: list[list[tuple[float, float]]],
    places: list[tuple[str, float, float]],
) -> str:
    """One self-contained SVG: the map (an embedded PNG, pixel (0, 0) at the north-west), lines
    and places in the same pixel space, the label, a colour scale, a legend and the sources."""
    pad, side = 24, 300
    foot = 40 + 15 * sum(len(_wrap(s, 150)) for s in [*sources, DATA_LICENCE])
    total_w, total_h = width + side + 2 * pad, max(height, 520) + 120 + foot
    e = html.escape
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" '
        f'viewBox="0 0 {total_w} {total_h}" font-family="Helvetica, Arial, sans-serif">',
        f'<rect width="{total_w}" height="{total_h}" fill="#ffffff"/>',
        f'<text x="{pad}" y="34" font-size="22" font-weight="bold">{e(title)}</text>',
        f'<text x="{pad}" y="58" font-size="14" fill="#333">{e(subtitle)}</text>',
        f'<rect x="{pad}" y="70" width="{total_w - 2 * pad}" height="30" fill="#fff4cc" '
        'stroke="#b58900"/>',
        f'<text x="{pad + 10}" y="91" font-size="16" font-weight="bold" fill="#5c4400">'
        f"{e(LABEL)}</text>",
        f'<defs><clipPath id="map"><rect width="{width}" height="{height}"/></clipPath></defs>',
        f'<g transform="translate({pad},110)" clip-path="url(#map)">',
        f'<rect width="{width}" height="{height}" fill="#f2f2f2"/>',
        f'<image width="{width}" height="{height}" style="image-rendering:pixelated" '
        f'href="data:image/png;base64,{base64.b64encode(png).decode()}"/>',
    ]
    for line in lines:
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in line)
        out.append(f'<polyline points="{pts}" fill="none" stroke="#222" stroke-width="0.8"/>')
    for name, x, y in places:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#000"/>')
        out.append(
            f'<text x="{x + 5:.1f}" y="{y - 4:.1f}" font-size="12" stroke="#fff" '
            f'stroke-width="3" paint-order="stroke">{e(name)}</text>'
        )
    out.append("</g>")
    lx = pad + width + pad
    vmin, vmax, unit = scale
    out.append(f'<g transform="translate({lx},120)">')
    out.append(f'<text x="0" y="0" font-size="14" font-weight="bold">{e(unit)}</text>')
    for k in range(100):
        c = ramp(np.array([vmin + (vmax - vmin) * (99 - k) / 99]), vmin, vmax)[0]
        out.append(f'<rect x="0" y="{12 + 2 * k}" width="24" height="2" '
                   f'fill="rgb({c[0]},{c[1]},{c[2]})"/>')  # fmt: skip
    out.append(f'<text x="32" y="22" font-size="12">{vmax:g}</text>')
    out.append(f'<text x="32" y="212" font-size="12">{vmin:g}</text>')
    y = 240
    for entry in [LegendEntry((0, 0, 0, 0), "No data, water or outside the study area"),
                  *extra_legend]:  # fmt: skip
        r, g, b, a = entry.colour
        fill = f"rgb({r},{g},{b})" if a else "none"
        out.append(f'<rect x="0" y="{y}" width="24" height="14" fill="{fill}" stroke="#666"/>')
        for k, part in enumerate(_wrap(entry.text, 34)):
            out.append(f'<text x="32" y="{y + 11 + 14 * k}" font-size="12">{e(part)}</text>')
        y += 22 + 14 * (len(_wrap(entry.text, 34)) - 1)
    out.append("</g>")
    y = 110 + max(height, 520) + 28
    out.append(f'<text x="{pad}" y="{y}" font-size="12" font-weight="bold">Sources</text>')
    for s in [*sources, DATA_LICENCE]:
        for part in _wrap(s, 150):
            y += 15
            out.append(f'<text x="{pad}" y="{y}" font-size="11" fill="#333">{e(part)}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _wrap(text: str, width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for w in words:
        if line and len(line) + 1 + len(w) > width:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    return [*lines, line] if line else lines
