"""Q2: the add-one selection redone with each block held out of it (leave-one-block-out), using the
fit's own selection rule (D135/D138: add-one vs base, interval WHOLLY ABOVE ZERO, resampling WEATHER
CELLS as t7_fit.diff does by default), then the held-out block is scored by the models the other
blocks' selection would have kept. Only add-one models and the one full model are cached, so a kept
set K is scored as base + sum_{c in K}(add-one_c - base) on the held-out block's rows (a proxy,
validated below against the real full model). Bootstrap only runs when the leave-out point is > 0
(an interval wholly above zero requires it, so skipping the rest cannot change a decision)."""
import sys, json
sys.path.insert(0, ".")
import numpy as np
from rv2lib import *

RES3 = int(sys.argv[1]) if len(sys.argv) > 1 else 300
# Four candidates only: the other four had negative points or an interval low far below 0 on all blocks.
# First attempt (8 candidates, 300 resamples) was too slow and stopped after 3 blocks:
# 03_run_aborted_first_attempt_300res_8cand.log
CAND = ["Larix", "Lithocarpus", "Chrysolepis", "Arbutus"]
m = load_main(); y, w, blocks, cell = m["y"], m["w"], m["blocks"], m["clusters"]
ub, bi = np.unique(blocks, return_inverse=True); nb = len(ub)
base, B, full = pred("base"), pred("B: f"), pred("full")
P = {c: pred("share_" + c) for c in CAND}


class Ranked:
    def __init__(self, s, y):
        o = np.argsort(s, kind="mergesort"); ss = s[o]
        self.o = o; self.g = np.cumsum(np.r_[True, ss[1:] != ss[:-1]]) - 1; self.n = self.g[-1] + 1
        self.pos = y[o] == 1
    def auc(self, w):
        w = w[self.o]
        wp = np.bincount(self.g, np.where(self.pos, w, 0.0), self.n)
        wn = np.bincount(self.g, np.where(self.pos, 0.0, w), self.n)
        below = np.cumsum(wn) - wn
        return (wp * (below + 0.5 * wn)).sum() / (wp.sum() * wn.sum())


def rule(sel, cand_pred, rng_seed=SEED):
    """kept? by the fit's rule on the rows `sel`: point > 0 and 2.5th pct of cell-bootstrap diff > 0"""
    yy, ww, cc = y[sel], w[sel], cell[sel]
    ra, rb = Ranked(cand_pred[sel], yy), Ranked(base[sel], yy)
    p = ra.auc(ww) - rb.auc(ww)
    if p <= 0:
        return False, p, None
    _, idx = np.unique(cc, return_inverse=True); n = idx.max() + 1
    rng = np.random.default_rng(rng_seed); d = np.empty(RES3)
    for i in range(RES3):
        t = np.bincount(rng.integers(0, n, size=n), minlength=n)[idx]
        d[i] = ra.auc(ww * t) - rb.auc(ww * t)
    lo = np.percentile(d, 2.5)
    return bool(lo > 0), p, float(lo)

# validation of the rule on all rows (should reproduce the fit's kept set up to resample count)
allsel = np.ones(len(y), bool)
print("rule on all blocks (weather-cell resampling, %d resamples)" % RES3, flush=True)
kept_all = []
for c in CAND:
    k, p, lo = rule(allsel, P[c]); print(f"  {c:12s} point {p:+.5f} lo {lo} kept={k}", flush=True)
    if k: kept_all.append(c)
nested_proxy = np.zeros(len(y)); loo = {}
for b in range(nb):
    sel = bi != b
    kept = []
    for c in CAND:
        k, p, lo = rule(sel, P[c])
        if k: kept.append(c)
    loo[int(ub[b])] = kept
    rows = bi == b
    nested_proxy[rows] = base[rows] + sum((P[c][rows] - base[rows] for c in kept), np.zeros(rows.sum()))
    print("block", int(ub[b]), "kept", kept, flush=True)
# proxy validation: base + sum of the three actually kept add-ones everywhere, against the real full model
Cb, M = pair_matrices(base, y, w, bi, nb); CB, _ = pair_matrices(B, y, w, bi, nb)
Cfull, _ = pair_matrices(full, y, w, bi, nb)
act = base + sum((P[c] - base for c in ("Lithocarpus", "Chrysolepis", "Arbutus")), np.zeros(len(y)))
Cact, _ = pair_matrices(act, y, w, bi, nb)
T = draws(nb)
res = {"loo_kept": loo, "kept_all_rule_check": kept_all, "resamples_rule": RES3}
res["proxy_validation_actual_set_minus_B"] = diff_ci(Cact, CB, M, T)
res["real_full_minus_B"] = diff_ci(Cfull, CB, M, T)
Cn, _ = pair_matrices(nested_proxy, y, w, bi, nb)
res["nested_minus_B"] = diff_ci(Cn, CB, M, T)
res["nested_minus_base"] = diff_ci(Cn, Cb, M, T)
res["base_minus_B"] = diff_ci(Cb, CB, M, T)
for k, v in res.items():
    if isinstance(v, (tuple, list)) and len(v) == 3: print(k, [round(x, 5) for x in v])
json.dump(res, open("03_results.json", "w"), indent=1)
