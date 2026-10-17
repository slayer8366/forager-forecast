"""Read-only probe: do weather cells straddle level III blocks in the main fit's table, and how
much within-cell pair weight sits in pairs whose presence and background lie in different blocks."""

import sys
from pathlib import Path

import numpy as np

REPO = Path(sys.argv[1])
sys.path.insert(0, str(REPO / "scripts"))
import t7_fit as tf  # noqa: E402

d = tf.Data(Path("/mnt/work/Zynergy/forecast-data/t7/fit"), tf.V9 / "presences_main.csv")
c, b, y, w = d.clusters, d.blocks, d.y, d.w
pos = y == 1
# pair mass per (cell) and per (cell, block) for same-block pairs
_, ci = np.unique(c, return_inverse=True)
nC = ci.max() + 1
mass_cell = np.bincount(ci, np.where(pos, w, 0), nC) * np.bincount(ci, np.where(pos, 0, w), nC)
key = ci.astype(np.int64) * 10000 + b
_, ki = np.unique(key, return_inverse=True)
nK = ki.max() + 1
mass_cb = np.bincount(ki, np.where(pos, w, 0), nK) * np.bincount(ki, np.where(pos, 0, w), nK)
nblocks = np.array([len(np.unique(b[ci == i])) for i in np.flatnonzero(mass_cell > 0)])
print("cells with pairs:", int((mass_cell > 0).sum()))
print("of those spanning >1 block:", int((nblocks > 1).sum()))
print("pair mass total:", mass_cell.sum(), "same-block share:", mass_cb.sum() / mass_cell.sum())
print("blocks with any pair:", len(np.unique(b[np.isin(ci, np.flatnonzero(mass_cell > 0))])))
