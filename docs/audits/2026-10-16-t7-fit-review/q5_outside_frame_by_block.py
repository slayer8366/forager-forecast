"""Q5 addendum: per level III block, the share of shaded cells outside T6's effort frame and the
mean score percentile (among all shaded cells) inside and outside the frame. Writes JSON."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
sys.path.insert(0, str(Path(__file__).parent))
import common as c
t = c.load_table()
meta = json.loads((c.WORK / "table_meta.json").read_text())
lvl = {e["code"]: e for e in meta["level3_table"]}
score = np.load(c.WORK / "scores_all.npy"); inside = np.load(c.WORK / "inside_all.npy")
inframe = np.isin(t["wkey"], c.frame_keys("all"))
pct = np.full(len(score), np.nan); pct[inside] = rankdata(score[inside]) / inside.sum()
rows = []
for b in np.unique(t["level3"]):
    s = inside & (t["level3"] == b)
    if s.sum() < 20000: continue
    o = s & ~inframe; i = s & inframe
    rows.append({"block": f"{lvl[int(b)]['level3']} {lvl[int(b)]['name']}", "shaded": int(s.sum()),
                 "outside_frame_share": float(o.sum() / s.sum()),
                 "pct_inside_frame": float(pct[i].mean()) if i.any() else None,
                 "pct_outside_frame": float(pct[o].mean()) if o.any() else None})
top = pct >= 0.8
out = {"top_fifth_cells_outside_frame_share": float((top & ~inframe).sum() / top.sum()),
       "all_shaded_outside_frame_share": float((inside & ~inframe).sum() / inside.sum()),
       "by_block": sorted(rows, key=lambda r: -r["outside_frame_share"])}
(Path(__file__).parent / "q5_outside_frame_by_block.json").write_text(json.dumps(out, indent=1) + "\n")
print(out["top_fifth_cells_outside_frame_share"], out["all_shaded_outside_frame_share"])
for r in out["by_block"]: print(r["block"][:40], r["shaded"], round(r["outside_frame_share"],2), r["pct_inside_frame"] and round(r["pct_inside_frame"],2), r["pct_outside_frame"] and round(r["pct_outside_frame"],2))
