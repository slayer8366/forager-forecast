"""03_nested_selection.py's final printing line crashed (a str in a list was rounded) AFTER the 24 leave-one-
block-out selections had printed their kept sets and BEFORE anything was scored or saved. Rerunning the
selection (about 40 minutes) was not needed: the kept sets are read from 03_run.log, and the scoring step
(unchanged from 03_nested_selection.py) is run here."""
import sys, re, json, ast
sys.path.insert(0, ".")
import numpy as np
from rv2lib import *
kept = {}
for line in open("03_run.log"):
    m = re.match(r"block (\d+) kept (\[.*\])", line)
    if m: kept[int(m.group(1))] = ast.literal_eval(m.group(2))
print("blocks read", len(kept))
CAND = ["Larix", "Lithocarpus", "Chrysolepis", "Arbutus"]
d = load_main(); y, w, blocks = d["y"], d["w"], d["blocks"]
ub, bi = np.unique(blocks, return_inverse=True); nb = len(ub)
assert sorted(kept) == [int(b) for b in ub]
base, B, full = pred("base"), pred("B: f"), pred("full")
P = {c: pred("share_" + c) for c in CAND}
nested = np.zeros(len(y))
for j, b in enumerate(ub):
    rows = bi == j
    nested[rows] = base[rows] + sum((P[c][rows] - base[rows] for c in kept[int(b)]), np.zeros(rows.sum()))
Cb, M = pair_matrices(base, y, w, bi, nb); CB, _ = pair_matrices(B, y, w, bi, nb); Cfull, _ = pair_matrices(full, y, w, bi, nb)
act = base + sum((P[c] - base for c in ("Lithocarpus", "Chrysolepis", "Arbutus")), np.zeros(len(y)))
Cact, _ = pair_matrices(act, y, w, bi, nb); Cn, _ = pair_matrices(nested, y, w, bi, nb)
T = draws(nb)
res = {"kept_sets_from_log": {str(k): v for k, v in kept.items()}}
res["real_full_minus_B"] = diff_ci(Cfull, CB, M, T)
res["proxy_actual_set_(Lith+Chrys+Arb additive)_minus_B"] = diff_ci(Cact, CB, M, T)
res["nested_minus_B"] = diff_ci(Cn, CB, M, T)
res["nested_minus_base"] = diff_ci(Cn, Cb, M, T)
res["base_minus_B"] = diff_ci(Cb, CB, M, T)
res["real_full_minus_base"] = diff_ci(Cfull, Cb, M, T)
from collections import Counter
res["band_kept_in_n_of_24_folds"] = dict(Counter(c for v in kept.values() for c in v))
for k, v in res.items():
    if k.startswith("kept_sets"): continue
    print(k, [round(x, 5) for x in v] if isinstance(v, (list, tuple)) else v)
json.dump(res, open("03_results.json", "w"), indent=1)
