import sys, json
sys.path.insert(0, ".")
import numpy as np
from rv2lib import *
d = load_main()
y, w, blocks, cell = d["y"], d["w"], d["blocks"], d["clusters"]
ub, bi = np.unique(blocks, return_inverse=True)
nb = len(ub)
print("blocks", nb, "n", len(y), "presences", int(y.sum()))
T = draws(nb)
P = {"A": pred("A: e"), "B": pred("B: f"), "base": pred("base"), "full": pred("full")}
CM = {k: pair_matrices(v, y, w, bi, nb) for k, v in P.items()}
M = CM["full"][1]
out = {}
for k in P:
    out["auc_" + k] = auc_point(*CM[k])
print({k: round(v, 5) for k, v in out.items()})
out["c1_full_minus_B"] = diff_ci(CM["full"][0], CM["B"][0], M, T)
out["base_minus_B"] = diff_ci(CM["base"][0], CM["B"][0], M, T)
out["full_minus_A_pooled_block"] = diff_ci(CM["full"][0], CM["A"][0], M, T)
print("cond1 full-B", out["c1_full_minus_B"]); print("base-B", out["base_minus_B"])
# within-cell
W = {k: pair_matrices(v, y, w, bi, nb, cell=cell) for k, v in P.items()}
Mw = W["full"][1]
print("within-cell pair share", Mw.sum() / M.sum())
for k in P:
    out["within_auc_" + k] = auc_point(*W[k])
out["c2_within_full_minus_A_block"] = diff_ci(W["full"][0], W["A"][0], Mw, T)
print({k: round(v, 5) for k, v in out.items() if k.startswith("within_auc")})
print("cond2", out["c2_within_full_minus_A_block"])
json.dump(out, open("01_results.json", "w"), indent=1)
