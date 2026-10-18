"""Q3 (a small, stated refit): ONE model on all rows with the final configuration the fit chose (c04) and
the fit's own constraints (monotone -1 on road distance, interaction groups habitat | effort+road), via
the repo's model module. Its raw score is a habitat part plus an effort+road part (the constraint makes
them additive). In-sample (optimistic on both parts alike); used only to ask how much of the ranking
sits in the part the map throws away, and how that part correlates with road distance. Not a result of
the judged fit."""
import sys, json
sys.path.insert(0, "."); sys.path.insert(0, "../../../src")
import numpy as np
from rv2lib import *
from forager_forecast.t7 import model as md
d = load_main(); y, w, blocks, cell = d["y"], d["w"], d["blocks"], d["clusters"]
cols = list(d["columns"]); x = d["x"]
FULL = ['share_Pseudotsuga', 'share_Tsuga', 'share_Picea', 'share_Abies', 'share_Pinus', 'share_Quercus', 'share_conifer',
        'share_broadleaf', 'total_cover_pct', 'ph_mean_0_30cm', 'share_Lithocarpus', 'share_Chrysolepis', 'share_Arbutus',
        'log_effort', 'access_dist_m']
cfg = {'id': 'c04', 'num_leaves': 15, 'min_data_in_leaf': 50, 'learning_rate': 0.03, 'feature_fraction': 0.7,
       'lambda_l2': 10.0, 'num_boost_round': 500}
X = x[:, [cols.index(c) for c in FULL]]
booster = md.train(cfg, FULL, X, y, w, threads=2, access_monotone=-1)
ub, bi = np.unique(blocks, return_inverse=True); nb = len(ub)
def raw(Xm): return booster.predict(Xm, raw_score=True)
full = raw(X)
Xh = X.copy()  # habitat held at medians -> effort+road part only
for i, c in enumerate(FULL):
    if c not in ("log_effort", "access_dist_m"): Xh[:, i] = np.median(X[:, i])
held_part = raw(Xh)
Xe = X.copy(); Xe[:, FULL.index("log_effort")] = np.median(X[:, FULL.index("log_effort")]); Xe[:, FULL.index("access_dist_m")] = float(d["held_access"])
hab_part = raw(Xe)
out = {}
for name, s in [("full raw", full), ("habitat part only (effort, road held)", hab_part), ("effort+road part only (habitat held)", held_part)]:
    C, M = pair_matrices(s, y, w, bi, nb); Cw, Mw = pair_matrices(s, y, w, bi, nb, cell=cell)
    out[name] = {"pooled_auc": float(C.sum() / M.sum()), "within_cell_auc": float(Cw.sum() / Mw.sum())}
    print(f"{name:42s} in-sample pooled AUC {out[name]['pooled_auc']:.4f}  within-cell {out[name]['within_cell_auc']:.4f}", flush=True)
from scipy.stats import spearmanr
bg = y == 0; acc = X[bg, FULL.index("access_dist_m")]
out["spearman_habitat_part_vs_road_distance_background"] = float(spearmanr(hab_part[bg], acc).statistic)
out["spearman_effort_road_part_vs_road_distance_background"] = float(spearmanr(held_part[bg], acc).statistic)
imp = dict(zip(FULL, booster.feature_importance("gain")))
out["gain_share"] = {k: float(v / sum(imp.values())) for k, v in sorted(imp.items(), key=lambda t: -t[1])}
print(json.dumps(out, indent=1))
json.dump(out, open("08_results.json", "w"), indent=1)
