"""T4's ten-cell check: the master grid and the archive against the SoilGrids source.

Usage: uv run python scripts/t4_ten_cells.py DATA_DIR [--out JSON]

DATA_DIR holds native/ (the stored SoilGrids subsets), master.tif and
archive/soil-ph-0-30cm.pmtiles,
as scripts/t4_build.py writes them. Exits 1 if any cell fails.

Independent of the pipeline on purpose (dispatch, Build): nothing from forager_forecast is imported.
The source value is estimated by dense point sampling, not by polygon clipping: each cell is
sampled at SAMPLES x SAMPLES points, each point taken to Homolosine with pyproj and looked up in the
stored native pixels, and the blend (5, 10, 15 over 0-5, 5-15, 15-30 cm, D80) is recomputed here.
Only rasterio (to read files and decode a PNG), pyproj and the pmtiles reader are shared.

The ten cells were fixed in docs/audits/2026-10-06-t4-verify-report.md, section 4.6, before any
value was seen: eight at the centres of a 4 x 2 lattice over the D82 rectangle, one coastal
(Kalaloch) and one high (Paradise, Mount Rainier). A cell that is no data in the source stays in
the check and must be no data (transparent) in both outputs.

Checks per cell:
1. master vs source: |master - sampled| <= TOLERANCE_PH for each of mean, Q0.05, Q0.95, or both
   no data. Near the valid-fraction threshold the sampled fraction can fall either side; such a
   cell is reported as "at threshold" and not failed.
2. archive vs master: the zoom-9 pixel containing the cell centre decodes to
   floor(v * 10 + 0.5) of the master cell under that pixel's own centre (which may be a neighbour
   of the checked cell), or both are no data.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import rasterio
from pmtiles.reader import MmapSource, Reader
from pyproj import Transformer
from rasterio.io import MemoryFile

CELLS = [
    *[
        (f"lattice {i + 1}", lon, lat)
        for i, (lat, lon) in enumerate(
            (lat, lon) for lat in (48.125, 46.375) for lon in (-124.5, -123.5, -122.5, -121.5)
        )
    ],
    ("coastal: Kalaloch", -124.374, 47.604),
    ("high: Paradise, Mount Rainier", -121.736, 46.786),
]
DEPTH_WEIGHTS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}
STATS = {"mean": 1, "Q0.05": 2, "Q0.95": 3}  # master band per statistic
SAMPLES = 40
MIN_VALID_FRACTION = 0.5
# Sized from the sampling error measured on synthetic noise in the real geometry
# (docs/audits/2026-10-06-t4-completion-report.md, ten-cell section).
TOLERANCE_PH = 0.01
THRESHOLD_BAND = 0.05
HALF_WORLD = math.pi * 6378137.0
Z9_PIXEL = 2 * HALF_WORLD / 256 / 512

TO_GRID = Transformer.from_crs("EPSG:4269", "ESRI:102008", always_xy=True)
GRID_TO_LONLAT = Transformer.from_crs("ESRI:102008", "EPSG:4269", always_xy=True)
TO_IGH = Transformer.from_crs("EPSG:4326", "+proj=igh +datum=WGS84 +no_defs", always_xy=True)
TO_MERC = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
MERC_TO_LONLAT = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)


def load_native(native_dir: Path):
    """Per statistic, the blended pH per native pixel, recomputed here. Also the native grid."""
    out = {}
    transform = None
    for stat in STATS:
        acc = None
        for depth, weight in DEPTH_WEIGHTS.items():
            with rasterio.open(native_dir / f"phh2o_{depth}_{stat}.tif") as ds:
                raw = ds.read(1)
                ph = np.where(raw == ds.nodata, np.nan, raw / 10.0)
                transform = ds.transform
            acc = ph * weight if acc is None else acc + ph * weight
        out[stat] = acc / sum(DEPTH_WEIGHTS.values())
    return out, transform


def sampled_value(native, transform, col, row):
    """Mean of valid samples over the cell, and the valid share of samples."""
    offs = (np.arange(SAMPLES) + 0.5) / SAMPLES * 250.0
    sx, sy = np.meshgrid(col * 250.0 + offs, row * 250.0 + offs)
    lon, lat = GRID_TO_LONLAT.transform(sx.ravel(), sy.ravel())
    hx, hy = TO_IGH.transform(lon, lat)
    pc = np.floor((np.asarray(hx) - transform.c) / transform.a).astype(int)
    pr = np.floor((np.asarray(hy) - transform.f) / transform.e).astype(int)
    result = {}
    for stat, arr in native.items():
        if pc.min() < 0 or pr.min() < 0 or pc.max() >= arr.shape[1] or pr.max() >= arr.shape[0]:
            raise ValueError("a checked cell reaches past the stored native subset")
        vals = arr[pr, pc]
        ok = np.isfinite(vals)
        frac = ok.mean()
        result[stat] = (float(vals[ok].mean()) if ok.any() else None, float(frac))
    return result


def master_at(master, col, row):
    t = master.transform
    r = int(round((t.f - (row + 1) * 250.0) / 250.0))
    c = int(round((col * 250.0 - t.c) / 250.0))
    if not (0 <= r < master.height and 0 <= c < master.width):
        return None
    win = rasterio.windows.Window(c, r, 1, 1)
    return [float(master.read(b, window=win)[0, 0]) for b in range(1, 7)]


def archive_pixel(pmtiles_path, lon, lat):
    mx, my = TO_MERC.transform(lon, lat)
    px = math.floor((mx + HALF_WORLD) / Z9_PIXEL)
    py = math.floor((HALF_WORLD - my) / Z9_PIXEL)
    with open(pmtiles_path, "rb") as f:
        data = Reader(MmapSource(f)).get(9, px // 256, py // 256)
    if data is None:
        grey, alpha = 0, 0
    else:
        with MemoryFile(data) as mem, mem.open() as ds:
            bands = ds.read()
        grey = int(bands[0][py % 256, px % 256])
        alpha = 255 if bands.shape[0] in (1, 3) else int(bands[-1][py % 256, px % 256])
    centre_x = -HALF_WORLD + (px + 0.5) * Z9_PIXEL
    centre_y = HALF_WORLD - (py + 0.5) * Z9_PIXEL
    clon, clat = MERC_TO_LONLAT.transform(centre_x, centre_y)
    gx, gy = TO_GRID.transform(clon, clat)
    return grey, alpha, (math.floor(gx / 250.0), math.floor(gy / 250.0)), (px, py)


def check(data_dir: Path) -> list[dict]:
    native, ntransform = load_native(data_dir / "native")
    rows = []
    with rasterio.open(data_dir / "master.tif") as master:
        for name, lon, lat in CELLS:
            gx, gy = TO_GRID.transform(lon, lat)
            col, row = math.floor(gx / 250.0), math.floor(gy / 250.0)
            src = sampled_value(native, ntransform, col, row)
            m = master_at(master, col, row)
            entry = {"cell": name, "lon": lon, "lat": lat, "col": col, "row": row, "checks": {}}
            ok = True
            for stat, band in STATS.items():
                sval, sfrac = src[stat]
                mval = m[band - 1] if m else math.nan
                mfrac = m[band + 2] if m else 0.0
                at_threshold = abs(sfrac - MIN_VALID_FRACTION) < THRESHOLD_BAND
                src_has = sval is not None and sfrac >= MIN_VALID_FRACTION
                if not math.isfinite(mval) and not src_has:
                    verdict = "both no data"
                elif math.isfinite(mval) and src_has and abs(mval - sval) <= TOLERANCE_PH:
                    verdict = "match"
                elif at_threshold:
                    verdict = "at threshold"
                else:
                    verdict = "FAIL"
                    ok = False
                entry["checks"][stat] = {
                    "source_sampled": sval,
                    "source_valid_fraction": sfrac,
                    "master": mval if math.isfinite(mval) else None,
                    "master_valid_fraction": mfrac,
                    "difference": (mval - sval)
                    if (sval is not None and math.isfinite(mval))
                    else None,
                    "verdict": verdict,
                }
            grey, alpha, (pcol, prow), (px, py) = archive_pixel(
                data_dir / "archive" / "soil-ph-0-30cm.pmtiles", lon, lat
            )
            under = master_at(master, pcol, prow)
            under_mean = under[0] if under else math.nan
            if math.isfinite(under_mean):
                expected = math.floor(under_mean * 10 + 0.5)
                a_ok = alpha == 255 and grey == expected
            else:
                expected = None
                a_ok = alpha == 0
            ok = ok and a_ok
            entry["archive"] = {
                "z9_pixel": [px, py],
                "grey": grey if alpha else None,
                "alpha": alpha,
                "master_cell_under_pixel_centre": [pcol, prow],
                "expected_grey": expected,
                "verdict": "match" if a_ok else "FAIL",
            }
            entry["ok"] = ok
            rows.append(entry)
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    rows = check(args.data_dir)
    text = json.dumps(
        {"tolerance_ph": TOLERANCE_PH, "samples_per_side": SAMPLES, "cells": rows}, indent=2
    )
    if args.out:
        args.out.write_text(text + "\n")
    print(text)
    failed = [r["cell"] for r in rows if not r["ok"]]
    print(f"{len(rows) - len(failed)} of {len(rows)} cells pass", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
