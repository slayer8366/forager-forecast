"""Review 2, questions 1, 2 and 4: the final full model and the comparison group's model refitted
at the manifest's configuration (c16) to reproduce the map scores, the gain weights and the 0.230
rank correlation; the area of applicability recomputed with my own code; the full map compared
with the effort surface over shaded cells.

Inputs (read only): the fit's table, the rows rebuilt by rebuild_rows.py, the fit's saved
scores_all.npy and inside_all.npy, the output rasters, T6's surface. Writes big arrays to my own
folder on /mnt/work and a JSON summary beside this script.

Project code used: ``EffortSurface.read``/``static_effort`` (T6's own reader, for log effort
values), ``cell_lonlat`` (pure geometry, master grid to longitude and latitude). LightGBM
parameters are built here from P5's rules (as unfixed_rerun.py).
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "src"))
from unfixed_rerun import FEATS, params  # noqa: E402
from forager_forecast.cells import Cell  # noqa: E402
from forager_forecast.effort import EffortSurface  # noqa: E402
from forager_forecast.t7.keying import static_effort, weather_cells_for_window  # noqa: E402
from forager_forecast.pnw import pnw_window  # noqa: E402

import lightgbm as lgb  # noqa: E402

WORK = Path("/mnt/work/Zynergy/forecast-data/t7/fit")
OUTS = Path("/mnt/work/Zynergy/forecast-data/t7/pnw-2026-10-17")
ROWS = Path("/mnt/work/Zynergy/forecast-data/t7-review-2")
META = HERE.parents[0] / "2026-10-16-t7-fit" / "table_meta.json"
REPORT = HERE.parents[0] / "2026-10-16-t7-fit" / "fit_report.json"
T6 = Path.home() / "Zynergy/forager-forecast-t6/data/t6"
SEED = 20260918
C16 = {"id": "c16", "num_leaves": 15, "min_data_in_leaf": 1000, "learning_rate": 0.03,
       "feature_fraction": 1.0, "lambda_l2": 10.0, "num_boost_round": 200}
FULL = FEATS["full"]
HAB = [f for f in FULL if f != "log_effort"]


def pack(lat_t, lon_t):
    return (np.asarray(lat_t, dtype=np.int64) + 1000) * 10_000 + (np.asarray(lon_t, dtype=np.int64) + 2000)


def log(msg):
    print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)


def columns(feat_block, names, le):
    cols = {n: feat_block[:, k] for k, n in enumerate(names)}
    cols["log_effort"] = le
    cols["conifer_cover_pct"] = cols["share_conifer"] * cols["total_cover_pct"]
    cols["broadleaf_cover_pct"] = cols["share_broadleaf"] * cols["total_cover_pct"]
    return cols


def train_all(rows, feats, names, feats_table):
    r = np.load(ROWS / f"rows_{rows}.npz")
    x = feats_table[r["idx"]].astype(np.float64)
    cols = columns(x, names, r["log_effort"])
    xm = np.column_stack([cols[c] for c in feats])
    w = r["w"] * len(r["w"]) / r["w"].sum()
    d = lgb.Dataset(xm, r["y"], weight=w, feature_name=feats, free_raw_data=True)
    return lgb.train(params(C16, feats), d, num_boost_round=C16["num_boost_round"]), xm, r


def main():
    out = {}
    names = json.loads(META.read_text())["features"]
    rep = json.loads(REPORT.read_text())
    tab = np.load(WORK / "table.npz")
    cell_id, wkey, level3, feats = tab["cell_id"], tab["wkey"], tab["level3"], tab["features"]
    held = rep["held_effort"]

    # 1. the final full model, refitted
    booster, xtr, r = train_all("main", FULL, names, feats)
    gains = dict(zip(FULL, booster.feature_importance("gain").tolist()))
    out["gains_refit"] = gains
    out["gains_report"] = rep["aoa"]["weights"]
    out["gains_max_rel_diff"] = max(abs(gains[k] - rep["aoa"]["weights"][k]) / max(rep["aoa"]["weights"][k], 1e-9) for k in HAB)
    log(f"final model refit; gain max rel diff {out['gains_max_rel_diff']:.2e}")

    # 2. the comparison group's model, refitted
    comp, _, _ = train_all("comparison", FULL, names, feats)

    # 3. scores for every eligible cell at the held effort, both models
    n = len(cell_id)
    score = np.empty(n, np.float32); cscore = np.empty(n, np.float32)
    e = FULL.index("log_effort")
    for i0 in range(0, n, 500_000):
        f = feats[i0:i0 + 500_000].astype(np.float64)
        cols = columns(f, names, np.full(len(f), held))
        xm = np.column_stack([cols[c] for c in FULL])
        score[i0:i0 + len(f)] = booster.predict(xm, raw_score=True)
        cscore[i0:i0 + len(f)] = comp.predict(xm, raw_score=True)
    saved = np.load(WORK / "scores_all.npy")
    inside_saved = np.load(WORK / "inside_all.npy")
    out["score_max_abs_diff_vs_saved"] = float(np.max(np.abs(score - saved)))
    out["score_spearman_vs_saved"] = float(spearmanr(score[::50], saved[::50]).statistic)
    log(f"scores: max abs diff vs saved {out['score_max_abs_diff_vs_saved']:.2e}")
    np.save(ROWS / "score_refit.npy", score); np.save(ROWS / "comp_refit.npy", cscore)

    # 4. the area of applicability, my own implementation (CAST's rule as read in aoa.py's docstring)
    hab_idx = [names.index(h) for h in HAB]
    xt = xtr[:, [FULL.index(h) for h in HAB]]
    gw = np.array([max(gains[h], 0.0) for h in HAB])
    centre, sd = xt.mean(0), xt.std(0, ddof=1)
    sd = np.where(sd > 0, sd, 1.0)
    z = (xt - centre) / sd * gw
    blocks = r["blocks"]
    nearest = np.empty(len(z))
    for b in np.unique(blocks):
        h = blocks == b
        nearest[h] = cKDTree(z[~h]).query(z[h], k=1)[0]
    rng = np.random.default_rng(12345)  # my own seed for the pair estimate
    m = len(z)
    est = []
    for _ in range(3):
        i = rng.integers(0, m, 2_000_000); j = rng.integers(0, m - 1, 2_000_000)
        j = np.where(j >= i, j + 1, j)
        est.append(float(np.linalg.norm(z[i] - z[j], axis=1).mean()))
    out["mean_distance_estimates_other_seed"] = est
    out["mean_distance_report"] = rep["aoa"]["mean_distance"]
    md = rep["aoa"]["mean_distance"]  # use the report's for the threshold comparison
    di = nearest / md
    q25, q75 = np.quantile(di, [0.25, 0.75])
    thr = float(min(q75 + 1.5 * (q75 - q25), di.max()))
    out["train_di_quantiles"] = np.quantile(di, [0, .25, .5, .75, 1]).tolist()
    out["threshold_recomputed_with_report_mean_distance"] = thr
    out["threshold_report"] = rep["aoa"]["threshold"]
    out["threshold_with_own_mean_distance"] = float(min(q75 * md / est[0] + 1.5 * (q75 - q25) * md / est[0], di.max() * md / est[0]))
    log(f"aoa threshold {thr:.5f} (report {rep['aoa']['threshold']:.5f})")
    tree = cKDTree(z)
    inside = np.empty(n, bool)
    for i0 in range(0, n, 500_000):
        zz = (feats[i0:i0 + 500_000][:, hab_idx].astype(np.float64) - centre) / sd * gw
        inside[i0:i0 + len(zz)] = tree.query(zz, k=1)[0] / md <= thr
    out["inside"] = int(inside.sum()); out["outside"] = int((~inside).sum())
    out["inside_disagreements_vs_saved"] = int((inside != inside_saved).sum())
    log(f"aoa inside {out['inside']} outside {out['outside']}; disagreements {out['inside_disagreements_vs_saved']}")

    # 5. the comparison correlation and the effort comparison over shaded cells
    sh = inside_saved
    out["rank_corr_full_vs_comparison_shaded"] = float(spearmanr(score[sh], cscore[sh]).statistic)
    out["rank_corr_report"] = rep["comparison_rank_correlation_over_shaded"]
    keys = np.unique(wkey)
    lat = keys // 10_000 - 1000; lon = keys % 10_000 - 2000
    eff = static_effort(EffortSurface.read(T6 / "all"), [Cell(int(a), int(b)) for a, b in zip(lat, lon)])
    eff_by_key = {int(pack(c.lat_tenths, c.lon_tenths)): v for c, v in eff.total.items()}
    le = np.array([eff_by_key.get(int(k), np.nan) for k in wkey])
    le = np.log(le)
    in_frame = np.isfinite(le)
    out["shaded_in_frame"] = int((sh & in_frame).sum()); out["shaded_out_of_frame"] = int((sh & ~in_frame).sum())
    sel = sh & in_frame
    out["rank_corr_map_vs_log_effort_shaded_in_frame"] = float(spearmanr(score[sel], le[sel]).statistic)
    # at each cell's own effort: raw score + effort part; the effort part is additive (P5), read
    # off the booster by predicting one row at two effort values
    probe = np.column_stack([columns(feats[:1].astype(np.float64), names, np.array([held]))[c] for c in FULL])
    def effort_part(v):
        p = probe.copy(); p[0, e] = v
        return booster.predict(p, raw_score=True)[0]
    grid_e = np.linspace(np.nanmin(le[sel]), np.nanmax(le[sel]), 400)
    g = np.array([effort_part(v) for v in grid_e]) - effort_part(held)
    own = score[sel] + np.interp(le[sel], grid_e, g)
    out["rank_corr_map_vs_full_at_own_effort_shaded_in_frame"] = float(spearmanr(score[sel], own).statistic)
    out["rank_corr_log_effort_vs_full_at_own_effort"] = float(spearmanr(le[sel], own).statistic)
    out["effort_part_range_over_frame_quantiles"] = [float(g.min()), float(g.max())]
    # where they differ most, by block: mean of (map rank - effort rank), ranks as fractions
    from scipy.stats import rankdata
    rm = rankdata(score[sel]) / sel.sum(); re = rankdata(le[sel]) / sel.sum()
    d = rm - re
    l3 = level3[sel]
    l3names = {int(x["code"]): f"{x['level3']} {x['name']}" for x in json.loads(META.read_text())["level3_table"]}
    by_block = {}
    for b in np.unique(l3):
        s = l3 == b
        by_block[l3names[int(b)]] = {"cells": int(s.sum()), "mean_map_rank": float(rm[s].mean()),
                                     "mean_effort_rank": float(re[s].mean()), "mean_rank_diff": float(d[s].mean())}
    out["by_block_map_vs_effort"] = dict(sorted(by_block.items(), key=lambda kv: kv[1]["mean_rank_diff"]))
    # mean map rank (over all shaded) by block, in and out of frame
    rank_all = rankdata(score[sh]) / sh.sum()
    l3s = level3[sh]; fr = in_frame[sh]
    by_block_all = {}
    for b in np.unique(l3s):
        s = l3s == b
        by_block_all[l3names[int(b)]] = {"shaded": int(s.sum()), "in_frame": int((s & fr).sum()),
                                         "mean_map_rank": float(rank_all[s].mean()),
                                         "mean_map_rank_in_frame": float(rank_all[s & fr].mean()) if (s & fr).any() else None,
                                         "mean_map_rank_out_of_frame": float(rank_all[s & ~fr].mean()) if (s & ~fr).any() else None}
    out["by_block_map_rank"] = dict(sorted(by_block_all.items(), key=lambda kv: -kv[1]["mean_map_rank"]))
    out["mean_map_rank_in_frame_vs_out"] = [float(rank_all[fr].mean()), float(rank_all[~fr].mean())]
    np.save(ROWS / "log_effort_all.npy", le)
    (HERE / "final_model_aoa_map.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
