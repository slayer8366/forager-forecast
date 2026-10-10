"""Reviewer: which T6b tiles hold study cells whose centre is in the PNW box, from mask.tif only.

Reads only mask.tif (country, ecoregion). Study and side rules restated here from D113, D115 item 1
and D117, not imported. Box 40 to 49 N, 111 to 125 W, edges inclusive, centre test, NAD83.
Writes box_tiles.json beside this script. Reads no tile and no manifest.
"""
import json, math, sys
from pathlib import Path
import numpy as np, rasterio
from rasterio.windows import Window
from pyproj import Transformer

T6B = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b")
OUT = Path(__file__).resolve().parent
C = 250
to_ll = Transformer.from_crs("ESRI:102008", "EPSG:4269", always_xy=True)

def lonlat(cols, rows):
    gx, gy = np.meshgrid((cols + 0.5) * C, (rows + 0.5) * C)
    lon, lat = to_ll.transform(gx, gy)
    return np.asarray(lon), np.asarray(lat)

def study_side(country, eco, lon, lat):
    study = ((country == 1) | (country == 2)) & (eco == 2)
    band = (lon >= -122.80) & (lon <= -95.15) & (lat >= 48.0) & (lat <= 50.0)
    side = np.where(band, np.where(lat >= 49.0, 2, 1),
                    np.where(country == 1, 1, np.where(country == 2, 2, 0)))
    return study, np.where(study, side, 0)

def in_box(lon, lat):
    return (lat >= 40) & (lat <= 49) & (lon >= -125) & (lon <= -111)

def main():
    # PNW window (left, bottom, right, top) as reported in check-rules.md; widened by one tree
    # tile on each side, so a tile partly outside it is still tested by the centre rule.
    left, bottom, right, top = -2295000, 95000, -1033000, 1367250
    s = 256 * C
    i0, i1 = math.floor(left / s) - 1, math.ceil(right / s) + 1
    j0, j1 = math.floor(bottom / s) - 1, math.ceil(top / s) + 1
    out = {"tree": {}, "soil": {}}
    with rasterio.open(T6B / "mask.tif") as ds:
        t = ds.transform
        for j in range(j1 - 1, j0 - 1, -1):
            for i in range(i0, i1):
                cols = np.arange(i * 256, i * 256 + 256)
                rows = np.arange(j * 256 + 255, j * 256 - 1, -1)  # north to south
                col0 = (i * s - int(t.c)) // C
                row0 = (int(t.f) - (j + 1) * s) // C
                win = Window(col0, row0, 256, 256)
                country = ds.read(1, window=win, boundless=True, fill_value=0)
                eco = ds.read(2, window=win, boundless=True, fill_value=0)
                if not (((country == 1) | (country == 2)) & (eco == 2)).any():
                    continue
                lon, lat = lonlat(cols, rows)
                study, side = study_side(country, eco, lon, lat)
                b = study & in_box(lon, lat)
                if not b.any():
                    continue
                key = f"256_{i}_{j}"
                out["tree"][key] = {
                    "box_study_us": int((b & (side == 1)).sum()),
                    "box_study_ca": int((b & (side == 2)).sum()),
                    "tile_study_us": int((study & (side == 1)).sum()),
                    "tile_study_ca": int((study & (side == 2)).sum()),
                }
                sk = f"2048_{i // 8}_{j // 8}"
                d = out["soil"].setdefault(sk, {"box_study": 0})
                d["box_study"] += int(b.sum())
    tot_us = sum(v["box_study_us"] for v in out["tree"].values())
    tot_ca = sum(v["box_study_ca"] for v in out["tree"].values())
    out["totals"] = {"tree_tiles": len(out["tree"]), "soil_tiles": len(out["soil"]),
                     "box_study_us": tot_us, "box_study_ca": tot_ca}
    (OUT / "box_tiles.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["totals"]))

main()
