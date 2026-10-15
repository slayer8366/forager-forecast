"""T7 verify V10 to V13: the PNW box's study cells against the 0.1 degree weather cells, the T6
effort frame and the CEC level III ecoregions. Read only; writes only <out.json>.

Reads the T6b mask, tree tiles (two bands), the level III shapefile on the drive, and the cell
keys (lat_tenths, lon_tenths) of T6's stored effort surface; no effort value is read, and no
record, presence or observation of any fungus is read. Usage:
    python box_cells.py <out.json>

- Weather cell of a master-grid cell: its centre (ESRI:102008) to longitude and latitude by the
  same transformer the mask uses (t6b_mask.cell_lonlat, GRID_CRS to GEOGRAPHIC_CRS), then the
  nearest 0.1 degree point. Vectorised here as floor(10 x + 0.5) on the float; every cell of a
  fixed sample is also put through cells.cell_for (the decimal rule, D46, D63, D64) and the two
  compared. Cells within 1e-9 of a tenth's half-way point are counted as near ties.
- Level III ecoregion of a cell: the polygon containing its centre, burned with t6b_mask._burn
  (GDAL's default rule, centre in polygon), the same route the mask's ecoregion band took (D117).
"""

import csv
import json
import struct
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import rasterio

from forager_forecast.cells import cell_for
from forager_forecast.grid import CELL_SIZE_M, GridWindow
from forager_forecast.pnw import PNW_BOX, pnw_window
from forager_forecast.t4_layer import box_mask
from forager_forecast.t6b_layers import tiles_over
from forager_forecast.t6b_mask import (
    SIDE_CA,
    SIDE_US,
    _burn,
    _to_grid,
    cell_lonlat,
    cells_in_study,
    read_mask,
    read_shapefile,
)

T6B = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b")
MASK = T6B / "mask.tif"
TREES = T6B / "tiles/trees"
US_HALF = T6B / "tiles/trees_us_half"
L3 = (T6B / "sources/terr_ecoregions_v2_level_iii_shapefile/NA_TerrEcoregions_III/data"
      / "NA_Terrestrial_Ecoregions_v2_level3.shp")  # fmt: skip
EFFORT_CELLS = Path.home() / "Zynergy/forager-forecast-t6/data/t6/all/cell_level.csv"
SAMPLE_PER_TILE = 64
SEED = 20260918


def read_dbf_columns(path: Path, names: tuple[str, ...]) -> dict[str, list[str]]:
    """t5_layer.read_dbf_columns, decoding UTF-8 (the file's .cpg) instead of ASCII: the level
    III names hold accented letters."""
    with open(path, "rb") as f:
        count, header_len, record_len = struct.unpack("<IHH", f.read(32)[4:12])
        fields = []
        while True:
            d = f.read(32)
            if not d or d[0] == 0x0D:
                break
            fields.append((d[:11].split(b"\0")[0].decode("ascii"), d[16]))
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


def tree_file(key):
    whole = TREES / f"trees_{key}.tif"
    return whole if whole.exists() else US_HALF / f"trees_us_half_{key}.tif"


def main(out_path):
    t0 = time.time()
    window = pnw_window()
    tiles = tiles_over(window, 256)
    big = GridWindow(
        min(t.window.left for t in tiles),
        min(t.window.bottom for t in tiles),
        max(t.window.right for t in tiles),
        max(t.window.top for t in tiles),
    )
    cols = read_dbf_columns(L3.with_suffix(".dbf"), ("LEVEL3", "NameL3_En", "LEVEL1", "NameL1_En"))
    codes = sorted(set(cols["LEVEL3"]))
    if len(codes) > 254:
        raise ValueError("too many level III codes for a uint8 burn")
    idx = {c: i + 1 for i, c in enumerate(codes)}
    name3 = dict(zip(cols["LEVEL3"], cols["NameL3_En"], strict=True))
    l1_of = dict(zip(cols["LEVEL3"], cols["LEVEL1"], strict=True))
    name1 = dict(zip(cols["LEVEL1"], cols["NameL1_En"], strict=True))
    polys = [(idx[c], _to_grid(r)) for r, c in zip(read_shapefile(L3), cols["LEVEL3"], strict=True)]
    eco = _burn(polys, big)
    del polys
    t_burn = round(time.time() - t0, 1)

    frame = set()
    with EFFORT_CELLS.open(encoding="utf-8", newline="") as h:
        for row in csv.DictReader(h):
            frame.add((int(row["lat_tenths"]), int(row["lon_tenths"])))

    rng = np.random.default_rng(SEED)
    wcells = Counter()  # (lat10, lon10) -> box study cells
    wcells_side = defaultdict(Counter)
    per_l3 = defaultdict(Counter)
    near_ties = Counter()
    sample = {"n": 0, "disagree": 0, "examples": []}
    study_not_in_l3 = 0
    for tile in tiles:
        tw = tile.window
        study, side = cells_in_study(tw, *read_mask(MASK, tw))
        pnw = study & box_mask(tw, PNW_BOX)
        if not pnw.any():
            continue
        r0, c0 = (big.top - tw.top) // CELL_SIZE_M, (tw.left - big.left) // CELL_SIZE_M
        e = eco[r0 : r0 + 256, c0 : c0 + 256]
        lon, lat = cell_lonlat(tw)
        lat10 = np.floor(lat * 10 + 0.5).astype(np.int64)
        lon10 = np.floor(lon * 10 + 0.5).astype(np.int64)
        for name, v in (("lat", lat), ("lon", lon)):
            frac = (v * 10) - np.floor(v * 10)
            near_ties[name] += int(((np.abs(frac - 0.5) < 1e-9) & pnw).sum())
        rows, cols_ = np.nonzero(pnw)
        pick = rng.choice(len(rows), size=min(SAMPLE_PER_TILE, len(rows)), replace=False)
        for k in pick:
            r, c = rows[k], cols_[k]
            cell = cell_for(float(lat[r, c]), float(lon[r, c]))
            sample["n"] += 1
            if (cell.lat_tenths, cell.lon_tenths) != (lat10[r, c], lon10[r, c]):
                sample["disagree"] += 1
                if len(sample["examples"]) < 10:
                    sample["examples"].append([float(lat[r, c]), float(lon[r, c])])
        with rasterio.open(tree_file(tile.key)) as ds:
            names = list(ds.descriptions)
            cover = ds.read(names.index("total_cover_pct") + 1)
            share = ds.read(names.index("share_conifer") + 1)
        study_not_in_l3 += int((pnw & (e == 0)).sum())
        pairs = np.stack([lat10[pnw], lon10[pnw]], axis=1)
        up, upn = np.unique(pairs, axis=0, return_counts=True)
        for (a, b), nn in zip(up.tolist(), upn.tolist(), strict=True):
            wcells[(a, b)] += nn
        for s_name, s_val in (("us", SIDE_US), ("ca", SIDE_CA)):
            sel = pnw & (side == s_val)
            if sel.any():
                pp = np.stack([lat10[sel], lon10[sel]], axis=1)
                up, upn = np.unique(pp, axis=0, return_counts=True)
                for (a, b), nn in zip(up.tolist(), upn.tolist(), strict=True):
                    wcells_side[s_name][(a, b)] += nn
        for code_i in np.unique(e[pnw]):
            sel = pnw & (e == code_i)
            key = codes[code_i - 1] if code_i else "none"
            per_l3[key]["study_us"] += int((sel & (side == SIDE_US)).sum())
            per_l3[key]["study_ca"] += int((sel & (side == SIDE_CA)).sum())
            per_l3[key]["with_total_cover"] += int((sel & np.isfinite(cover)).sum())
            per_l3[key]["with_shares_canopy_ge_10pct"] += int((sel & np.isfinite(share)).sum())
    out_frame = {k: v for k, v in wcells.items() if k not in frame}
    l3 = {}
    for code, c in sorted(per_l3.items(), key=lambda kv: -sum(kv[1].values())):
        l3[code] = {"name": name3.get(code, "none"), "level1": l1_of.get(code),
                    "level1_name": name1.get(l1_of.get(code)), **c}  # fmt: skip
    l1 = defaultdict(Counter)
    for c in l3.values():
        for k in ("study_us", "study_ca", "with_total_cover", "with_shares_canopy_ge_10pct"):
            l1[f"{c['level1']} {c['level1_name']}"][k] += c[k]
    lattice = [(a, b) for a in range(400, 491) for b in range(-1250, -1109)]
    res = {
        "seconds": round(time.time() - t0, 1), "burn_seconds": t_burn,
        "effort_frame_cells": len(frame),
        "weather_cells": {
            "lattice_points_in_box_40_49N_125_111W": len(lattice),
            "with_box_study_cells": len(wcells),
            "with_box_study_cells_by_side": {s: len(v) for s, v in wcells_side.items()},
            "outside_effort_frame": len(out_frame),
            "box_study_cells_in_them": int(sum(out_frame.values())),
            "outside_frame_by_side": {
                s: {"weather_cells": sum(1 for k in v if k not in frame),
                    "study_cells": int(sum(n for k, n in v.items() if k not in frame))}
                for s, v in wcells_side.items()
            },
            "box_study_cells_total": int(sum(wcells.values())),
            "lat_tenths_range": [min(k[0] for k in wcells), max(k[0] for k in wcells)],
            "lon_tenths_range": [min(k[1] for k in wcells), max(k[1] for k in wcells)],
        },
        "keying": {"near_ties_within_1e-9": dict(near_ties), "decimal_sample": sample},
        "level3": {"blocks_with_box_study_cells": len([k for k in l3 if k != "none"]),
                   "study_cells_in_no_level3_polygon": study_not_in_l3, "by_block": l3},
        "level1": {k: dict(v) for k, v in l1.items()},
    }  # fmt: skip
    Path(out_path).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
