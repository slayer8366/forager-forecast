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

## 1. P10b reproduced (`recompute_p10b.py`, `.json`, `.log`)

The rows rebuilt by the review's code are the coder's rows: 15,624 presences and 500,000 background from a pool of 3,745,167 (COMPUTED, equal to `fit_report.json`), and the background draw's sha256 equals the report's `3a411eb2…`. The fast AUC and the pair count agree on a 3,000-row sample to 4e-14. Every pooled held-out AUC in `fit_report.json` (A, B, base, the eight add-ones, full) is reproduced to 1e-9.

| P10b condition | the review's figure | the coder's | matched |
|---|---|---|---|
| 1. full minus B, block-clustered | +0.00379 [+0.00105, +0.00924] | the same | yes, to 1e-9 |
| 2. full minus A within a weather cell, level III blocks resampled with condition 1's draw (D145 as amended) | −0.00722 [−0.02570, +0.01614] | the same | yes |
| 3. mycorrhizal gain (+0.00488) minus saprotroph gain (+0.00209), one block draw for both | +0.00279 [−0.00196, +0.01054] | the same | yes |
| 4. specimens above road-matched background, AUC minus 0.5 | see section 5 | +0.19615 [+0.06645, +0.28547] | yes (section 5) |

**Verdict confirmed: P10b fails**, on conditions 2 and 3. COMPUTED.

Also reproduced to 1e-9: the weather-cell version of condition 2 that `fit.log` printed (−0.00722 [−0.02327, +0.00794]; the coder's reading of that line is right, and the verdict does not turn on which interval is used); P10's two weather-cell intervals (+0.00488 [+0.00276, +0.00724]; +0.00379 [+0.00210, +0.00545]), so **P10 passes** as reported; full minus A block-clustered (+0.00488 [−0.00008, +0.01281], which includes zero); base minus B, block (+0.00163 [−0.00131, +0.00670]) and weather cell (+0.00163 [−0.00008, +0.00329]); the four within-cell AUCs (A 0.6481, B 0.6115, base 0.6366, full 0.6409); the eight add-one differences and their verdicts; the saprotroph group's rows (509,591), gain, weather-cell and within-cell figures; the contrast over the 13 shared forested blocks (+0.00301 [−0.00156, +0.01022]); *Laetiporus*'s gain (+0.01407 [+0.00047, +0.02900]). Nothing in `fit_report.json` that I recomputed differs from it.

One figure not in the report, COMPUTED: **full minus base**, block-clustered, is +0.00216 [+0.00078, +0.00353]. That is the part of condition 1's margin the three selected bands supply; it is larger than base minus B (+0.00163), the part that needed no selection. Section 2 takes this up.

## 3. Road access

**Is it implemented as D156 states?** READ, `src/forager_forecast/t7/model.py` at `da1f207`:
- `ladder_with_access` puts `access_dist_m` beside `log_effort` in A, B, the base and every add-one, and raises if access is offered as a candidate or a base band (lines 118 to 127).
- `lgb_params` builds `interaction_constraints = [others, held]` with `held` = effort and access, so no habitat band may share a tree with either; `monotone_constraints` carries +1 for effort and the passed direction for access, and a model with access and no direction refuses to build (lines 38 to 65). The cache's `lobo_*.json` files all record `access_monotone: -1` and `access_band: dist_road_m` (READ).
- `habitat_features` drops both held features, and `scripts/t7_fit.py` `area_of_applicability` fits the area on those alone (READ, lines 173 to 181); the manifest records `aoa.excluded = [log_effort, access_dist_m]`.
- The map holds access at `held_access` = the median of `dist_road_m` over the background draw as drawn, 258.287 m (`Data.__init__`, READ), and P6's check was run at the background quartiles 97 m and 702 m with the ranking unchanged (READ, `fit_report.json` `access`).

So yes: in effort's interaction group, monotone decreasing, held at 258.3 m, outside the area of applicability. One reading the dispatch's wording invites and the code does not do: access is held at the *background's* median, not at the map cells' median (305 m over shaded cells, section 6). Under P6 the choice shifts every cell by the same amount, so it does not matter to the ranking.

**Does holding access on the map remove habitat signal that is correlated with remoteness?** Two different things are in that question.
- *On the map*: no. The raw score is a habitat part plus a part in (effort, access), because no tree may mix the two groups; holding access adds one constant to every cell. P6 passed at both quartiles (READ), which is the empirical check of that. INFERRED from the constraint, confirmed by P6.
- *In the fit*: partly, by design, and that is what D156 asked for. A within-cell gradient that habitat and road distance both explain goes to whichever the trees pick first; the monotone −1 constraint on access means any *rise* with distance must go to habitat, while any *fall* may go to either. The direction of the result is the opposite of "habitat lost to access": the map's top tenth moved **away** from roads (median road distance 593 m to 793 m, READ from the coder's `map_comparison.json`; section 6 confirms 793 m from the raster), and my Spearman of the map's rank against road distance over shaded cells is given in section 6. INFERRED: with access constrained to fall, the habitat part absorbed the far-from-road preference, which is the intended outcome, not a loss.

**Condition 2's collapse (+0.054 to −0.007): the road band, or something else?** The road band, and alone. COMPUTED from the table's `dist_road_m` on the training rows, no model:
- the negated road distance by itself ranks within-cell pairs at **0.6537**, above A's 0.6481 (effort and road, fitted) and above full's 0.6409;
- pooled, the negated road distance alone scores 0.6508;
- within one cell, full minus (−road) is −0.01282 [−0.02746, +0.01520] and A minus (−road) is −0.00559 [−0.01205, +0.00375] (block-resampled);
- on 2026-10-16, within one cell A ranked at 0.494 (effort is one value in a cell, so A was noise) and full at 0.548. The +0.054 was habitat against noise. Now the bar within a cell is the road band, and habitat does not clear it.

Per informative block, within-cell AUC (COMPUTED; `recompute_p10b.json` `within_cell_by_informative_block`):

| block | presences | A | B | base | full | −road alone |
|---|---:|---:|---:|---:|---:|---:|
| 7.1.8 Coastal Range | 5,992 | 0.656 | 0.585 | 0.651 | 0.657 | 0.668 |
| 6.2.7 Cascades | 3,137 | 0.668 | 0.633 | 0.647 | 0.648 | 0.668 |
| 7.1.7 Puget Lowland | 2,330 | **0.470** | 0.534 | 0.490 | 0.517 | 0.471 |
| 6.2.5 North Cascades | 1,422 | 0.626 | 0.604 | 0.631 | 0.626 | 0.634 |
| 7.1.9 Willamette Valley | 636 | 0.571 | 0.582 | 0.596 | 0.571 | 0.570 |
| 6.2.3 Columbia Mtns/N. Rockies | 463 | 0.657 | 0.617 | 0.623 | 0.622 | 0.654 |
| 6.2.11 Klamath | 462 | 0.705 | 0.633 | 0.646 | 0.645 | 0.704 |
| 6.2.15 Idaho Batholith | 410 | 0.777 | 0.746 | 0.730 | 0.747 | 0.783 |
| 6.2.8 Eastern Cascades | 229 | 0.690 | 0.665 | 0.693 | 0.695 | 0.690 |
| 6.2.13 Wasatch and Uinta | 179 | 0.659 | 0.673 | 0.674 | 0.674 | 0.641 |
| 6.2.9 Blue Mountains | 141 | 0.785 | 0.757 | 0.761 | 0.757 | 0.785 |
| 6.2.10 Middle Rockies | 91 | 0.716 | 0.706 | 0.648 | 0.646 | 0.703 |
| 6.2.4 Canadian Rockies | 53 | 0.665 | 0.724 | 0.689 | 0.703 | 0.631 |
| 11.1.1 Central California Foothills | 37 | 0.580 | 0.533 | 0.590 | 0.584 | 0.567 |

A's within-cell AUC tracks the road band's within 0.01 in every large block: A is the road band. In the Puget Lowland, the one urban block, presences sit **farther** from roads than background within a cell (0.470, below chance), and the monotone-decreasing constraint cannot follow that; there the habitat bands add +0.047 within cells (full 0.517), and B's forest cover does better still (0.534). INFERRED: the one place habitat beats access inside a cell is the one place the access direction is wrong, which says something about where the signal lives (lowland parks and greenbelts away from arterial roads), not about mycorrhizal hosts.

## 4. Condition 3 and the comparison groups

COMPUTED, all matching `fit_report.json`: the saprotroph group's gain over A is +0.00209 (weather-cell interval +0.00084 to +0.00337, block-resampled within-cell −0.00694 [−0.01643, +0.01317]); the mycorrhizal gain is +0.00488; the contrast +0.00279 [−0.00196, +0.01054] fails, and over the 13 shared forested blocks +0.00301 [−0.00156, +0.01022] fails. *Laetiporus* (606 presences) gains +0.01407 over A, weather-cell interval [+0.00047, +0.02900]; block-clustered, which the report does not print, it is [−0.00825, +0.04367]. The mycorrhizal gain minus the *Laetiporus* gain (not a ruled figure) is −0.00919 [−0.03479, +0.01844].

Inside the mycorrhizal group, the gain over A by genus (presences against the shared background; genera with 100 or more presences; COMPUTED, `per_genus_gain_full_minus_A`): the gains sit in the boletes and tooth fungi (*Sarcodon* +0.039 on 102, *Albatrellopsis* +0.036, *Caloboletus* +0.032, *Boletus* +0.019 on 916, *Turbinellus* +0.018, *Aureoboletus* +0.018, *Hydnellum* +0.017, *Cortinarius* +0.012 on 954). The six genera with the most presences after *Cortinarius* gain nothing or lose: *Amanita* (2,614) −0.001, *Russula* (1,008) −0.004, *Cantharellus* (851) −0.000, *Suillus* (850) −0.001, *Helvella* (832) −0.008, *Lactarius* (807) −0.003. Every genus here is weighted equally, so the group gain is a mean over genera, and most of the common ones do not carry it.

**Does the evidence support anything "mycorrhizal" in a label?** No. (i) The host-specific contrast is the one test built to tell host dependence from forest in general, and it fails on both block sets. (ii) A wood-rot genus gains three times as much from the same bands, and the group's gain is not shown above it. (iii) Inside the group, the common ectomycorrhizal genera (*Amanita*, *Russula*, *Lactarius*, *Suillus*) gain nothing from the host bands; the gain comes from a few bolete and tooth-fungus genera, which is a real pattern worth a look of its own but is not "mycorrhizal mushrooms as a group". (iv) The three bands that carry condition 1 are southwestern broadleaf hosts (tanoak, chinquapin, madrone), and nothing in the design ties their effect to mycorrhizal association rather than to the Klamath and southern Oregon forest types they mark. INFERRED from (i) to (iv). What the evidence does support, read strictly, is "the full model ranks reported mycorrhizal finds a little better than effort, road access and forest cover do, between weather cells, over the PNW box".
