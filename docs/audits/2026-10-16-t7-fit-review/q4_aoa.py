"""Q4: recompute the area-of-applicability threshold with the reviewer's own code.

CAST's rule as aoa.py's docstring states it (read), re-written here: centre and scale each habitat
predictor by the training mean and sd (n-1), multiply by its gain weight (the weights recorded in
fit_report.json, aoa.weights); training DI = distance to the nearest training point in another
level III block / mean pairwise training distance; threshold = Q75 + 1.5 IQR, capped at the max.
The mean pairwise distance is estimated twice: with 2,000,000 pairs at a different seed, and with
10,000,000 pairs, to see how much the estimate moves the threshold and the inside count.
Also recounts inside/outside on all eligible cells. Writes q4_aoa.json."""

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).parent))
import common as c  # noqa: E402

t0 = time.time()
rep = json.loads(c.FIT_REPORT.read_text())
gw = rep["aoa"]["weights"]
habitat = list(gw)
meta = json.loads((c.WORK / "table_meta.json").read_text())
names = meta["features"]
t = c.load_table(features=True)
rows = c.Rows(c.V9 / "presences_main.csv", table=t)
cols = [names.index(h) for h in habitat]
x = t["features"][rows.idx][:, cols].astype(np.float64)
w = np.array([gw[h] for h in habitat])
mu, sd = x.mean(0), x.std(0, ddof=1)
sd = np.where(sd > 0, sd, 1.0)
z = (x - mu) / sd * w
near = np.empty(len(z))
for b in np.unique(rows.block):
    m = rows.block == b
    near[m] = cKDTree(z[~m]).query(z[m], k=1)[0]
print("nearest done", round(time.time() - t0), flush=True)


def mean_dist(n_pairs, seed):
    rng = np.random.default_rng(seed)
    tot, done = 0.0, 0
    while done < n_pairs:
        k = min(1_000_000, n_pairs - done)
        i = rng.integers(0, len(z), k)
        j = rng.integers(0, len(z), k)
        ok = i != j
        tot += np.linalg.norm(z[i[ok]] - z[j[ok]], axis=1).sum()
        done += int(ok.sum())
    return tot / done


out = {"n_train": len(z), "reported": {k: rep["aoa"][k] for k in ("threshold", "mean_distance",
                                                                    "train_di_quantiles")}}
tree = cKDTree(z)
feats = t["features"]
for label, md in (("2M pairs seed 7", mean_dist(2_000_000, 7)),
                  ("10M pairs seed 11", mean_dist(10_000_000, 11))):
    di = near / md
    q25, q75 = np.quantile(di, [0.25, 0.75])
    thr = float(min(q75 + 1.5 * (q75 - q25), di.max()))
    out[label] = {"mean_distance": md, "threshold": thr,
                  "di_quantiles": np.quantile(di, [0, .25, .5, .75, 1]).tolist()}
    print(label, out[label], flush=True)
# inside count over all eligible cells at the reported threshold and mean distance, and at mine
thr_rep, md_rep = rep["aoa"]["threshold"], rep["aoa"]["mean_distance"]
d_all = np.empty(len(feats))
for i0 in range(0, len(feats), 500_000):
    zz = (feats[i0:i0 + 500_000][:, cols].astype(np.float64) - mu) / sd * w
    d_all[i0:i0 + len(zz)] = tree.query(zz, k=1)[0]
out["outside_at_reported"] = int((d_all / md_rep > thr_rep).sum())
for label in ("2M pairs seed 7", "10M pairs seed 11"):
    o = out[label]
    o["outside_cells"] = int((d_all / o["mean_distance"] > o["threshold"]).sum())
inside_fit = np.load(c.WORK / "inside_all.npy")
out["fit_outside_cells"] = int((~inside_fit).sum())
out["agreement_with_fit_inside"] = float(((d_all / md_rep <= thr_rep) == inside_fit).mean())
out["seconds"] = round(time.time() - t0)
(Path(__file__).parent / "q4_aoa.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
