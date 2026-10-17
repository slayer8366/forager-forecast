"""Review 2, question 3: the main group's verdict comparison re-run with the UNFIXED weights
(no rescaling to a mean of 1), at the full run's chosen configurations, no re-tuning; and, as a
control, model A re-run with the FIXED weights to show this script reproduces the cache.

Inputs (read only): the fit's table features, the manifest's chosen configurations, the committed
tuning grid, the rows rebuilt by rebuild_rows.py. LightGBM parameters are built here from P5's
rules as read in model.py:28-46 (binary, seed, deterministic, force_row_wise, monotone rising on
log_effort, log_effort in its own interaction group). No project code is imported.

Usage: unfixed_rerun.py fixed|unfixed MODEL [MODEL...]   (MODEL in A, B, full)
"""

import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from recompute_auc import boot_diff, wauc  # noqa: E402

WORK = Path("/mnt/work/Zynergy/forecast-data/t7/fit")
ROWS = Path("/mnt/work/Zynergy/forecast-data/t7-review-2")
MANIFEST = Path("/mnt/work/Zynergy/forecast-data/t7/pnw-2026-10-17/manifest.json")
GRID = HERE.parents[0] / "2026-10-15-t7-build" / "tuning_grid.json"
META = HERE.parents[0] / "2026-10-16-t7-fit" / "table_meta.json"
SEED = 20260918
THREADS = 4
BASE = ["share_Pseudotsuga", "share_Tsuga", "share_Picea", "share_Abies", "share_Pinus",
        "share_Quercus", "share_conifer", "share_broadleaf", "total_cover_pct", "ph_mean_0_30cm"]
FEATS = {
    "A": ["log_effort"],
    "B": ["log_effort", "conifer_cover_pct", "broadleaf_cover_pct"],
    "full": [*BASE, "share_Larix", "share_Chrysolepis", "share_Arbutus", "log_effort"],
}
NAME = {"A": "A: effort only", "B": "B: forest only", "full": "full"}


def params(config, features):
    e = features.index("log_effort")
    others = [i for i in range(len(features)) if i != e]
    p = {"objective": "binary", "verbose": -1, "seed": SEED, "deterministic": True,
         "force_row_wise": True, "num_threads": THREADS, "bagging_seed": SEED,
         "feature_fraction_seed": SEED,
         "monotone_constraints": [1 if i == e else 0 for i in range(len(features))],
         "interaction_constraints": [others, [e]] if others else [[e]],
         **{k: v for k, v in config.items() if k not in ("id", "num_boost_round")}}
    return p


def fit_predict(config, features, xtr, ytr, wtr, xte):
    d = lgb.Dataset(xtr, ytr, weight=wtr, feature_name=features, free_raw_data=True)
    return lgb.train(params(config, features), d, num_boost_round=config["num_boost_round"]).predict(xte)


def main(mode, models):
    r = np.load(ROWS / "rows_main.npz")
    idx, y, w, blocks, clusters, le = r["idx"], r["y"], r["w"], r["blocks"], r["clusters"], r["log_effort"]
    names = json.loads(META.read_text())["features"]
    tab = np.load(WORK / "table.npz")
    f = tab["features"][idx].astype(np.float64)
    del tab
    cols = {n: f[:, k] for k, n in enumerate(names)}
    cols["log_effort"] = le
    cols["conifer_cover_pct"] = cols["share_conifer"] * cols["total_cover_pct"]
    cols["broadleaf_cover_pct"] = cols["share_broadleaf"] * cols["total_cover_pct"]
    if mode == "fixed":
        w_used = w * len(w) / w.sum()
    elif mode == "unfixed":
        w_used = w
    else:
        raise SystemExit(mode)
    grid = {c["id"]: c for c in json.loads(GRID.read_text())["configurations"]}
    chosen = json.loads(MANIFEST.read_text())["chosen_configurations"]
    out = {"mode": mode, "weight_sum": float(w_used.sum()), "weight_mean": float(w_used.mean())}
    preds = {}
    for m in models:
        feats = FEATS[m]
        x = np.column_stack([cols[c] for c in feats])
        p = np.full(len(y), np.nan)
        t = time.monotonic()
        for b in np.unique(blocks):
            te = blocks == b
            cfg = grid[chosen[NAME[m]][str(int(b))]]
            # the training weights are the unscaled (or scaled) weights of the training rows only;
            # in the fit script the rescale happens inside train() on the training rows, so for
            # "fixed" the per-fold mean is 1 over the training rows: reproduce that exactly
            wtr = w[~te]
            if mode == "fixed":
                wtr = wtr * len(wtr) / wtr.sum()
            p[te] = fit_predict(cfg, feats, x[~te], y[~te], wtr, x[te])
            print(f"{mode} {m} block {b}: {cfg['id']} {round(time.monotonic() - t)} s", flush=True)
        preds[m] = p
        np.save(ROWS / f"pred_{mode}_{m}.npy", p)
        out[f"auc_{m}"] = wauc(p, y, w)
        cache = WORK / "cache" / f"lobo_{ {'A': 'A: e', 'B': 'B: f', 'full': 'full'}[m] }.npy"
        c = np.load(cache)
        out[f"max_abs_diff_vs_cache_{m}"] = float(np.max(np.abs(c - p)))
        out[f"auc_cache_{m}"] = wauc(c, y, w)
        out[f"distinct_{m}"] = int(np.unique(p).size)
    if "full" in preds and "A" in preds and "B" in preds:
        meta = json.loads(META.read_text())
        study = {int(k): v for k, v in meta["block_study_cells"].items()}
        share = {int(k): v for k, v in meta["block_share_cells"].items()}
        forested = sorted({b for b, n in study.items() if n > 0 and share.get(b, 0) / n >= 0.15}
                          & set(np.unique(blocks).tolist()))
        fs = np.isin(blocks, forested)
        out["p10"] = {
            "all_A": boot_diff(preds["full"], preds["A"], y, w, clusters),
            "all_B": boot_diff(preds["full"], preds["B"], y, w, clusters),
            "forested_A": boot_diff(preds["full"][fs], preds["A"][fs], y[fs], w[fs], clusters[fs]),
            "forested_B": boot_diff(preds["full"][fs], preds["B"][fs], y[fs], w[fs], clusters[fs]),
        }
        out["p10_passes"] = all(v["above_zero"] for v in out["p10"].values())
    (HERE / f"unfixed_rerun_{mode}_{'_'.join(models)}.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
