"""Reviewer's own reconstruction of the T7 training rows (D18 review, 2026-10-16).

Written from the rules (D133, D144 rule 4, D139), not by importing t7_fit.Data. Inputs are the
fit's own work files on /mnt/work (read only) and T6's stored surface's cell list. The only project
code used is none: weights, pool, draw, ordering and AUC are all written here.

Row order matches t7_fit.Data: entering presences in file order, then the background ids sorted.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

WORK = Path("/mnt/work/Zynergy/forecast-data/t7/fit")
V9 = Path("/mnt/work/Zynergy/forecast-data/t7/v9")
T6 = Path.home() / "Zynergy/forager-forecast-t6/data/t6"
SEED = 20260918
FIT_REPORT = Path(__file__).resolve().parents[1] / "2026-10-16-t7-fit" / "fit_report.json"


def key(lat_t, lon_t):
    # same packing as the table's wkey: (lat+1000)*10000 + (lon+2000)
    return (np.asarray(lat_t, np.int64) + 1000) * 10_000 + (np.asarray(lon_t, np.int64) + 2000)


def frame_keys(track="all"):
    ks = []
    with open(T6 / track / "cell_level.csv", newline="") as f:
        for r in csv.DictReader(f):
            ks.append(int(key(int(r["lat_tenths"]), int(r["lon_tenths"]))))
    return np.unique(np.array(ks, np.int64))


def load_table(features=False):
    z = np.load(WORK / "table.npz")
    out = {k: z[k] for k in ("cell_id", "wkey", "level3")}
    if features:
        out["features"] = z["features"]
    return out


class Rows:
    def __init__(self, presence_file, track="all", min_alone=30, table=None):
        t = table if table is not None else load_table()
        cid, wkey, l3 = t["cell_id"], t["wkey"], t["level3"]
        fall = frame_keys("all")
        ftrack = fall if track == "all" else frame_keys(track)
        with open(presence_file, newline="") as f:
            rows = list(csv.DictReader(f))
        pc = np.array([int(r["cell_id"]) for r in rows], np.int64)
        pos = np.clip(np.searchsorted(cid, pc), 0, len(cid) - 1)
        elig = cid[pos] == pc
        has = elig & np.isin(wkey[pos], ftrack)
        self.n_file = len(rows)
        self.n_eligible = int(elig.sum())
        self.n_enter = int(has.sum())
        keep = np.nonzero(has)[0]
        genus = [rows[i]["genus"] for i in keep]
        year = np.array([int(rows[i]["year"]) for i in keep])
        n_by = Counter(genus)
        unit = {g: (g if n >= min_alone else "_pooled") for g, n in n_by.items()}
        n_unit = Counter(unit[g] for g in genus)
        pw = np.array([1.0 / n_unit[unit[g]] for g in genus])
        self.units_alone = sum(1 for u in n_unit if u != "_pooled")
        self.pooled = n_unit.get("_pooled", 0)
        # background: unique eligible ids whose weather cell is in the ALL frame, seed draw
        pool = np.unique(cid[np.isin(wkey, fall)].astype(np.uint32))
        self.pool = len(pool)
        pick = np.random.default_rng(SEED).choice(len(pool), size=500_000, replace=False)
        bc = np.sort(pool[pick])
        self.bg_sha = hashlib.sha256(bc.astype("<u4").tobytes()).hexdigest()
        bpos = np.searchsorted(cid, bc.astype(np.int64))
        bkeep = np.isin(wkey[bpos], ftrack)
        self.bg_dropped = int((~bkeep).sum())
        bpos = bpos[bkeep]
        bw = np.full(len(bpos), pw.sum() / len(bpos))
        idx = np.concatenate([pos[keep], bpos])
        self.idx = idx
        self.y = np.r_[np.ones(len(keep)), np.zeros(len(bpos))]
        self.w = np.r_[pw, bw]
        self.wkey = wkey[idx]
        self.block = l3[idx].astype(np.int64)
        self.year = np.r_[year, np.zeros(len(bpos), int)]
        self.genus = genus


def wauc(score, y, w):
    """Weighted AUC: P(score_pos > score_neg) + 0.5 P(tie), pairs weighted w_p * w_n.
    Implemented with a weight-of-negatives-below lookup over unique scores."""
    score = np.asarray(score, np.float64)
    u, inv = np.unique(score, return_inverse=True)
    neg = np.bincount(inv, weights=w * (y == 0), minlength=len(u))
    pos = np.bincount(inv, weights=w * (y == 1), minlength=len(u))
    below = np.concatenate([[0.0], np.cumsum(neg)[:-1]])
    return float((pos * (below + 0.5 * neg)).sum() / (pos.sum() * neg.sum()))


class Pre:
    """Unique-score inverse precomputed so resamples are cheap."""

    def __init__(self, score, y):
        self.u, self.inv = np.unique(np.asarray(score, np.float64), return_inverse=True)
        self.y = y

    def auc(self, w):
        m = len(self.u)
        neg = np.bincount(self.inv, weights=w * (self.y == 0), minlength=m)
        pos = np.bincount(self.inv, weights=w * (self.y == 1), minlength=m)
        below = np.cumsum(neg) - neg
        return float((pos * (below + 0.5 * neg)).sum() / (pos.sum() * neg.sum()))


def boot_diff(a, b, y, w, clusters, n=1000, seed=SEED):
    pa, pb = Pre(a, y), Pre(b, y)
    labels, ci = np.unique(clusters, return_inverse=True)
    k = len(labels)
    rng = np.random.default_rng(seed)
    d = np.empty(n)
    for i in range(n):
        mult = np.bincount(rng.integers(0, k, size=k), minlength=k)
        wi = w * mult[ci]
        d[i] = pa.auc(wi) - pb.auc(wi)
    point = pa.auc(w) - pb.auc(w)
    lo, hi = np.percentile(d, [2.5, 97.5])
    return point, float(lo), float(hi)


def cache(name):
    p = WORK / "cache" / f"lobo_{name}.npy"
    m = json.loads((WORK / "cache" / f"lobo_{name}.json").read_text())
    return np.load(p), m


# --- model fitting (reviewer's own call into LightGBM, parameters as model.py lgb_params) -------

EFFORT = "log_effort"
GRID = Path(__file__).resolve().parents[1] / "2026-10-15-t7-build" / "tuning_grid.json"
BASE = ["share_Pseudotsuga", "share_Tsuga", "share_Picea", "share_Abies", "share_Pinus",
        "share_Quercus", "share_conifer", "share_broadleaf", "total_cover_pct", "ph_mean_0_30cm"]
FULL = [*BASE, "share_Larix", "share_Chrysolepis", "share_Arbutus", EFFORT]
B_FEATS = [EFFORT, "conifer_cover_pct", "broadleaf_cover_pct"]


def config(cid):
    return {c_["id"]: c_ for c_ in json.loads(GRID.read_text())["configurations"]}[cid]


def params(cfg, feats, threads):
    e = feats.index(EFFORT)
    others = [i for i in range(len(feats)) if i != e]
    p = {"objective": "binary", "verbose": -1, "seed": SEED, "deterministic": True,
         "force_row_wise": True, "num_threads": threads, "bagging_seed": SEED,
         "feature_fraction_seed": SEED,
         "monotone_constraints": [1 if i == e else 0 for i in range(len(feats))],
         "interaction_constraints": [others, [e]] if others else [[e]]}
    p.update({k: v for k, v in cfg.items() if k not in ("id", "num_boost_round")})
    return p


def fit(cfg, feats, x, y, w, threads=4, rescale=True):
    import lightgbm as lgb
    w = np.asarray(w, np.float64)
    if rescale:
        w = w * (len(w) / w.sum())
    d = lgb.Dataset(np.asarray(x), np.asarray(y), weight=w, feature_name=list(feats),
                    free_raw_data=True)
    return lgb.train(params(cfg, feats, threads), d, num_boost_round=cfg["num_boost_round"])


def effort_by_key(track="all", keys=None):
    """log of T6's static effort per weather-cell key (project EffortSurface: an input)."""
    from forager_forecast.cells import Cell
    from forager_forecast.effort import EffortSurface
    from forager_forecast.t7.keying import static_effort
    keys = np.unique(keys)
    cells = [Cell(int(k // 10_000 - 1000), int(k % 10_000 - 2000)) for k in keys]
    eff = static_effort(EffortSurface.read(T6 / track), cells)
    return {int(k): float(np.log(eff.total[cl])) for k, cl in zip(keys, cells) if cl in eff.total}


def design(rows, feats, table_features, names, le):
    f = table_features[rows.idx].astype(np.float64)
    cols = {n: f[:, i] for i, n in enumerate(names)}
    cols[EFFORT] = np.array([le[int(k)] for k in rows.wkey])
    cols["conifer_cover_pct"] = cols["share_conifer"] * cols["total_cover_pct"]
    cols["broadleaf_cover_pct"] = cols["share_broadleaf"] * cols["total_cover_pct"]
    return np.column_stack([cols[c_] for c_ in feats])
