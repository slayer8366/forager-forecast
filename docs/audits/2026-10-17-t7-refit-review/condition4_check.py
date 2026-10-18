"""Review 1, question 5: P10b condition 4 recomputed from the written raster and the kept
specimen file with the review's own code, then stressed.

Reproduction (D158 as the code applies it): each scorable specimen (own cell eligible and inside
the area of applicability) scored by the raster's mean over the cells whose centres lie within its
stated uncertainty radius (own cell always), ten background cells per specimen from the same road
band (edges 50, 100, 250, 500, 1000, 2000, 5000 m) drawn without replacement within the band, seed
20260918, bands ascending, each scored at the specimen's radius; AUC minus 0.5, interval over
whole level III blocks.

Variants (the review's, not rulings): the point value instead of the circle mean; background
matched on road band AND the specimen's own level III block; background matched on road band AND
the specimen's own weather cell (falling back to the block where the cell's pool is too small);
the figure by era (before 2000 / 2000 on), by herbarium (the one that holds 72% / the rest), and
by the four western blocks against the rest. Writes condition4_check.json into this folder.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_common as rc  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = Path("/mnt/work/Zynergy/forecast-data/t7/refit/outputs")
SPECIMENS = Path("/mnt/work/Zynergy/forecast-data/t7/specimens/specimens_kept.csv")
REPORT = HERE.parent / "2026-10-17-t7-refit" / "fit_report.json"
BANDS = np.array([50.0, 100.0, 250.0, 500.0, 1000.0, 2000.0, 5000.0])
PER = 10
CELL = 250.0
UW_MACROFUNGI = "96ccdb74-f762-11e1-a439-00145eb45e9a"  # 4,338 of 6,026 kept records
WESTERN_FOUR = {"7.1.7", "7.1.8", "6.2.7", "6.2.5"}  # Puget Lowland, Coastal Range, Cascades, North Cascades


def band_of(d):
    return np.searchsorted(BANDS, np.asarray(d, dtype=np.float64), side="right")


def circle_mean(raster, left, top, x, y, r):
    r0 = int(np.floor((top - y) / CELL))
    c0 = int(np.floor((x - left) / CELL))
    k = int(np.ceil(r / CELL)) + 1
    rows = np.arange(max(r0 - k, 0), min(r0 + k + 1, raster.shape[0]))
    cols = np.arange(max(c0 - k, 0), min(c0 + k + 1, raster.shape[1]))
    rr, cc = np.meshgrid(rows, cols, indexing="ij")
    cx = left + (cc + 0.5) * CELL
    cy = top - (rr + 0.5) * CELL
    take = ((cx - x) ** 2 + (cy - y) ** 2 <= r * r) | ((rr == r0) & (cc == c0))
    v = raster[rr[take], cc[take]].astype(np.float64)
    v = v[np.isfinite(v)]
    return float(v.mean()) if len(v) else float("nan")


def point_value(raster, left, top, x, y):
    r0 = int(np.floor((top - y) / CELL))
    c0 = int(np.floor((x - left) / CELL))
    return float(raster[r0, c0])


def cell_centre(cell_id):
    ids = np.asarray(cell_id, dtype=np.int64)
    col = (ids & 0xFFFF) - (1 << 15)
    row = (ids >> 16) - (1 << 15)
    return (col + 0.5) * CELL, (row + 0.5) * CELL


def draw_matched(spec_bands, spec_radii, pool_cells, pool_bands, seed=rc.SEED):
    """The coder's rule, re-derived: bands ascending, one generator, without replacement."""
    rng = np.random.default_rng(seed)
    cells, radii, owner = [], [], []
    for b in np.unique(spec_bands):
        which = np.flatnonzero(spec_bands == b)
        cand = pool_cells[pool_bands == b]
        need = PER * len(which)
        if len(cand) < need:
            raise SystemExit(f"band {b}: {len(cand)} pool cells for {need}")
        cells.append(rng.choice(cand, size=need, replace=False))
        radii.append(np.repeat(spec_radii[which], PER))
        owner.append(np.repeat(which, PER))
    return np.concatenate(cells), np.concatenate(radii), np.concatenate(owner)


def draw_matched_within(spec_bands, spec_groups, spec_radii, pool_cells, pool_bands, pool_groups,
                        fallback_groups=None, pool_fallback=None, seed=rc.SEED):
    """Ten per specimen from the same road band and the same group (block or weather cell),
    without replacement within each (band, group); where a (band, group) pool holds fewer than
    needed, the fallback group (the block) is used for those specimens and counted."""
    rng = np.random.default_rng(seed)
    cells, radii, owner, fell_back = [], [], [], 0
    keys = np.unique(np.stack([spec_bands, spec_groups], 1), axis=0)
    pool_key = pool_bands.astype(np.int64) * (10 ** 12) + pool_groups.astype(np.int64)
    order = np.argsort(pool_key, kind="mergesort")
    pk_sorted = pool_key[order]
    for b, g in keys:
        which = np.flatnonzero((spec_bands == b) & (spec_groups == g))
        key = int(b) * (10 ** 12) + int(g)
        lo, hi = np.searchsorted(pk_sorted, [key, key + 1])
        cand = pool_cells[order[lo:hi]]
        need = PER * len(which)
        if len(cand) >= need:
            cells.append(rng.choice(cand, size=need, replace=False))
            radii.append(np.repeat(spec_radii[which], PER))
            owner.append(np.repeat(which, PER))
            continue
        if fallback_groups is None:
            raise SystemExit(f"band {b} group {g}: {len(cand)} pool cells for {need}")
        # fall back per specimen to its block
        for s in which:
            fb = fallback_groups[s]
            cand2 = pool_cells[(pool_bands == b) & (pool_fallback == fb)]
            if len(cand2) < PER:
                cand2 = pool_cells[pool_bands == b]
            cells.append(rng.choice(cand2, size=PER, replace=False))
            radii.append(np.full(PER, spec_radii[s]))
            owner.append(np.full(PER, s))
            fell_back += 1
    return np.concatenate(cells), np.concatenate(radii), np.concatenate(owner), fell_back


def figure(s_scores, b_scores, s_blocks, b_blocks, seed=rc.SEED):
    scores = np.concatenate([s_scores, b_scores])
    y = np.concatenate([np.ones(len(s_scores)), np.zeros(len(b_scores))])
    blocks = np.concatenate([s_blocks, b_blocks])
    d = rc.auc_difference(scores, np.zeros(len(scores)), y, np.ones(len(scores)), blocks, seed=seed)
    d["specimens"] = int(len(s_scores))
    d["background"] = int(len(b_scores))
    d["specimen_median"] = float(np.median(s_scores))
    d["background_median"] = float(np.median(b_scores))
    return d


def main() -> None:
    t0 = time.monotonic()
    rep = json.loads(REPORT.read_text())["condition_4"]
    table = rc.Table()
    inside = np.load(rc.WORK / "inside_all.npy")
    road = table.road()
    level3 = table.level3
    l3_names = {e["code"]: e["level3"] for e in table.meta["level3_table"]}
    with rasterio.open(OUT / "relative_habitat_pnw.tif") as ds:
        raster = ds.read(1)
        left, top = ds.transform.c, ds.transform.f
    # scorable: table cells inside the area of applicability equal the raster's valued cells
    sx_all, sy_all = cell_centre(table.cell_id)
    rr = np.floor((top - sy_all) / CELL).astype(int)
    cc = np.floor((sx_all - left) / CELL).astype(int)
    valued = np.isfinite(raster[rr, cc])
    checks = {"valued_cells_equal_inside_cells": bool(np.array_equal(valued, inside)),
              "valued_count": int(valued.sum()), "inside_count": int(inside.sum()),
              "nan_cells_in_raster": int(np.isnan(raster).sum()),
              "raster_cells": int(raster.size)}
    del sx_all, sy_all, rr, cc

    with open(SPECIMENS, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    lon = np.array([float(r["lon"]) for r in rows])
    lat = np.array([float(r["lat"]) for r in rows])
    x, y = Transformer.from_crs("EPSG:4269", "ESRI:102008", always_xy=True).transform(lon, lat)
    cell = np.array([int(r["cell_id"]) for r in rows])
    radius = np.array([float(r["uncertainty_m"]) for r in rows])
    interior = np.array([r["interior"] == "True" for r in rows])
    year = np.array([int(r["year"]) if r["year"].strip().isdigit() else -1 for r in rows])
    uw = np.array([r["dataset_key"] == UW_MACROFUNGI for r in rows])
    pos = np.clip(np.searchsorted(table.cell_id, cell), 0, len(table.cell_id) - 1)
    ok = (table.cell_id[pos] == cell) & inside[pos]
    checks["specimens_in"] = len(rows)
    checks["specimens_scorable"] = int(ok.sum())
    checks["theirs_scored"] = rep["whole_box"]["specimens_scored"]
    # own-cell check: the record's point falls in the cell the file names
    own_col = np.floor(x / CELL).astype(int)
    own_row = np.floor(y / CELL).astype(int)
    checks["point_in_named_cell"] = int(((own_col == (cell & 0xFFFF) - (1 << 15))
                                        & (own_row == (cell >> 16) - (1 << 15))).sum())
    # filters as stated (D158): licence, uncertainty, genus list
    lic = {r["license"] for r in rows} | {r["dataset_licence"] for r in rows}
    checks["licences_in_file"] = sorted(lic)
    checks["max_uncertainty_m"] = float(radius.max())
    checks["min_uncertainty_m"] = float(radius.min())
    main_genera = set()
    with open(rc.V9 / "presences_main.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            main_genera.add(r["genus"])
    spec_genera = {r["genus"] for r in rows}
    checks["genera_in_specimens_not_in_main_run_presences"] = sorted(spec_genera - main_genera)
    checks["genera_in_specimens"] = len(spec_genera)

    pool = table.cell_id[inside]
    pool_band = band_of(road[inside])
    pool_block = level3[inside]
    pool_wcell = table.wkey[inside]
    pos_ok = pos[ok]
    s_band = band_of(road[pos_ok])
    s_block = level3[pos_ok]
    s_wcell = table.wkey[pos_ok]
    sx, sy, sr = x[ok], y[ok], radius[ok]
    s_scores = np.array([circle_mean(raster, left, top, a, b, r) for a, b, r in zip(sx, sy, sr)])
    s_point = np.array([point_value(raster, left, top, a, b) for a, b in zip(sx, sy)])
    print("specimens scored", round(time.monotonic() - t0), "s", flush=True)

    out = {"checks": checks, "reproduction": {}, "variants": {}}
    # --- reproduction, whole box
    b_cells, b_r, owner = draw_matched(s_band, sr, pool, pool_band)
    bx, by = cell_centre(b_cells)
    b_scores = np.array([circle_mean(raster, left, top, a, b, r) for a, b, r in zip(bx, by, b_r)])
    b_pos = np.searchsorted(table.cell_id, b_cells)
    b_block = level3[b_pos]
    whole = figure(s_scores, b_scores, s_block, b_block)
    theirs = rep["whole_box"]["difference"]
    out["reproduction"]["whole_box"] = {"mine": whole, "theirs": theirs,
                                        "match": all(abs(whole[k] - theirs[k]) < 1e-9 for k in ("point", "low", "high"))}
    out["reproduction"]["background_bands_match"] = {
        "mine": {int(k): int(v) for k, v in zip(*np.unique(band_of(road[b_pos]), return_counts=True))},
        "theirs": rep["whole_box"]["background_road_bands"]}
    # interior
    inner = interior[ok]
    bi_cells, bi_r, _ = draw_matched(s_band[inner], sr[inner], pool, pool_band)
    bix, biy = cell_centre(bi_cells)
    bi_scores = np.array([circle_mean(raster, left, top, a, b, r) for a, b, r in zip(bix, biy, bi_r)])
    bi_block = level3[np.searchsorted(table.cell_id, bi_cells)]
    inner_fig = figure(s_scores[inner], bi_scores, s_block[inner], bi_block)
    theirs_i = rep["interior_no_verdict"]["difference"]
    out["reproduction"]["interior"] = {"mine": inner_fig, "theirs": theirs_i,
                                       "match": all(abs(inner_fig[k] - theirs_i[k]) < 1e-9 for k in ("point", "low", "high"))}
    print("reproduction", round(time.monotonic() - t0), "s", flush=True)

    # --- variants
    b_point = np.array([point_value(raster, left, top, a, b) for a, b in zip(bx, by)])
    out["variants"]["point_value_instead_of_circle_mean"] = figure(s_point, b_point, s_block, b_block)
    out["variants"]["unweighted_pooled_auc_no_matching_(all_scorable_cells_as_background)"] = {
        "auc_minus_half": rc.weighted_auc(np.concatenate([s_point, raster[np.isfinite(raster)][::7]]),
                                          np.r_[np.ones(len(s_point)), np.zeros(len(raster[np.isfinite(raster)][::7]))],
                                          np.ones(len(s_point) + len(raster[np.isfinite(raster)][::7]))) - 0.5,
        "note": "every seventh valued raster cell as background, no road matching; point scores"}
    # specimen and matched-background subsets by era, herbarium, region (same pairs, subset)
    def subset(mask_s, label):
        keep_b = mask_s[owner]
        out["variants"][label] = figure(s_scores[mask_s], b_scores[keep_b], s_block[mask_s], b_block[keep_b])
    yr = year[ok]
    subset(yr >= 2000, "era_2000_on")
    subset((yr >= 0) & (yr < 2000), "era_before_2000")
    subset((yr >= 0) & (yr < 1970), "era_before_1970")
    subset(uw[ok], "herbarium_UW_macrofungi")
    subset(~uw[ok], "herbarium_other")
    west = np.array([l3_names.get(int(b), "") in WESTERN_FOUR for b in s_block])
    subset(west, "specimens_in_western_four_blocks")
    subset(~west, "specimens_outside_western_four_blocks")
    out["variants"]["specimen_block_shares"] = {l3_names.get(int(k), str(k)): int(v) for k, v in zip(*np.unique(s_block, return_counts=True))}
    out["variants"]["background_block_shares"] = {l3_names.get(int(k), str(k)): int(v) for k, v in zip(*np.unique(b_block, return_counts=True))}
    print("subsets", round(time.monotonic() - t0), "s", flush=True)

    # block-matched background
    bb_cells, bb_r, bb_owner, fb = draw_matched_within(s_band, s_block, sr, pool, pool_band, pool_block)
    bbx, bby = cell_centre(bb_cells)
    bb_scores = np.array([circle_mean(raster, left, top, a, b, r) for a, b, r in zip(bbx, bby, bb_r)])
    bb_block = level3[np.searchsorted(table.cell_id, bb_cells)]
    out["variants"]["background_matched_on_road_band_and_level3_block"] = {
        **figure(s_scores, bb_scores, s_block, bb_block), "fell_back_to_band_only": fb}
    print("block-matched", round(time.monotonic() - t0), "s", flush=True)
    # weather-cell-matched background, falling back to the block
    wc_cells, wc_r, wc_owner, fb2 = draw_matched_within(s_band, s_wcell, sr, pool, pool_band, pool_wcell,
                                                        fallback_groups=s_block, pool_fallback=pool_block)
    wcx, wcy = cell_centre(wc_cells)
    wc_scores = np.array([circle_mean(raster, left, top, a, b, r) for a, b, r in zip(wcx, wcy, wc_r)])
    wc_block = level3[np.searchsorted(table.cell_id, wc_cells)]
    out["variants"]["background_matched_on_road_band_and_weather_cell_(block_fallback)"] = {
        **figure(s_scores, wc_scores, s_block, wc_block), "specimens_that_fell_back_to_block": fb2}
    # within-weather-cell AUC of specimens against their own cell's matched background
    out["variants"]["within_weather_cell_auc_specimens_vs_cell_matched_background"] = rc.within_cluster_auc(
        np.concatenate([s_scores, wc_scores]), np.r_[np.ones(len(s_scores)), np.zeros(len(wc_scores))],
        np.ones(len(s_scores) + len(wc_scores)), np.concatenate([s_wcell, table.wkey[np.searchsorted(table.cell_id, wc_cells)]]))
    # distinct cells and weather cells among scorable specimens (collecting stations)
    out["variants"]["distinct_specimen_cells"] = int(len(np.unique(cell[ok])))
    out["variants"]["distinct_specimen_weather_cells"] = int(len(np.unique(s_wcell)))
    out["variants"]["specimens_per_distinct_cell_top"] = sorted(np.unique(cell[ok], return_counts=True)[1].tolist(), reverse=True)[:10]
    out["seconds"] = round(time.monotonic() - t0)
    (HERE / "condition4_check.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps({k: (rc.fmt(v) if "point" in v else v) for k, v in out["variants"].items() if isinstance(v, dict) and "point" in v}, indent=1))
    print("reproduction match:", out["reproduction"]["whole_box"]["match"], out["reproduction"]["interior"]["match"])
    print("done", out["seconds"], "s")


if __name__ == "__main__":
    main()
