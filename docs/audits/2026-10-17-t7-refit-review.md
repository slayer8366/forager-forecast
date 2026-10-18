# T7 re-fit review 1 (D18): the PNW habitat map under P10b, read by Sorrel Tally

Sorrel Tally (independent reviewer), review 1 of two, on a model other than the coder's. Written 2026-10-18 UTC for the planner (Rowan Waymark).

- **Dispatch:** `docs/dispatch/2026-10-17-t7-refit-review.md` (branch `t7-strengthen-plan`, 83f0258). The owner's go, verbatim (Forager RECORD -1232): "Go ahead and start the reviews."
- **Under review:** branch `t7-refit` at `da1f207`: `docs/audits/2026-10-17-t7-refit-report.md` and `docs/audits/2026-10-17-t7-refit/`; the run's outputs in `/mnt/work/Zynergy/forecast-data/t7/refit/`.
- **This review's branch:** `t7-refit-review`, cut from `t7-refit` at `da1f207`. Evidence folder: `docs/audits/2026-10-17-t7-refit-review/`. Review 2 was not read.
- **Flags:** READ means a file or the code says so; COMPUTED means a script in the evidence folder produced it; INFERRED means my reasoning.
- **Nothing was shown or published.** Rendered images are in the evidence folder for the planner and owner only.

## Mechanism prediction (written before any figure was computed; scored at the end)

Written 2026-10-18T03:22Z, after reading the dispatch, the coder's report and `fit_report.json`, the code, and the decision rows, and before running any script.

1. **Reproduction.** All four P10b figures, their intervals, and the beside figures (P10, base minus B, within-cell AUCs, the saprotroph and *Laetiporus* gains) reproduce exactly from the cache with my own AUC and resampling code, given the same seed and draw order. The verdict (fail on 2 and 3) is confirmed.
2. **Condition 1 and the selection.** Without any band selection, condition 1 is base minus B: +0.0016 with a block interval including zero. It fails. A leave-one-block-out selection (candidates re-chosen on the other 23 blocks' held-out predictions) will not pick the same three bands for every block: *Lithocarpus*'s lower bound (+0.00008) is thin, and *Larix*'s (−0.000004) is on the other side of zero by a hair. So the nested estimate of condition 1 will sit between base minus B and the reported +0.0038, and its interval will include zero. I expect to say: condition 1 would not pass without the selection.
3. **Road access.** The interaction groups, the monotone direction, the held median and the exclusion from the area of applicability are implemented as D156 states. Within one weather cell, the negated road distance alone will rank pairs at about A's 0.648 (within 0.01), so A's within-cell AUC is the road band and nothing else. Condition 2's collapse is that: once road distance is known, the habitat bands add nothing inside a cell, and even cost a little. Holding access on the map does not remove habitat signal from the ranking, because the raw score is additive in the held group (P6 passed); what it does is settle, at fit time, which of the two correlated inputs gets the within-cell gradient, and the monotone constraint pushes that toward access. The map's top tenth moved away from roads, so the ranking was not pulled toward them.
4. **Condition 3.** The saprotroph gain (+0.0021) and *Laetiporus* gain (+0.0141) reproduce. The evidence does not support "mycorrhizal" in a label: a wood-rot genus gains three times as much from the same bands.
5. **Condition 4.** The filters are as D158 states. The pass is mostly geography, not habitat: 4,666 of 6,026 kept specimens are in four western blocks (Puget Lowland, Coastal Range, Cascades, North Cascades), and the background is matched on road band but drawn from the whole box. Scoring by the point value instead of the circle mean will give a similar figure (within 0.03). Drawing the matched background from the specimen's own level III block will drop AUC minus 0.5 well below the reported +0.196, to under +0.10, with an interval including zero. Specimens from 2000 on will score about the same as older ones. The interior figure (390 specimens, −0.157 to +0.240) is not usable as a verdict either way.
6. **The map.** Interior mountain conifer forest ranks highest; the Canadian side is a flat masked band with a hard edge at the border; cells outside the area of applicability are few and scattered. Against 2026-10-16 the picture is close (rank 0.91), with the top tenth shifted toward the Cascades and away from the Columbia Plateau's edges.

(The sections below are filled in as the review runs.)

## Baseline (every premise re-checked before use)

| premise (dispatch) | checked | result |
|---|---|---|
| `t7-refit` at `da1f207`, holding the report and `docs/audits/2026-10-17-t7-refit/` | `git ls-remote`, `git log` | READ: matches; the review branch was cut from it |
| the fit ran code `0560dae` | `manifest.json` `code_commit`, `fit_report.json` `code_commit` | READ: `0560daeed37d…`, both |
| draft PR #5 open | `gh pr list` | READ: #5 DRAFT, into t7-build |
| manifest sha256 `af0fc2dd…48ec` | `sha256sum` of `refit/outputs/manifest.json`; `fit.log` last line | COMPUTED: equal, both |
| outputs in `/mnt/work/Zynergy/forecast-data/t7/refit/outputs/` | listing | READ: the six files the report lists |
| the four conditions as reported | `fit_report.json` `p10b` | READ: as the dispatch states them; recomputed below |
| specimen download key `0032050-260928105237408`, DOI `10.15468/dl.5mvzg2`, zip sha256 `28efb80e…34ad` | `t7/specimens/fetch.log`, the zip's name | READ: matches |
| `t6b-night` running and untouched | `systemctl --user list-units` | READ: active, running; nothing under `t6b/` was opened for writing |

No mismatch; no stop. Review 2's branch and worktree exist on this machine and were not opened.

**The environment.** The review worktree's venv was built with `uv sync --frozen` (numpy 2.5.3, lightgbm 4.7.0, rasterio 1.5.1). Every heavy step ran as `systemd-run --user --scope -q -p MemoryMax=4G -p MemorySwapMax=0 nice -n 10 …`, one at a time, beside t6b-night. Nothing was fitted: every figure below comes from the cached held-out predictions (`refit/cache/lobo_*.npy`), the saved table (`refit/table.npz`), `inside_all.npy`, the written rasters and the kept specimen file.

**The review's own code** (`review_common.py`) rebuilds the training rows from the data files without the coder's `t7` package: the presences from `presences_main.csv` kept when their cell is in the table and their cell's weather cell is in T6's `cell_level.csv`; weights one per genus with 30 or more presences and one for the pooled rest; the background as 500,000 cells drawn from the eligible in-frame cells with seed 20260918 and sorted; blocks and weather cells from the table. The AUC is a rank-sum count of weighted pairs with ties half; the intervals redraw whole units with seed 20260918 and multiply each row's weight by its unit's draw count. Four tests check this code against pair-by-pair brute force on small synthetic data with ties (`test_review_common.py`), and two revert checks (`revert_check.py`, `revert_check.txt`) show the tests bite: with the block draw counts no longer multiplying the row weights, the within-cell test fails on its own message ("rows must be weighted by their block's draw count"); with ties counted as concordant, exactly the two tests that compare a pooled AUC with the pair count fail, the first on "ties must count half". Each revert was restored from a saved copy, the compile step was checked first, and the forward line was confirmed present afterwards.
