# Independent review (D18) of the T7 PNW fit

Reviewer: an independent agent session started by the Forager planner (Rowan Waymark). Dispatch:
`docs/dispatch/2026-10-16-t7-fit-review.md` at `d911bf2`. Reviewed: branch `t7-build` at `b5c3d26`
(report) and `17bb84e` (evidence), code at `41f9c79`. Written 2026-10-17 UTC (evening of 2026-10-16
Pacific).

Flags: READ means a file says so (file and line given). COMPUTED means my own code, in
`docs/audits/2026-10-16-t7-fit-review/`, printed it. INFERRED means my reasoning.

## Prediction (mechanism, reviewer), written before computing anything

Written after reading the dispatch, the fit report and `src/forager_forecast/t7/model.py`, before
running any code.

1. **Habitat or effort.** `model.py` keeps `log_effort` in its own interaction group, so every fitted
   model is additive: habitat part plus effort part. The map at the held effort is the habitat part
   plus a constant, and model A at the held effort is a constant everywhere. So the dispatch's
   "effort-only map" can only mean A at each cell's own effort, the effort surface itself. I predict
   the habitat part correlates positively but only moderately with the effort surface (Spearman about
   0.3 to 0.5 over shaded cells inside T6's frame), because the habitat bands partly proxy for reachable,
   low-elevation, west-side forest that people search. Where they differ most: remote high forest
   (Cascade crest, Idaho Batholith, north Rockies) shaded high by habitat with low effort, and
   urban/valley lowlands (Willamette, Puget) with high effort but middling habitat. The pooled AUCs and
   the weather-cell intervals reproduce to rounding; block intervals include zero.
2. **Mycorrhizal-specific.** The habitat inputs carry a general "forest that people report fungi in"
   signal plus host-specific parts. *Laetiporus* gains more because its effort-only baseline is weaker
   (0.844) and broadleaf/oak shares carry real host signal for it. I predict the evidence supports
   "forest-associated fungal reporting" at most, not "mycorrhizal habitat", and that the comparison
   correlation reproduces near 0.23.
3. **Weight fix.** With the comparison group's weights summing to 2 over about 500,000 points, the
   per-point hessian is about 1e-6, so a 1,000-point leaf's hessian sum is about 1e-3 times
   p(1-p), under `min_sum_hessian_in_leaf` (1e-3): no split, so B equals A. For the main group (total
   about 90) a leaf's hessian clears the floor, so it splits, but `lambda_l2 = 10` is large against
   hessian sums of order 1 to 20, so leaf values shrink hard and the unfixed main fit is much more
   heavily regularised. Rescaling by a constant changes no share, threshold or sample, and leaves the
   weighted AUC unchanged. I predict the main group's sign of full minus A survives the unfixed weights
   but the margin changes, and I cannot predict its direction with confidence. The revert check fails
   with the "fit split at all" or the allclose assertion.
4. **D18 checks.** V9 counts reproduce exactly; 26 level III blocks with study cells is right and 25
   is a headline slip, as the report says.
5. **The map.** High along the west-side Cascades and Coast Range and the Puget lowland, low in the
   Columbia Plateau and basin and range. Artefacts I expect to look for: a hard edge at 49°N (Canada,
   code 3), possible seams at T6b's 256-tile edges and the `us_half` tiles, and blocky texture from the
   coarse soil pH layer.

(Findings follow below.)

## Verify first: the Baseline (all confirmed)

- `origin/t7-build` is at `b5c3d26`, with `17bb84e` and `41f9c79` beneath it (READ, `git log`).
  This branch is `t7-build` plus the dispatch commit `d911bf2`.
- The report and evidence folder are where stated (READ).
- `pnw-2026-10-17/manifest.json` sha256 is `f041714e…49d5` (COMPUTED). The output files hash to
  the manifest's `outputs` (COMPUTED): `relative_habitat_pnw.tif` `c186977d…6ff6`,
  `applicability_pnw.tif` `07baec5f…9c67` and `mask_map.png` `bb0f0df8…fc44`. The four presence
  files hash to the manifest's `inputs.presence_files` (COMPUTED). I did not re-hash the 892
  T6b tile files. They sit on the flash drive the t6b-night job is reading.
- `fit/cache/` holds 42 files: 21 prediction arrays, each with its JSON (READ, `ls`).
- `fit.log:111` reads "2026-10-16T11:43:32+00:00 P10: fail", and `fit.log:248` reads
  "2026-10-17T01:34:58+00:00 P10: pass" (READ). The smoke manifest records `dccb1f4`, the commit
  before the fix (READ, `smoke-evidence/fit_report.json`).

No mismatch, so no stop.

## Q1. Habitat or search effort?

### Headline figures, recomputed (COMPUTED, `recompute_figures.py` → `figures.json`)

I rebuilt the training rows with my own code (`common.py`), from the rules, without importing
`t7_fit.Data`. The rebuild gives:
- 23,069 presences in the file, 15,626 eligible and 15,624 entering;
- 44 genera that count alone, with 285 presences pooled;
- a pool of 3,745,167, and 500,000 background cells whose id-list sha256 is `3a411eb2…5184`,
  the manifest's value;
- total weight 45 on the presences and 45 on the background.

My row count equals each cache file's `n` (515,624), so the cached predictions line up row for row.

The AUC and the cluster bootstrap are my own code. The bootstrap uses the ruled seed (20260918)
and 1,000 resamples.

| figure | mine | report | match |
|---|---:|---:|---|
| pooled AUC A / B / base / full | 0.87728 / 0.87880 / 0.87961 / 0.88146 | same | exact (all digits) |
| full − A, weather-cell interval | +0.00419 (+0.00211, +0.00629) | same | exact |
| full − B, weather-cell interval | +0.00266 (+0.00100, +0.00423) | same | exact |
| full − A, forested, weather-cell | +0.00408 (+0.00201, +0.00623) | same | exact |
| full − B, forested, weather-cell | +0.00266 (+0.00094, +0.00435) | same | exact |
| full − A, block interval | +0.00419 (−0.00063, +0.01200) | same | exact |
| full − B, block interval | +0.00266 (−0.00041, +0.00811) | same | exact |
| full − A, forested, block | +0.00408 (−0.00091, +0.01152) | same | exact |
| full − B, forested, block | +0.00266 (−0.00013, +0.00826) | same | exact |
| ladder (8 add-one rows) | as the report's table | same | exact |

Further checks:
- **Monte Carlo stability.** With a different bootstrap seed (1), full − A is (+0.00224, +0.00621)
  and full − B is (+0.00107, +0.00419). Both stay above zero, so the ruled interval does not hang
  on the seed.
- **Intervals the report did not compute** (item 6: the base model involves no selection).
  - Base − A: +0.00233 (+0.00016, +0.00462) by weather cell, and (−0.00313, +0.01066) by block.
  - Base − B: +0.00081 (**−0.00093**, +0.00256) by weather cell.

  **Without the add-one selection, the habitat model does not beat B.** The P10 margin over B
  rests on the three bands chosen by looking at the same held-out blocks. INFERRED: so part of
  that margin is selection optimism, though how much is not measured.

### The map against the effort surface (COMPUTED, `q1_effort_map.py` → `q1_effort_map.json`)

**What "the effort-only map" is.** Model A is effort only, and monotone in `log_effort`
(`src/forager_forecast/t7/model.py:42`, `monotone_constraints`). Every model keeps effort in its
own interaction group (`model.py:45-46`, `interaction_constraints`), so the map at the held effort is the habitat part plus a
constant. At the held effort, A is the same constant everywhere. A meaningful effort-only map is
therefore A at each cell's own effort. That ranks cells as T6's log effort does, up to A's
plateaus. I compare the fit's own map pass (`fit/scores_all.npy`) with log effort per weather cell,
read through the project's `EffortSurface` (an input, not under review).

The held effort recomputes to 1.440701 (the report gives 1.4407).

**The map is not the effort surface.** Over the 3,738,115 shaded cells inside T6's frame:
- the Spearman correlation of the habitat score with log effort is **−0.007**;
- over the 3,959 weather cells, the cell-mean habitat score against log effort gives **+0.063**;
- half the score's rank variance (50.5%) lies within weather cells, where effort is constant;
- of the top-fifth habitat cells, 16% are in the top fifth for effort and 29% in the bottom fifth.

**Where they differ most.** By level III block, mean percentile among shaded in-frame cells,
habitat against effort:

| block | habitat percentile | effort percentile |
|---|---:|---:|
| Canadian Rockies | 0.74 | 0.35 |
| Idaho Batholith | 0.69 | 0.33 |
| Columbia Mountains/Northern Rockies | 0.62 | 0.33 |
| Blue Mountains | 0.59 | 0.33 |
| Middle Rockies | 0.42 | 0.26 |
| Central California Foothills | 0.10 | 0.52 |
| Puget Lowland | 0.39 | 0.79 |
| Willamette Valley | 0.42 | 0.73 |
| Klamath Mountains | 0.26 | 0.52 |

The first five are interior mountain forests, ranked much higher than the search effort there.
The last four are lowlands and the southwest, ranked lower.

**Outside the frame.** 3,212,655 shaded cells (46% of all shaded) lie outside T6's frame, where no
effort surface exists. Their scores span the in-frame distribution: quartiles at the 11th, 41st
and 75th in-frame percentiles.

**What a reader is told that effort alone would not tell them** (INFERRED from the above): which
forest, at 250 m, the model ranks for this group once search is held level. That ranking puts
interior mountain forest at the top (which bands drive it is in Q2), and puts the coastal lowlands, the Klamath and
the California foothills, where most people search, lower. That is a real difference in pattern.

**What the reader is not told: whether that ranking is right.** Its whole held-out value is the
+0.004 AUC above. It is negative at level I in Marine West Coast Forests, and it loses in the
Klamath, which the map ranks low (0.26). The pattern is not effort's.
Its skill is thin and not shown across blocks.

**The planner's prediction "the map is dominated by the effort surface's pattern" is not
supported.** My own prediction, a moderate positive correlation, was wrong too.

## Q2. Is it mycorrhizal-specific?

### Recomputed (COMPUTED, `recompute_figures.py` and `final_models.py`)

**The comparison group (*Laetiporus*).** The rows rebuild to 606 presences and 500,000
background, matching the cache's `n` (500,606).

| figure | mine | report | match |
|---|---:|---:|---|
| AUC full / A / B | 0.8670 / 0.8438 / 0.8517 | same | exact |
| full − A, weather-cell | +0.0232 (+0.0104, +0.0376) | same | exact |
| full − B, weather-cell | +0.0153 (+0.0053, +0.0267) | same | exact |
| full − A / − B, forested | +0.0235 (+0.0107, +0.0367) / +0.0159 (+0.0051, +0.0271) | same | exact |
| full − A, block-clustered (not in the report) | +0.0232 (−0.0018, +0.0530) | n/a | new |

**The side runs** reproduce exactly too: the licence track at 0.8344, 0.8150 and 0.8262, with
full − B at +0.0082 (−0.0005, +0.0167); the M2 side run at 0.8815, 0.8776 and 0.8793.

**The final models and the maps.**
- I retrained the final all-data model with my own LightGBM call (`common.fit`; c16 and the
  parameters of `model.py:28-47`). It reproduces the fit's `scores_all.npy` **bit for bit**: max
  absolute difference 0.0 over 6,967,248 cells.
- The comparison group's map against the main map, over shaded cells: Spearman **0.2295**. The
  report gives 0.230; mine matches to every digit, 0.22953581619880717.

### New evidence beyond the report (COMPUTED)

- **The main map against B's map.** B's map is effort plus conifer cover and broadleaf cover,
  scored at the held effort. Over shaded cells its Spearman with the main map is **0.456**. Nearly
  half the main map's ranking is what two plain cover layers already give.
- **What each final model leans on** (share of total gain):

  | input | main group | *Laetiporus* |
  |---|---:|---:|
  | effort | 90.0% | 58.5% |
  | every habitat band together | 10.0% | 41.5% |
  | soil pH | 1.2% | 12.3% (the largest single band) |
  | *Pinus* | 1.0% | 5.9% |
  | conifer share | 0.6% | 4.3% |

  The main group's largest habitat bands are *Picea* 1.6% and *Pseudotsuga* 1.3%, then soil pH
  1.2% and total cover 1.1%. The ectomycorrhizal host bands are not a dominant part of the main
  model, and the same bands carry more weight for a wood-rot genus.
- **Headroom.** The main group's A already scores 0.877, and *Laetiporus*'s A scores 0.844. As a
  share of the distance left to an AUC of 1:
  - the main group's habitat inputs close 3.4% of it (0.0042 of 0.1227);
  - *Laetiporus*'s close 14.9% (0.0232 of 0.1562).

  So *Laetiporus* gains more even after allowing for its lower baseline.
- **Configurations.** The comparison runs reuse the main run's per-fold configurations, as P7
  point 9 says (`scripts/t7_fit.py:623-642`). So its gain was obtained without tuning to it. That
  makes it, if anything, a conservative estimate.

### Reading (INFERRED)

The habitat inputs here carry a general signal: where in forest any fungus gets reported, after
effort. Soil pH, the pine and conifer shares and total cover help a wood-rot genus more than they
help the ectomycorrhizal group. The two maps share little (0.23), so the main map is not a copy of a
generic one. But nothing shows its specific part is host-driven:
- the host bands' gains are small;
- the selected extras are *Arbutus* (an ectomycorrhizal-capable host, but also a marker of
  southwest Oregon and northern California lowland) and *Chrysolepis*, both regional markers as
  much as hosts;
- the main map correlates more with plain cover (0.46) than with *Laetiporus* (0.23).

**Recommendation on wording (the owner's choice).** The evidence does not support "mycorrhizal
habitat". It supports at most a model-specific description: **"where mycorrhizal mushrooms are
reported, relative to search effort, by forest type"**, flagged as a pilot. The dispatch's
"forest-associated fungal reporting" is the safer and more honest of the two options it offers. I
would not use "habitat" alone without a qualifier that says the ranking is relative to reporting,
not to fruiting or presence.

## Q3. The weighting fix after a failed trial (`41f9c79`)

### What the fix is (READ)

`git show 41f9c79` touches two files:
- `src/forager_forecast/t7/model.py` gains `unit_mean_weights` (lines 50-59, `w * len(w) / w.sum()`),
  and `train` passes `weight=unit_mean_weights(w)` (line 65);
- `tests/test_t7_model_outputs.py` gains one test (lines 162-174).

Nothing else changed between the smoke run's commit `dccb1f4` (recorded in the smoke
`fit_report.json`) and the full run's `41f9c79`.

### Is it mechanically required? Did the unfixed fit split at all? (COMPUTED, `q3_unfixed.py`, `q3_split_features.py`)

I fitted c16 on all rows, once with the weights as M3 gives them and once rescaled:

| group, model | weights total | distinct predictions, unfixed | distinct predictions, rescaled |
|---|---:|---:|---:|
| *Laetiporus*, B | 2 | 3 | 26,589 |
| *Laetiporus*, full | 2 | 3 | 273,081 |
| main, B | 90 | 22 | 25,113 |
| main, full | 90 | 22 | 299,354 |

**Which inputs the main full model splits on:**
- **Unfixed:** `log_effort` only, 824 splits. Not one habitat input enters. The trees have 4 to 6
  leaves, against the 15 allowed.
- **Rescaled:** effort 1,767 splits, and every one of the 13 habitat bands is used (24 to 140
  splits each). The trees have 14 to 15 leaves.

**So without the fix the main group's full model is an effort-only model too, not only the
comparison group's.** The report's "the main run … was affected less, but was affected"
(report, Premises 1) understates it. At full background size the unfixed main model contains no
habitat at all.

INFERRED mechanism:
- At a total weight of 90 over 515,624 rows, the whole hessian is about 22 (90 × 0.25).
- `lambda_l2 = 10` is then of the same order as any leaf's hessian, so every leaf value is shrunk
  hard, and effort's residual stays the largest gain at every tree's root for all 200 rounds.
- `interaction_constraints` (`model.py:45-46`) then confine each tree that starts on effort to
  effort.

The smoke pass used a tenth of the background, so its per-point weights were ten times larger, and
it did split on habitat. That is why the bug showed there only in the one-unit comparison group.

### Does it change a ruled share, threshold or sample? (READ and COMPUTED)

No.
- **Shares.** The rescale multiplies every weight by one constant (`model.py:59`), so every M3 and
  P3 share is unchanged.
- **Sample.** The background draw does not read the weights (`background.py`, `draw_background`).
  My rebuild gives the manifest's background sha256 (Q1).
- **Thresholds.** The weighted AUC is a ratio (`metrics.py`, `_Ranked.auc`), and so is the tuning
  log loss (`folds.py:99-103` divides by `w.sum()`). Both are unchanged by a constant factor. The
  P10 rule, the D139 cuts and the AOA rule do not read the weight scale.
- **The AOA weights** are the final model's gains, so they do change, but only because the fitted
  model changes. The rule does not.

### Does the main group's result depend on it? (COMPUTED, `q3_unfixed.py` part 2)

I re-ran the verdict-relevant comparison with the unfixed weights:
- held-out predictions over all 24 blocks for A, B and full;
- each fold reusing the per-fold configuration the fit chose (`manifest.json`,
  `chosen_configurations`; no re-tuning, a disclosed shortcut).

| unfixed weights | value |
|---|---:|
| pooled AUC A / B / full | 0.8762 / 0.8681 / 0.8681 |
| full − A (weather-cell interval) | −0.0081 (−0.0113, −0.0050) |
| full − B | **0.00000 exactly**: full and B give identical predictions |

Under the unfixed weights there is no habitat model to judge. Full and B are both the same
effort-only fit, and both are worse than A (whose folds mostly used c15, which allows a deeper
effort curve). **The result depends on the fix entirely, because without it the model the plan
specifies is never fitted.** That is a defect being repaired, not a verdict being chosen.

### Was the fix tuned to the verdict? (READ and INFERRED)

No evidence that it was.
- **Timing.** The smoke run finished at 11:50Z (`fit/smoke.out`, manifest line), and the fix was
  committed at 11:56Z.
- **The defect the commit message names is visible in the smoke output.** The comparison group's
  B AUC equals its A AUC to every digit, 0.7948342574257433 (`smoke-evidence/fit_report.json`,
  `side_runs`).
- **There was one candidate change, and it is the standard one.** A scale normalisation leaves
  every ruled quantity alone, and there is no sign of another one tried.
- **It was test-first,** and my revert check below bites.
- **INFERRED:** the smoke run's P10 "fail" was itself produced by the defective weighting, with
  2 configurations, 50 resamples and a tenth of the background. It is not a verdict the fix
  overturned.

### Revert check (COMPUTED, `revert_check.sh`; output in `revert_check.out`)

The runner follows CLAUDE.md's rules:
- it saves a copy before editing;
- it reverts the one line `weight=unit_mean_weights(w),` to `weight=np.asarray(w),`;
- it runs `tests/test_t7_model_outputs.py`;
- it scans the log for import or collection errors before reading results;
- it restores from the saved copy, not git;
- it confirms the forward change is present again.

Results:
- **Forward:** 10 passed.
- **Reverted:** 1 failed and 9 passed, with no collection error. The other nine tests of the
  module ran, so the reverted build ran. The failure is
  `test_a_fit_does_not_depend_on_the_scale_of_the_weights` at `assert np.allclose(small, unit)`,
  a failure this revert can produce: a raw total-2 fit against a unit-mean fit.
- **Restored:** the sha256 equals the saved copy (`f18a9928…24b3`), and `unit_mean_weights(w)` is
  present once in `train`.

**The test bites.**

## Q4. The usual D18 checks

### V9 counts against the D26 data (COMPUTED, `q4_v9_recount.py` → `q4_v9_recount.json`)

Three genera were recounted with my own code: *Cantharellus* (main, a large genus), *Humaria*
(main, at 33 just over the count-alone line of 30) and *Laetiporus* (the comparison group).

The code streams `occurrence.txt` out of the D26 zip and re-implements each rule from its text,
not by import:
- the one-day date rule;
- the user-obscured test;
- uncertainty present and at most 250 m;
- the observer duplicate key, with tenths taken in decimal arithmetic, ties toward +∞;
- the box, tested at the 250 m cell centre in ESRI:102008;
- one per genus per cell, lowest gbifID.

It read 2,493,578 rows, the download's `total_records`.

| genus | mine | `counts.json` | presence file | gbifID sets equal |
|---|---:|---:|---:|---|
| *Cantharellus* | 1,059 | 1,059 | 1,059 | yes |
| *Humaria* | 33 | 33 | 33 | yes |
| *Laetiporus* | 820 | 820 | 820 | yes |

They match exactly, down to the records chosen.

### The block table (COMPUTED, `figures.json`)

- **Presences and background.** All 24 blocks in the fit match `fit_report.json` exactly.
- **Held-out AUCs.** For the 14 informative blocks they match `fit_report.json` with a maximum
  absolute difference of 0, and so do the five level I rows.
- **One transcription slip in the report's Markdown table.** 6.2.8 Eastern Cascades' B is
  0.84747, which rounds to **0.847**; the report prints 0.848. It affects nothing.
- **Forested blocks.** D139's 15% rule on `table_meta.json` gives 18 forested blocks in the box
  and 17 in the fit, the report's set.

### The area-of-applicability threshold (COMPUTED, `q4_aoa.py` → `q4_aoa.json`)

My own code re-implements the CAST rule as `aoa.py`'s docstring states it:
- each band centred, scaled (n−1) and weighted by gain;
- the nearest training point in another block, via a k-d tree;
- Q75 + 1.5 IQR, capped at the maximum.

The weights are the gains recorded in `fit_report.json`; Q2's retrained model reproduces the
fitted model exactly.

| | threshold | training-DI quartiles | cells outside |
|---|---:|---|---:|
| report | 0.198183 | 0.04259 / 0.06871 / 0.10483 | 16,478 |
| mine, 2M pairs, seed 7 | 0.198227 | 0.04260 / 0.06872 / 0.10485 | 16,478 |
| mine, 10M pairs, seed 11 | 0.198192 | 0.04259 / 0.06871 / 0.10483 | 16,478 |

My cell-by-cell inside/outside at the reported threshold agrees with `inside_all.npy` on 100% of
the 6,967,248 cells.

Two observations:
- **The mean-distance estimate cannot change which cells are inside** (INFERRED, then confirmed
  by the identical counts). Training DI, new DI and the threshold are all divided by the same mean
  distance, so it cancels. `aoa.py`'s disclosed departure, the sampled mean, is harmless by
  construction.
- **The area of applicability is permissive in geography.** It excludes only 0.24% of eligible
  cells. It still shades 3,212,655 cells outside T6's frame, because it measures distance in
  habitat-band space, which the background covers. So it is not a guard against extrapolating to
  unsearched country. INFERRED: a reader should not read "inside the area of applicability" as
  "validated there".

### The coder's readings beyond the plan (READ: report "Premises that were wrong" and "Decided beyond scope"; Forager RECORD -1126)

1. **The weight scale.** See Q3. It is correct and required, but the report understates its
   reach. The unfixed main model contained no habitat split, not "affected less".
2. **The add-one runs reuse the base model's configurations.** This is a sound way to break the
   circularity, and it is disclosed. The selection-optimism point that follows from it is in Q1:
   base − B alone is not above zero.
3. **D144 rule 4 applied to the presences entering the fit (44 genera alone) rather than to all
   box presences (V9: 47).** It is a reasonable reading, disclosed, and it changes which genera
   are pooled, so it changes the M3 weights. Its effect on the AUCs was not measured; that would
   need refits. It is the planner's or owner's to confirm.
4. **The licence track drops background with no CC-surface value (307,407 of 500,000), counted.**
   My rebuild drops the same number. The track is not like-for-like with the main run, as the
   report says.
5. **The under-minimum blocks are read as D139's "uninformative", not a halt.** That matches
   D139's text.
6. **The final model's configuration** is chosen by inner grouped 4-fold over all blocks. It is
   c16, and I reproduced the model bit for bit.
7. **Forager RECORD -1126 says "Tuning chose the most regularised configuration in every fold."**
   The report is more exact: B, base and full chose c16 in every fold, but A chose c15 in 18 of 24
   and c01, c07, c09 and c16 elsewhere (manifest `chosen_configurations`). The RECORD line
   overstates it slightly.

### The "25 vs 26 level III blocks" premise (COMPUTED from `fit/table_meta.json`; READ the verify report)

**25 is right, and the "26" correction is itself wrong.**
- `table_meta.json`'s `block_study_cells` has exactly 25 keys, every one with study cells. Colorado
  Plateaus (832 cells) is among them.
- The verify report's per-block list (`docs/audits/2026-10-15-t7-verify-report.md:233-246`) also
  names 25, Colorado Plateaus included. I counted the names.

So the V9 report ("The fit's tile table finds 26 level III blocks", `2026-10-16-t7-v9-counts.md`,
"Things the count showed") and the fit report ("24 level III blocks take part, of 26", and
Premises 3) both misstate the count. **No figure depends on it:**
- the fit uses the blocks actually present: 25, minus the Canada-only 7.1.5, gives 24;
- D139's 18 and 17 forested blocks stand.

It is a documentation correction.

## Q5. Looking at the map

The images were rendered by `render.py`, my own code, and are in this folder. They are not
published. I looked at each of them; what follows is OBSERVED by eye unless marked COMPUTED.

The images are drawn in the grid's equal-area projection, so the box's edges at 49°N and −111°
appear as slanted straight lines.

| image | what it shows |
|---|---|
| `habitat_overview.png` | the score as its percentile among shaded cells, dark purple (low) to yellow (high), at 1.25 km |
| `applicability_overview.png` | the codes alone |
| `searched_overlay.png` | the same score, with shaded cells outside T6's frame in a separate blue-to-pale ramp |
| `crop_*.png` | 150 km squares at 250 m: Puget and the border, Mount Hood, the Oregon Coast Range, the Klamath, the Idaho Batholith |

**Where it is high:**
- the northern Rockies interior: north Idaho, the Idaho Batholith, northeast Washington and
  western Montana, broadly yellow;
- the Blue and Wallowa Mountains;
- the higher west-side Cascades: around Mount Hood the mid and upper west slopes are bright;
- parts of the Olympics and the North Cascades. In the North Cascades crop the bright cells form
  bands along valley sides, and the broad uplands between them are darker.

**Where it is low:**
- the Klamath and Siskiyou region and southwest Oregon, mostly dark blue and purple;
- the dry east slope of the Oregon Cascades and the pine country east of it, the darkest
  continuous band on the map;
- scattered woodland in the Great Basin and Snake River ranges;
- the California foothills.

The Oregon Coast Range is mixed, mid-range.

COMPUTED (`render.json`): the mean percentile rises from 0.31 to 0.36 between 40° and 43°N to
0.54 to 0.60 between 44° and 49°N. By longitude it peaks at 0.64 to 0.67 between −117° and −115°.

This matches Q1's block table: the map's high ground is not where people search most.

**Artefacts:**
- **Tile seams: none seen, and none measured.** The mean absolute change in percentile across
  T6b's 256-cell tile edges is 0.1233 (columns) and 0.1235 (rows). One cell away from an edge it is
  0.1237 and 0.1222. No straight seams are visible in any crop.
- **Stripes: none visible.** The mean change between adjacent row means and adjacent column means
  is under 0.008 (COMPUTED).
- **The Canada mask edge.** The box's north edge is 49°N, so on the mainland the border and the
  box edge coincide, and the map simply stops at a straight line. Code 3 (pale blue) shows only
  south of 49° on southern Vancouver Island and the Gulf Islands, as expected. There is no visible
  artefact along it. A reader will see the shading end abruptly at the border with no "Canada not
  modelled" cue unless the legend gives one.
- **Code 2 (outside the area of applicability)** shows as scattered single red pixels, densest in
  the Klamath and the Siskiyous. These are speckle, not blocks.
- **Code 4 (no host shares)** dominates the Columbia Plateau and the Great Basin as grey, as
  expected.

**Shading in forest no one searched:**
- COMPUTED: 46% of shaded cells, 3,212,655, sit outside T6's frame. Their mean percentile is
  0.47, against 0.53 inside.
- COMPUTED (`q5_outside_frame_by_block.py`): 47% of the top-fifth cells are outside the frame,
  about the same as the 46% of all shaded cells.
- In the interior forest blocks the map ranks highest, most shaded cells are outside the frame
  (the basin-and-range blocks run higher still, 83 to 89%, but score low):

  | block | shaded cells outside the frame | mean percentile, outside the frame |
  |---|---:|---:|
  | Idaho Batholith | 66% | 0.67 |
  | Canadian Rockies | 65% | 0.72 |
  | Blue Mountains | 65% | 0.45 |
  | Columbia Mountains/Northern Rockies | 56% | 0.58 |

  It is lowest in the Puget Lowland (2%) and the Willamette Valley (1%).
- OBSERVED: `searched_overlay.png` shows the same thing.

So the map's brightest region rests largely on forest with no effort surface. That is where the
held-out test, which needs presences, could not look (INFERRED).

## The predictions, scored

**Planner's predictions:**
- "Headline AUCs and weather-cell intervals reproduce": **yes, exactly**.
- "Block intervals include zero": **yes**.
- "The fix is mechanically required: without it the comparison group's B doesn't split": **yes,
  and for the main group too**.
- "The map is dominated by the effort surface's pattern": **no**. Spearman is −0.007.

**My mechanism predictions:**
1. **Wrong** on the effort correlation: I said moderate and positive, and it is about zero.
   **Right** that the main AUC figures reproduce.
2. **Right:** the comparison correlation reproduces, and the wording should not say "mycorrhizal
   habitat".
3. **Right** on the comparison group's fit. **Wrong** that the main group's unfixed fit would split
   on habitat: it does not split on habitat at all. The mechanism (L2 against a small hessian)
   holds, but the effect was larger than I predicted.
4. **Right** on V9. **Wrong** on the blocks: I took "26" from the coder, and 25 is correct.
5. **Wrong** on where the map is high: I said west-side Cascades, Coast Range and Puget, and it is
   the northern Rockies interior. **Right** to expect no seams.

## Verdict

### Blocking

1. **The label "mycorrhizal habitat" is not supported by the evidence** (Q2). Two reasons:
   - the same inputs help a wood-rot genus more, by +0.023 against +0.004, and still more as a
     share of headroom;
   - the main model's ectomycorrhizal host bands carry little gain, and its map shares more with
     plain conifer and broadleaf cover (0.46) than it differs from it.

   The wording is the owner's to choose. Under that label, publishing should not proceed.

Nothing in the computation is blocking: every figure reproduces exactly, and the weight fix is
sound.

### Should-fix (before any pilot goes out)

1. **Say what the shading outside the effort frame means, or show it differently.** 46% of shaded
   cells, and most of the map's brightest interior blocks, lie outside T6's frame, where the
   held-out test had no presences to look at. The area of applicability does not exclude them,
   because it works in habitat space, not geography (Q4, Q5).
2. **Put the selection caveat beside the pass.** The base model, which involves no selection, is
   not above B: +0.0008 (−0.0009, +0.0026). The P10 margin over B rests on bands chosen on the same
   blocks (Q1).
3. **Correct the record of the weight fix.** Without it the main group's model is effort-only,
   with full identical to B. It is not "affected less" (Q3; report, Premises 1).
4. **Correct "26 level III blocks" back to 25,** in the V9 report and in the fit report's Data
   section and Premises 3 (Q4). No figure changes.
5. **Two small record slips.** 6.2.8's B is 0.847, not 0.848 (fit report, block table). Forager
   RECORD -1126's "the most regularised configuration in every fold" holds for B, base and full,
   not for A.
6. **Show the Canada cutoff on the map.** A legend line saying Canada is not modelled
   (code 3, D136) would cover it.

### Notes

- **The rule 4 reading.** Counting genera alone on the presences entering the fit, 44 rather than
  V9's 47, is disclosed and reasonable. Its effect on the AUCs was not measured.
- **The area of applicability's sampled mean distance** cancels out of the inside/outside decision
  by construction.
- **The map has no tile seams or stripes,** and the code 2 speckle is sparse.
- **The comparison runs reuse the main run's configurations,** so *Laetiporus*'s larger gain is
  not a tuning artefact.

## What I could not check, or did not

- **The 892 T6b tile files were not re-hashed.** They are on the flash drive the t6b-night job
  reads. The fit's `table` step hashed them against the T6b manifest (READ, report).
- **T6's effort surface** was read through the project's `EffortSurface`/`static_effort` as an
  input, not re-implemented.
- **The unfixed-weights rerun reused the fit's per-fold configurations** rather than re-tuning.
  INFERRED: it would not rescue the fit, since c16, the configuration the full model chose,
  already shows no habitat split.
- **V9 was recounted for three genera,** not all 86.
- **The effect of the rule 4 reading,** and the optimism from the add-one selection, are not
  measured.
- **LightGBM determinism was checked at 4 threads only,** the thread count the fit used. The
  retrain matched bit for bit.
- **`mask_map.png` (the fit's own image) was not opened.** I rendered my own.
- **CI was not run,** and no code changed here.
- **Nothing was published,** and no network request was made beyond the git remote.

## Two answers

**Does the evidence support publishing this as a pilot habitat layer, and under what wording?**
Only as a clearly labelled pilot of where mycorrhizal mushrooms are reported relative to search
effort, by forest type (or the owner's "forest-associated fungal reporting"). It does not support
"mycorrhizal habitat": its held-out skill is +0.004 AUC, not shown across blocks, and nearly half
its shading lies where there are no search data.

**What would most strengthen the habitat signal?**
A test that does not ride on reporting effort. That means presences from the unsearched interior,
or independent plot or survey data, scored against the map. Short of that, a contrast against the
wood-rot comparison group, which would isolate the host-specific part.
