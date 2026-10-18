# Review 2 of the T7 PNW re-fit under P10b

Sorrel Tally, independent reviewer, review 2 of two. Written 2026-10-17 (Pacific). Session model as the session header gives it: claude-sonnet-5-5 (the coder was Opus). Dispatch: `docs/dispatch/2026-10-17-t7-refit-review.md` (branch `t7-strengthen-plan`, 83f02582). Owner's go: Forager RECORD -1232. Branch `t7-refit-review-2`, from `t7-refit` at `da1f207`. I did not read review 1.

Flags: **READ** is something a file or log says. **COMPUTED** is my own code on the cached data. **INFERRED** is my reasoning. Every script and log is in `docs/audits/2026-10-17-t7-refit-review-2/`, committed as it ran (edits made during the session are listed under "Provenance").

## Mechanism prediction (written before computing; `PREDICTION.md` in the folder), scored at the end

- P1. All four figures reproduce exactly.
- P2. The three bands picked on the scoring blocks explain more than half of condition 1's margin; without the selection the lower bound crosses zero.
- P3. Road access is implemented as stated, but holding it on the map also flattens real remoteness-correlated habitat signal; condition 2's collapse is the road band absorbing within-cell reporting.
- P4. Mycorrhizal minus saprotroph gain is indistinguishable from zero; Laetiporus gains as much; nothing supports a "mycorrhizal" label.
- P5. Condition 4 passes but cannot bear much (old records, one herbarium, shared stations); the interior is unusable.
- P6. The map moved mostly near roads, with a visible hard edge at the Canada mask.

## Baseline (READ and COMPUTED, all matched)

- `origin/t7-refit` = `da1f2078`; `origin/t7-build` = `5c1a9df`. `0560dae` is an ancestor of `t7-refit`, and `git diff --stat 0560dae origin/t7-refit -- src scripts` is empty, so the fit's code is what is on the branch.
- `outputs/manifest.json` sha256 `af0fc2dd…b648ec`, the raster `504d59b3…`, the applicability raster `ee8b9e44…`, the block report `ceaa6ed8…`: all equal to the report's table. The manifest's `code_commit` is `0560daeed37da46a…`.
- `fit.log` last line: manifest `af0fc2dd…`, done in 51,983 s. Draft PR #5 is open (`gh pr view`: `isDraft true`, `state OPEN`).
- Specimen zip sha256 `28efb80e2d1e662c5dd389308ef608dd4a5760c60ca1178237249bb76d8634ad` matches `fetch.log`.
- The training table (assembled by the coder's `Data` loader, input assembly only, `00_dump_inputs.py`): 15,624 presences, 500,000 background, 24 level III blocks, held road distance 258.287 m.

## Verdict

**P10b fails, and I reproduce it: conditions 1 and 4 pass, conditions 2 and 3 do not.** I found no defect in the fit's code or arithmetic. What I found is about what the passes mean.

### Blocking
- None against the coder's work. For any showing: P10b (the owner's bar, D145) is not met, by my own recomputation (Q1), so the map must not be shown under that bar, and not under a "mycorrhizal" label on any bar (Q4).

### Should-fix
1. **The ladder's selection rule and condition 1 use different resampling units, and the kept bands change with the unit.** READ: `t7_fit.py` `diff()` defaults to weather-cell clusters, and the add-one step keeps a band when that interval is above zero (fit_report `add_one`: Lithocarpus +0.00055 [+0.00008, +0.00101] kept; Larix [-0.000004, +0.00074] not kept). COMPUTED: under condition 1's own block resampling Lithocarpus is not kept (+0.00055 [-0.00077, +0.00150]) and Larix is (+0.00041 [+0.00012, +0.00133]); Chrysolepis and Arbutus are kept either way. The report does not say this. Either rule is defensible; the report should say which was used and that the other keeps a different set. Whether the other set would pass condition 1 is **not checked** (it needs a fit).
2. **Condition 1's selection optimism is now measured, and it matters (Q2).** The report lists it under "not checked"; the figure is below. The wording "condition 1 passes" should carry it.
3. **Laetiporus's "almost three times the mycorrhizal group's gain" is a point comparison.** Under block resampling (D145's unit) Laetiporus's gain is +0.0141 [-0.0082, +0.0437] and the mycorrhizal-minus-Laetiporus contrast is -0.0092 [-0.0348, +0.0184]. The report's own interval for Laetiporus (+0.0005 to +0.0290) is the weather-cell one. The difference is not shown either way; it should not be written as a finding.
4. **Condition 4's clustering is not in the report's caveats.** 625 of the 6,026 kept records sit at one coordinate (48.546864, -123.011438), 233 at another and 142 at a third; the 4,014 scorable specimens fall in 860 distinct 250 m cells (COMPUTED, `04_specimen_stats.py`, `05_condition4.py`). My checks (Q5) show the pass survives this, but the report should state it.
5. **`fit.log` prints only the weather-cell interval for condition 2** (the coder says so; confirmed). Print both.

### Notes
- The 2,012 non-scorable specimens (33%) are mostly on cells with no host shares (code 4) or no soil pH (code 5), or outside the box or the study area, so the condition is scored on forested cells only (COMPUTED, code counts in `04_results.txt`: 1,053 on code 4 and 749 on code 5, plus 126, 35 and 32).
- Within one weather cell, presences are paired with very few background points: the within-cell pairs hold 0.027% of all pair weight (COMPUTED, `01_results`/log). Condition 2's interval is wide for that reason (the block interval's upper end is +0.016).
- The tuning ran to the edge of the grid again (the coder's item 8); I did not test a wider grid.
- My CI wording, "wholly above zero", follows the code; none of my figures is a new threshold.

## Q1. Reproduction (COMPUTED, `01_reproduce_conditions_1_2.py`, `02_condition3_and_selection.py`, `05_condition4.py`)

My own code. A pooled AUC under a block draw is a quadratic form in the draw counts over a 24 by 24 matrix of concordant pair weights (`rv2lib.py`, explained in its docstring), with the fit's draws (seed 20260918, 1,000 resamples, 24 sorted blocks). It equals a brute-force O(n squared) computation on a tie-heavy subsample, with and without a block draw, pooled and within one cell (`09_positive_control_and_revert.py`: "POSITIVE CONTROL OK").

| condition | reported | mine | matched |
|---|---|---|---|
| pooled AUC A / B / base / full | 0.88782 / 0.88891 / 0.89054 / 0.89270 | 0.88782 / 0.88891 / 0.89054 / 0.89270 | yes |
| 1. full minus B, blocks | +0.00379 [+0.00105, +0.00924] | +0.00379 [+0.00105, +0.00924] | yes |
| 2. full minus A within a weather cell, level III block resampling | -0.00722 [-0.02570, +0.01614] | -0.00722 [-0.02570, +0.01614] | yes |
| 3. contrast (union of 24 blocks, one draw for both groups) | +0.00279 [-0.00196, +0.01054] | +0.00279 [-0.00196, +0.01054]; gains +0.00488 and +0.00209 | yes |
| 4. whole box | +0.19615 [+0.06645, +0.28547] | +0.19615 [+0.06645, +0.28547] | yes |
| 4. interior (no verdict) | +0.10333 [-0.15708, +0.23985] | +0.10333 [-0.15708, +0.23985] | yes |

D145's amendment, as I read it: condition 2's interval comes from block draws multiplying each row's weight by its block's count, pairs inside a weather cell kept even where the cell straddles blocks. A pair across two blocks weighs the product of the two counts; the matrix form builds that in. Because the figures agree to five places, the reading is the same as the coder's. Verdict confirmed: 2 and 3 are not wholly above zero, so P10b fails.

One caveat on method: the training table itself (which rows, weights, folds) came from the coder's loader; I did not independently rebuild it. The cached predictions are the coder's. I confirmed neither is internally inconsistent (row counts, held access 258.287 m, presences 15,624, background 500,000).

## Q2. Condition 1's pass and the selection (COMPUTED, `02_`, `03_`, `03b_`, `03c_`, `03d_`)

Plain answer: **no, condition 1 does not pass without the selection.** Base minus B is +0.00163 [-0.00131, +0.00670] (matches the report). Under a leave-one-block-out repeat of the selection it is +0.0022 [-0.0008, +0.0075], also not above zero.

Method for the second figure. For each held-out block, I redo the add-one selection on the other 23 blocks with the fit's own rule (candidate against base, weather-cell resampling, 2.5th percentile above zero, 150 resamples), then score the held-out block with the bands that selection kept. Only the add-one models and the one full model are cached, so a kept set is scored as the base's prediction plus the sum of each kept band's add-one change (a proxy). Validation of the proxy: the real three bands combined this way give +0.00351 [+0.00070, +0.00934] against the real full model's +0.00379 [+0.00105, +0.00924]. The candidate list was cut to the four bands that could be kept (Larix, Lithocarpus, Chrysolepis, Arbutus), because the other four had negative points or a weather-cell lower bound far below zero on all blocks; INFERRED that leaving one block out cannot move those over the line. A first attempt with all eight candidates and 300 resamples was too slow and stopped after three blocks (`03_run_aborted_first_attempt_300res_8cand.log`, the same kept sets).

| quantity | point and block interval |
|---|---|
| condition 1 as run: full minus B | +0.00379 [+0.00105, +0.00924] |
| selection-free: base minus B | +0.00163 [-0.00131, +0.00670] |
| leave-one-block-out selection ("nested") minus B | +0.00221 [-0.00075, +0.00747] |
| as run, minus the nested figure | about 0.0016, **42% of the margin** |
| upper bound on what selection can explain: full minus base | +0.00216 [+0.00078, +0.00353], **57% of the margin** |
| each single band added to B | +0.0022 to +0.0026 per band, every interval including zero |

What drives the gap between as-run and nested (`03c`): the selection is stable across folds (Chrysolepis kept in 24 of 24, Arbutus 23, Lithocarpus 21, Larix 19), so the loss does not come from picking different bands. It comes from three folds (the Puget Lowland, Coastal Range and Willamette Valley blocks) where Lithocarpus fails the rule once that block's own data are removed from the selection: scoring those blocks without Lithocarpus takes the figure from +0.0035 to +0.0022 (`03c_run.log`). So Lithocarpus's evidence lives in the same western blocks that score it. Per-block gains (`03d_run.log`): the largest contributions to the pooled full-minus-base gain are the Coastal Range, Klamath Mountains, Cascades and Puget Lowland blocks. INFERRED: tanoak, chinquapin and madrone shares are close to zero across Puget and the Willamette, so in those blocks they act as a position-in-the-south marker rather than a habitat measure; nothing here tests that.

Why this is not the whole story: the nested estimate is still positive (+0.0022), and its interval's upper end (+0.0075) is far above zero. What it shows is that the lower bound (+0.00105) in condition 1 depends on selecting on the scoring blocks. Under my nested repeat the lower bound is below zero.

## Q3. Road access (READ code, COMPUTED figures)

**Implemented as stated: yes.** READ: `model.py:46-52` puts `access_dist_m` in the features with monotone direction -1; `lgb_params` builds interaction groups `[habitat bands]` and `[log_effort, access_dist_m]` (`model.py:65-66`), so the raw score is a habitat part plus an effort-and-road part; `map_columns` and `predict_held` hold effort and road at constants; `area_of_applicability` takes only `habitat_features` (excluding both). The run's own log line reads "access: dist_road_m, monotone -1, held 258.3 m". COMPUTED: the held 258.2871 m is the background median in my table, and the ranking is unchanged at the road quartiles (shift identical), as the report says.

**Does holding it remove habitat signal correlated with remoteness? Not on the evidence I can compute; the map tilts toward remote places more, not less.**
- COMPUTED (`07`): on the background rows, road distance correlates weakly with the habitat columns: Spearman +0.24 with Abies share, -0.15 with Douglas-fir, -0.16 with broadleaf cover, +0.12 with conifer cover, and no more than 0.08 with the rest.
- COMPUTED (`11`): across the shaded map, the score's Spearman with road distance is +0.171 now against +0.113 on 2026-10-16; the top tenth's median road distance is 793 m against 593 m (the report's figures, matched).
- COMPUTED, a small stated refit (`08`, one model on all rows, final configuration c04, the repo's own training function; in-sample on both parts, so only for shares and correlations): the model's gain is 69% effort and 7% road distance; the habitat part alone correlates +0.20 with road distance on the background rows. So the road term took out the near-road reporting tilt, and the leftover habitat part leans toward remote cells.
- The remaining question, whether the road term over-absorbed real habitat (near-road forest types), cannot be separated from reporting with these data, because road distance is the only handle. **Unverified.**

**Condition 2's collapse (+0.054 before, -0.007 now): INFERRED to be the road band explaining reporting within a cell, with a limit on how hard that can be said.**
- COMPUTED (`07`): within one weather cell, the **negative of road distance alone**, with no model, ranks presences above background at 0.654 [0.571, 0.698]. Model A with the road band scores 0.648; the full model 0.641; base 0.637; B 0.612. The 2026-10-16 full model's within-cell figure was 0.548. So road distance alone beats everything the habitat bands gave last time.
- Single habitat columns within a cell: total cover 0.488, conifer cover 0.494, Abies share 0.467, soil pH 0.558 [0.499, 0.592]. None is meaningfully above 0.5.
- The limit: the block interval for condition 2 is [-0.026, +0.016], so "the habitat bands add nothing within a cell" is not shown either; what is shown is that they add nothing detectable, on a pair set that is 0.027% of all pair weight.
- "Reporting effort" is also my inference: road distance may be a landscape proxy (roadless forest) as much as a collector's habit.

## Q4. Condition 3 and the comparison groups (COMPUTED, `02_`)

- **Matched.** Mycorrhizal gain (full minus A) +0.00488; saprotroph +0.00209; contrast +0.00279 [-0.00196, +0.01054].
- **Block-resampled gains, which D145's unit makes the right ones to quote:** mycorrhizal [-0.00008, +0.01281] (just crosses zero); saprotroph [+0.00010, +0.00528].
- **Laetiporus:** gain +0.01407, block interval [-0.00825, +0.04367] (606 presences). The coder's interval for it, [+0.0005, +0.0290], is the weather-cell one. Mycorrhizal minus Laetiporus: -0.00919 [-0.03479, +0.01844].
- **Does the evidence support "mycorrhizal" in a label? No.** The mycorrhizal group's own gain over A has a block interval reaching zero; the contrast with the saprotroph group is not above zero; and a wood-rot genus gains at least as much by point. The predictors are tree-genus shares, cover and soil acidity, none of which is specific to a mycorrhizal association as the model uses them. The rank correlation of 0.28 between the two maps (the report) shows the maps differ; it does not show host-specificity.

## Q5. Condition 4, the specimens (COMPUTED, `04_`, `05_`, `10_`)

**Filters.** I re-derived the kept set from the zip with my own filter: basis PRESERVED_SPECIMEN, dataset licence and record licence CC0 or CC BY, stated uncertainty 1,000 m or less, genus in the main run (ectomycorrhizal, certainty clear, 312 genera). I get 6,024; the coder's file has 6,026. The two extra are gbif ids 3962309388 and 3962310392. They belong to dataset 7827f68d (Intermountain Herbarium, "Vasc. &amp; Algae"), which my rights lookup missed because the title spells "&amp;" in the XML and "&" in `rights.txt` (READ both). The file's `dataset_licence` for them is CC0. So the filters reproduce: 6,026. Exclusions in order (mine): 75,904 dataset licence, 32 record licence, 63,255 no uncertainty, 86,188 over 1,000 m, 25,375 genus not in the main run.

**Scoring.** My own circle mean, matched draw (10 background per specimen, same road band and radius), unweighted AUC and block bootstrap reproduce the report's whole-box and interior figures exactly (table in Q1). The road bands are the coder's edges (50, 100, 250, 500, 1,000, 2,000, 5,000 m); matching is on road band at the specimen's own cell only.

**What the pass can bear.** The records are old (decade counts: 1930s 164, 1940s 673, 1950s 511, 1960s 859, 1970s 1,053, 1980s 708, 1990s 1,208, 2000s 433, 2010s 211, 2020s 68, no year 100); 72% (4,338) come from one herbarium (University of Washington, dataset 96ccdb74), 10% from another (San Francisco State, 4d69b363). I tested whether the pass survives what the report lists as not matched:

| subset | specimens | AUC minus 0.5 [block interval] | within-block pairs only |
|---|---:|---|---|
| whole box (as run) | 4,014 | +0.196 [+0.066, +0.285] | +0.207 [+0.069, +0.276] |
| each 250 m cell counted once | 4,014 | +0.167 [+0.086, +0.234] | +0.161 [+0.063, +0.216] |
| cells with 25 records or fewer | 2,474 | +0.181 [+0.096, +0.244] | +0.171 [+0.077, +0.231] |
| without the largest herbarium | 1,244 | +0.156 [-0.004, +0.279] | +0.176 [-0.033, +0.335] |
| year 2000 or later | 460 | +0.214 [+0.141, +0.267] | +0.211 [+0.166, +0.224] |
| year 2000 or later, not the largest herbarium | 214 | +0.187 [+0.065, +0.251] | +0.191 [+0.075, +0.274] |
| before 1970 | 1,267 | +0.166 [+0.043, +0.295] | +0.207 [+0.059, +0.318] |
| interior (no verdict) | 390 | +0.103 [-0.157, +0.240] | +0.024 [-0.224, +0.105] |

Single columns at the own cell, same matched draw (not the circle mean, so compare with the map at its own cell, +0.192): canopy cover +0.080, conifer share -0.150, soil pH -0.259; within-block pairs all about zero. So no one habitat column reproduces the map's figure.

My reading (INFERRED): the pass is more robust than the report's caveats suggested. It does not depend on the cluster of records at a few stations, on old records, or on comparing across regions (the within-block column). It does not stand alone on the second herbarium: without the largest one the interval crosses zero by a hair (-0.004) on 1,244 records, though the point is similar. What it measures is that the map ranks places where herbarium collectors of these genera have worked above road-matched forest cells; it is **not** a test of fruiting or of a forager's chance of finding anything, and the matching does not cover collecting stations (terrain, access beyond roads) or decade.

**The interior result is not usable:** 390 specimens in 140 cells, +0.103 [-0.157, +0.240], and within-block pairs only +0.024 [-0.224, +0.105]. It can neither support nor weaken the pass in the region where D158 asked the question.

## Q6. The map (COMPUTED and looked at: `06_render_maps.py`; PNGs `map_new_rank.png`, `map_old_rank.png`, `map_rank_shift_red_up_blue_down.png`)

PNGs show each map as percentile ranks among its own shaded cells, drawn every fifth cell, in this evidence folder only. I opened the new map, the old one and the shift image at an earlier, finer step (every third cell) and then re-rendered at every fifth to stay under the repository's 1 MB file limit.

- **Codes.** The two maps have the same grid and the same 6,967,248 eligible cells; 6,950,510 are shaded now (6,950,770 before); out of the area of applicability 16,738 (16,478); Canada 102,543 (same); no host shares 9,447,216 (same); no soil pH 23,834; water 133,292. So the map shades about a quarter of the box's cells; the grey-beige of the rest is forest-free, and it spans the Columbia Plateau and the Great Basin.
- **What it looks like.** Bright (high) values run along the Cascade crest and the north Washington Cascades, the Idaho Batholith and the northern Rockies in Idaho and Montana, and the western slope of the Wasatch; dark (low) values lie in the Klamath Mountains and southwest Oregon, the Willamette-side foothills, the Blue Mountains' margins and the small dry mountain islands in the south-east. The Oregon Coast Range reads mid to low and speckled.
- **How it moved.** The rank correlation with the 2026-10-16 map is 0.912 over the 6,941,779 cells shaded in both (matched to the report). Half the cells moved by less than 0.07 in rank, 5.5% by more than 0.25. The largest rises are the Olympic Peninsula, the North Cascades and the Washington Cascades, the Wasatch and the northern California and southern Oregon coast. The largest falls are the Oregon Coast Range and Pacific coast, the northern Idaho panhandle and the Columbia Mountains. **That is regional, not "near roads become lower" only**: the map's overall tilt to remote cells is real (Q3: +0.113 to +0.171), but the pattern in the shift image is blocks of whole mountain ranges and the coast, not road-lines.
- **Artefacts.** The shift image shows coarse patches with straight edges: for example, a roughly square rise over the Olympic Peninsula and a square-edged rise at the Cascades' west side. I did not trace them to a cause; they may be a class edge in the tree layer's tiles or a real step at a split; **unverified**. The speckle in the Oregon coast and the Idaho interior in the shift image is the single-cell noise a 250 m tree-share product has.
- **The Canada mask edge.** Only Vancouver Island is drawn as Canada (the grey block at the top left, a hard polygon edge, 102,543 cells); the box stops at 49 N, so the mainland's Canadian side is outside the map and drawn white. The edge is crisp and the same in both maps. The sea shows white; lakes show blue (they are code 6).

## Q7. One-line answers (recommendations; publishing and the next step are the owner's)

1. **Does the evidence support showing this map to anyone, and under what wording?** No under D145's bar, which my own recomputation shows is not met; if the owner decides to show it anyway, the only wording the evidence supports is: *"Experimental relative habitat index for the Pacific Northwest, built from where a group of fungal genera has been recorded, adjusted for reporting effort and road distance. Not a forecast, not host-specific, not validated within a weather cell. Ranks places against each other only."* Not "mycorrhizal habitat".
2. **Is a further strengthening step likely to change the P10b verdict, and which one?** Unlikely for conditions 2 and 3. For condition 2: road distance alone ranks pairs within a cell as well as the models do (0.654), and no habitat column does better than 0.56 there. The only lever not yet tried that could bring within-cell signal is terrain (elevation, aspect, slope), which varies inside a weather cell; no evidence here says it would. For condition 3, the predictors cannot tell a mycorrhizal group from a wood-rot one; more tree bands are not a route to host-specificity. Condition 1 would still lean on selection.
3. **Or does the evidence point to stopping T7 for the PNW?** It points to stopping the chase for P10b's "mycorrhizal habitat" claim for the PNW. What remains true and usable internally: a reporting-adjusted relative habitat index that passes P10 and an independent specimen check; whether that is worth carrying is the owner's call.

## Prediction scored

- P1 **right.** All six figures matched to five places.
- P2 **half right.** Selection explains 42% (57% at most), not "more than half"; without it condition 1 fails (base minus B +0.0016 [-0.0013, +0.0067], nested +0.0022 [-0.0008, +0.0075]), as predicted.
- P3 **half right.** Implemented as stated, yes; the road band explains the within-cell figure, yes (road distance alone 0.654). "Flattens real remoteness-correlated habitat signal": **not supported**; the map tilts toward remote places more than before, and the habitat part retains +0.20 correlation with remoteness.
- P4 **right**, with a correction I did not foresee: Laetiporus's gain exceeds the mycorrhizal one by point only; its block interval includes zero.
- P5 **half wrong.** The interior result is unusable, as predicted. But I expected the whole-box pass to be hollow; it survives the cell-weighted, recent-only, cap and within-block checks (smallest lower bound +0.043, apart from the without-largest-herbarium subset, which crosses zero by -0.004).
- P6 **partly wrong.** The map moved regionally (whole ranges and the coast), not mainly along roads; the Canada edge is a hard polygon on Vancouver Island only, as expected.

## Revert check (CLAUDE.md runner rules) on a result I depend on

Result depended on: the within-cell restriction (the same-cell pair set), which carries condition 2's figure and the road-distance-alone comparison. `09_revert_runner.sh`: saved `rv2lib.py` to a copy outside git before editing; one-line mutation (the same-cell branch counts a presence as concordant when it scores *below* the background point); `py_compile` of the mutated file passed before the run, and the runner refuses to cite results if it fails (it did not); ran; restored from the saved copy; sha256 of the restored file equals the original (`675215de…`, in `09_revert_run.log`); forward run after the restore shows "POSITIVE CONTROL OK" and the within-cell diff -0.00722 again. Under the mutation the within-cell positive control fails on its own line: pooled figures unchanged (0.64035 and 0.67178, equal to brute force), within-cell 0.35984 against brute force 0.64016 (the mirror, 1 minus 0.64016), then the assertion fails. A failure that this edit and only this edit could produce: the pooled lines stay correct, the same-cell lines mirror. I confirmed the forward change was still present afterwards by running the forward script, not from the runner's say-so.

## Not checked

- The training table and the cached predictions are the coder's; I did not rebuild the table or re-fit any of the ladder's models. I made one small stated refit (Q3, `08_`), a single model, in-sample, for shares and correlations only.
- Whether the block-clustered kept set (Larix, Chrysolepis, Arbutus) would pass condition 1: needs a fit.
- The cause of the straight-edged patches in the shift image.
- A wider tuning grid; LightGBM's thread determinism.
- The nested figure uses a proxy for combined bands (validated to within 0.0003) and 150 resamples for the selection rule (the coder used 1,000).

## Provenance and edits during the session

- `rv2lib.py`: my AUC and pair-matrix library; the revert check restored it byte for byte.
- Scratch data (not committed): `/mnt/work/Zynergy/rv2-scratch/` (tables dumped by `00_dump_inputs.py`, `00b_dump_side_inputs.py`; the first dump went to `/tmp`, which was full for the user's quota, and was redone into scratch).
- `03_nested_selection.py` crashed at its last print line (a string in a list was rounded) after the 24 selections had printed and before any scoring; the kept sets are read from `03_run.log` in `03b_nested_scoring_from_log.py`, which runs the unchanged scoring step. `03c` and `03d` are follow-ups to it.
- `05_condition4.py` was edited twice during the session (an unsigned cell id wrapped in the decode, fixed by a cast; a within-block column added) and the committed run log is from its final form. `06_render_maps.py` was run at a finer step first, then at every fifth cell for size.
- Nothing under `t6b` or `forecast-data/t7` was written; nothing was published; I never touched the other review's branch, worktree or report.
