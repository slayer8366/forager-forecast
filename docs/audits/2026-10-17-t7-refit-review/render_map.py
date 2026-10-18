"""Review 1, question 6: the re-fit's habitat raster and applicability mask rendered to PNG in this
folder, with the 2026-10-16 (judged) map beside and a difference map, and a few figures about where
the two maps disagree. Rendering only: nothing is published. PNGs are written through rasterio's
PNG driver (no plotting library is in the environment).

Reads the two output folders read-only. Writes map_refit.png, map_judged.png, map_rank_shift.png,
mask_refit.png, canada_edge_refit.png and render_map.json here.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from rasterio.io import MemoryFile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_common as rc  # noqa: E402

HERE = Path(__file__).resolve().parent
REFIT = Path("/mnt/work/Zynergy/forecast-data/t7/refit/outputs")
JUDGED = Path("/mnt/work/Zynergy/forecast-data/t7/pnw-2026-10-17")
STEP = 4  # 1 km pixels
GREENS = [(247, 252, 245), (199, 233, 192), (116, 196, 118), (35, 139, 69), (0, 68, 27)]
GREYS = {0: (255, 255, 255), 2: (255, 120, 0), 3: (210, 210, 230), 4: (235, 235, 225),
         5: (215, 200, 200), 6: (160, 190, 230)}


def png(path: Path, rgb: np.ndarray) -> None:
    h, w, _ = rgb.shape
    with MemoryFile() as mem:
        with mem.open(driver="PNG", width=w, height=h, count=3, dtype="uint8") as dst:
            dst.write(np.moveaxis(rgb, -1, 0))
        path.write_bytes(mem.read())


def quintile_render(score, code, edges=None):
    rgb = np.zeros(code.shape + (3,), dtype=np.uint8)
    rgb[...] = 255
    for c, col in GREYS.items():
        rgb[code == c] = col
    ok = np.isfinite(score)
    if edges is None:
        edges = np.quantile(score[ok], [0.2, 0.4, 0.6, 0.8])
    cls = np.digitize(score, edges)
    for k, col in enumerate(GREENS):
        rgb[ok & (cls == k)] = col
    return rgb, edges


def main() -> None:
    t0 = time.monotonic()
    out = {}
    with rasterio.open(REFIT / "relative_habitat_pnw.tif") as ds:
        s_new = ds.read(1)
        left, top = ds.transform.c, ds.transform.f
    with rasterio.open(REFIT / "applicability_pnw.tif") as ds:
        c_new = ds.read(1)
    with rasterio.open(JUDGED / "relative_habitat_pnw.tif") as ds:
        s_old = ds.read(1)
    with rasterio.open(JUDGED / "applicability_pnw.tif") as ds:
        c_old = ds.read(1)
    out["shape"] = list(s_new.shape)
    out["codes_refit"] = {int(k): int(v) for k, v in zip(*np.unique(c_new, return_counts=True))}
    out["codes_judged"] = {int(k): int(v) for k, v in zip(*np.unique(c_old, return_counts=True))}
    out["valued_equals_code_1"] = bool(np.array_equal(np.isfinite(s_new), c_new == 1))
    both = np.isfinite(s_new) & np.isfinite(s_old)
    out["cells_valued_in_both"] = int(both.sum())
    out["valued_only_refit"] = int((np.isfinite(s_new) & ~np.isfinite(s_old)).sum())
    out["valued_only_judged"] = int((~np.isfinite(s_new) & np.isfinite(s_old)).sum())

    # ranks (percentiles) over the cells valued in both, for the shift map and the agreement
    from scipy.stats import rankdata, spearmanr  # noqa: PLC0415

    rn = rankdata(s_new[both]) / both.sum()
    ro = rankdata(s_old[both]) / both.sum()
    out["spearman_over_both"] = float(spearmanr(s_new[both], s_old[both]).statistic)
    top_new, top_old = rn >= 0.9, ro >= 0.9
    out["top_tenth_overlap_share"] = float((top_new & top_old).sum() / top_new.sum())
    shift = np.full(s_new.shape, np.nan, dtype=np.float32)
    shift[both] = rn - ro
    out["rank_shift_quantiles"] = np.quantile(rn - ro, [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).tolist()
    out["share_moved_more_than_0.2_in_rank"] = float((np.abs(rn - ro) > 0.2).mean())
    print("ranks", round(time.monotonic() - t0), "s", flush=True)

    # by block: where the top tenth sits, and the mean rank shift
    table = rc.Table()
    names = {e["code"]: f"{e['level3']} {e['name']}" for e in table.meta["level3_table"]}
    ids = table.cell_id.astype(np.int64)
    col = (ids & 0xFFFF) - (1 << 15)
    row = (ids >> 16) - (1 << 15)
    rr = (int(top // 250) - 1 - row)
    cc = (col - int(left // 250))
    inb = both[rr, cc]
    blk = table.level3[inb]
    sh = shift[rr[inb], cc[inb]]
    rk_new = np.full(s_new.shape, np.nan, dtype=np.float32)
    rk_new[both] = rn
    rk = rk_new[rr[inb], cc[inb]]
    road = table.road()[inb]
    by_block = {}
    for b in np.unique(blk):
        sel = blk == b
        if sel.sum() < 1000:
            continue
        by_block[names.get(int(b), str(b))] = {
            "cells": int(sel.sum()),
            "mean_rank_refit": float(rk[sel].mean()),
            "mean_rank_shift": float(sh[sel].mean()),
            "share_of_refit_top_tenth": float(((rk >= 0.9) & sel).sum() / (rk >= 0.9).sum()),
            "share_of_block_in_top_tenth": float((rk[sel] >= 0.9).mean()),
        }
    out["by_block"] = dict(sorted(by_block.items(), key=lambda kv: -kv[1]["share_of_refit_top_tenth"]))
    out["top_tenth_median_road_m"] = {"refit": float(np.median(road[rk >= 0.9])),
                                      "all_valued": float(np.median(road))}
    # correlation of the score with road distance over valued cells (is remoteness in the ranking?)
    out["spearman_rank_vs_road_distance"] = float(spearmanr(rk[::20], road[::20]).statistic)
    # the Canadian edge: rows of code 3 and the valued cells just south of them
    canada = c_new == 3
    out["canada_cells"] = int(canada.sum())
    rows_with_canada = np.flatnonzero(canada.any(axis=1))
    out["canada_rows_span"] = [int(rows_with_canada.min()), int(rows_with_canada.max())] if len(rows_with_canada) else None
    print("blocks", round(time.monotonic() - t0), "s", flush=True)

    # renders
    s_new_d, c_new_d = s_new[::STEP, ::STEP], c_new[::STEP, ::STEP]
    s_old_d, c_old_d = s_old[::STEP, ::STEP], c_old[::STEP, ::STEP]
    rgb, edges = quintile_render(s_new_d, c_new_d)
    png(HERE / "map_refit.png", rgb)
    rgb_o, _ = quintile_render(s_old_d, c_old_d)
    png(HERE / "map_judged.png", rgb_o)
    # rank shift: blue = fell, red = rose, white = unchanged; grey where not valued in both
    sd = shift[::STEP, ::STEP]
    rgb_s = np.full(sd.shape + (3,), 200, dtype=np.uint8)
    okd = np.isfinite(sd)
    v = np.clip(sd[okd] / 0.3, -1, 1)
    r = np.where(v > 0, 255, 255 * (1 + v))
    g = 255 * (1 - np.abs(v))
    b = np.where(v < 0, 255, 255 * (1 - v))
    rgb_s[okd] = np.stack([r, g, b], 1).astype(np.uint8)
    png(HERE / "map_rank_shift.png", rgb_s)
    # mask only
    rgb_m = np.zeros(c_new_d.shape + (3,), dtype=np.uint8)
    rgb_m[...] = 255
    for c, colr in {**GREYS, 1: (120, 200, 120)}.items():
        rgb_m[c_new_d == c] = colr
    png(HERE / "mask_refit.png", rgb_m)
    # the Canada edge at full resolution: a 600 x 1200 window around the border's row span
    if out["canada_rows_span"]:
        r1 = out["canada_rows_span"][1]
        r0 = max(r1 - 300, 0)
        win = (slice(r0, min(r1 + 300, s_new.shape[0])), slice(1800, 3000))
        rgb_e, _ = quintile_render(s_new[win], c_new[win], edges)
        png(HERE / "canada_edge_refit.png", rgb_e)
        out["canada_edge_window"] = {"rows": [win[0].start, win[0].stop], "cols": [win[1].start, win[1].stop]}
    out["quintile_edges_refit_raw_score"] = edges.tolist()
    out["seconds"] = round(time.monotonic() - t0)
    (HERE / "render_map.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "by_block"}, indent=1))


if __name__ == "__main__":
    main()
