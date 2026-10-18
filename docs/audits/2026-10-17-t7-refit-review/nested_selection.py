"""Review 1, question 2: how much of condition 1's margin the band selection explains.

The coder's add-one step kept a candidate band when its held-out gain over the base, with a
weather-cell-clustered interval over all 24 blocks, was wholly above zero (fit_report.json
``add_one``; t7_fit.py ``diff`` defaults to weather-cell clusters). The full model was then scored
on the same held-out blocks. This script re-runs that selection leaving one block out at a time:
for held-out block k, the candidates are chosen on the other 23 blocks' held-out predictions by
the same rule, and block k is scored by the model that choice names. That nested full model is
then compared with B under condition 1's block-clustered interval.

Only cached models can serve: the base, the base plus one candidate, and the full model as
built (base plus Lithocarpus, Chrysolepis and Arbutus). A block whose nested choice names any
other set has no cached held-out predictions; it is scored by the base (the choice that adds no
band), which is the conservative side for the gain, and counted.

Reads the cache only; never fits. Writes nested_selection.json into this folder.
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
A_KEY, B_KEY = "A: e", "B: f"
CANDIDATES = ("share_Larix", "share_Betula", "share_Populus", "share_Alnus", "share_Lithocarpus",
              "share_Chrysolepis", "share_Arbutus", "share_ecm_hosts")
KEPT = ("share_Lithocarpus", "share_Chrysolepis", "share_Arbutus")


class Ranked:
    """Scores sorted once; a weighted AUC under new weights is one pass."""

    def __init__(self, scores, y):
        s = np.asarray(scores, dtype=np.float64)
        self.order = np.argsort(s, kind="mergesort")
        s = s[self.order]
        new = np.r_[True, s[1:] != s[:-1]]
        self.g = np.cumsum(new) - 1
        self.ng = int(self.g[-1]) + 1
        self.pos = (np.asarray(y) == 1)[self.order]

    def auc(self, w) -> float:
        w = np.asarray(w, dtype=np.float64)[self.order]
        wp = np.bincount(self.g, weights=np.where(self.pos, w, 0.0), minlength=self.ng)
        wn = np.bincount(self.g, weights=np.where(self.pos, 0.0, w), minlength=self.ng)
        below = np.cumsum(wn) - wn
        return float((wp * (below + 0.5 * wn)).sum() / (wp.sum() * wn.sum()))


def main() -> None:
    t0 = time.monotonic()
    table = rc.Table()
    main = rc.rows_for(table, rc.V9 / "presences_main.csv")
    n = len(main["y"])
    y, w, blocks, clusters = main["y"], main["w"], main["blocks"], main["clusters"]
    preds = {k: rc.cached(k, n) for k in (B_KEY, "base", "full", *CANDIDATES)}
    # the selection as run, on all blocks, with the review's code (must give KEPT)
    all_blocks = {c: rc.auc_difference(preds[c], preds["base"], y, w, clusters) for c in CANDIDATES}
    kept_all = tuple(c for c in CANDIDATES if all_blocks[c]["above_zero"])
    print("selection on all blocks:", kept_all, round(time.monotonic() - t0), "s", flush=True)

    nested = {}
    nested_full = np.empty(n)
    unavailable = []
    for k in np.unique(blocks):
        sel = blocks != k
        ys, ws = y[sel], w[sel]
        _, cidx = np.unique(clusters[sel], return_inverse=True)
        nc = int(cidx.max()) + 1
        ranked = {c: Ranked(preds[c][sel], ys) for c in ("base", *CANDIDATES)}
        point = {c: ranked[c].auc(ws) - ranked["base"].auc(ws) for c in CANDIDATES}
        rng = np.random.default_rng(rc.SEED)
        diffs = {c: np.empty(rc.RESAMPLES) for c in CANDIDATES}
        for i in range(rc.RESAMPLES):
            t = np.bincount(rng.integers(0, nc, size=nc), minlength=nc)[cidx]
            wi = ws * t
            base_auc = ranked["base"].auc(wi)
            for c in CANDIDATES:
                diffs[c][i] = ranked[c].auc(wi) - base_auc
        chosen = []
        detail = {}
        for c in CANDIDATES:
            lo, hi = rc.interval(diffs[c])
            detail[c] = {"point": point[c], "low": lo, "high": hi}
            if lo > 0:
                chosen.append(c)
        chosen = tuple(chosen)
        hold = blocks == k
        if chosen == kept_all:
            source = "full"
        elif len(chosen) == 1:
            source = chosen[0]
        elif len(chosen) == 0:
            source = "base"
        else:
            source = "base (no cached model for this set)"
            unavailable.append(int(k))
        nested_full[hold] = preds["full" if source == "full" else
                                  ("base" if source.startswith("base") else source)][hold]
        nested[int(k)] = {"presences_held_out": int((y[hold] == 1).sum()), "chosen": list(chosen),
                          "same_as_all_blocks": chosen == kept_all, "scored_by": source,
                          "add_one": detail}
        print(f"block {k}: chosen {chosen} -> {source}; {round(time.monotonic() - t0)} s",
              flush=True)

    out = {
        "selection_on_all_blocks": {"kept": list(kept_all), "matches_coder": kept_all == KEPT,
                                    "add_one": all_blocks},
        "nested_by_held_out_block": nested,
        "blocks_where_choice_differs": [k for k, v in nested.items() if not v["same_as_all_blocks"]],
        "blocks_scored_by_base_for_want_of_a_cached_model": unavailable,
        "condition_1_as_reported_full_minus_B_block": rc.auc_difference(preds["full"], preds[B_KEY], y, w, blocks),
        "condition_1_nested_full_minus_B_block": rc.auc_difference(nested_full, preds[B_KEY], y, w, blocks),
        "condition_1_no_selection_base_minus_B_block": rc.auc_difference(preds["base"], preds[B_KEY], y, w, blocks),
        "nested_full_minus_A_block": rc.auc_difference(nested_full, rc.cached(A_KEY, n), y, w, blocks),
        "pooled_auc": {"full": rc.weighted_auc(preds["full"], y, w),
                       "nested_full": rc.weighted_auc(nested_full, y, w),
                       "base": rc.weighted_auc(preds["base"], y, w),
                       "B": rc.weighted_auc(preds[B_KEY], y, w)},
        "seconds": round(time.monotonic() - t0),
    }
    (HERE / "nested_selection.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for k in ("condition_1_as_reported_full_minus_B_block", "condition_1_nested_full_minus_B_block",
              "condition_1_no_selection_base_minus_B_block"):
        print(k, rc.fmt(out[k]))
    print("differs:", out["blocks_where_choice_differs"], "unavailable:", unavailable)


if __name__ == "__main__":
    main()
