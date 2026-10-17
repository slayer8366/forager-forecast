"""T7 item 7: the tile reader. One 256-cell tree tile with its soil, mask, keys and blocks.

Applies P4 as ruled (D134, D136, D137): a cell enters only if it is in the study area and the box
(by cell centre), on the US side, has every share band defined (canopy at least 10% and at least
half valid, D89 (3)) and has a soil pH mean (D74). Every other cell gets a code saying why, never a
filled value (P9's codes):

    0 outside the study area or the box   3 Canada, out of the pilot (D136)
    1 in (shaded)                          4 no host shares: canopy under 10% or under half valid
    2 out of the area of applicability     5 no soil pH
                                           6 water or unmapped: no valid tree pixel at all

Precedence is the order 0, 3, 6, 4, 5. Code 2 is set later, by the area of applicability.

Access bands (T7 part B, dispatch 2026-10-17-T7B; the owner's ruling 1 in Forager RECORD -1168)
are off by default and held apart from ``FEATURES``, so a run that does not ask for them reads
exactly what it read before. ``ACCESS_MAIN_BANDS`` (distance to the nearest road) is the main fit's
access band; ``ACCESS_SIDE_BANDS`` (trails, and the nearer of road and trail) are for a side check
only. A trail value is NaN where the Forest Service published trail records without lines, and is
passed on as NaN, never filled.

Shares below ``SHARE_FLOOR`` read as 0 (D137). Tier B is left out (zero across the box, P4 point
5). A study cell in the box that reads "pending" (flag 4, D119) stops the run (plan, abort
conditions), and so does a tile whose band layout is not this code's.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds

from forager_forecast.grid import CELL_SIZE_M, GridWindow
from forager_forecast.t4_layer import LonLatBox, box_mask
from forager_forecast.t6b_hosts import BAND_LAYOUT
from forager_forecast.t6b_layers import TREE_BANDS, Tile
from forager_forecast.t6b_mask import SIDE_CA, SIDE_US, cells_in_study, read_mask
from forager_forecast.t7.ecoregions import burn_level3
from forager_forecast.t7.keying import weather_cells_for_window

CODE_OUTSIDE = 0
CODE_IN = 1
CODE_OUT_OF_AOA = 2
CODE_CANADA = 3
CODE_NO_SHARES = 4
CODE_NO_SOIL = 5
CODE_WATER = 6
CODE_LEGEND = (
    "0 outside the study area or box; 1 in (shaded); 2 out of the area of applicability; "
    "3 Canada, out of the pilot (D136); 4 no host shares (canopy cover under D89 (3)'s threshold, "
    "or under half the cell valid); 5 no soil pH; 6 water or unmapped (no valid tree pixel)"
)
SHARE_FLOOR = 0.01
FLAG_PENDING = 4

BASE_BANDS = (
    "share_Pseudotsuga", "share_Tsuga", "share_Picea", "share_Abies", "share_Pinus",
    "share_Quercus", "share_conifer", "share_broadleaf", "total_cover_pct", "ph_mean_0_30cm",
)  # fmt: skip
CANDIDATE_BANDS = (
    "share_Larix", "share_Betula", "share_Populus", "share_Alnus", "share_Lithocarpus",
    "share_Chrysolepis", "share_Arbutus", "share_ecm_hosts",
)  # fmt: skip
LEFT_OUT_BANDS = ("share_Fagus", "share_Carya", "share_Tilia", "share_Ostrya", "share_Carpinus")
FEATURES = (*BASE_BANDS, *CANDIDATE_BANDS)
ACCESS_MAIN_BANDS = ("dist_road_m",)
ACCESS_SIDE_BANDS = ("dist_trail_m", "dist_any_m")
ACCESS_BANDS = (*ACCESS_MAIN_BANDS, *ACCESS_SIDE_BANDS)


class PendingCell(RuntimeError):
    pass


class LayoutMismatch(ValueError):
    pass


@dataclass
class TileCells:
    tile: str
    code: np.ndarray  # (h, w) uint8
    cell_id: np.ndarray  # (n,) uint32, eligible cells, raster order
    rows: np.ndarray  # (n,) raster row within the tile
    cols: np.ndarray
    features: np.ndarray  # (n, len(FEATURES)) float64
    lat_tenths: np.ndarray
    lon_tenths: np.ndarray
    level3: np.ndarray
    tree_attribution: str
    soil_attribution: str
    canadian_values_read: bool
    access: np.ndarray  # (n, len(access_bands)) float64; (n, 0) when off, the default
    access_bands: tuple[str, ...]

    def code_counts(self) -> dict[int, int]:
        values, counts = np.unique(self.code, return_counts=True)
        return {int(v): int(n) for v, n in zip(values, counts, strict=True)}


def _bands(path: Path, window: GridWindow, wanted, check_layout: bool):
    with rasterio.open(path) as ds:
        tags = ds.tags()
        if check_layout and tags.get("band_layout") != BAND_LAYOUT:
            raise LayoutMismatch(
                f"{Path(path).name}: band layout {tags.get('band_layout')!r}, not {BAND_LAYOUT!r}"
            )
        index = {d: k for k, d in enumerate(ds.descriptions, start=1) if d}
        missing = [b for b in wanted if b not in index]
        if missing:
            raise LayoutMismatch(f"{Path(path).name}: no band {missing}")
        win = from_bounds(window.left, window.bottom, window.right, window.top, ds.transform)
        win = win.round_offsets().round_lengths()
        out = {
            b: ds.read(index[b], window=win, boundless=True, fill_value=np.nan).astype(np.float64)
            if ds.dtypes[index[b] - 1].startswith("float")
            else ds.read(index[b], window=win, boundless=True, fill_value=0)
            for b in wanted
        }
    return out, tags


def _cell_ids(window: GridWindow, rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
    col = window.left // CELL_SIZE_M + cols
    row = window.top // CELL_SIZE_M - 1 - rows
    return (((row + (1 << 15)) << 16) | (col + (1 << 15))).astype(np.uint32)


def read_tile(tile: Tile, tree_path: Path, flags_path: Path, soil_path: Path, mask_path: Path,
              box: LonLatBox, level3_polygons, access_path: Path | None = None,
              access_bands: tuple[str, ...] = ()) -> TileCells:  # fmt: skip
    window = tile.window
    access_bands = tuple(access_bands)
    if access_bands and access_path is None:
        raise ValueError(f"access bands {access_bands} asked for with no access file")
    share_names = [b for b in TREE_BANDS if b.startswith("share_")]
    values, tree_tags = _bands(tree_path, window, TREE_BANDS, check_layout=True)
    flags, _ = _bands(flags_path, window, [f"flag_{b[6:]}" for b in share_names], True)
    soil, soil_tags = _bands(soil_path, window, ["ph_mean_0_30cm"], check_layout=False)
    study, side = cells_in_study(window, *read_mask(mask_path, window))
    inside = study & box_mask(window, box)

    pending = values["source"] == FLAG_PENDING
    for f in flags.values():
        pending |= f == FLAG_PENDING
    if (pending & inside).any():
        raise PendingCell(f"tile {tile.key}: {int((pending & inside).sum())} study cells pending")

    code = np.full((window.height, window.width), CODE_OUTSIDE, dtype=np.uint8)
    us = inside & (side == SIDE_US)
    code[inside & (side == SIDE_CA)] = CODE_CANADA
    valid = np.nan_to_num(values["valid_fraction"], nan=0.0)
    water = us & ~(valid > 0)
    shares_defined = np.ones_like(us)
    for b in (*BASE_BANDS, *CANDIDATE_BANDS):
        if b != "ph_mean_0_30cm":
            shares_defined &= np.isfinite(values[b])
    ph = soil["ph_mean_0_30cm"]
    code[water] = CODE_WATER
    code[us & ~water & ~shares_defined] = CODE_NO_SHARES
    code[us & ~water & shares_defined & ~np.isfinite(ph)] = CODE_NO_SOIL
    eligible = us & ~water & shares_defined & np.isfinite(ph)
    code[eligible] = CODE_IN

    rows, cols = np.nonzero(eligible)
    columns = []
    for name in FEATURES:
        v = ph[rows, cols] if name == "ph_mean_0_30cm" else values[name][rows, cols]
        if name.startswith("share_"):
            v = np.where(v < SHARE_FLOOR, 0.0, v)
        columns.append(v)
    features = np.column_stack(columns) if columns else np.empty((0, len(FEATURES)))
    lat_t, lon_t = weather_cells_for_window(window)
    level3 = burn_level3(level3_polygons, window)
    access = np.empty((len(rows), 0))
    if access_bands:
        acc, _ = _bands(access_path, window, list(access_bands), check_layout=False)
        access = np.column_stack([acc[b][rows, cols] for b in access_bands])
    return TileCells(
        tile=tile.key,
        code=code,
        cell_id=_cell_ids(window, rows, cols),
        rows=rows,
        cols=cols,
        features=features,
        lat_tenths=lat_t[rows, cols],
        lon_tenths=lon_t[rows, cols],
        level3=level3[rows, cols],
        tree_attribution=tree_tags.get("attribution", ""),
        soil_attribution=soil_tags.get("attribution", ""),
        canadian_values_read=bool((eligible & (side == SIDE_CA)).any()),
        access=access,
        access_bands=access_bands,
    )
