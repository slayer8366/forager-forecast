"""Q1/Q2/Q5 support: retrain the final all-data models with the reviewer's own LightGBM call
(c16, the manifest's final configuration), score every eligible cell at the held effort, and
compare:
  - main full, retrained, against the fit's own scores_all.npy (reproduction);
  - comparison group (Laetiporus) full against main full, over shaded cells (report: 0.2295);
  - main B (effort + conifer and broadleaf cover) against main full, over shaded cells.
Writes final_models.json and maps.npz (float32 scores for the map renders, not committed)."""

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
import common as c  # noqa: E402

THREADS = 4
t0 = time.time()
OUT = Path(__file__).parent / "final_models.json"
meta = json.loads((c.WORK / "table_meta.json").read_text())
names = meta["features"]
t = c.load_table(features=True)
feats_all = t["features"]
le = c.effort_by_key("all", t["wkey"])
held = float(np.median(list(le.values())))
cfg = c.config("c16")
out = {"held_effort": held, "names": names}

main = c.Rows(c.V9 / "presences_main.csv", table=t)
comp = c.Rows(c.V9 / "presences_comparison.csv", table=t)
models = {}
for tag, rows, feats in (("main_full", main, c.FULL), ("comp_full", comp, c.FULL),
                         ("main_B", main, c.B_FEATS)):
    s = time.time()
    x = c.design(rows, feats, feats_all, names, le)
    bst = c.fit(cfg, feats, x, rows.y, rows.w, THREADS)
    gain = bst.feature_importance("gain")
    out[tag] = {"seconds": round(time.time() - s),
                "gain_share": {f: float(g / gain.sum()) for f, g in zip(feats, gain)}}
    models[tag] = (bst, feats)
    print(tag, out[tag], flush=True)
    del x

n = len(t["cell_id"])
maps = {k: np.empty(n, np.float32) for k in models}
for i0 in range(0, n, 500_000):
    f = feats_all[i0:i0 + 500_000].astype(np.float64)
    cols = {nm: f[:, i] for i, nm in enumerate(names)}
    cols[c.EFFORT] = np.full(len(f), held)
    cols["conifer_cover_pct"] = cols["share_conifer"] * cols["total_cover_pct"]
    cols["broadleaf_cover_pct"] = cols["share_broadleaf"] * cols["total_cover_pct"]
    for k, (bst, feats) in models.items():
        maps[k][i0:i0 + len(f)] = bst.predict(np.column_stack([cols[q] for q in feats]),
                                              raw_score=True)
print("map pass", round(time.time() - t0), flush=True)
fit_scores = np.load(c.WORK / "scores_all.npy")
inside = np.load(c.WORK / "inside_all.npy")
d = np.abs(maps["main_full"] - fit_scores)
out["reproduce_scores_all"] = {"max_abs_diff": float(d.max()), "identical": bool((d == 0).all())}
out["spearman_shaded"] = {
    "comp_full_vs_main_full": float(spearmanr(maps["comp_full"][inside],
                                              maps["main_full"][inside]).statistic),
    "comp_full_vs_fit_scores_all": float(spearmanr(maps["comp_full"][inside],
                                                   fit_scores[inside]).statistic),
    "main_B_vs_main_full": float(spearmanr(maps["main_B"][inside],
                                           maps["main_full"][inside]).statistic),
    "comp_full_vs_main_B": float(spearmanr(maps["comp_full"][inside],
                                           maps["main_B"][inside]).statistic),
}
np.savez(Path("/tmp") / "t7_review_maps.npz", **maps)
out["seconds"] = round(time.time() - t0)
OUT.write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
