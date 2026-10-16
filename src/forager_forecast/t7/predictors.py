"""T7 item 7: the tile reader. One 256-cell tree tile with its soil, mask, keys and blocks.

Applies P4 as ruled (D133 to D141): a cell enters only if it is in the study area and the box (by
cell centre), on the US side, has every share band defined (canopy at least 10% and at least half
valid, D89 (3)) and has a soil pH mean (D74). Every other cell gets a code saying why, never a
filled value (P9's codes):

    0 outside the study area or the box   3 Canada, out of the pilot (D136)
    1 in (shaded)                          4 no host shares: canopy under 10% or under half valid
    2 out of the area of applicability     5 no soil pH
                                           6 water or unmapped: no valid tree pixel at all

Precedence is the order 0, 3, 6, 4, 5. Code 2 is set later, by the area of applicability.

Shares below ``SHARE_FLOOR`` read as 0 (D137). Tier B is left out (zero across the box, P4 point
5). A study cell in the box that reads "pending" (flag 4, D119) stops the run (plan, abort
conditions), and so does a tile whose band layout is not this code's.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from forager_forecast.t4_layer import LonLatBox
from forager_forecast.t6b_layers import Tile

_STUB = "T7 build: not written yet (tests first)"

CODE_OUTSIDE = 0
CODE_IN = 1
CODE_OUT_OF_AOA = 2
CODE_CANADA = 3
CODE_NO_SHARES = 4
CODE_NO_SOIL = 5
CODE_WATER = 6
CODE_LEGEND = (
    "0 outside the study area or box; 1 in (shaded); 2 out of the area of applicability; "
    "3 Canada, out of the pilot (D136); 4 no host shares (canopy under 10% or under half valid); "
    "5 no soil pH; 6 water or unmapped (no valid tree pixel)"
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

    def code_counts(self) -> dict[int, int]:
        raise NotImplementedError(_STUB)


def read_tile(tile: Tile, tree_path: Path, flags_path: Path, soil_path: Path, mask_path: Path,
              box: LonLatBox, level3_polygons) -> TileCells:  # fmt: skip
    raise NotImplementedError(_STUB)
