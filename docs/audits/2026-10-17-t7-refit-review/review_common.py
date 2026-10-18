"""Review 1 of the T7 re-fit (Sorrel Tally): the rows, weights and groups rebuilt from the data
files, and the review's own AUC and resampling code. Nothing here imports the coder's t7 package
(only the grid/keying constants are re-derived below), so a match is two implementations agreeing.

Reads only: the re-fit work dir (table.npz, cache), V9/V9C presence files, T6's cell_level.csv.
Writes nothing.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

WORK = Path("/mnt/work/Zynergy/forecast-data/t7/refit")
V9 = Path("/mnt/work/Zynergy/forecast-data/t7/v9")
V9C = Path("/mnt/work/Zynergy/forecast-data/t7/v9c")
T6_ALL = Path.home() / "Zynergy/forager-forecast-t6/data/t6/all/cell_level.csv"
T6_CC = Path.home() / "Zynergy/forager-forecast-t6/data/t6/cc/cell_level.csv"
SEED = 20260918
RESAMPLES = 1000
BACKGROUND_SIZE = 500_000
MIN_PRESENCES_PER_GENUS = 30

# weather-cell key packing, as t7/keying.py documents it: (lat+1000)*10000 + (lon+2000)
def pack(lat_tenths, lon_tenths):
    lat = np.asarray(lat_tenths, dtype=np.int64)
    lon = np.asarray(lon_tenths, dtype=np.int64)
    return (lat + 1000) * 10_000 + (lon + 2000)


def frame_keys(path: Path = T6_ALL) -> np.ndarray:
    keys = set()
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            keys.add(int(pack(int(row["lat_tenths"]), int(row["lon_tenths"]))))
    return np.array(sorted(keys), dtype=np.int64)


class Table:
    def __init__(self, work: Path = WORK) -> None:
        z = np.load(work / "table.npz")
        self.cell_id = z["cell_id"]
        self.wkey = z["wkey"]
        self.level3 = z["level3"].astype(np.int64)
        self.access = z["access"]
        self.meta = json.loads((work / "table_meta.json").read_text())
        self.access_bands = list(self.meta["access_bands"])
        self._features = None
        self._work = work

    @property
    def features(self):
        if self._features is None:
            self._features = np.load(self._work / "table.npz")["features"]
        return self._features

    def road(self) -> np.ndarray:
        return self.access[:, self.access_bands.index("dist_road_m")].astype(np.float64)


def draw_background(pool_cells: np.ndarray, n: int = BACKGROUND_SIZE, seed: int = SEED):
    pool = np.unique(pool_cells.astype(np.uint32))
    picks = np.random.default_rng(seed).choice(len(pool), size=n, replace=False)
    return np.sort(pool[picks])


def rows_for(table: Table, presence_file: Path, track_frame: Path = T6_ALL) -> dict:
    """The training rows as the fit built them: presences (eligible, in the effort frame) in file
    order, then the background draw (eligible cells in the all-licence frame, seed 20260918,
    sorted), each with its weight, level III block and weather cell."""
    frame_all = frame_keys(T6_ALL)
    frame_track = frame_all if track_frame == T6_ALL else frame_keys(track_frame)
    with open(presence_file, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    p_cell = np.array([int(r["cell_id"]) for r in rows], dtype=np.int64)
    pos = np.clip(np.searchsorted(table.cell_id, p_cell), 0, len(table.cell_id) - 1)
    eligible = table.cell_id[pos] == p_cell
    in_frame = np.isin(table.wkey[pos], frame_track)
    keep = eligible & in_frame
    kept_rows = [r for r, k in zip(rows, keep, strict=True) if k]
    genus = [r["genus"] for r in kept_rows]
    per_genus = Counter(genus)
    unit_of = {g: (g if n >= MIN_PRESENCES_PER_GENUS else "(pooled)") for g, n in per_genus.items()}
    per_unit = Counter()
    for g, n in per_genus.items():
        per_unit[unit_of[g]] += n
    pw = np.array([1.0 / per_unit[unit_of[g]] for g in genus])
    pi = pos[keep]

    bg_pool_sel = np.isin(table.wkey, frame_all)
    bcells = draw_background(table.cell_id[bg_pool_sel])
    bi = np.searchsorted(table.cell_id, bcells)
    assert np.array_equal(table.cell_id[bi], bcells)
    b_has = np.isin(table.wkey[bi], frame_track)
    bi = bi[b_has]
    bw = np.full(len(bi), pw.sum() / len(bi))
    idx = np.concatenate([pi, bi])
    return {
        "idx": idx,
        "y": np.concatenate([np.ones(len(pi)), np.zeros(len(bi))]),
        "w": np.concatenate([pw, bw]),
        "blocks": table.level3[idx],
        "clusters": table.wkey[idx],
        "year": np.array([int(r["year"]) for r in kept_rows]),
        "genus": genus,
        "background_sha256": hashlib.sha256(bcells.astype("<u4").tobytes()).hexdigest(),
        "background_pool": int(bg_pool_sel.sum()),
        "n_presences": int(len(pi)),
        "n_background": int(len(bi)),
        "presences_in_file": len(rows),
        "eligible_not_in_frame": int((eligible & ~in_frame).sum()),
    }


def cached(key: str, n: int) -> np.ndarray:
    p = np.load(WORK / "cache" / f"lobo_{key}.npy")
    meta = json.loads((WORK / "cache" / f"lobo_{key}.json").read_text())
    if len(p) != n or meta["n"] != n:
        raise SystemExit(f"cache {key}: {len(p)} rows, expected {n}")
    return p


# --- the review's own AUC ----------------------------------------------------------------------


class Ranked:
    """Scores sorted once with their tie groups, so an AUC under new row weights is one pass."""

    def __init__(self, scores, y):
        s = np.asarray(scores, dtype=np.float64)
        self.order = np.argsort(s, kind="mergesort")
        s = s[self.order]
        new = np.r_[True, s[1:] != s[:-1]]
        self.g = np.cumsum(new) - 1
        self.ng = int(self.g[-1]) + 1 if len(s) else 0
        self.pos = (np.asarray(y) == 1)[self.order]

    def auc(self, w) -> float:
        """Weighted share of (presence, background) pairs ranked correctly, ties half."""
        w = np.asarray(w, dtype=np.float64)[self.order]
        wp = np.bincount(self.g, weights=np.where(self.pos, w, 0.0), minlength=self.ng)
        wn = np.bincount(self.g, weights=np.where(self.pos, 0.0, w), minlength=self.ng)
        below = np.cumsum(wn) - wn
        return float((wp * (below + 0.5 * wn)).sum() / (wp.sum() * wn.sum()))


def weighted_auc(scores, y, w) -> float:
    return Ranked(scores, y).auc(w)


def weighted_auc_bruteforce(scores, y, w) -> float:
    """O(n^2) pair count, for checking weighted_auc on small samples."""
    s = np.asarray(scores, dtype=np.float64)
    y = np.asarray(y) == 1
    w = np.asarray(w, dtype=np.float64)
    sp, wp = s[y], w[y]
    sn, wn = s[~y], w[~y]
    d = sp[:, None] - sn[None, :]
    c = (d > 0) + 0.5 * (d == 0)
    return float((wp[:, None] * wn[None, :] * c).sum() / (wp.sum() * wn.sum()))


def _draws(units, resamples, seed):
    _, index = np.unique(np.asarray(units), return_inverse=True)
    n = int(index.max()) + 1
    rng = np.random.default_rng(seed)
    for _ in range(resamples):
        yield np.bincount(rng.integers(0, n, size=n), minlength=n)[index]


def interval(values, level=0.95):
    tail = (1 - level) / 2 * 100
    lo, hi = np.percentile(values, [tail, 100 - tail])
    return float(lo), float(hi)


def auc_difference(a, b, y, w, units, resamples=RESAMPLES, seed=SEED) -> dict:
    """AUC(a) - AUC(b); interval over whole-unit resamples, rows weighted by their unit's draw
    count (one draw per resample, both models on it)."""
    ra, rb = Ranked(a, y), Ranked(b, y)
    w = np.asarray(w, dtype=np.float64)
    point = ra.auc(w) - rb.auc(w)
    diffs = np.array([ra.auc(w * t) - rb.auc(w * t) for t in _draws(units, resamples, seed)])
    lo, hi = interval(diffs)
    return {"point": point, "low": lo, "high": hi, "resamples": resamples, "above_zero": lo > 0}


class WithinRanked:
    """Scores sorted once by cluster then score, so the within-cluster concordant pair weight
    (ties half) and the pair weight per cluster, under new row weights, are one pass."""

    def __init__(self, scores, y, clusters):
        s = np.asarray(scores, dtype=np.float64)
        _, c = np.unique(np.asarray(clusters), return_inverse=True)
        self.c = c
        self.n = int(c.max()) + 1
        self.pos_rows = np.asarray(y) == 1
        self.order = np.lexsort((s, c))
        s, cs = s[self.order], c[self.order]
        self.pos = self.pos_rows[self.order]
        new = np.r_[True, (s[1:] != s[:-1]) | (cs[1:] != cs[:-1])]
        self.g = np.cumsum(new) - 1
        self.ng = int(self.g[-1]) + 1
        self.gc = cs[new]
        self.first = np.r_[True, self.gc[1:] != self.gc[:-1]]
        self.first_of = np.cumsum(self.first) - 1

    def parts(self, w):
        w0 = np.asarray(w, dtype=np.float64)
        w = w0[self.order]
        wp = np.bincount(self.g, weights=np.where(self.pos, w, 0.0), minlength=self.ng)
        wn = np.bincount(self.g, weights=np.where(self.pos, 0.0, w), minlength=self.ng)
        cum = np.cumsum(wn)
        start = (cum - wn)[self.first][self.first_of]
        below = cum - wn - start
        concordant = np.bincount(self.gc, weights=wp * (below + 0.5 * wn), minlength=self.n)
        p0 = self.pos_rows
        mass = (np.bincount(self.c, weights=np.where(p0, w0, 0.0), minlength=self.n)
                * np.bincount(self.c, weights=np.where(p0, 0.0, w0), minlength=self.n))
        return concordant, mass


def within_cluster_parts(scores, y, w, clusters):
    """Per cluster: concordant pair weight (ties half) and pair weight, over pairs inside it."""
    return WithinRanked(scores, y, clusters).parts(w)


def within_cluster_auc(scores, y, w, clusters) -> float:
    con, mass = within_cluster_parts(scores, y, w, clusters)
    return float(con.sum() / mass.sum())


def within_cluster_difference(a, b, y, w, clusters, resample_by, resamples=RESAMPLES,
                              seed=SEED) -> dict:
    """Within-cluster AUC(a) - AUC(b) over pairs inside one cluster; interval from resampling
    ``resample_by`` units (level III blocks), each row's weight times its unit's draw count
    (D145 as amended). Pairs straddling two units weigh the product of the draw counts."""
    w = np.asarray(w, dtype=np.float64)
    ra, rb = WithinRanked(a, y, clusters), WithinRanked(b, y, clusters)

    def stat(wi):
        ca, mass = ra.parts(wi)
        cb, _ = rb.parts(wi)
        return (ca - cb).sum() / mass.sum()

    point = stat(w)
    diffs = np.array([stat(w * t) for t in _draws(resample_by, resamples, seed)])
    lo, hi = interval(diffs)
    return {"point": float(point), "low": lo, "high": hi, "resamples": resamples,
            "above_zero": lo > 0}


def within_cluster_difference_cluster_resampled(a, b, y, w, clusters, resamples=RESAMPLES,
                                                seed=SEED) -> dict:
    """The weather-cell-resampled version the log printed (not D145's)."""
    ca, mass = within_cluster_parts(a, y, w, clusters)
    cb, _ = within_cluster_parts(b, y, w, clusters)
    n = len(mass)
    rng = np.random.default_rng(seed)
    out = np.empty(resamples)
    for i in range(resamples):
        t = np.bincount(rng.integers(0, n, size=n), minlength=n)
        out[i] = (t * (ca - cb)).sum() / (t * mass).sum()
    lo, hi = interval(out)
    return {"point": float((ca - cb).sum() / mass.sum()), "low": lo, "high": hi,
            "resamples": resamples, "above_zero": lo > 0}


def contrast(g1: dict, g2: dict, resamples=RESAMPLES, seed=SEED) -> dict:
    """(AUC full - AUC A) of group 1 minus the same of group 2, one block draw for both groups
    (units: the union of both groups' blocks)."""
    units = np.unique(np.concatenate([g1["blocks"], g2["blocks"]]))
    n = len(units)
    u1 = np.searchsorted(units, g1["blocks"])
    u2 = np.searchsorted(units, g2["blocks"])

    ranked = {id(g): (Ranked(g["full"], g["y"]), Ranked(g["a"], g["y"])) for g in (g1, g2)}

    def gain(g, wi):
        rf, ra = ranked[id(g)]
        return rf.auc(wi) - ra.auc(wi)

    point = gain(g1, g1["w"]) - gain(g2, g2["w"])
    rng = np.random.default_rng(seed)
    out = np.empty(resamples)
    for i in range(resamples):
        t = np.bincount(rng.integers(0, n, size=n), minlength=n)
        out[i] = gain(g1, g1["w"] * t[u1]) - gain(g2, g2["w"] * t[u2])
    lo, hi = interval(out)
    return {"point": float(point), "low": lo, "high": hi, "resamples": resamples,
            "above_zero": lo > 0}


def fmt(d: dict) -> str:
    return f"{d['point']:+.5f} [{d['low']:+.5f}, {d['high']:+.5f}]"
