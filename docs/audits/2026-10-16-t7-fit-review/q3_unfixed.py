"""Q3: the weight rescale in 41f9c79, tested independently of any verdict.

Part 1 (mechanical): fit c16 on all rows of each group with the weights as M3 gives them (no
rescale) and with the rescale; count trees that split and distinct predictions. The comparison
group's weights total 2, the main group's 90.

Part 2 (verdict-relevant, main group): held-out predictions over the 24 blocks for A, B and the
full feature set with the UNFIXED weights, reusing the fit's per-fold chosen configurations from
the manifest (no re-tuning: a disclosed shortcut), then pooled AUCs and weather-cell intervals.
Writes q3_unfixed.json."""

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import common as c  # noqa: E402

THREADS = 4
t0 = time.time()
OUT = Path(__file__).parent / "q3_unfixed.json"
meta = json.loads((c.WORK / "table_meta.json").read_text())
names = meta["features"]
man = json.loads(Path("/mnt/work/Zynergy/forecast-data/t7/pnw-2026-10-17/manifest.json").read_text())
chosen = man["chosen_configurations"]
t = c.load_table(features=True)
le = c.effort_by_key("all", t["wkey"])
out = {"part1": {}, "part2": {}}


def describe(bst, x):
    d = bst.dump_model()
    leaves = [tr["num_leaves"] for tr in d["tree_info"]]
    p = bst.predict(x)
    return {"trees": len(leaves), "trees_that_split": int(sum(n > 1 for n in leaves)),
            "distinct_predictions": int(np.unique(np.round(p, 12)).size)}


main = c.Rows(c.V9 / "presences_main.csv", table=t)
comp = c.Rows(c.V9 / "presences_comparison.csv", table=t)
for gname, rows in (("comparison", comp), ("main", main)):
    for mname, feats in (("B", c.B_FEATS), ("full", c.FULL)):
        x = c.design(rows, feats, t["features"], names, le)
        for resc in (False, True):
            bst = c.fit(c.config("c16"), feats, x, rows.y, rows.w, THREADS, rescale=resc)
            k = f"{gname} {mname} c16 {'rescaled' if resc else 'unfixed'}"
            out["part1"][k] = {"weight_total": float(rows.w.sum()), **describe(bst, x)}
            print(k, out["part1"][k], flush=True)
    del x
OUT.write_text(json.dumps(out, indent=1) + "\n")

# part 2: main group, unfixed weights, LOBO with the fit's chosen configurations
fsel_blocks = json.loads(c.FIT_REPORT.read_text())["forested_blocks_in_fit"]
preds = {}
for mname, feats, ck in (("A", [c.EFFORT], "A: effort only"), ("B", c.B_FEATS, "B: forest only"),
                         ("full", c.FULL, None)):
    s = time.time()
    x = c.design(main, feats, t["features"], names, le)
    ch = chosen[ck if ck else "full"]
    p = np.full(len(main.y), np.nan)
    for b in np.unique(main.block):
        te = main.block == b
        bst = c.fit(c.config(ch[str(b)]), feats, x[~te], main.y[~te], main.w[~te], THREADS,
                    rescale=False)
        p[te] = bst.predict(x[te])
    assert not np.isnan(p).any()
    preds[mname] = p
    np.save(Path("/tmp") / f"t7_review_unfixed_{mname}.npy", p)
    print(mname, round(time.time() - s), "s", c.wauc(p, main.y, main.w), flush=True)
    del x
fs = np.isin(main.block, fsel_blocks)
r2 = {"pooled_auc": {k: c.wauc(v, main.y, main.w) for k, v in preds.items()}}
for sel_name, sel in (("all", np.ones(len(main.y), bool)), ("forested", fs)):
    for o in ("A", "B"):
        r2[f"weather_cell|{sel_name}|full-{o}"] = c.boot_diff(
            preds["full"][sel], preds[o][sel], main.y[sel], main.w[sel], main.wkey[sel])
        r2[f"block|{sel_name}|full-{o}"] = c.boot_diff(
            preds["full"][sel], preds[o][sel], main.y[sel], main.w[sel], main.block[sel])
out["part2"] = r2
out["seconds"] = round(time.time() - t0)
OUT.write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
