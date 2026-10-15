"""T7 verify V4, V5, V7: the PNW box's tree and soil tiles on the drive, read only.

Reads T6b's tiles, flags, mask and manifest under the drive's t6b folder; writes nothing there.
No record, presence or observation of any fungus is read. Usage:
    python box_layers.py <out.json>
Tile by tile (one tree tile or one soil tile in memory at a time), for the cells whose centre is
in the box 40 to 49 N, 125 to 111 W (pnw.PNW_BOX) and in the study area (t6b_mask), by side.
"""

import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import rasterio

from forager_forecast.grid import CELL_SIZE_M
from forager_forecast.pnw import PNW_BOX, pnw_window
from forager_forecast.t4_layer import box_mask
from forager_forecast.t6b_layers import tiles_over, us_half_names
from forager_forecast.t6b_mask import SIDE_CA, SIDE_US, cells_in_study, read_mask

T6B = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b")
TREES, US_HALF, SOIL = T6B / "tiles/trees", T6B / "tiles/trees_us_half", T6B / "tiles/soil"
MANIFEST, MASK = T6B / "manifest.jsonl", T6B / "mask.tif"
LAYOUT = "t6b-bands-f4e9b848ba51"
CANADIAN_8 = ["256_-29_20", "256_-30_19", "256_-30_20", "256_-30_21", "256_-31_19", "256_-31_20",
              "256_-31_21", "256_-32_20"]  # fmt: skip


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def latest_lines() -> dict:
    out = {}
    with open(MANIFEST) as f:
        for line in f:
            d = json.loads(line)
            if d.get("kind") == "unit":
                out[(d.get("layer"), d["unit"])] = d
    return out


def main(out_path: str) -> None:
    t0 = time.time()
    lines = latest_lines()
    window = pnw_window()
    res = {"box": "40 to 49 N, 125 to 111 W by cell centre", "manifest_unit_keys": len(lines)}
    # --- trees ---
    side_tot = Counter()
    finite = defaultdict(Counter)  # band -> side -> cells with a finite value
    positive = defaultdict(Counter)  # band -> side -> cells with a value above 0
    flagc = defaultdict(Counter)  # band -> (side, flag) -> cells
    finite_outside_study = Counter()
    tiles = {}
    band_names = None
    for tile in tiles_over(window, 256):
        tw = tile.window
        study, side = cells_in_study(tw, *read_mask(MASK, tw))
        box = box_mask(tw, PNW_BOX)
        pnw = study & box
        if not pnw.any():
            continue
        whole = TREES / f"trees_{tile.key}.tif"
        half = US_HALF / us_half_names(tile.key)[0]
        if whole.exists():
            vpath, fpath = whole, TREES / f"trees_flags_{tile.key}.tif"
            unit, layer = tile.key, "trees"
        elif half.exists():
            vpath, fpath = half, US_HALF / us_half_names(tile.key)[1]
            unit, layer = f"us-half:{tile.key}", "trees-us-half"
        else:
            tiles[tile.key] = {"state": "no file", "box_study_cells": int(pnw.sum())}
            continue
        ln = lines.get((layer, unit), {})
        files = ln.get("files", {})
        hv, hf = sha(vpath), sha(fpath)
        rec = {
            "state": layer,
            "box_study_us": int((pnw & (side == SIDE_US)).sum()),
            "box_study_ca": int((pnw & (side == SIDE_CA)).sum()),
            "line_status": ln.get("status"),
            "line_band_layout": ln.get("band_layout"),
            "hash_match": files.get(vpath.name) == hv and files.get(fpath.name) == hf,
        }
        with rasterio.open(vpath) as ds, rasterio.open(fpath) as fs:
            names = list(ds.descriptions)
            fnames = list(fs.descriptions)
            rec["tag_band_layout"] = ds.tags().get("band_layout")
            rec["n_bands"] = len(names)
            if band_names is None:
                band_names = names
                res["value_bands"], res["flag_bands"] = names, fnames
            elif names != band_names:
                rec["band_names_differ"] = names
            vals = ds.read()
            flags = fs.read()
        for s_name, s_val in (("us", SIDE_US), ("ca", SIDE_CA)):
            sel = pnw & (side == s_val)
            side_tot[s_name] += int(sel.sum())
            for k, b in enumerate(names):
                finite[b][s_name] += int((np.isfinite(vals[k]) & sel).sum())
                with np.errstate(invalid="ignore"):
                    positive[b][s_name] += int(((vals[k] > 0) & sel).sum())
            for k, b in enumerate(fnames):
                u, c = np.unique(flags[k][sel], return_counts=True)
                for uu, cc in zip(u, c, strict=True):
                    flagc[b][f"{s_name}:{int(uu)}"] += int(cc)
        src = vals[names.index("source")]
        rec["box_cells_source_4"] = int(((src == 4) & pnw).sum())
        rec["box_cells_any_flag_4"] = int(((flags == 4).any(axis=0) & pnw).sum())
        for k, b in enumerate(names):
            if b.startswith("share_") or b == "total_cover_pct":
                finite_outside_study[b] += int((np.isfinite(vals[k]) & box & ~study).sum())
        tiles[tile.key] = rec
        del vals, flags
    res["trees"] = {
        "tiles_with_box_study_cells": len(tiles),
        "states": dict(Counter(t["state"] for t in tiles.values())),
        "box_study_cells": dict(side_tot),
        "finite_cells_by_band_and_side": {b: dict(v) for b, v in finite.items()},
        "positive_cells_by_band_and_side": {b: dict(v) for b, v in positive.items()},
        "flag_counts_by_band": {b: dict(v) for b, v in flagc.items()},
        "finite_in_box_outside_study": dict(finite_outside_study),
        "tiles_line_not_ok": [k for k, t in tiles.items() if t.get("line_status") != "ok"],
        "tiles_layout_not_current": [
            k
            for k, t in tiles.items()
            if t.get("line_band_layout") != LAYOUT or t.get("tag_band_layout") != LAYOUT
        ],  # fmt: skip
        "tiles_hash_mismatch": [k for k, t in tiles.items() if not t.get("hash_match")],
        "box_cells_source_4": sum(t.get("box_cells_source_4", 0) for t in tiles.values()),
        "box_cells_any_flag_4": sum(t.get("box_cells_any_flag_4", 0) for t in tiles.values()),
        "canadian_8": {k: tiles.get(k) for k in CANADIAN_8},
        "tiles": tiles,
    }
    # --- soil ---
    soil = {"tiles": {}, "box_study_cells": 0, "box_study_with_mean": 0, "box_with_mean": 0,
            "box_study_with_valid_fraction_ge_0_5": 0}  # fmt: skip
    for tile in tiles_over(window, 2048):
        tw = tile.window
        study, side = cells_in_study(tw, *read_mask(MASK, tw))
        box = box_mask(tw, PNW_BOX)
        pnw = study & box
        if not box.any():
            continue
        p = SOIL / f"soil_{tile.key}.tif"
        ln = lines.get(("soil", tile.key), {})
        rec = {"exists": p.exists(), "box_study_cells": int(pnw.sum()),
               "line_status": ln.get("status")}  # fmt: skip
        if p.exists() and pnw.any():
            rec["hash_match"] = ln.get("sha256") == sha(p) if ln else None
            with rasterio.open(p) as ds:
                names = list(ds.descriptions)
                rec["bands"] = names
                ph = ds.read(names.index("ph_mean_0_30cm") + 1)
                vf = ds.read(names.index("valid_fraction_mean") + 1)
                rec["min_valid_fraction_tag"] = ds.tags().get("min_valid_fraction")
            soil["box_study_cells"] += int(pnw.sum())
            soil["box_study_with_mean"] += int((np.isfinite(ph) & pnw).sum())
            soil["box_with_mean"] += int((np.isfinite(ph) & box).sum())
            soil["box_study_with_valid_fraction_ge_0_5"] += int(((vf >= 0.5) & pnw).sum())
            low = np.isfinite(ph) & (vf < 0.5) & pnw
            rec["mean_where_valid_fraction_lt_0_5"] = int(low.sum())
            del ph, vf
        soil["tiles"][tile.key] = rec
    res["soil"] = soil
    res["seconds"] = round(time.time() - t0, 1)
    res["cell_size_m"] = CELL_SIZE_M
    Path(out_path).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
