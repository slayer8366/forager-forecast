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

## 2. Condition 1's pass and the band selection (`nested_selection.py`, `.json`, `.log`)

**What the selection was.** READ, `scripts/t7_fit.py` `cmd_fit`: each candidate band's held-out gain over the base is `diff(data, preds[key], preds["base"])`, whose interval is clustered by **weather cell** (the `diff` default), over all 24 blocks; a band is kept when that interval is wholly above zero. Condition 1 then scores the full model on the same 24 blocks' held-out predictions. My reproduction of the eight add-one figures matches the report to 1e-9 and picks the same three bands.

**How much of the margin the selection explains.** Condition 1's point is +0.00379. Of that, base minus B (no selection) is +0.00163 and full minus base (the three selected bands) is +0.00216 [+0.00078, +0.00353] block-clustered (section 1). So the selected bands supply **57% of the point margin**, and base minus B alone has a block interval that includes zero (−0.00131 to +0.00670). COMPUTED.

**Leave-one-block-out selection.** I re-ran the add-one rule 24 times, each time on the other 23 blocks' held-out predictions (the same rule, the same weather-cell resampling, 1,000 draws, seed 20260918), to see which bands a selection that had never seen the held-out block would choose. COMPUTED:

- With all 24 blocks the rule picks *Lithocarpus*, *Chrysolepis*, *Arbutus*: the coder's set.
- **In 20 of the 24 folds the chosen set differs.** In 16 of them *Larix* joins the three (its all-block lower bound is −0.000004; drop almost any block and it is +0.00001 to +0.0001). Holding out the Coastal Range (5,992 presences) the set is *Larix*, *Chrysolepis*, *Arbutus*, *ecm_hosts*; the Puget Lowland, *Larix*, *Populus*, *Chrysolepis*, *Arbutus*; the Klamath Mountains, *Larix*, *Lithocarpus*, *Chrysolepis*; the Willamette Valley, *Larix*, *Chrysolepis*, *Arbutus*. *Lithocarpus*'s lower bound turns negative whenever any one of the three big western blocks is held out (−0.00035 to −0.00056), so its gain lives in those blocks.
- Only 4 folds (Colorado Plateaus, Middle Rockies, Idaho Batholith, Northwestern Great Plains) choose the coder's set; three of those hold out 0 to 91 presences.
- **The nested condition 1 cannot be computed from the cache.** A fold whose choice is a set of two or four bands has no held-out predictions for that model (only the base, base plus one band, and the one full model were fitted). Fitting the twenty missing models is twenty leave-one-block-out ladders, about the cost of the main fit's full model each: not a small refit, so a stop under the dispatch, not done.
- **The strongest bound I can give.** Scoring those 20 blocks by the base (the choice that adds no band; a lower bound on the gain for any set that helps, and the honest fallback where the chosen set is unknown) gives nested full minus B = **+0.00182 [−0.00129, +0.00733]**, pooled nested AUC 0.8907 against the base's 0.8905 and full's 0.8927. That is a lower bound dominated by the base, not an estimate. The upper bound is the reported +0.00379, which assumes the selection carries no optimism at all. The truth is between, and the one thing the folds show for certain is that the rule's output is not stable to a single block.

**Would condition 1 pass without the selection?** **No.** The unselected habitat model is base minus B, +0.00163 [−0.00131, +0.00670], and it fails. The only way condition 1 passes is through three bands chosen on the same held-out blocks that score it, by a rule whose choice changes in 20 of 24 leave-one-out folds, and whose decisive member in the biggest blocks (*Lithocarpus*) has a lower bound of +0.00008 on all blocks and a negative one when any of those blocks is withheld. COMPUTED for the figures; INFERRED for the reading. A refit with a nested selection (choose on the 23 training blocks inside each outer fold, D138's rule unchanged) would settle it, and is the one strengthening step I can see that bears on condition 1 (section 7).

## 5. Condition 4, the specimens (`condition4_check.py`, `.json`, `.log`)

**The filters, as D158 states them.** READ, `src/forager_forecast/t7/specimens.py`: `classify` drops a record whose dataset licence is not CC0 or CC BY (both URL and code spellings; BY-NC and BY-SA are None), then whose own licence is not, then with no stated uncertainty, then over 1,000 m, then whose names do not join the mycorrhizal main run through the same `Join` V9 used; `assert_open_licences` re-checks every kept row. COMPUTED on `specimens_kept.csv` (6,026 rows, sha256 as registered): the licence columns hold only CC0 and CC BY 4.0 in either spelling; uncertainty runs 1 m to 1,000 m; every record's point falls in the cell the file names. **One thing the filter admits that the dispatch's wording ("genera") may not have meant:** 99 genera are in the kept set, and **23 of them have no presence at all in the platform main run** the map was fitted on (*Tomentella*, *Piloderma*, *Sebacina*, *Hysterangium*, *Amphinema*, *Dermocybe*, *Gymnomyces*, *Macowanites* and the rest: resupinate, corticioid and false-truffle ectomycorrhizal fungi that herbaria hold and the platforms do not report). They join the main run by the membership list, so the rule was followed; they are a slightly different group from the one the map was trained on. Their count among the scorable 4,014 is not separated out (not checked).

**Scoring and matching, reproduced.** COMPUTED with my own circle mean, band edges and draw: the raster's valued cells are exactly the table's cells inside the area of applicability (6,950,510 both ways); 4,014 of 6,026 specimens are scorable; the background's road-band counts equal ten times the specimens' in every band; the whole-box figure is **+0.19615 [+0.06645, +0.28547]** and the interior's **+0.10333 [−0.15708, +0.23985]**, both equal to the report's to 1e-9. The specimen median score is −1.654 against the background's −2.102.

**What the pass can bear.** I had predicted (prediction 5) that the margin was mostly geography between blocks and would fall below +0.10 with a block-matched background. **That prediction was wrong**, and the figures are the correction:

| variant (the review's; not rulings) | specimens / background | AUC − 0.5 [block interval] |
|---|---:|---|
| as ruled (circle mean, road-band match, whole box) | 4,014 / 40,140 | +0.196 [+0.066, +0.285] |
| the map's value at the own cell instead of the circle mean | 4,014 / 40,140 | +0.192 [+0.098, +0.262] |
| background matched on road band **and the specimen's level III block** | 4,014 / 40,140 | **+0.178 [+0.104, +0.239]** |
| background matched on road band **and the specimen's weather cell** (2,262 specimens fell back to their block where the cell's band held fewer than ten cells) | 4,014 / 40,140 | +0.129 [+0.030, +0.202] |
| within one weather cell only: specimens against their own cell's matched background, pair AUC | — | **0.513** |
| specimens from 2000 on | 460 / 4,600 | +0.211 [+0.138, +0.271] |
| before 2000 | 3,504 / 35,040 | +0.193 [+0.051, +0.287] |
| before 1970 | 1,267 / 12,670 | +0.169 [+0.043, +0.301] |
| the one herbarium (UW macrofungi) | 2,770 / 27,700 | +0.216 [+0.078, +0.320] |
| the other herbaria | 1,244 / 12,440 | +0.153 [+0.002, +0.286] |
| specimens in the four western blocks | 3,281 / 32,810 | +0.227 [+0.042, +0.335] (9 of 1,000 draws held no specimen, left out and counted) |
| specimens outside those four | 733 / 7,330 | **+0.063 [−0.046, +0.177]** |
| no matching at all: every seventh valued cell as background, point scores | 4,014 / ~993,000 | +0.162 (no interval) |

Reading, INFERRED from the table:
- **The pass is not an artefact of the circle mean, of the decade, or of one herbarium.** Point scoring gives the same answer; the 460 post-2000 specimens score as high as the old ones; the other herbaria pass on their own, barely.
- **It is not mostly between-block geography either**, which is where my prediction failed: matching the background inside the specimen's own block keeps +0.178 with a tighter interval. Inside blocks, specimens sit on cells the map rates higher than road-matched cells of the same block.
- **It is largely within-block, between-weather-cell structure, and it fades inside a weather cell.** Matching inside the weather cell drops the figure to +0.129 (and more than half the specimens could not be matched inside their cell at all); over the pairs that do share a cell the map ranks specimens at 0.513, close to chance. That is the same shape condition 2 found with the platform data: the map's information about where a find is lies at the scale of tens of kilometres, not of 250 m cells.
- **Outside the four western blocks it does not pass** (+0.063, interval including zero, on 733 specimens), and the interior sub-box does not pass (+0.103, −0.157 to +0.240, on 390). The pass is a western-Washington-and-Oregon result.
- **Clustering.** The 4,014 scorable specimens occupy 860 distinct cells and 481 weather cells; the ten most-collected cells hold 233, 142, 127, 101, 86, 73, 57, 55, 53 and 52 specimens each. The block bootstrap treats each block as a unit, which covers this, but the effective sample is a few hundred stations, not four thousand records, and the matched background is drawn fresh per record (ten cells each), so the background is far less clustered than the specimens. A background drawn per station would be the honest comparison and was not built (a design choice beyond a review).
- **Is the interior result usable?** As a verdict, no: 390 specimens from a handful of stations, an interval from −0.157 to +0.240, and 340 of the 751 interior records dropped because their cells have no host shares. As a description it says one thing: nothing in the interior contradicts the map, and nothing confirms it.

What condition 4 shows, read as far as it goes: herbarium collectors in western Washington and Oregon, from the 1930s to the 2020s, collected these fungi in places the map rates higher than road-matched places nearby, inside the same ecoregion, by a margin that survives every slice I tried except the within-weather-cell one and the interior. It does not show that the map ranks *mycorrhizal* habitat (section 4), and the 0.513 within a cell says it does not show the map's 250 m detail is right.

## 6. The map (`render_map.py`, `.json`; the PNGs in the evidence folder)

Rendered, not shown: `map_refit.png` (1 km pixels, five equal-count greens over the shaded cells, greys for the codes), `map_judged.png` (the 2026-10-16 map, same classes), `map_rank_shift.png` (rank percentile in the re-fit minus rank in the judged map, blue fell, red rose, saturated at ±0.3), `mask_refit.png` (the codes alone; orange is code 2, outside the area of applicability), `canada_edge_refit.png` (full resolution, 600 by 1,200 cells across the northern edge).

**Counts, COMPUTED from the rasters.** 25,689,272 cells in the window; code 1 (shaded) 6,950,510, equal to the cells with a value; code 2 (outside the area of applicability) 16,738 (16,478 on 2026-10-16); code 3 (Canada) 102,543; code 4 (no host shares) 9,447,216; code 5 (no pH) 23,834; code 6 (water or unmapped) 133,292. 6,941,779 cells are valued in both maps; 8,731 only now, 8,991 only before. Spearman between the two maps over those cells 0.9117 (the coder's 0.912 matches); 58.0% of the re-fit's top tenth was in the judged top tenth (matches). 10.1% of cells moved more than 0.2 in rank; the 1st and 99th percentiles of the shift are −0.32 and +0.33.

**What the map shows, in words.** The darkest fifth is the high conifer forest: the North Cascades from the Skagit to the border, the Cascade crest south through Washington into Oregon, the Idaho Batholith and the Columbia Mountains/Northern Rockies up to the border, the Canadian Rockies' edge, and the Blue and Wallowa mountains. Middle shades cover the Coast Range and the Olympics' lower slopes, the eastern Cascades and the Middle Rockies. The pale fifths are the Klamath Mountains and the southern Oregon coast, the Willamette Valley's margins, the Puget Lowland's remaining forest, and the foothill forest of the Great Basin ranges. Half of the shaded area in the box (every non-forest cell, code 4) is blank. By block the top tenth is 20% Columbia Mountains/Northern Rockies, 18% Idaho Batholith, 12% North Cascades, 11% Cascades, 10% Canadian Rockies, 8% Blue Mountains, 8% Middle Rockies, 7% Coast Range, and under 1% each in the Puget Lowland, Klamath and Willamette. The top tenth's median road distance is 793 m against 305 m over all shaded cells (COMPUTED; matches the coder's figure), and Spearman of the map's rank against road distance over shaded cells is +0.17: the map leans gently toward remote forest, not toward roads.

**Where it moved.** The shift map has two layers: a fine speckle of ±0.1 everywhere (the three new bands and the access term re-weighting cells individually), and coherent regions. **Rose:** the North Cascades (mean rank shift +0.074), the Wasatch and Uinta (+0.096), the southern Oregon coast and the Klamath coast strip (where tanoak, chinquapin and madrone grow), the Olympic Peninsula's northeast, the Northern Basin and Range foothills. **Fell:** the Willamette Valley (−0.092), the outer Olympic coast and the central Oregon Coast Range (a blue band along the coast), the Columbia Mountains (−0.020) and the Idaho Batholith (−0.018) slightly, the Eastern Cascades slopes. The western valleys and the wettest coast fell, the dry-side mountains and the broadleaf south coast rose. INFERRED: the first is the access term taking the near-road, near-town signal those lowlands carried; the second is the three southwestern broadleaf bands.

**Artefacts.** None of the kind I looked for. No tile seams, no striping and no blocky edges are visible at 1 km, and none at full resolution across the 600 by 1,200 cells of the northern edge. The code-2 cells are speckles, concentrated in the southern Oregon Coast Range and Klamath coast (the extreme of the new broadleaf bands) and along the Olympic coast, consistent with what an area-of-applicability test should flag; they are 0.24% of shaded cells. The Canadian side is a single flat lavender region in the top-left corner (the box's northern edge sits at 49 N, so Canada enters only where the border bends south along the Strait of Georgia); its edge against the US cells is the straight box boundary and the shoreline, with no halo or gradient on the US side. Water bodies (Puget Sound, the Columbia, the large reservoirs and lakes) read as code 6 and look right.

One thing worth stating for the owner: half the shaded cells (3,212,602 of 6,950,510, READ from `fit_report.json` `aoa.counts.inside_outside_frame`) lie in weather cells outside T6's effort frame, where no background was drawn and no presence could enter. The area of applicability covers habitat space, not geography, so the map is extrapolating there in effort, not in habitat. P6 makes that harmless for the ranking, but anyone reading the map should know that the eastern and southern thirds were never scored against a single record.

## 7. Verdict and the one-line answers

### Mechanism prediction, scored

| predicted | found | |
|---|---|---|
| 1. everything reproduces exactly from the cache | every figure matched to 1e-9, including condition 4 and the side runs | right |
| 2. base minus B fails; the leave-one-out selection does not pick the same bands every time; the nested estimate sits between base minus B and the reported figure with an interval including zero | base minus B fails; the chosen set differs in 20 of 24 folds; the nested figure cannot be computed from the cache, and its lower bound (+0.00182 [−0.00129, +0.00733]) includes zero | right on the first two; the third is a bound, not an estimate, which the prediction did not foresee |
| 3. the road band alone ranks within-cell pairs at about A's 0.648; the collapse is the road band; holding access does not pull the map toward roads | −road alone 0.654, above A and above full; top tenth median road distance 793 m against 305 m overall; Spearman of rank against road distance +0.17 | right |
| 4. the saprotroph and *Laetiporus* gains reproduce; "mycorrhizal" is not supported | reproduced; and inside the group the common ectomycorrhizal genera gain nothing | right |
| 5. condition 4's pass is mostly between-block geography; block-matched background drops it under +0.10 with an interval including zero; point scoring and era make little difference | **wrong on the main claim**: block-matched is +0.178 [+0.104, +0.239]; right that point scoring (+0.192) and era (post-2000 +0.211) change little; what does bring it down is matching inside the weather cell (+0.129; 0.513 on the pairs that share a cell) and leaving the four western blocks (+0.063, includes zero) | half wrong |
| 6. interior conifer forest highest; a flat Canadian band with a hard border edge; few scattered code-2 cells; close to 2026-10-16 with the top tenth shifted toward the Cascades | as predicted, except that Canada is a corner, not a band (the box ends at 49 N), and the clearest regional moves were the Willamette Valley and outer coast falling and the southern Oregon coast rising, which I had not named | mostly right |

Where I was wrong (5), I was wrong in the direction of under-rating the specimen result. It is more robust than I expected, and section 5 says so.

### Verdict

**Blocking** (for showing this map to anyone as what its label says):
1. **P10b fails, confirmed by independent recomputation** (conditions 2 and 3). Under D145 that is the bar, and nothing in this review moves either failing condition: within a weather cell the habitat bands add nothing to the road band (section 3), and the mycorrhizal gain is not shown above the saprotroph group's (section 4).
2. **Condition 1's pass rests on a selection step that is not stable** (section 2): the full model's margin over B is 57% selected bands, the unselected model fails the condition, and the selection rule's output changes in 20 of 24 leave-one-block-out folds. The nested figure is not computable from the cache; its lower bound includes zero. Condition 1 should be read as "not established" rather than "pass" until a nested selection is run.
3. **The label "mycorrhizal" is not supported by any test in the run** (section 4). This holds whatever happens to conditions 1 and 2.

**Should-fix** (in the report and the next step, not blocking a decision):
4. The report's condition 1 row should carry the selection caveat in the verdict table, not three sections below it; a reader of the table alone takes a pass.
5. `fit.log` should print the block-resampled condition 2 interval, as the coder notes.
6. The specimen set's 23 herbarium-only genera (no platform presence) should be counted and reported in condition 4, with the figure beside for the 76 genera the map was trained on.
7. Condition 4's background should be drawn per collecting station (distinct cell), or the specimens thinned to one per cell, so both sides carry the same clustering; the block bootstrap covers blocks, not stations.
8. The map's reader should be told that half the shaded cells lie outside the effort frame (section 6).
9. The report's "within one weather cell: A 0.6481" deserves one more sentence: the raw road distance does better (0.654), so A's within-cell figure is the road band and nothing fitted.

**Notes:**
10. The coder's report is accurate everywhere I checked it: every number, the reading of the condition 2 log line, the per-block table and the map comparison. Its caveats (items 3 and 4 of its "what changed" section) are the right ones, and this review mostly sharpens them.
11. The access ruling (D156) is implemented as stated, and it did what it was meant to: the map moved away from roads, and the within-cell test became honest.
12. The Puget Lowland is the one block where presences sit farther from roads than background inside a cell (within-cell A 0.470); the monotone −1 constraint is wrong there. It is 2,330 presences, 15% of the run. Not a bug, a limit of a one-direction access term in urban forest.
13. Condition 4 is the strongest evidence in the run, and it is evidence for a modest claim: the map's between-weather-cell ranking agrees with where western-Washington-and-Oregon herbarium collectors found these fungi, after road matching. It is not evidence for the 250 m detail (0.513 within a cell), the interior, or the word "mycorrhizal".
14. Tuning at the grid's edge (every B, base and full fold at `c16`) stands as the coder reported; not re-examined here.

### The one-line answers

- **Does the evidence support showing this map to anyone, and under what wording?** Not under any wording that includes "mycorrhizal", "habitat" for a group, or a 250 m claim; the bar the owner set (P10b) fails on the two conditions built to test exactly those words. If the owner chooses to show it anyway as a research view, the wording the evidence supports is: "where reported finds of this fungus group cluster in the Pacific Northwest, after allowing for where people search and how near roads they are; a relative ranking at the scale of tens of kilometres; not a habitat model; not reviewed as one". Publishing is the owner's decision, not this review's.
- **Is a further strengthening step likely to change the P10b verdict, and which one?** Not the verdict. One step is worth running for the record: a nested band selection (choose the candidate bands on the 23 training blocks inside each outer fold), which settles condition 1 either way at about the cost of one full model per fold; and condition 4 per station. Neither can rescue condition 2, whose failure is structural (the road band ranks within cells better than the fitted habitat does), nor condition 3, where the comparison group gains as much. A different design could: a host-specific target (the bolete and tooth genera that do gain, section 4) against a matched saprotroph set, tested within cells. That is a new question, not a strengthening of this one.
- **Or does the evidence point to stopping T7 for the PNW?** For the question T7 asked, "does a mycorrhizal-host habitat map add to effort and access, and can it be shown", the answer is in: no, on this data, and the two re-fits have measured why. I would stop T7 as posed, keep the two maps and the rasters as the record of it, and treat the within-block-between-cell signal that condition 4 found, and the per-genus gains, as leads for a narrower question rather than a reason to run a third fit of the same design.

## Not checked

- No model was refitted; the nested-selection estimate (section 2) is therefore a bound, not a figure.
- The 23 herbarium-only genera's share of the 4,014 scorable specimens.
- LightGBM's determinism across thread counts; the tuning grid's edge; the `NotGeoreferencedWarning` the coder noted.
- Whether the specimen records duplicate any platform record.
- Review 2 was not read, by the dispatch's rule.
- The recompute script was run twice: once as first committed and once after `review_common.py` gained the degenerate-draw count (section 5); the figures are identical both times (the second run's `recompute_p10b.log` and `.json` are the committed ones), and that is stated here rather than left to the commit history.

## Decided beyond scope

- `pyproject.toml`: the review's evidence scripts are added to ruff's exclude list, as D124 and D132 do for committed evidence scripts, so the branch's lint stays green without reformatting what ran. One line.
- The run logs are force-added past the repository's `*.log` ignore rule, as the evidence of what ran; they are small.
- The rank-shift image is rendered at 2 km pixels because the 1 km file exceeded the repository's 1 MB hook.
- Degenerate bootstrap draws (a resample holding no specimen) are counted in the output rather than raising; one variant (the four western blocks) had 9 of 1,000.
