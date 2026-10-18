import sys, csv
sys.path.insert(0, ".")
import numpy as np
from rv2lib import *
names = {int(r["code"]): (r["name"], r["presences"]) for r in csv.DictReader(open("/mnt/work/Zynergy/forecast-data/t7/refit/outputs/block_report.csv"))}
d = load_main(); y, w, blocks = d["y"], d["w"], d["blocks"]
ub, bi = np.unique(blocks, return_inverse=True); nb = len(ub)
base = pred("base"); Cb, M = pair_matrices(base, y, w, bi, nb)
print("block, name, presences | own-block AUC gain over base: Lith, Chrys, Arb, full | contribution to pooled gain (sum of row/col i of C diff / total M)")
tot = {}
for c in ("Lithocarpus", "Chrysolepis", "Arbutus"):
    Cc, _ = pair_matrices(pred("share_" + c), y, w, bi, nb); tot[c] = Cc - Cb
Cf, _ = pair_matrices(pred("full"), y, w, bi, nb); tot["full"] = Cf - Cb
for j, b in enumerate(ub):
    g = {k: v[j, j] / M[j, j] for k, v in tot.items()}
    contrib = {k: (v[j, :].sum() + v[:, j].sum() - v[j, j]) / M.sum() for k, v in tot.items()}
    print(int(b), names.get(int(b), ("?", "?"))[0][:34].ljust(34), str(names.get(int(b), ("?", "?"))[1]).rjust(5), "|", " ".join(f"{g[k]:+.4f}" for k in ("Lithocarpus", "Chrysolepis", "Arbutus", "full")), "|", " ".join(f"{contrib[k]:+.5f}" for k in ("Lithocarpus", "full")))
