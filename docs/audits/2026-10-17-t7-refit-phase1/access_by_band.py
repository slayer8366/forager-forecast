"""Evidence for the open ruling on the access band's monotone direction (dispatch 2026-10-17-T7R,
Phase 1 item 1, "Open, for your report"). Descriptive only: no model is fitted.

For each group's training rows as the re-fit builds them (``t7_fit.Data`` on the re-fit's table,
the road band), the weighted share of presences and of background in each road-distance band, and
their ratio. A ratio that falls with distance is what a falling constraint (-1) would allow; a
ratio that rises anywhere is where a -1 constraint would bind; within one weather cell the same
table is split by whether the cell's presences sit nearer roads than its background.

Usage: python access_by_band.py <work dir> <out json>
"""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
EDGES = [0, 50, 100, 250, 500, 1000, 2000, 5000, np.inf]


def fit_module():
    spec = importlib.util.spec_from_file_location("t7_fit", REPO / "scripts" / "t7_fit.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def by_band(d, md):
    a = d.cols([md.ACCESS])[:, 0]
    pos, w = d.y == 1, d.w
    rows = []
    for lo, hi in zip(EDGES[:-1], EDGES[1:], strict=True):
        sel = (a >= lo) & (a < hi)
        p = float(w[pos & sel].sum() / w[pos].sum())
        b = float(w[~pos & sel].sum() / w[~pos].sum())
        rows.append({"band_m": [lo, None if np.isinf(hi) else hi],
                     "presences": int((pos & sel).sum()), "background": int((~pos & sel).sum()),
                     "presence_weight_share": p, "background_weight_share": b,
                     "ratio": (p / b) if b > 0 else None})  # fmt: skip
    # within one weather cell: weighted median distance of presences against background
    keys = np.unique(d.clusters[pos])
    nearer = farther = 0
    for k in keys:
        s = d.clusters == k
        if not (s & ~pos).any():
            continue
        mp = np.median(a[s & pos])
        mb = np.median(a[s & ~pos])
        nearer += int(mp < mb)
        farther += int(mp > mb)
    return {
        "bands": rows,
        "weather_cells_with_both": nearer + farther,
        "cells_presence_median_nearer_road": nearer,
        "cells_presence_median_farther_from_road": farther,
    }


def main(work: Path, out: Path) -> None:
    t7 = fit_module()
    md = t7.md
    runs = {
        "mycorrhizal main": (t7.V9 / "presences_main.csv", "all"),
        "saprotroph main": (t7.V9C / "presences_saprotroph_main.csv", "all"),
        "comparison group (Laetiporus)": (t7.V9 / "presences_comparison.csv", "all"),
    }
    result = {"note": "descriptive; no model fitted; road band dist_road_m; weights as fitted"}
    for name, (path, track) in runs.items():
        d = t7.Data(work, path, track=track, access_band=t7.MAIN_ACCESS)
        result[name] = by_band(d, md)
        del d
    out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
