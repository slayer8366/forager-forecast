"""Reviewer: the samples, drawn before any manifest line or tile value was read.

Seed 20261011. Inputs: box_tiles.json (from mask.tif only) and mask.tif. Output prereg.json.
"""
import json
from pathlib import Path
import numpy as np, rasterio
from rasterio.windows import Window
from pyproj import Transformer

SEED = 20261011
T6B = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b")
HERE = Path(__file__).resolve().parent
C = 250
rng = np.random.default_rng(SEED)
d = json.loads((HERE / "box_tiles.json").read_text())
tree = d["tree"]
us_only = sorted(k for k, v in tree.items() if v["tile_study_ca"] == 0)
mixed = sorted(k for k, v in tree.items() if v["tile_study_ca"] > 0 and v["tile_study_us"] > 0)
eight = sorted(k for k, v in tree.items() if v["box_study_ca"] > 0)
soil = sorted(d["soil"])
to_ll = Transformer.from_crs("ESRI:102008", "EPSG:4269", always_xy=True)
to_g = Transformer.from_crs("EPSG:4269", "ESRI:102008", always_xy=True)

def cell_info(col, row, ds):
    t = ds.transform
    c, r = (col * C - int(t.c)) // C, (int(t.f) - (row + 1) * C) // C
    country = int(ds.read(1, window=Window(c, r, 1, 1))[0, 0])
    eco = int(ds.read(2, window=Window(c, r, 1, 1))[0, 0])
    lon, lat = to_ll.transform((col + 0.5) * C, (row + 0.5) * C)
    band = -122.80 <= lon <= -95.15 and 48.0 <= lat <= 50.0
    side = (2 if lat >= 49.0 else 1) if band else {1: 1, 2: 2}.get(country, 0)
    study = country in (1, 2) and eco == 2
    inbox = 40 <= lat <= 49 and -125 <= lon <= -111
    return {"col": col, "row": row, "lon": round(lon, 5), "lat": round(lat, 5),
            "country": country, "eco": eco, "study": study, "side": side if study else 0,
            "in_box": inbox, "tree_tile": f"256_{col // 256}_{row // 256}",
            "soil_tile": f"2048_{col // 2048}_{row // 2048}"}

def draw_cells(keys, weight_key, want_side, n, ds):
    w = np.array([tree[k][weight_key] for k in keys], dtype=float)
    out = []
    while len(out) < n:
        k = keys[rng.choice(len(keys), p=w / w.sum())]
        _, i, j = (int(x) for x in k.split("_"))
        col = i * 256 + int(rng.integers(256)); row = j * 256 + int(rng.integers(256))
        info = cell_info(col, row, ds)
        if info["study"] and info["in_box"] and (want_side is None or info["side"] == want_side):
            out.append(info)
    return out

with rasterio.open(T6B / "mask.tif") as ds:
    allk = sorted(tree)
    soil_cells = draw_cells(allk, "box_study_us", None, 3, ds)
    us_cells = draw_cells(allk, "box_study_us", 1, 3, ds)
    ca_cells = draw_cells(eight, "box_study_ca", 2, 2, ds)
    x, y = to_g.transform(-116.79, 47.705)  # fixed by hand: Coeur d'Alene Lake's north shore
    fixed = cell_info(int(x // C), int(y // C), ds)

pre = {
    "seed": SEED,
    "hash_sample": {
        "us_only_tree_tiles": sorted(rng.choice(us_only, 6, replace=False).tolist()),
        "us_half_tiles": sorted(rng.choice(mixed, 4, replace=False).tolist()),
        "soil_tiles": sorted(rng.choice(soil, 3, replace=False).tolist()),
        "canadian_tiles_all": eight,
    },
    "cells": {"soil": soil_cells, "trees_us": us_cells, "trees_ca": ca_cells,
              "trees_fixed_shore_guess": fixed},
}
(HERE / "prereg.json").write_text(json.dumps(pre, indent=1) + "\n")
print(json.dumps(pre, indent=1))
