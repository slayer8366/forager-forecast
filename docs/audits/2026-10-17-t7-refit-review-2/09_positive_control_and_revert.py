"""(a) positive control: the pair-matrix AUC and its block-resampled value against a brute-force O(n^2)
computation with explicit weights on a subsample with forced ties; (b) revert check on the within-cell
restriction (run by 09_revert_runner.sh, which saves a copy of rv2lib.py first, never uses git)."""
import sys
sys.path.insert(0, ".")
import numpy as np
import rv2lib as L

def brute(s, y, w, rowmult=None, cell=None):
    wt = w if rowmult is None else w * rowmult
    num = den = 0.0
    P = np.flatnonzero(y == 1); N = np.flatnonzero(y == 0)
    for p in P:
        for n in N:
            if cell is not None and cell[p] != cell[n]:
                continue
            pw = wt[p] * wt[n]
            den += pw
            num += pw * ((s[p] > s[n]) + 0.5 * (s[p] == s[n]))
    return num / den

rng = np.random.default_rng(7)
n = 600
y = (rng.random(n) < 0.3).astype(int); s = np.round(rng.normal(size=n) + y * 0.5, 1)  # rounding forces ties
w = rng.random(n) + 0.1; blk = rng.integers(0, 5, size=n); cell = rng.integers(0, 40, size=n)
ub, bi = np.unique(blk, return_inverse=True); nb = len(ub)
t = np.array([2., 0., 1., 3., 1.])  # one block draw
C, M = L.pair_matrices(s, y, w, bi, nb)
print("pooled, no draw   :", L.auc_point(C, M), brute(s, y, w))
print("pooled, with draw :", float(t @ C @ t / (t @ M @ t)), brute(s, y, w, rowmult=t[bi]))
Cw, Mw = L.pair_matrices(s, y, w, bi, nb, cell=cell)
print("within-cell, no draw :", L.auc_point(Cw, Mw), brute(s, y, w, cell=cell))
print("within-cell, draw    :", float(t @ Cw @ t / (t @ Mw @ t)), brute(s, y, w, rowmult=t[bi], cell=cell))
assert np.isclose(L.auc_point(C, M), brute(s, y, w)) and np.isclose(t @ C @ t / (t @ M @ t), brute(s, y, w, rowmult=t[bi]))
assert np.isclose(L.auc_point(Cw, Mw), brute(s, y, w, cell=cell)) and np.isclose(t @ Cw @ t / (t @ Mw @ t), brute(s, y, w, rowmult=t[bi], cell=cell))
print("POSITIVE CONTROL OK")
# (b) the figure the revert is meant to move: the real within-cell full-minus-A point
d = L.load_main(); ub, bi = np.unique(d["blocks"], return_inverse=True); nb = len(ub)
Cf, Mf = L.pair_matrices(L.pred("full"), d["y"], d["w"], bi, nb, cell=d["clusters"])
Ca, _ = L.pair_matrices(L.pred("A: e"), d["y"], d["w"], bi, nb, cell=d["clusters"])
print("REAL within-cell full AUC %.5f A AUC %.5f diff %.5f pairmass %.3e" % (Cf.sum()/Mf.sum(), Ca.sum()/Mf.sum(), (Cf.sum()-Ca.sum())/Mf.sum(), Mf.sum()))
