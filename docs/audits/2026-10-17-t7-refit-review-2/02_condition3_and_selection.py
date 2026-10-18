import sys, json
sys.path.insert(0, ".")
import numpy as np
from rv2lib import *
CAND = ["Larix", "Betula", "Populus", "Alnus", "Lithocarpus", "Chrysolepis", "Arbutus", "ecm_hosts"]
out = {}
# ---------------- condition 3 and the groups -------------------------------------------------
def grp(tag, kfull, ka):
    d = np.load(f"/mnt/work/Zynergy/rv2-scratch/{tag}.npz")
    return dict(y=d["y"], w=d["w"], blocks=d["blocks"], full=pred(kfull), a=pred(ka))
myc = load_main(); myc.update(full=pred("full"), a=pred("A: e"))
sap = grp("sap", "saprotroph main-full", "saprotroph main-A: e")
lae = grp("lae", "comparison group-full", "comparison group-A: e")
def union_blocks(*gs):
    return np.unique(np.concatenate([g["blocks"] for g in gs]))
def gain_mats(g, ub):
    bi = np.searchsorted(ub, g["blocks"])
    Cf, M = pair_matrices(g["full"], g["y"], g["w"], bi, len(ub))
    Ca, _ = pair_matrices(g["a"], g["y"], g["w"], bi, len(ub))
    return Cf - Ca, Cf, Ca, M
def contrast(g1, g2, ub, shared=None, label=""):
    T = draws(len(ub))
    D1, _, _, M1 = gain_mats(g1, ub); D2, _, _, M2 = gain_mats(g2, ub)
    one = np.ones(len(ub))
    gain1 = (one @ D1 @ one) / (one @ M1 @ one); gain2 = (one @ D2 @ one) / (one @ M2 @ one)
    q = lambda D, M: np.einsum("ri,ij,rj->r", T, D, T) / np.einsum("ri,ij,rj->r", T, M, T)
    c = q(D1, M1) - q(D2, M2)
    lo, hi = np.percentile(c, [2.5, 97.5])
    g1d = q(D1, M1); g2d = q(D2, M2)
    r = dict(gain1=float(gain1), gain2=float(gain2), contrast=float(gain1 - gain2), lo=float(lo), hi=float(hi),
             gain1_ci=[float(x) for x in np.percentile(g1d, [2.5, 97.5])],
             gain2_ci=[float(x) for x in np.percentile(g2d, [2.5, 97.5])])
    print(label, {k: (round(v, 5) if not isinstance(v, list) else [round(x, 5) for x in v]) for k, v in r.items()})
    return r
ub = union_blocks(myc, sap)
print("union blocks myc+sap", len(ub), "myc", len(np.unique(myc["blocks"])), "sap", len(np.unique(sap["blocks"])))
out["c3_myc_vs_sap"] = contrast(myc, sap, ub, label="cond3 myc-sap")
ub2 = union_blocks(myc, lae)
out["myc_vs_laetiporus"] = contrast(myc, lae, ub2, label="myc-lae")
# gains of laetiporus alone w/ own block draws
ubl = np.unique(lae["blocks"])
bi = np.searchsorted(ubl, lae["blocks"]); T = draws(len(ubl))
D, Cf, Ca, M = gain_mats(lae, ubl)
out["laetiporus_full_minus_A"] = diff_ci(Cf, Ca, M, T)
print("lae full-A block-clustered", out["laetiporus_full_minus_A"], "blocks", len(ubl))
# ---------------- condition 1 selection -------------------------------------------------------
m = load_main(); y, w, blocks = m["y"], m["w"], m["blocks"]
ub, bi = np.unique(blocks, return_inverse=True); nb = len(ub)
P = {c: pred("share_" + c) for c in CAND}
base, B, full = pred("base"), pred("B: f"), pred("full")
Cm = {c: pair_matrices(P[c], y, w, bi, nb) for c in CAND}
Cb, Mfull = pair_matrices(base, y, w, bi, nb)
CB, _ = pair_matrices(B, y, w, bi, nb)
Cfull, _ = pair_matrices(full, y, w, bi, nb)
T = draws(nb)
print("add-one vs base, all blocks (their rule: interval wholly above 0)")
sel_all = {}
for c in CAND:
    p, lo, hi = diff_ci(Cm[c][0], Cb, Mfull, T)
    sel_all[c] = (p, lo, hi)
    print(f"  {c:12s} {p:+.5f} [{lo:+.5f},{hi:+.5f}] {'KEPT' if lo > 0 else ''}")
out["add_one"] = {c: list(v) for c, v in sel_all.items()}
# contribution of each band vs B
for c in CAND:
    out.setdefault("add_one_minus_B", {})[c] = diff_ci(Cm[c][0], CB, Mfull, T)
# gain split: full - base, base - B, full - B
out["full_minus_base"] = diff_ci(Cfull, Cb, Mfull, T)
print("full-base", out["full_minus_base"])
# Nested leave-one-block-out selection (proxy, single-band): the selection is redone on the other 23 blocks
one = np.ones(nb)
def point_diff_masked(Ca, Cb_, M, keep):
    k = keep.astype(float)
    return (k @ (Ca - Cb_) @ k) / (k @ M @ k)
nested = np.zeros(len(y)); chosen = {}
rng_seed = SEED
for b in range(nb):
    keep = np.ones(nb); keep[b] = 0
    idx = np.flatnonzero(keep)
    Tb = draws(len(idx))  # resample the 23 other blocks
    Tfull = np.zeros((Tb.shape[0], nb)); Tfull[:, idx] = Tb
    best, bestp = None, 0.0
    kept = []
    for c in CAND:
        p, lo, hi = diff_ci_masked = None, None, None
        d = np.einsum("ri,ij,rj->r", Tfull, Cm[c][0] - Cb, Tfull) / np.einsum("ri,ij,rj->r", Tfull, Mfull, Tfull)
        lo, hi = np.percentile(d, [2.5, 97.5])
        p = point_diff_masked(Cm[c][0], Cb, Mfull, keep)
        if lo > 0:
            kept.append((c, p))
    chosen[int(ub[b])] = [c for c, _ in kept]
    rows = bi == b
    if kept == []:
        nested[rows] = base[rows]
    else:
        # use the add-one model of the best kept band on this block (single-band proxy)
        cbest = max(kept, key=lambda t: t[1])[0]
        nested[rows] = P[cbest][rows]
print("leave-one-block-out kept sets:", chosen)
out["loo_kept"] = chosen
Cn, _ = pair_matrices(nested, y, w, bi, nb)
out["nested_minus_B"] = diff_ci(Cn, CB, Mfull, T)
out["nested_minus_base"] = diff_ci(Cn, Cb, Mfull, T)
print("nested(proxy) - B", out["nested_minus_B"], " nested - base", out["nested_minus_base"])
json.dump(out, open("02_results.json", "w"), indent=1)
