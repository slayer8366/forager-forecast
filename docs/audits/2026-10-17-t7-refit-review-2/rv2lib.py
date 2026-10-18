"""Review 2 (Sorrel Tally), own code. Pair-count matrices by level III block.

A pooled weighted AUC is  sum_{p,n} w_p w_n [s_p>s_n + .5 s_p==s_n] / (sum w_p * sum w_n).
Resampling blocks with replacement and multiplying every row's weight by its block's draw count t
multiplies each pair's weight by t_block(p)*t_block(n). So with C[i,j] = concordant pair weight for
presences in block i and background in block j, and M[i,j] = (presence weight in i)(background
weight in j), every resampled AUC is  t'Ct / t'Mt.  The same holds within one weather cell if C and
M are restricted to pairs sharing a cell. Draws follow the fit's protocol: rng=default_rng(seed);
per resample rng.integers(0,n,size=n), n = number of distinct blocks in the table (sorted).
"""
import json
import numpy as np

SEED = 20260918
RES = 1000
CACHE = "/mnt/work/Zynergy/forecast-data/t7/refit/cache/"


def load_main():
    d = np.load("/mnt/work/Zynergy/rv2-scratch/main.npz")
    return {k: d[k] for k in d.files}


def pred(key):
    return np.load(CACHE + f"lobo_{key}.npy")


def _blocks_index(blocks):
    ub, bi = np.unique(blocks, return_inverse=True)
    return ub, bi


def pair_matrices(s, y, w, bi, nb, cell=None):
    """C, M (nb x nb). cell=None: all pairs; else only pairs in the same cell."""
    pos = y == 1
    sp, wp, bp = s[pos], w[pos], bi[pos]
    C = np.zeros((nb, nb))
    M = np.zeros((nb, nb))
    if cell is None:
        for j in range(nb):
            m = (~pos) & (bi == j)
            if not m.any():
                continue
            sq, wq = s[m], w[m]
            o = np.argsort(sq, kind="mergesort")
            sq, wq = sq[o], wq[o]
            cum = np.r_[0.0, np.cumsum(wq)]
            lo = np.searchsorted(sq, sp, "left")
            hi = np.searchsorted(sq, sp, "right")
            below = cum[lo]
            tie = cum[hi] - cum[lo]
            val = wp * (below + 0.5 * tie)
            C[:, j] = np.bincount(bp, weights=val, minlength=nb)
            M[:, j] = np.bincount(bp, weights=wp, minlength=nb) * wq.sum()
        return C, M
    # within one cell
    cp, cq = cell[pos], cell[~pos]
    sq_all, wq_all, bq_all = s[~pos], w[~pos], bi[~pos]
    oq = np.argsort(cq, kind="mergesort")
    cq_s, sq_s, wq_s, bq_s = cq[oq], sq_all[oq], wq_all[oq], bq_all[oq]
    op = np.argsort(cp, kind="mergesort")
    cp_s, sp_s, wp_s, bp_s = cp[op], sp[op], wp[op], bp[op]
    cells, pstart = np.unique(cp_s, return_index=True)
    pend = np.r_[pstart[1:], len(cp_s)]
    qlo = np.searchsorted(cq_s, cells, "left")
    qhi = np.searchsorted(cq_s, cells, "right")
    flat, cw, mw = [], [], []
    for k in range(len(cells)):
        a, b = qlo[k], qhi[k]
        if a == b:
            continue
        ps, pw, pb = sp_s[pstart[k]:pend[k]], wp_s[pstart[k]:pend[k]], bp_s[pstart[k]:pend[k]]
        qs, qw, qb = sq_s[a:b], wq_s[a:b], bq_s[a:b]
        S = (ps[:, None] > qs[None, :]) + 0.5 * (ps[:, None] == qs[None, :])
        W = pw[:, None] * qw[None, :]
        F = pb[:, None] * nb + qb[None, :]
        flat.append(F.ravel()); cw.append((S * W).ravel()); mw.append(W.ravel())
    flat = np.concatenate(flat)
    C = np.bincount(flat, weights=np.concatenate(cw), minlength=nb * nb).reshape(nb, nb)
    M = np.bincount(flat, weights=np.concatenate(mw), minlength=nb * nb).reshape(nb, nb)
    return C, M


def draws(nb, res=RES, seed=SEED):
    rng = np.random.default_rng(seed)
    return np.array([np.bincount(rng.integers(0, nb, size=nb), minlength=nb) for _ in range(res)],
                    dtype=np.float64)


def stat(C, M, T):
    """AUC for each draw row of T (res x nb)."""
    return np.einsum("ri,ij,rj->r", T, C, T) / np.einsum("ri,ij,rj->r", T, M, T)


def diff_ci(Ca, Cb, M, T):
    """(point, lo, hi) for AUC(a)-AUC(b) with a shared pair-weight matrix M."""
    one = np.ones(M.shape[0])
    point = (one @ Ca @ one - one @ Cb @ one) / (one @ M @ one)
    d = np.einsum("ri,ij,rj->r", T, Ca - Cb, T) / np.einsum("ri,ij,rj->r", T, M, T)
    lo, hi = np.percentile(d, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def auc_point(C, M):
    return float(C.sum() / M.sum())
