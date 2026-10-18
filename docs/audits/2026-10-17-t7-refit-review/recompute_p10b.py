"""Review 1, question 1 (and parts of 3 and 4): every P10b figure recomputed from the cache with
the review's own code (review_common.py), beside the coder's fit_report.json values.

Reads: the re-fit work dir and cache, V9/V9C presences, T6's frame. Writes recompute_p10b.json
into this folder.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_common as rc  # noqa: E402

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent / "2026-10-17-t7-refit" / "fit_report.json"
A_KEY, B_KEY = "A: e", "B: f"
CANDIDATES = ("share_Larix", "share_Betula", "share_Populus", "share_Alnus", "share_Lithocarpus",
              "share_Chrysolepis", "share_Arbutus", "share_ecm_hosts")


def match(mine: dict, theirs: dict, tol=1e-9) -> dict:
    ok = all(abs(mine[k] - theirs[k]) <= tol for k in ("point", "low", "high"))
    return {"mine": rc.fmt(mine), "theirs": rc.fmt(theirs), "match": ok}


def main() -> None:
    t0 = time.monotonic()
    rep = json.loads(REPORT.read_text())
    table = rc.Table()
    out: dict = {"checks": {}, "p10b": {}, "beside": {}, "condition_3": {}, "notes": []}

    # --- the main run's rows
    main = rc.rows_for(table, rc.V9 / "presences_main.csv")
    n = len(main["y"])
    out["checks"]["rows"] = {"mine": n, "theirs": rep["presences"] + rep["background"],
                             "presences": [main["n_presences"], rep["presences"]],
                             "background": [main["n_background"], rep["background"]],
                             "background_pool": [main["background_pool"], rep["background_pool"]],
                             "background_sha256_match": main["background_sha256"]
                             == rep["background_sha256"]}
    y, w, blocks, clusters = main["y"], main["w"], main["blocks"], main["clusters"]
    preds = {k: rc.cached(k, n) for k in (A_KEY, B_KEY, "base", "full", *CANDIDATES)}
    pooled = {k: rc.weighted_auc(p, y, w) for k, p in preds.items()}
    theirs_pooled = rep["pooled_auc"]
    name_of = {A_KEY: "A: effort only", B_KEY: "B: forest only", "base": "base", "full": "full",
               **{c: f"base + {c}" for c in CANDIDATES}}
    out["checks"]["pooled_auc"] = {k: {"mine": pooled[k], "theirs": theirs_pooled[name_of[k]],
                                       "match": abs(pooled[k] - theirs_pooled[name_of[k]]) < 1e-9}
                                   for k in preds}
    # brute-force check of the AUC code on a sample
    rng = np.random.default_rng(1)
    pick = rng.choice(n, 3000, replace=False)
    out["checks"]["auc_bruteforce_sample"] = {
        "fast": rc.weighted_auc(preds["full"][pick], y[pick], w[pick]),
        "brute": rc.weighted_auc_bruteforce(preds["full"][pick], y[pick], w[pick])}
    print("rows and pooled AUCs checked", round(time.monotonic() - t0), "s", flush=True)

    # --- condition 1: full minus B, block clustered
    c1 = rc.auc_difference(preds["full"], preds[B_KEY], y, w, blocks)
    out["p10b"]["1_full_minus_B_block"] = match(
        c1, rep["p10b"]["conditions"]["1_block_clustered_full_minus_B"])
    # --- condition 2: within cell full minus A, block resampled (D145 amended)
    c2 = rc.within_cluster_difference(preds["full"], preds[A_KEY], y, w, clusters, blocks)
    out["p10b"]["2_within_cell_full_minus_A_block_resampled"] = match(
        c2, rep["p10b"]["conditions"]["2_within_cell_full_minus_A_block_resampled"])
    c2_cell = rc.within_cluster_difference_cluster_resampled(preds["full"], preds[A_KEY], y, w,
                                                            clusters)
    out["beside"]["within_cell_full_minus_A_weather_cell_resampled_(log_line)"] = match(
        c2_cell, rep["within_weather_cell_no_verdict"]["full_minus_A"])
    print("conditions 1 and 2", round(time.monotonic() - t0), "s", flush=True)

    # --- beside: P10 (weather-cell intervals), block-clustered full minus A, base minus B
    out["beside"]["p10_full_minus_A_weather_cell"] = match(
        rc.auc_difference(preds["full"], preds[A_KEY], y, w, clusters),
        rep["p10_no_verdict"]["all_blocks"]["A"])
    out["beside"]["p10_full_minus_B_weather_cell"] = match(
        rc.auc_difference(preds["full"], preds[B_KEY], y, w, clusters),
        rep["p10_no_verdict"]["all_blocks"]["B"])
    out["beside"]["full_minus_A_block"] = match(
        rc.auc_difference(preds["full"], preds[A_KEY], y, w, blocks),
        rep["block_clustered_intervals_no_verdict"]["all"]["A"])
    out["beside"]["base_minus_B_block"] = match(
        rc.auc_difference(preds["base"], preds[B_KEY], y, w, blocks),
        rep["base_minus_B_no_verdict"]["block_clustered"])
    out["beside"]["base_minus_B_weather_cell"] = match(
        rc.auc_difference(preds["base"], preds[B_KEY], y, w, clusters),
        rep["base_minus_B_no_verdict"]["weather_cell"])
    out["beside"]["full_minus_base_block"] = rc.auc_difference(preds["full"], preds["base"], y, w,
                                                               blocks)
    out["beside"]["within_cell_auc"] = {
        k: {"mine": rc.within_cluster_auc(preds[k], y, w, clusters),
            "theirs": rep["within_weather_cell_no_verdict"]["auc"][s]["point"]}
        for k, s in ((A_KEY, "A"), (B_KEY, "B"), ("base", "base"), ("full", "full"))}
    # the add-one selection as the coder ran it (weather-cell intervals), for the record
    out["beside"]["add_one_weather_cell"] = {
        c: match(rc.auc_difference(preds[c], preds["base"], y, w, clusters), rep["add_one"][c])
        for c in CANDIDATES}
    print("beside figures", round(time.monotonic() - t0), "s", flush=True)

    # --- question 3: the road band alone, within one weather cell
    road = table.road()[main["idx"]]
    out["beside"]["within_cell_auc_of_minus_road_distance_alone"] = rc.within_cluster_auc(
        -road, y, w, clusters)
    out["beside"]["within_cell_auc_of_minus_log1p_road_distance"] = rc.within_cluster_auc(
        -np.log1p(road), y, w, clusters)
    out["beside"]["pooled_auc_of_minus_road_distance_alone"] = rc.weighted_auc(-road, y, w)
    out["beside"]["within_cell_full_minus_minus_road"] = rc.within_cluster_difference(
        preds["full"], -road, y, w, clusters, blocks)
    out["beside"]["within_cell_A_minus_minus_road"] = rc.within_cluster_difference(
        preds[A_KEY], -road, y, w, clusters, blocks)
    # the within-cell AUC per level III block, the four models and the road band
    per_block = {}
    for b in np.unique(blocks):
        sel = blocks == b
        if (y[sel] == 1).sum() < 30:
            continue
        per_block[int(b)] = {
            "presences": int((y[sel] == 1).sum()),
            **{s: rc.within_cluster_auc(preds[k][sel], y[sel], w[sel], clusters[sel])
               for k, s in ((A_KEY, "A"), (B_KEY, "B"), ("base", "base"), ("full", "full"))},
            "minus_road": rc.within_cluster_auc(-road[sel], y[sel], w[sel], clusters[sel]),
            "full_minus_A_pooled": rc.weighted_auc(preds["full"][sel], y[sel], w[sel])
            - rc.weighted_auc(preds[A_KEY][sel], y[sel], w[sel]),
            "full_minus_B_pooled": rc.weighted_auc(preds["full"][sel], y[sel], w[sel])
            - rc.weighted_auc(preds[B_KEY][sel], y[sel], w[sel]),
        }
    out["beside"]["within_cell_by_informative_block"] = per_block
    print("question 3 figures", round(time.monotonic() - t0), "s", flush=True)

    # --- condition 3: the saprotroph group and the comparison group
    sap = rc.rows_for(table, rc.V9C / "presences_saprotroph_main.csv")
    ns = len(sap["y"])
    sp = {k: rc.cached(f"saprotroph main-{k}", ns) for k in ("full", A_KEY, B_KEY)}
    g_sap = {"full": sp["full"], "a": sp[A_KEY], "y": sap["y"], "w": sap["w"],
             "blocks": sap["blocks"]}
    g_myc = {"full": preds["full"], "a": preds[A_KEY], "y": y, "w": w, "blocks": blocks}
    gain = lambda g: rc.weighted_auc(g["full"], g["y"], g["w"]) - rc.weighted_auc(g["a"], g["y"], g["w"])  # noqa: E731
    out["condition_3"]["rows_saprotroph"] = {"mine": ns, "theirs": rep["side_runs"]["saprotroph main"]["presences"] + rep["side_runs"]["saprotroph main"]["background"]}
    out["condition_3"]["gain_mycorrhizal"] = {"mine": gain(g_myc), "theirs": rep["condition_3"]["gain_mycorrhizal_full_minus_A"]}
    out["condition_3"]["gain_saprotroph"] = {"mine": gain(g_sap), "theirs": rep["condition_3"]["gain_saprotroph_full_minus_A"]}
    c3 = rc.contrast(g_myc, g_sap)
    out["p10b"]["3_contrast"] = match(c3, rep["condition_3"]["contrast_all_blocks"])
    shared = rep["condition_3"]["shared_forested_blocks"]
    sub = lambda g: {k: (v[np.isin(g["blocks"], shared)] if isinstance(v, np.ndarray) else v) for k, v in g.items()}  # noqa: E731
    out["condition_3"]["contrast_shared_forested"] = match(
        rc.contrast(sub(g_myc), sub(g_sap)), rep["condition_3"]["contrast_shared_forested_blocks_no_verdict"])
    out["condition_3"]["saprotroph_full_minus_A_weather_cell"] = match(
        rc.auc_difference(sp["full"], sp[A_KEY], sap["y"], sap["w"], sap["clusters"]),
        rep["side_runs"]["saprotroph main"]["full_minus_A"])
    out["condition_3"]["saprotroph_within_cell_full_minus_A_block"] = match(
        rc.within_cluster_difference(sp["full"], sp[A_KEY], sap["y"], sap["w"], sap["clusters"], sap["blocks"]),
        rep["side_runs"]["saprotroph main"]["within_weather_cell_block_clustered"]["full_minus_A"])
    comp = rc.rows_for(table, rc.V9 / "presences_comparison.csv")
    nc = len(comp["y"])
    cp = {k: rc.cached(f"comparison group-{k}", nc) for k in ("full", A_KEY, B_KEY)}
    g_comp = {"full": cp["full"], "a": cp[A_KEY], "y": comp["y"], "w": comp["w"], "blocks": comp["blocks"]}
    out["condition_3"]["gain_laetiporus"] = {"mine": gain(g_comp), "theirs": rep["side_runs"]["comparison group"]["full_minus_A"]["point"]}
    out["condition_3"]["laetiporus_full_minus_A_weather_cell"] = match(
        rc.auc_difference(cp["full"], cp[A_KEY], comp["y"], comp["w"], comp["clusters"]),
        rep["side_runs"]["comparison group"]["full_minus_A"])
    out["condition_3"]["laetiporus_full_minus_A_block"] = rc.auc_difference(cp["full"], cp[A_KEY], comp["y"], comp["w"], comp["blocks"])
    out["condition_3"]["contrast_mycorrhizal_minus_laetiporus_(not_ruled)"] = rc.contrast(g_myc, g_comp)
    # the per-genus gains inside the mycorrhizal group (for the label question)
    genus = np.array(main["genus"] + [""] * main["n_background"])
    per_genus = {}
    for g in sorted(set(main["genus"])):
        sel = (y == 0) | (genus == g)
        npres = int((genus == g).sum())
        if npres < 100:
            continue
        per_genus[g] = {"presences": npres,
                        "full_minus_A": rc.weighted_auc(preds["full"][sel], y[sel], w[sel]) - rc.weighted_auc(preds[A_KEY][sel], y[sel], w[sel])}
    out["condition_3"]["per_genus_gain_full_minus_A_(100+_presences)"] = dict(sorted(per_genus.items(), key=lambda kv: -kv[1]["full_minus_A"]))
    out["seconds"] = round(time.monotonic() - t0)
    (HERE / "recompute_p10b.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(out["p10b"], indent=1))
    print("done", out["seconds"], "s")


if __name__ == "__main__":
    main()
