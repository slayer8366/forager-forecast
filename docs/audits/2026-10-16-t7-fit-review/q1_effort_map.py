"""Q1: the full map (scores_all.npy, the fit's own map pass at the held effort) against the
effort surface, over shaded cells (inside the area of applicability).

Model A is effort only and monotone in log effort (model.py lgb_params, monotone_constraints), so
"the effort-only map" at each cell's own effort ranks cells as log effort does, up to A's plateaus.
At the held effort A is a constant, so the comparison has to be against the effort surface itself.

Effort per weather cell: T6's stored surface read through the project's EffortSurface and
static_effort (inputs, not under review). Everything else is the reviewer's code."""

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr

sys.path.insert(0, str(Path(__file__).parent))
import common as c  # noqa: E402

from forager_forecast.cells import Cell  # noqa: E402
from forager_forecast.effort import EffortSurface  # noqa: E402
from forager_forecast.t7.keying import static_effort  # noqa: E402

t0 = time.time()
OUT = Path(__file__).parent / "q1_effort_map.json"
t = c.load_table()
wkey, l3 = t["wkey"], t["level3"]
score = np.load(c.WORK / "scores_all.npy")
inside = np.load(c.WORK / "inside_all.npy")
meta = json.loads((c.WORK / "table_meta.json").read_text())
lvl = {e["code"]: e for e in meta["level3_table"]}

uk = np.unique(wkey)
lat_t, lon_t = uk // 10_000 - 1000, uk % 10_000 - 2000
cells = [Cell(int(a), int(b)) for a, b in zip(lat_t, lon_t)]
eff = static_effort(EffortSurface.read(c.T6 / "all"), cells)
le = {}
for k, cell in zip(uk.tolist(), cells):
    if cell in eff.total:
        le[k] = float(np.log(eff.total[cell]))
print("weather cells with eligible cells:", len(uk), "with effort:", len(le), flush=True)
held = float(np.median(list(le.values())))
keys = np.array(sorted(le), np.int64)
vals = np.array([le[k] for k in keys])
pos = np.clip(np.searchsorted(keys, wkey), 0, len(keys) - 1)
inframe = keys[pos] == wkey
cell_le = np.where(inframe, vals[pos], np.nan)

out = {"held_effort_recomputed": held, "weather_cells_with_effort": len(le),
       "shaded": int(inside.sum()), "shaded_in_frame": int((inside & inframe).sum()),
       "shaded_outside_frame": int((inside & ~inframe).sum())}
s = inside & inframe
x, e = score[s].astype(np.float64), cell_le[s]
out["spearman_cell_score_vs_log_effort"] = float(spearmanr(x, e).statistic)

# weather-cell level: mean habitat score per weather cell against its effort
wk = wkey[s]
u, inv = np.unique(wk, return_inverse=True)
mean_score = np.bincount(inv, weights=x) / np.bincount(inv)
eff_u = np.array([le[int(k)] for k in u])
out["spearman_weathercell_mean_score_vs_log_effort"] = float(spearmanr(mean_score, eff_u).statistic)
out["weather_cells_shaded_in_frame"] = int(len(u))

# share of the score's rank variance that lies within weather cells (effort is constant there)
rk = rankdata(x) / len(x)
m = np.bincount(inv, weights=rk) / np.bincount(inv)
within = float(((rk - m[inv]) ** 2).sum())
total = float(((rk - rk.mean()) ** 2).sum())
out["rank_variance_within_weather_cells_share"] = within / total

# top-quintile overlap
q_s = x >= np.quantile(x, 0.8)
q_e = e >= np.quantile(e, 0.8)
out["top20_habitat_cells_also_top20_effort"] = float((q_s & q_e).sum() / q_s.sum())
lo_e = e <= np.quantile(e, 0.2)
out["top20_habitat_cells_in_bottom20_effort"] = float((q_s & lo_e).sum() / q_s.sum())

# by block: mean percentile of habitat vs mean percentile of effort (over shaded, in frame)
pr_s = rankdata(x) / len(x)
pr_e = rankdata(e) / len(e)
bl = l3[s]
rows = []
for b in np.unique(bl):
    sel = bl == b
    if sel.sum() < 20000:
        continue
    rows.append({"block": f"{lvl[int(b)]['level3']} {lvl[int(b)]['name']}",
                 "cells": int(sel.sum()),
                 "habitat_pct": float(pr_s[sel].mean()), "effort_pct": float(pr_e[sel].mean()),
                 "gap": float(pr_s[sel].mean() - pr_e[sel].mean()),
                 "spearman_within_block": float(spearmanr(x[sel], e[sel]).statistic)})
out["by_block"] = sorted(rows, key=lambda r: r["gap"])

# shaded cells outside the frame: where do they sit in the in-frame score distribution
xo = score[inside & ~inframe].astype(np.float64)
out["outside_frame_score_percentile_in_frame_quartiles"] = (
    np.searchsorted(np.sort(x), np.quantile(xo, [0.25, 0.5, 0.75])) / len(x)).tolist()
out["seconds"] = round(time.time() - t0)
OUT.write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
