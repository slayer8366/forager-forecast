"""Positive control for old_vs_new_tiles.py: the same comparison between an old tile and a
different tile's new file must report differences. Read only; prints one line."""

import importlib.util
import sys
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("m", Path(__file__).with_name("old_vs_new_tiles.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
old = m.bands(m.SUP[0] / "trees_256_-30_20.tif")["share_Pseudotsuga"]
new = m.bands(m.T6B / "tiles/trees/trees_256_-31_20.tif")["share_Pseudotsuga"]
same = (old == new) | (np.isnan(old) & np.isnan(new))
print({"old": "256_-30_20", "new": "256_-31_20", "cells_differ": int((~same).sum())})
sys.exit(0)
