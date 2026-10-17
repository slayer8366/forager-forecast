"""Q1, Q2 and Q4 (block table): recompute the fit's headline figures from the cached held-out
predictions with the reviewer's own rows, AUC and bootstrap (common.py). Writes figures.json."""

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import common as c  # noqa: E402

OUT = Path(__file__).parent / "figures.json"
t0 = time.time()
rep = json.loads(c.FIT_REPORT.read_text())
meta = json.loads((c.WORK / "table_meta.json").read_text())
lvl = {e["code"]: e for e in meta["level3_table"]}
table = c.load_table()
out = {}

r = c.Rows(c.V9 / "presences_main.csv", table=table)
out["main_rows"] = {"file": r.n_file, "eligible": r.n_eligible, "entering": r.n_enter,
                    "units_alone": r.units_alone, "pooled_presences": r.pooled, "pool": r.pool,
                    "background": int((r.y == 0).sum()), "bg_sha256": r.bg_sha,
                    "presence_weight_total": float(r.w[r.y == 1].sum()),
                    "background_weight_total": float(r.w[r.y == 0].sum())}
print(out["main_rows"], flush=True)

study = {int(k): v for k, v in meta["block_study_cells"].items()}
share = {int(k): v for k, v in meta["block_share_cells"].items()}
forested_box = {b for b, n in study.items() if n > 0 and share.get(b, 0) / n >= 0.15}
in_fit = set(np.unique(r.block).tolist())
forested = sorted(forested_box & in_fit)
out["blocks"] = {"in_fit": len(in_fit), "forested_in_box": len(forested_box),
                 "forested_in_fit": forested,
                 "study_blocks_in_box": len([b for b, n in study.items() if n > 0])}
fsel = np.isin(r.block, forested)

preds = {}
for name, k in (("A", "A: e"), ("B", "B: f"), ("base", "base"), ("full", "full")):
    p, m = c.cache(k)
    assert m["n"] == len(r.y), (k, m["n"], len(r.y))
    preds[name] = p
out["pooled_auc"] = {k: c.wauc(v, r.y, r.w) for k, v in preds.items()}
out["forested_auc"] = {k: c.wauc(v[fsel], r.y[fsel], r.w[fsel]) for k, v in preds.items()}
for band in ("Larix", "Betula", "Populus", "Alnus", "Lithocarpus", "Chrysolepis", "Arbutus",
             "ecm_hosts"):
    p, _ = c.cache(f"share_{band}")
    out.setdefault("add_one", {})[band] = c.boot_diff(p, preds["base"], r.y, r.w, r.wkey)
print(out["pooled_auc"], flush=True)

iv = {}
for cl_name, cl in (("weather_cell", r.wkey), ("block", r.block)):
    for sel_name, sel in (("all", np.ones(len(r.y), bool)), ("forested", fsel)):
        for other in ("A", "B"):
            iv[f"{cl_name}|{sel_name}|full-{other}"] = c.boot_diff(
                preds["full"][sel], preds[other][sel], r.y[sel], r.w[sel], cl[sel])
# base (no selection) against A and B, intervals the report did not compute
for other in ("A", "B"):
    iv[f"weather_cell|all|base-{other}"] = c.boot_diff(preds["base"], preds[other], r.y, r.w,
                                                       r.wkey)
    iv[f"block|all|base-{other}"] = c.boot_diff(preds["base"], preds[other], r.y, r.w, r.block)
# Monte Carlo stability: a second seed for the ruled interval
for other in ("A", "B"):
    iv[f"weather_cell|all|full-{other}|seed1"] = c.boot_diff(preds["full"], preds[other], r.y,
                                                             r.w, r.wkey, seed=1)
out["intervals"] = iv
for k, v in iv.items():
    print(k, ["%+.5f" % x for x in v], flush=True)

# block table and level I
bt = []
for b in sorted(in_fit):
    s = r.block == b
    npres = int((r.y[s] == 1).sum())
    row = {"code": b, "level3": lvl[b]["level3"], "name": lvl[b]["name"],
           "level1": lvl[b]["level1"], "presences": npres, "background": int((r.y[s] == 0).sum())}
    if npres >= 30:
        row.update({k: c.wauc(preds[k][s], r.y[s], r.w[s]) for k in ("full", "A", "B")})
    bt.append(row)
out["block_table"] = bt
l1 = {}
for L in sorted({lvl[b]["level1"] for b in in_fit}):
    s = np.isin(r.block, [b for b in in_fit if lvl[b]["level1"] == L])
    npres = int((r.y[s] == 1).sum())
    l1[L] = {"presences": npres}
    if npres:
        l1[L].update({k: c.wauc(preds[k][s], r.y[s], r.w[s]) for k in ("full", "A", "B")})
out["level1"] = l1

# Q2: comparison group (and the other side runs)
for name, f, track in (("comparison group", "presences_comparison.csv", "all"),
                       ("licence track", "presences_licence_track.csv", "cc"),
                       ("M2 side run", "presences_side.csv", "all")):
    s = c.Rows(c.V9 / f, track=track, table=table)
    sp = {}
    for k, ck in (("full", "full"), ("A", "A: e"), ("B", "B: f")):
        p, m = c.cache(f"{name}-{ck}")
        assert m["n"] == len(s.y), (name, k, m["n"], len(s.y))
        sp[k] = p
    sf = np.isin(s.block, forested)
    out.setdefault("side", {})[name] = {
        "presences": int((s.y == 1).sum()), "background": int((s.y == 0).sum()),
        "bg_dropped": s.bg_dropped,
        "auc": {k: c.wauc(v, s.y, s.w) for k, v in sp.items()},
        "full-A": c.boot_diff(sp["full"], sp["A"], s.y, s.w, s.wkey),
        "full-B": c.boot_diff(sp["full"], sp["B"], s.y, s.w, s.wkey),
        "forested full-A": c.boot_diff(sp["full"][sf], sp["A"][sf], s.y[sf], s.w[sf], s.wkey[sf]),
        "forested full-B": c.boot_diff(sp["full"][sf], sp["B"][sf], s.y[sf], s.w[sf], s.wkey[sf]),
        "block full-A": c.boot_diff(sp["full"], sp["A"], s.y, s.w, s.block),
        "block full-B": c.boot_diff(sp["full"], sp["B"], s.y, s.w, s.block),
    }
    print(name, out["side"][name], flush=True)

# compare with the report's JSON
cmp = {"pooled_auc": {k: [out["pooled_auc"][k], rep["pooled_auc"][kk]] for k, kk in
                      (("A", "A: effort only"), ("B", "B: forest only"), ("base", "base"),
                       ("full", "full"))}}
cmp["intervals"] = {}
for sel, rk in (("all", "all_blocks"), ("forested", "forested_blocks")):
    for o in ("A", "B"):
        d = rep["p10"][rk][o]
        cmp["intervals"][f"weather_cell|{sel}|full-{o}"] = [iv[f"weather_cell|{sel}|full-{o}"],
                                                            [d["point"], d["low"], d["high"]]]
        d = rep["block_clustered_intervals_no_verdict"][sel][o]
        cmp["intervals"][f"block|{sel}|full-{o}"] = [iv[f"block|{sel}|full-{o}"],
                                                     [d["point"], d["low"], d["high"]]]
out["compare_with_report"] = cmp
out["seconds"] = round(time.time() - t0)
OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
print("done", out["seconds"], "s")
