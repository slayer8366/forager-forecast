"""CEC level III ecoregion per 0.1 degree cell, for T8's leave-one-ecoregion-out (plan section 6;
D125; reported with no verdict).

A cell's block is the level III polygon its centre falls in (design.PENDING M-ecoregion, proposed
reading), tested by the even-odd rule over all of the polygon's rings, so holes are honoured. The
cell centre is projected to the file's Lambert azimuthal equal-area plane on its sphere, the same
convention t6b_mask uses for this file (CEC_LAEA, _CEC_LONLAT). A centre in no polygon is the block
NO_BLOCK. A centre on a shared edge that two polygons both claim takes the lower code, and the
count of such centres is returned.

The file is the T6b drive's `sources/cec_ecoregions_l3.zip`, sha256 checked against its request
record before its members are extracted to scratch (never beside the original).
"""

from __future__ import annotations

import hashlib
import zipfile
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from pyproj import Transformer

from forager_forecast.cells import Cell
from forager_forecast.t5_layer import read_dbf_columns
from forager_forecast.t6b_mask import _CEC_LONLAT, CEC_LAEA, read_shapefile

NO_BLOCK = "none"
SHP_STEM = "terr_ecoregions_v2_level_iii_shapefile/NA_TerrEcoregions_III/data/"
SHP_STEM += "NA_Terrestrial_Ecoregions_v2_level3"


def extract_level3(zip_path: Path, expected_sha256: str, scratch: Path) -> Path:
    h = hashlib.sha256()
    with zip_path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    if h.hexdigest() != expected_sha256:
        raise ValueError(f"{zip_path} sha256 {h.hexdigest()} differs from {expected_sha256}")
    scratch.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        for ext in (".shp", ".shx", ".dbf", ".prj"):
            z.extract(SHP_STEM + ext, scratch)
    return scratch / (SHP_STEM + ".shp")


def read_level3(shp: Path) -> list[tuple[str, list[np.ndarray]]]:
    """(LEVEL3 code, rings in the file's plane) per polygon."""
    codes = read_dbf_columns(Path(shp).with_suffix(".dbf"), ("LEVEL3",))["LEVEL3"]
    return [(code, rings) for rings, code in zip(read_shapefile(shp), codes, strict=True) if rings]


def project_centres(cells: Sequence[Cell]) -> np.ndarray:
    forward = Transformer.from_crs(_CEC_LONLAT, CEC_LAEA, always_xy=True)
    x, y = forward.transform(
        np.array([c.center_longitude for c in cells]), np.array([c.center_latitude for c in cells])
    )
    return np.column_stack([x, y])


def inside_rings(points: np.ndarray, rings: list[np.ndarray]) -> np.ndarray:
    """Even-odd point-in-polygon over every ring."""
    px, py = points[:, 0], points[:, 1]
    inside = np.zeros(len(points), dtype=bool)
    for ring in rings:
        x0, y0 = ring[:-1, 0], ring[:-1, 1]
        x1, y1 = ring[1:, 0], ring[1:, 1]
        if not (px.max() >= ring[:, 0].min() and px.min() <= ring[:, 0].max()):
            continue
        for a, b, c, d in zip(x0, y0, x1, y1, strict=True):
            crosses = (b > py) != (d > py)
            if not crosses.any():
                continue
            with np.errstate(divide="ignore", invalid="ignore"):
                xs = a + (py - b) * (c - a) / (d - b)
            inside ^= crosses & (px < xs)
    return inside


def assign(
    cells: Sequence[Cell], polygons: list[tuple[str, list[np.ndarray]]]
) -> tuple[list[str], int]:
    """(level III code per cell, centres claimed by two codes)."""
    pts = project_centres(cells)
    claims: list[set[str]] = [set() for _ in cells]
    for code, rings in polygons:
        lo = np.min([r.min(axis=0) for r in rings], axis=0)
        hi = np.max([r.max(axis=0) for r in rings], axis=0)
        near = np.where(
            (pts[:, 0] >= lo[0]) & (pts[:, 0] <= hi[0]) & (pts[:, 1] >= lo[1]) & (pts[:, 1] <= hi[1])
        )[0]
        if len(near) == 0:
            continue
        hit = inside_rings(pts[near], rings)
        for i in near[hit]:
            claims[i].add(code)
    shared = sum(len(c) > 1 for c in claims)
    return [min(c) if c else NO_BLOCK for c in claims], shared
