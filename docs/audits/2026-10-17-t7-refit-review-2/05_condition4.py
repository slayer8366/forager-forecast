"""Q5: condition 4 recomputed with my own scoring and pair-matrix bootstrap, plus sensitivity checks.
Geometry helpers (lon/lat -> grid, the PNW window, cell centres) are the repository's; the circle mean,
the matched draw, the AUC and the block bootstrap are written here."""
import sys, json, csv, math, collections
sys.path.insert(0, "."); sys.path.insert(0, "../../../src")
import numpy as np, rasterio
from rv2lib import *
from forager_forecast.grid import lonlat_transformer, CELL_SIZE_M
from forager_forecast.pnw import pnw_window

WORK = "/mnt/work/Zynergy/forecast-data/t7/refit/"
tab = np.load(WORK + "table.npz"); meta = json.load(open(WORK + "table_meta.json"))
cell_id = tab["cell_id"]; level3 = tab["level3"]
road = tab["access"][:, meta["access_bands"].index("dist_road_m")].astype(np.float64)
inside = np.load(WORK + "inside_all.npy")
feat = tab["features"]; fnames = meta["features"]
win = pnw_window()
raster = rasterio.open(WORK + "outputs/relative_habitat_pnw.tif").read(1)
print("raster", raster.shape, "finite", int(np.isfinite(raster).sum()), "inside", int(inside.sum()))
rows = list(csv.DictReader(open("/mnt/work/Zynergy/forecast-data/t7/specimens/specimens_kept.csv")))
lon = np.array([float(r["lon"]) for r in rows]); lat = np.array([float(r["lat"]) for r in rows])
sx, sy = lonlat_transformer().transform(lon, lat)
scell = np.array([int(r["cell_id"]) for r in rows]); srad = np.array([float(r["uncertainty_m"]) for r in rows])
sint = np.array([r["interior"] == "True" for r in rows]); syear = np.array([int(r["year"]) if r["year"] else 0 for r in rows])
sds = np.array([r["dataset_key"] for r in rows])
BANDS = np.array([50., 100., 250., 500., 1000., 2000., 5000.])
band = lambda d: np.searchsorted(BANDS, d, side="right")

def cx_cy(ids):
    ids = np.asarray(ids).astype(np.int64)  # table cell ids are unsigned; the offset subtraction would wrap
    col = (ids & 0xFFFF) - (1 << 15); rw = (ids >> 16) - (1 << 15)
    return (col + 0.5) * CELL_SIZE_M, (rw + 0.5) * CELL_SIZE_M

def circle_mean(x, y, r, ras=raster):
    r0 = math.floor((win.top - y) / CELL_SIZE_M); c0 = math.floor((x - win.left) / CELL_SIZE_M)
    k = math.ceil(r / CELL_SIZE_M) + 1
    rr, cc = np.meshgrid(np.arange(max(r0 - k, 0), min(r0 + k + 1, ras.shape[0])),
                         np.arange(max(c0 - k, 0), min(c0 + k + 1, ras.shape[1])), indexing="ij")
    px = win.left + (cc + .5) * CELL_SIZE_M; py = win.top - (rr + .5) * CELL_SIZE_M
    take = ((px - x) ** 2 + (py - y) ** 2 <= r * r) | ((rr == r0) & (cc == c0))
    v = ras[rr[take], cc[take]].astype(np.float64); v = v[np.isfinite(v)]
    return v.mean() if len(v) else np.nan

pos = np.clip(np.searchsorted(cell_id, scell), 0, len(cell_id) - 1)
ok = (cell_id[pos] == scell) & inside[pos]
print("kept", len(rows), "scorable", int(ok.sum()), "not scorable", int((~ok).sum()))
pool = cell_id[inside]; pool_band = band(road[inside])

def draw(sband, srad_, per=10, seed=SEED):
    rng = np.random.default_rng(seed); cells, rad, owner = [], [], []
    for b in np.unique(sband):
        which = np.nonzero(sband == b)[0]
        cand = pool[pool_band == b]
        pick = rng.choice(cand, size=per * len(which), replace=False)
        cells.append(pick); rad.append(np.repeat(srad_[which], per)); owner.append(np.repeat(which, per))
    return np.concatenate(cells), np.concatenate(rad), np.concatenate(owner)

def run(keep, label, weights_by_cell=False, per=10, score="circle"):
    idx = np.flatnonzero(keep)
    sb = band(road[pos[idx]])
    bc, br, bo = draw(sb, srad[idx], per)
    bx, by = cx_cy(bc)
    if score == "circle":
        ss = np.array([circle_mean(sx[i], sy[i], srad[i]) for i in idx])
        bs = np.array([circle_mean(x, y, r) for x, y, r in zip(bx, by, br)])
    else:  # own cell only, score = a table feature or the raster's own cell
        j = fnames.index(score) if score in fnames else None
        sp = pos[idx]; bp = np.searchsorted(cell_id, bc)
        if j is None:
            vals = np.full(len(cell_id), np.nan); vals[inside] = raster_flat
            ss, bs = vals[sp], vals[bp]
        else:
            ss, bs = feat[sp, j].astype(float), feat[bp, j].astype(float)
    if not (np.isfinite(ss).all() and np.isfinite(bs).all()):
        print("DEBUG nan spec", int((~np.isfinite(ss)).sum()), "nan bg", int((~np.isfinite(bs)).sum()), "of", len(ss), len(bs), "win", win.left, win.top, "ex", sx[idx][:2], sy[idx][:2], bx[:2], by[:2]); raise SystemExit(1)
    s = np.concatenate([ss, bs]); yv = np.r_[np.ones(len(ss)), np.zeros(len(bs))]
    blk = np.concatenate([level3[pos[idx]], level3[np.searchsorted(cell_id, bc)]])
    if weights_by_cell:
        cnt = collections.Counter(scell[idx]); ws = np.array([1.0 / cnt[scell[i]] for i in idx])
        w = np.r_[ws, np.repeat(ws, 1)[bo] / per]
    else:
        w = np.ones(len(s))
    ub, bi = np.unique(blk, return_inverse=True); nb = len(ub)
    C, M = pair_matrices(s, yv, w, bi, nb)
    T = draws(nb)
    pt = C.sum() / M.sum() - 0.5
    d = np.einsum("ri,ij,rj->r", T, C, T) / np.einsum("ri,ij,rj->r", T, M, T) - 0.5
    lo, hi = np.percentile(d, [2.5, 97.5])
    # pairs inside one level III block only (a regional-composition control; the reported figure uses box-wide pairs)
    dC, dM = np.diag(C), np.diag(M)
    wb = dC.sum() / dM.sum() - 0.5
    tt = T ** 2
    dwb = (tt @ dC) / (tt @ dM) - 0.5
    wlo, whi = np.percentile(dwb, [2.5, 97.5])
    res = dict(within_block_point=float(wb), within_block_lo=float(wlo), within_block_hi=float(whi), label=label, n_spec=int(len(idx)), n_bg=int(len(bc)), point=float(pt), lo=float(lo), hi=float(hi),
               blocks=nb, eff_cells=int(len(set(scell[idx]))))
    print(f"{label:55s} n={len(idx):5d} cells={res['eff_cells']:5d} AUC-0.5 {pt:+.5f} [{lo:+.5f},{hi:+.5f}] blocks={nb}  | within-block pairs only {wb:+.5f} [{wlo:+.5f},{whi:+.5f}]", flush=True)
    return res

R = {}
R["whole"] = run(ok, "V0 whole box (reported: +0.19615 [+0.06645,+0.28547])")
R["interior"] = run(ok & sint, "V0 interior (reported: +0.10333 [-0.15708,+0.23985])")
R["cellweighted"] = run(ok, "V1 each 250 m cell counts once (weights 1/n)", weights_by_cell=True)
cnt = collections.Counter(scell)
R["capped25"] = run(ok & np.array([cnt[c] <= 25 for c in scell]), "V2 drop cells holding >25 records")
big = sds == collections.Counter(sds).most_common(1)[0][0]
R["no_main_herbarium"] = run(ok & ~big, "V3 without the largest dataset")
R["main_herbarium_only"] = run(ok & big, "V3b largest dataset only")
R["from1990"] = run(ok & (syear >= 1990), "V4 year >= 1990")
R["from2000"] = run(ok & (syear >= 2000), "V4 year >= 2000")
R["before1970"] = run(ok & (syear > 0) & (syear < 1970), "V4 year < 1970")
R["fr_2000_nomain"] = run(ok & (syear >= 2000) & ~big, "V4 year>=2000 and not largest dataset")
R["ownocell_map"] = None
# single-feature comparators at the own cell (no circle), same draw
raster_flat = np.load(WORK + "scores_all.npy")[inside].astype(np.float64)
R["own_cell_map"] = run(ok, "own-cell score = map", score="map")
for f in ("total_cover_pct", "share_conifer", "ph_mean_0_30cm"):
    R["own_cell_" + f] = run(ok, f"own-cell score = {f}", score=f)
json.dump(R, open("05_results.json", "w"), indent=1)
