"""What the re-fit's map ranks highest, against the judged 2026-10-16 map (read only). Both maps'
raw scores are aligned to the same table rows (the re-fit table equals the judged table on every
existing array, Phase 1 report). Over cells shaded in both: the rank correlation; the overlap of
the top decile; and, for each map's top decile, the share by level III block, the median road
distance and the mean of each habitat band. Usage: python map_comparison.py <out json>"""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

T7 = Path("/mnt/work/Zynergy/forecast-data/t7")
old_s, old_in = np.load(T7 / "fit/scores_all.npy"), np.load(T7 / "fit/inside_all.npy")
new_s, new_in = np.load(T7 / "refit/scores_all.npy"), np.load(T7 / "refit/inside_all.npy")
tab = np.load(T7 / "refit/table.npz")
meta = json.loads((T7 / "refit/table_meta.json").read_text())
names = meta["features"]
road = tab["access"][:, meta["access_bands"].index("dist_road_m")]
l3 = tab["level3"]
l3n = {e["code"]: f"{e['level3']} {e['name']}" for e in meta["level3_table"]}
both = old_in & new_in
out = {"cells_shaded_both": int(both.sum()),
       "spearman_old_new": float(spearmanr(old_s[both], new_s[both]).statistic)}
idx = np.nonzero(both)[0]
feats = tab["features"]


def top(scores):
    s = scores[idx]
    return idx[s >= np.quantile(s, 0.9)]


def describe(sel):
    f = feats[sel].astype(np.float64)
    u, n = np.unique(l3[sel], return_counts=True)
    blocks = sorted(((l3n.get(int(a), str(a)), round(int(b) / len(sel), 4)) for a, b in zip(u, n)),
                    key=lambda t: -t[1])[:10]
    return {"cells": int(len(sel)), "median_road_m": float(np.median(road[sel])),
            "share_road_over_1km": float((road[sel] > 1000).mean()),
            "top_blocks_share": blocks,
            "band_means": {b: round(float(np.nanmean(f[:, k])), 4) for k, b in enumerate(names)}}


to, tn = top(old_s), top(new_s)
out["top_decile_overlap_share"] = float(len(np.intersect1d(to, tn)) / len(to))
out["all_shaded"] = describe(idx)
out["top_decile_2026_10_16"] = describe(to)
out["top_decile_refit"] = describe(tn)
Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps({k: out[k] for k in ("cells_shaded_both", "spearman_old_new", "top_decile_overlap_share")}))
for k in ("all_shaded", "top_decile_2026_10_16", "top_decile_refit"):
    d = out[k]
    print(k, d["median_road_m"], d["share_road_over_1km"], d["top_blocks_share"][:6])
    print("  ", {b: v for b, v in d["band_means"].items() if b.startswith("share_") or b in ("total_cover_pct", "ph_mean_0_30cm")})
