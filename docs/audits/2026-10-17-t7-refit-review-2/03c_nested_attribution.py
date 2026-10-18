"""Why is the nested figure below the additive proxy of the real set? Two variants of 03b, same kept sets:
(i) the real three bands plus Larix in every block; (ii) in each block only the bands of the real three that
that fold's selection also kept (Larix dropped everywhere)."""
import sys, re, json, ast
sys.path.insert(0, ".")
import numpy as np
from rv2lib import *
kept = {}
for line in open("03_run.log"):
    m = re.match(r"block (\d+) kept (\[.*\])", line)
    if m: kept[int(m.group(1))] = ast.literal_eval(m.group(2))
CAND = ["Larix", "Lithocarpus", "Chrysolepis", "Arbutus"]; REAL = ["Lithocarpus", "Chrysolepis", "Arbutus"]
d = load_main(); y, w, blocks = d["y"], d["w"], d["blocks"]
ub, bi = np.unique(blocks, return_inverse=True); nb = len(ub)
base, B = pred("base"), pred("B: f"); P = {c: pred("share_" + c) for c in CAND}
M = pair_matrices(base, y, w, bi, nb)[1]; CB = pair_matrices(B, y, w, bi, nb)[0]; Cb = pair_matrices(base, y, w, bi, nb)[0]
T = draws(nb)
def score(sets):
    s = base.copy()
    for j, b in enumerate(ub):
        rows = bi == j
        s[rows] = base[rows] + sum((P[c][rows] - base[rows] for c in sets(int(b))), np.zeros(rows.sum()))
    return pair_matrices(s, y, w, bi, nb)[0]
out = {}
for name, f in [("real three everywhere", lambda b: REAL), ("real three + Larix everywhere", lambda b: REAL + ["Larix"]),
                ("Larix only everywhere", lambda b: ["Larix"]),
                ("fold selection restricted to the real three", lambda b: [c for c in kept[b] if c in REAL]),
                ("fold selection incl. Larix (the nested figure)", lambda b: kept[b])]:
    C = score(f); out[name] = {"minus_B": diff_ci(C, CB, M, T), "minus_base": diff_ci(C, Cb, M, T)}
    print(f"{name:50s} minus B {out[name]['minus_B'][0]:+.5f} [{out[name]['minus_B'][1]:+.5f},{out[name]['minus_B'][2]:+.5f}]   minus base {out[name]['minus_base'][0]:+.5f} [{out[name]['minus_base'][1]:+.5f},{out[name]['minus_base'][2]:+.5f}]")
json.dump(out, open("03c_results.json", "w"), indent=1)
