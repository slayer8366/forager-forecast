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
(`src/forager_forecast/t7/model.py:41`, `monotone_constraints`). Every model keeps effort in its
own interaction group (`model.py:45-46`), so the map at the held effort is the habitat part plus a
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
  point 9 says (`scripts/t7_fit.py:575-583`). So its gain was obtained without tuning to it. That
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
