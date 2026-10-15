"""As old_vs_new_tiles.py, for the 13 US-half files rebuilt on 2026-10-15 (D119). Read only."""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("m", Path(__file__).with_name("old_vs_new_tiles.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
out = {}
cur = m.T6B / "tiles/trees_us_half"
for sup in sorted(m.T6B.glob("superseded/20261015T*-trees/tiles/trees_us_half")):
    for old in sorted(sup.glob("trees*_us_half_256_*.tif")):
        new = cur / old.name
        if not new.exists():
            out[f"{sup.parent.parent.name}/{old.name}"] = "no current file (whole tile replaces it)"
            continue
        ob, nb = m.bands(old), m.bands(new)
        d = {}
        for k, a in ob.items():
            b = nb[k]
            same = (a == b) | (np.isnan(a) & np.isnan(b)) if a.dtype.kind == "f" else a == b
            if (~same).sum():
                d[k] = int((~same).sum())
        out[f"{sup.parent.parent.name}/{old.name}"] = d or "shared bands identical"
Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n")
