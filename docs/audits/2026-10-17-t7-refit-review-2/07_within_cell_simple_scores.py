"""Q3: what ranks presences above background WITHIN one weather cell? Single raw columns as scores
(no model), same pair set and weights as condition 2. Plus the share of within-cell presences/pairs."""
import sys, json
sys.path.insert(0, ".")
import numpy as np
from rv2lib import *
d = load_main(); y, w, blocks, cell = d["y"], d["w"], d["blocks"], d["clusters"]
cols = list(d["columns"]); x = d["x"]
ub, bi = np.unique(blocks, return_inverse=True); nb = len(ub); T = draws(nb)
out = {}
def within(s):
    C, M = pair_matrices(s, y, w, bi, nb, cell=cell); return C, M
# pair coverage
Cf, Mw = within(pred("full"))
pres_cells = set(cell[y == 1].tolist()); both = set(cell[y == 0].tolist()) & pres_cells
share_pres = float(np.isin(cell[y == 1], list(both)).mean())
print("weather cells with presences", len(pres_cells), "also with background", len(both),
      "share of presence rows in a cell that also holds background", round(share_pres, 3),
      "share of presence weight", round(float(w[(y==1)&np.isin(cell, list(both))].sum()/w[y==1].sum()), 3))
out["cells_with_presences"] = len(pres_cells); out["cells_with_both"] = len(both); out["pres_share_in_both"] = share_pres
for name, s in [("-access_dist (nearer road ranks higher)", -x[:, cols.index("access_dist_m")]),
                ("total_cover_pct", x[:, cols.index("total_cover_pct")]),
                ("conifer_cover_pct", x[:, cols.index("conifer_cover_pct")]),
                ("share_Abies", x[:, cols.index("share_Abies")]),
                ("ph_mean_0_30cm", x[:, cols.index("ph_mean_0_30cm")]),
                ("model A", pred("A: e")), ("model B", pred("B: f")), ("model base", pred("base")), ("model full", pred("full"))]:
    C, M = within(s)
    p = C.sum() / M.sum()
    dd_ = np.einsum("ri,ij,rj->r", T, C, T) / np.einsum("ri,ij,rj->r", T, M, T)
    out[name] = [float(p), *map(float, np.percentile(dd_, [2.5, 97.5]))]
    print(f"{name:42s} within-cell AUC {p:.4f} [{out[name][1]:.4f},{out[name][2]:.4f}]")
# correlation of access with habitat columns on background rows (pooled)
bg = y == 0
from scipy.stats import spearmanr
acc = x[bg, cols.index("access_dist_m")]
for c in ("total_cover_pct", "conifer_cover_pct", "broadleaf_cover_pct", "share_Abies", "share_Tsuga", "share_Pseudotsuga", "share_Pinus", "ph_mean_0_30cm", "share_Lithocarpus", "log_effort"):
    r = spearmanr(acc, x[bg, cols.index(c)]).statistic
    out["spearman_access_vs_" + c] = float(r); print(f"  Spearman(road distance, {c}) on background: {r:+.3f}")
json.dump(out, open("07_results.json", "w"), indent=1)
