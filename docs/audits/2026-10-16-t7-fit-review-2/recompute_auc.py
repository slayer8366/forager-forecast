"""Review 2, step 2: every headline AUC figure recomputed from the cached held-out predictions
with my own AUC and bootstrap code; plus a within-weather-cell AUC the report does not have.

Inputs (read only): the fit's cache (`lobo_*.npy`), the rows rebuilt by rebuild_rows.py, the
fit's table_meta.json (block study and share counts, level III names). No project code is
imported.

AUC here: the weighted probability that a presence outranks a background point, ties half, by
sorting background scores once and placing each presence with searchsorted (a different route
from metrics.py's cumulative tie-group sums).
"""

import json
import sys
from pathlib import Path

import numpy as np

CACHE = Path("/mnt/work/Zynergy/forecast-data/t7/fit/cache")
ROWS = Path("/mnt/work/Zynergy/forecast-data/t7-review-2")
EVID = Path(__file__).resolve().parent
META = EVID.parents[0] / "2026-10-16-t7-fit" / "table_meta.json"
SEED = 20260918
RESAMPLES = 1000


def wauc(score, y, w):
    score = np.asarray(score, float); y = np.asarray(y); w = np.asarray(w, float)
    pos, neg = y == 1, y == 0
    s_neg = score[neg]; w_neg = w[neg]
    order = np.argsort(s_neg, kind="mergesort")
    s_neg, w_neg = s_neg[order], w_neg[order]
    cum = np.concatenate([[0.0], np.cumsum(w_neg)])
    total_neg = cum[-1]; total_pos = w[pos].sum()
    if total_neg <= 0 or total_pos <= 0:
        return None
    lo = np.searchsorted(s_neg, score[pos], side="left")
    hi = np.searchsorted(s_neg, score[pos], side="right")
    below = cum[lo]; tied = cum[hi] - cum[lo]
    return float((w[pos] * (below + 0.5 * tied)).sum() / (total_pos * total_neg))


class Placed:
    """One model's scores sorted once: each presence's place among the background scores
    (strictly below, tied) is fixed, so an AUC under new weights is a cumsum and two gathers."""

    def __init__(self, score, y):
        score = np.asarray(score, float); y = np.asarray(y)
        self.pos, self.neg = y == 1, y == 0
        s_neg = score[self.neg]
        self.order = np.argsort(s_neg, kind="mergesort")
        s_sorted = s_neg[self.order]
        self.lo = np.searchsorted(s_sorted, score[self.pos], side="left")
        self.hi = np.searchsorted(s_sorted, score[self.pos], side="right")

    def auc(self, w):
        w = np.asarray(w, float)
        w_neg = w[self.neg][self.order]
        cum = np.concatenate([[0.0], np.cumsum(w_neg)])
        wp = w[self.pos]
        tp, tn = wp.sum(), cum[-1]
        if tp <= 0 or tn <= 0:
            return None
        return float((wp * (cum[self.lo] + 0.5 * (cum[self.hi] - cum[self.lo]))).sum() / (tp * tn))


def boot_diff(a, b, y, w, clusters, seed=SEED, resamples=RESAMPLES):
    pa, pb = Placed(a, y), Placed(b, y)
    assert abs(pa.auc(w) - wauc(a, y, w)) < 1e-12  # the two routes agree
    _, inv = np.unique(clusters, return_inverse=True)
    n = inv.max() + 1
    rng = np.random.default_rng(seed)
    out = np.empty(resamples)
    for i in range(resamples):
        times = np.bincount(rng.integers(0, n, size=n), minlength=n)
        wi = w * times[inv]
        out[i] = pa.auc(wi) - pb.auc(wi)
    lo, hi = np.percentile(out, [2.5, 97.5])
    return {"point": pa.auc(w) - pb.auc(w), "low": float(lo), "high": float(hi),
            "above_zero": bool(lo > 0)}


def within_cluster_auc(score, y, w, clusters):
    """Weighted AUC over presence-background pairs that share a cluster: each cluster's AUC,
    weighted by its (presence weight x background weight) pair mass."""
    _, inv = np.unique(clusters, return_inverse=True)
    num = den = 0.0
    for c in range(inv.max() + 1):
        sel = inv == c
        ys = y[sel]
        if (ys == 1).any() and (ys == 0).any():
            ws = w[sel]
            mass = ws[ys == 1].sum() * ws[ys == 0].sum()
            num += wauc(score[sel], ys, ws) * mass
            den += mass
    return num / den, den


def load(key):
    return np.load(CACHE / f"lobo_{key}.npy")


def main(run):
    r = np.load(ROWS / f"rows_{run}.npz")
    y, w, blocks, clusters, year = r["y"], r["w"], r["blocks"], r["clusters"], r["year"]
    meta = json.loads(META.read_text())
    study = {int(k): v for k, v in meta["block_study_cells"].items()}
    share = {int(k): v for k, v in meta["block_share_cells"].items()}
    forested_all = {b for b, n in study.items() if n > 0 and share.get(b, 0) / n >= 0.15}
    in_fit = set(np.unique(blocks).tolist())
    forested = sorted(forested_all & in_fit)
    fsel = np.isin(blocks, forested)
    informative = sorted(int(b) for b in in_fit if (y[blocks == b] == 1).sum() >= 30)
    names = {e["code"]: (e["level3"], e["name"], e["level1"]) for e in meta["level3_table"]}
    out = {"run": run, "n": int(len(y)), "forested_in_box": len(forested_all),
           "forested_in_fit": forested, "informative": informative}

    if run == "main":
        keys = {"A": "A: e", "B": "B: f", "base": "base", "full": "full"}
        p = {k: load(v) for k, v in keys.items()}
        assert all(len(v) == len(y) for v in p.values())
        out["pooled_auc"] = {k: wauc(v, y, w) for k, v in p.items()}
        out["forested_auc"] = {k: wauc(v[fsel], y[fsel], w[fsel]) for k, v in p.items()}
        out["p10_weather_cell"] = {
            "all_A": boot_diff(p["full"], p["A"], y, w, clusters),
            "all_B": boot_diff(p["full"], p["B"], y, w, clusters),
            "forested_A": boot_diff(p["full"][fsel], p["A"][fsel], y[fsel], w[fsel], clusters[fsel]),
            "forested_B": boot_diff(p["full"][fsel], p["B"][fsel], y[fsel], w[fsel], clusters[fsel]),
        }
        out["p10_weather_cell_other_seed_7"] = {
            "all_A": boot_diff(p["full"], p["A"], y, w, clusters, seed=7),
            "all_B": boot_diff(p["full"], p["B"], y, w, clusters, seed=7),
        }
        out["p10_block_clustered"] = {
            "all_A": boot_diff(p["full"], p["A"], y, w, blocks),
            "all_B": boot_diff(p["full"], p["B"], y, w, blocks),
            "forested_A": boot_diff(p["full"][fsel], p["A"][fsel], y[fsel], w[fsel], blocks[fsel]),
            "forested_B": boot_diff(p["full"][fsel], p["B"][fsel], y[fsel], w[fsel], blocks[fsel]),
        }
        out["base_minus_A"] = boot_diff(p["base"], p["A"], y, w, clusters)
        out["base_minus_B"] = boot_diff(p["base"], p["B"], y, w, clusters)
        bands = ["share_Larix", "share_Betula", "share_Populus", "share_Alnus", "share_Lithocarpus",
                 "share_Chrysolepis", "share_Arbutus", "share_ecm_hosts"]
        out["add_one"] = {b: boot_diff(load(b), p["base"], y, w, clusters) for b in bands}
        out["by_block"] = {
            f"{names[b][0]} {names[b][1]}": {
                "presences": int((y[blocks == b] == 1).sum()),
                "background": int((y[blocks == b] == 0).sum()),
                "informative": b in informative, "forested": b in forested,
                **({k: wauc(v[blocks == b], y[blocks == b], w[blocks == b]) for k, v in p.items()}
                   if b in informative else {}),
            } for b in sorted(in_fit)
        }
        out["level1"] = {}
        for l1 in sorted({names[b][2] for b in in_fit}):
            sel = np.isin(blocks, [b for b in in_fit if names[b][2] == l1])
            out["level1"][l1] = {"presences": int((y[sel] == 1).sum()),
                                 **{k: wauc(v[sel], y[sel], w[sel]) for k, v in p.items()}}
        out["by_year"] = {}
        for yr in sorted(set(year[y == 1].tolist())):
            sel = (y == 0) | ((y == 1) & (year == yr))
            out["by_year"][int(yr)] = {"presences": int(((y == 1) & (year == yr)).sum()),
                                       **{k: wauc(v[sel], y[sel], w[sel]) for k, v in p.items()}}
        # within weather cell: the pairs effort cannot separate
        wc = {}
        for k, v in p.items():
            a, mass = within_cluster_auc(v, y, w, clusters)
            wc[k] = a
        out["within_weather_cell_auc"] = wc
        out["within_weather_cell_pair_mass_share"] = float(mass / (w[y == 1].sum() * w[y == 0].sum()))
        wb = {}
        for k, v in p.items():
            a, massb = within_cluster_auc(v, y, w, blocks)
            wb[k] = a
        out["within_block_auc"] = wb
        out["within_block_pair_mass_share"] = float(massb / (w[y == 1].sum() * w[y == 0].sum()))
    else:
        label = {"comparison": "comparison group", "licence": "licence track", "side": "M2 side run"}[run]
        p = {k: load(f"{label}-{v}") for k, v in {"A": "A: e", "B": "B: f", "full": "full"}.items()}
        assert all(len(v) == len(y) for v in p.values()), {k: len(v) for k, v in p.items()}
        out["pooled_auc"] = {k: wauc(v, y, w) for k, v in p.items()}
        out["full_minus_A"] = boot_diff(p["full"], p["A"], y, w, clusters)
        out["full_minus_B"] = boot_diff(p["full"], p["B"], y, w, clusters)
        out["forested_full_minus_A"] = boot_diff(p["full"][fsel], p["A"][fsel], y[fsel], w[fsel], clusters[fsel])
        out["forested_full_minus_B"] = boot_diff(p["full"][fsel], p["B"][fsel], y[fsel], w[fsel], clusters[fsel])
        out["block_clustered_full_minus_A"] = boot_diff(p["full"], p["A"], y, w, blocks)
        out["block_clustered_full_minus_B"] = boot_diff(p["full"], p["B"], y, w, blocks)
        wc = {}
        for k, v in p.items():
            a, _ = within_cluster_auc(v, y, w, clusters)
            wc[k] = a
        out["within_weather_cell_auc"] = wc
        out["distinct_predictions"] = {k: int(np.unique(v).size) for k, v in p.items()}
        out["B_equals_A"] = bool(np.array_equal(p["A"], p["B"]))
    (EVID / f"auc_{run}.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
