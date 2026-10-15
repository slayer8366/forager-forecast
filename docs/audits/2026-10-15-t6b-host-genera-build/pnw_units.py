"""Read-only: which tree units a --box run would offer on the drive, for two candidate boxes.

Reads the drive's tiles_trees.json, mask.tif and a listing of scanfi_layers/ (never writes under
t6b/). Same selection rule as scripts/t6b_run.py box_tile_keys and the stages' filters.
Prints JSON; the output is committed beside this file as pnw_units.out.json.
"""

import json
import os
from pathlib import Path

from forager_forecast.t4_layer import LonLatBox, box_mask, master_window
from forager_forecast.t6b_layers import SCANFI_LAYERS, Tile
from forager_forecast.t6b_mask import SIDE_CA, SIDE_US, cells_in_study, read_mask

T6B = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b")
tiles = json.loads((T6B / "tiles_trees.json").read_text())
layer_files = set(os.listdir(T6B / "scanfi_layers"))


def ready(key):
    return all(f"scanfi_{layer}_{key}.npz" in layer_files for layer in SCANFI_LAYERS)


out = {}
for name, box in {"40-49N": LonLatBox(40.0, 49.0, -125.0, -111.0),
                  "40-49.5N": LonLatBox(40.0, 49.5, -125.0, -111.0)}.items():  # fmt: skip
    mw = master_window(box)
    kinds = {"us_only": 0, "mixed_layers_ready": 0, "mixed_waiting": 0,
             "canada_only_layers_ready": 0, "canada_only_waiting": 0}  # fmt: skip
    keys = []
    for t in tiles:
        w = Tile(t["i"], t["j"], t["n"]).window
        if w.right <= mw.left or w.left >= mw.right or w.top <= mw.bottom or w.bottom >= mw.top:
            continue
        study, side = cells_in_study(w, *read_mask(T6B / "mask.tif", w))
        if not (study & box_mask(w, box)).any():
            continue
        keys.append(t["key"])
        us, ca = bool((side == SIDE_US).any()), bool((side == SIDE_CA).any())
        if not ca:
            kinds["us_only"] += 1
        elif us:
            kinds["mixed_layers_ready" if ready(t["key"]) else "mixed_waiting"] += 1
        else:
            kinds["canada_only_layers_ready" if ready(t["key"]) else "canada_only_waiting"] += 1
    out[name] = {"tree_tiles": len(keys), **kinds,
                 "trees_units": kinds["us_only"] + kinds["mixed_layers_ready"]
                 + kinds["canada_only_layers_ready"],
                 "us_half_units": kinds["mixed_waiting"], "keys": sorted(keys)}  # fmt: skip
print(json.dumps(out, indent=1))
