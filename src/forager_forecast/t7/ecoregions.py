"""T7 item 2: a CEC level III ecoregion code per master-grid cell (D125's validation blocks).

The study-area mask stores no level III code (T7 verify report V12; ``t6b_mask.py`` band 2 holds
none, Arctic or other), so T7 burns level III itself, by cell centre, with the same rule as the
mask's ``_burn`` (GDAL's default rasterize rule; only rings whose bounding box meets the window are
passed). Codes are 1 to n over the file's level III identifiers in sorted order; 0 is "in no level
III polygon". The table of codes is part of every output's manifest.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_origin

from forager_forecast.grid import CELL_SIZE_M, GridWindow
from forager_forecast.t6b_mask import _to_grid, read_shapefile

NO_BLOCK = 0


@dataclass(frozen=True)
class Level3:
    code: int
    level3: str
    level1: str
    name: str


def read_dbf_text(path: Path, names: tuple[str, ...]) -> dict[str, list[str]]:
    """Named character columns of a dBase table, decoded as UTF-8 (the CEC file's .cpg)."""
    with open(path, "rb") as f:
        count, header_len, record_len = struct.unpack("<IHH", f.read(32)[4:12])
        fields = []
        while True:
            d = f.read(32)
            if not d or d[0] == 0x0D:
                break
            fields.append((d[:11].split(b"\0")[0].decode("ascii"), d[16]))
        missing = [n for n in names if n not in {name for name, _ in fields}]
        if missing:
            raise ValueError(f"{Path(path).name} has no field {missing}")
        f.seek(header_len)
        out: dict[str, list[str]] = {n: [] for n in names}
        for _ in range(count):
            record = f.read(record_len)
            pos = 1
            for name, size in fields:
                if name in out:
                    out[name].append(record[pos : pos + size].decode("utf-8").strip())
                pos += size
    return out


def read_level3(shp: Path) -> tuple[list[Level3], list[tuple[int, list[np.ndarray]]]]:
    """(code table, (code, rings on the master grid) per polygon) from the level III file."""
    cols = read_dbf_text(Path(shp).with_suffix(".dbf"), ("LEVEL1", "LEVEL3", "NameL3_En"))
    names: dict[str, tuple[str, str]] = {}
    for l1, l3, name in zip(cols["LEVEL1"], cols["LEVEL3"], cols["NameL3_En"], strict=True):
        if l3 in names and names[l3] != (l1, name):
            raise ValueError(f"level III {l3} carries two level I codes or names")
        names[l3] = (l1, name)
    order = sorted(names)  # plain string order: fixed, and needs no reading of the codes
    code_of = {l3: k for k, l3 in enumerate(order, start=1)}
    if len(code_of) >= 1 << 16:
        raise ValueError("too many level III regions for a uint16 code")
    table = [Level3(code_of[c], c, names[c][0], names[c][1]) for c in order]
    polygons = [
        (code_of[l3], _to_grid(rings))
        for rings, l3 in zip(read_shapefile(shp), cols["LEVEL3"], strict=True)
        if rings
    ]
    return table, polygons


def burn_level3(polygons: list[tuple[int, list[np.ndarray]]], window: GridWindow) -> np.ndarray:
    """uint16 level III code per cell of ``window`` by cell centre; 0 where none."""
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
            shapes.append(({"type": "Polygon", "coordinates": kept}, int(value)))
    if not shapes:
        return np.zeros((window.height, window.width), dtype=np.uint16)
    return rasterize(
        shapes,
        out_shape=(window.height, window.width),
        transform=from_origin(left, top, CELL_SIZE_M, CELL_SIZE_M),
        fill=NO_BLOCK,
        dtype="uint16",
    )
