# T7 fit report: the PNW habitat map for mycorrhizal mushrooms as a group, P3 to P10

Written 2026-10-17 (UTC; evening of 2026-10-16 Pacific) by the T7 run coder for the Forager planner
(Rowan Waymark), on the owner's go (Forager RECORD -1081, D144; the owner, verbatim: "3 start the
model, let's get the full one going"). This passes RECORD -1030's second point of no return, the
fit. **The third is not passed: nothing is shown or published anywhere.** The mask map image was
written to `/mnt/work` and was not opened.

- **Code:** branch `t7-build` at `41f9c79`, the commit in the output manifest. The run script is
  `scripts/t7_fit.py`.
- **Evidence:** `docs/audits/2026-10-16-t7-fit/`, containing:
  - `fit_report.json`, which holds every figure below;
  - `block_report.csv`;
  - `timing.json`;
  - `table_meta.json`, with every input file's sha256;
  - `fit_log.txt` and `table_log.txt`;
  - `output_manifest.json`, a copy of the output manifest.
- **Flags.** OBSERVED means this run printed it into those files. READ means a file says so.
  INFERRED means it is my reasoning.
- **Machine.**
  - Every heavy step ran at `nice -n 10` under `systemd-run --user --scope -p MemoryMax=5G
    -p MemorySwapMax=0`. LightGBM used 4 threads.
  - The peak was 3,006 MB.
  - T6b's night run (`t6b-night`) shared the laptop until its 07:00 stop. The flash drive was read
    only. No PAUSE file was touched.
  - No GBIF, climate or Open-Meteo request was made.

## Verdict

**The P10 bar (D140) is met.** The full model's pooled held-out AUC is above both comparison
models. Each difference has a 95% interval wholly above zero: 1,000 resamples clustered by 0.1°
weather cell, seed 20260918. That holds over all blocks and over the forested blocks alone.

| difference in pooled held-out AUC | point | 95% interval (weather-cell clusters) | above zero |
|---|---:|---|---|
| full minus A (effort only), all 24 blocks | +0.00419 | +0.00211 to +0.00629 | yes |
| full minus B (effort plus conifer and broadleaf cover), all 24 blocks | +0.00266 | +0.00100 to +0.00423 | yes |
| full minus A, 17 forested blocks | +0.00408 | +0.00201 to +0.00623 | yes |
| full minus B, 17 forested blocks | +0.00266 | +0.00094 to +0.00435 | yes |

| pooled held-out AUC | all blocks | forested blocks |
|---|---:|---:|
| A: effort only | 0.87728 | 0.87671 |
| B: forest only | 0.87880 | 0.87813 |
| base (10 habitat bands plus effort) | 0.87961 | 0.87888 |
| **full** (base plus *Larix*, *Chrysolepis*, *Arbutus*) | **0.88146** | **0.88079** |

Passing shows nothing by itself (D140, M8 (a)). **Read the pass together with the next section.**
The margin is small, and several figures reported beside it, with no verdict, point the other way.

## What the pass does and does not say (read before deciding anything)

1. **Effort carries almost all of it.** Effort alone scores 0.877. Every habitat input together adds
   0.004 to that. Where people search explains nearly all of where the group is reported. The
   habitat signal is real by the ruled test, and it is thin.
2. **The interval clustered by block includes zero.** P7 point 6 has it printed beside, with no
   verdict.

   | difference | point | 95% interval (block clusters) |
   |---|---:|---|
   | full minus A, all blocks | +0.00419 | −0.00063 to +0.01200 |
   | full minus B, all blocks | +0.00266 | −0.00041 to +0.00811 |
   | full minus A, forested blocks | +0.00408 | −0.00091 to +0.01152 |
   | full minus B, forested blocks | +0.00266 | −0.00013 to +0.00826 |

   With 24 blocks, of which 14 are informative, the result is not shown to hold across ecoregions
   as units. The proposal expected this interval to be rougher (INFERRED there). It was.
3. **Block by block it is a split.** Of the 14 informative blocks (30 or more presences), the full
   model is above A in 7 and above B in 9. It is below both in:
   - 6.2.11 Klamath Mountains, 0.771 against 0.788 and 0.773;
   - 6.2.3 Columbia Mountains/Northern Rockies, 0.816 against 0.829 and 0.823;
   - 6.2.4 Canadian Rockies, 0.828 against 0.833 and 0.830;
   - 7.1.9 Willamette Valley, 0.871 against 0.872 and 0.873.

   **At level I it loses in Marine West Coast Forests**, where 8,958 of the 15,624 presences are:
   0.880 against A's 0.885 and B's 0.883. It wins in Northwestern Forested Mountains (6,594
   presences): 0.839 against 0.830 and 0.833.
4. **The comparison group gains more from the same inputs.** Chicken of the woods (*Laetiporus*, a
   wood-rot genus, M4) was fitted on the same design, reusing the main run's chosen configurations.

   | comparison group, pooled held-out AUC | value |
   |---|---:|
   | full | 0.8670 |
   | A | 0.8438 |
   | B | 0.8517 |

   | comparison group, difference | point | interval |
   |---|---:|---|
   | full minus A | +0.0232 | +0.0104 to +0.0376 |
   | full minus B | +0.0153 | +0.0053 to +0.0267 |
   | full minus A, forested blocks | +0.0235 | +0.0107 to +0.0367 |
   | full minus B, forested blocks | +0.0159 | +0.0051 to +0.0271 |

   The two all-data maps have a rank correlation of **0.230** over shaded cells. So the maps differ.
   But the habitat inputs help a non-mycorrhizal group at least as much, so the gain here is not
   shown to be specific to mycorrhizal hosts.

   P10 named no threshold for this. P7 says "should not simply reproduce the mycorrhizal one", and
   a correlation of 0.23 says it does not. INFERRED: part of what the inputs teach both models may
   be forest that is easy to reach, which effort at 0.1° cannot see (P3's stated limit).
5. **The licence track does not pass B.** On CC0 and CC BY records only (1,586 presences):

   | licence track | value |
   |---|---:|
   | AUC full | 0.8344 |
   | AUC A | 0.8150 |
   | AUC B | 0.8262 |
   | full minus A | +0.0194 (+0.0082 to +0.0306) |
   | full minus B | +0.0082 (**−0.0005** to +0.0167) |
   | full minus B, forested blocks | +0.0080 (**−0.0006** to +0.0162) |

   This track is reported beside (SPEC constraint, D108), not part of the bar.
6. **The add-one selection and the verdict use the same held-out blocks.**
   - D138 keeps a band when its held-out difference over the base has an interval above zero. The
     full model is then scored on the same held-out predictions' blocks.
   - The selection looked at those blocks, so the full model's lead carries some optimism (INFERRED;
     not measured).
   - *Larix* was kept on a lower bound of +0.000044, the thinnest of the three.
   - The base model alone, which involves no selection, is +0.0023 over A and +0.0008 over B as a
     point difference. Its intervals were not computed.
7. **Tuning ran to the edge of the grid.**
   - Every outer fold of B, base and full chose `c16`, the most regularised of the 20 configurations:
     15 leaves, 1,000 points per leaf, rate 0.03, L2 10, 200 rounds.
   - A chose `c15` in 18 of 24 folds.
   - The final all-data model is `c16` too.
   - INFERRED: a grid reaching further toward simpler models might choose differently. The grid is
     D31's committed one and was not changed.
8. **The by-year table** is printed beside, with no verdict (P7 point 8). The full model is below A
   in 2016 (0.668 against 0.704; 55 presences), 2018 and 2021. It is above A in the other eight
   years.

## Numbers in full

### Data (OBSERVED)

- **Presences entering the fit: 15,624** of V9's 23,069 thinned main-run presences. They were lost
  by P4's codes (D134):

  | cell code | presences |
  |---|---:|
  | 1 in | 15,626 |
  | 4 no host shares | 4,160 |
  | 3 Canada | 1,928 |
  | 5 no soil pH | 1,025 |
  | 0 outside | 329 |
  | 6 water | 1 |

  Two more, eligible, sit in a weather cell outside T6's frame (effort is refused, D107) and are left
  out, which gives 15,624. Effort is keyed by the 250 m cell centre's weather cell. For 223 entering
  presences this differs from the record's own weather cell.
- **Weights (M3, D144 rule 4, applied to the presences entering the fit):** 44 genera count alone;
  the rest are pooled, with 285 presences. In V9, over all box presences, the split was 47 alone and
  39 pooled. Applying rule 4 to what the model sees is my reading.
- **Background (D133):**
  - 500,000 cells drawn without replacement, seed 20260918, from 3,745,167 eligible cells in the
    frame.
  - The cell list's sha256 is `3a411eb2...5184`.
  - The background's total weight equals the presences' total weight.
  - Before fitting, weights are rescaled to a mean of 1 (see "Premises that were wrong" 1).
- **Eligible cells in the box: 6,967,248.** By code over the output window:

  | code | cells |
  |---|---:|
  | 0 | 2,449,579 |
  | 1 | 6,950,770 |
  | 2 | 16,478 |
  | 3 | 102,543 |
  | 4 | 9,447,216 |
  | 5 | 23,834 |
  | 6 | 133,292 |

  Code 1 plus code 2 is 6,967,248, which checks.
- **Blocks:**
  - 24 level III blocks take part, of 26 with study cells in the box.
  - 7.1.5 is Canadian only, and so is masked.
  - 9.3.1 has background only.
  - 14 blocks are informative.
  - 17 forested blocks are in the fit, of D139's 18; Coastal Western Hemlock-Sitka Spruce is
    masked. These include Colorado Plateaus (2 background points) and NW Great Plains (133
    background, no presence).
- **Held effort (P6):** median log effort over the frame's weather cells holding an eligible cell,
  **1.4407**. The ranking at the 25th and 75th percentiles (0.380 and 2.570) is identical on 200,000
  sampled cells. The score shifts by the same 2.3140 for each cell (P5's constraint, OBSERVED).
- **Inputs:** every tree, flags and soil tile file hashed to its T6b manifest line, with no
  mismatch. The mask and the level III file are hashed in `table_meta.json`. The T6 stored surface
  matches `stored_surface_sha256.txt`. The D26 zip, the membership list and the presence files are
  hashed in the manifest.

### The ladder (D138)

Each candidate band was added to the base alone, with the base's per-fold configurations:

| band | difference | 95% interval | kept |
|---|---:|---|---|
| *Larix* | +0.00046 | +0.00004 to +0.00081 | yes |
| *Betula* | +0.00019 | −0.00015 to +0.00053 | no |
| *Populus* | −0.00033 | −0.00073 to +0.00006 | no |
| *Alnus* | −0.00040 | −0.00081 to +0.00003 | no |
| *Lithocarpus* | +0.00012 | −0.00036 to +0.00058 | no |
| *Chrysolepis* | +0.00067 | +0.00028 to +0.00103 | yes |
| *Arbutus* | +0.00122 | +0.00076 to +0.00168 | yes |
| `ecm_hosts` | −0.00024 | −0.00099 to +0.00052 | no |

### Per block (informative blocks; held-out AUC full / A / B)

| block | presences | full | A | B |
|---|---:|---:|---:|---:|
| 7.1.8 Coastal Range | 5,992 | 0.906 | 0.909 | 0.903 |
| 6.2.7 Cascades | 3,137 | 0.812 | 0.803 | 0.807 |
| 7.1.7 Strait of Georgia/Puget Lowland | 2,330 | 0.855 | 0.850 | 0.857 |
| 6.2.5 North Cascades | 1,422 | 0.827 | 0.817 | 0.819 |
| 7.1.9 Willamette Valley | 636 | 0.871 | 0.872 | 0.873 |
| 6.2.3 Columbia Mountains/Northern Rockies | 463 | 0.816 | 0.829 | 0.823 |
| 6.2.11 Klamath Mountains | 462 | 0.771 | 0.788 | 0.773 |
| 6.2.15 Idaho Batholith | 410 | 0.846 | 0.847 | 0.844 |
| 6.2.8 Eastern Cascades Slopes and Foothills | 229 | 0.859 | 0.846 | 0.848 |
| 6.2.13 Wasatch and Uinta Mountains | 179 | 0.822 | 0.822 | 0.815 |
| 6.2.9 Blue Mountains | 141 | 0.813 | 0.767 | 0.798 |
| 6.2.10 Middle Rockies | 91 | 0.837 | 0.824 | 0.818 |
| 6.2.4 Canadian Rockies | 53 | 0.828 | 0.833 | 0.830 |
| 11.1.1 Central California Foothills and Coastal Mountains | 37 | 0.950 | 0.949 | 0.944 |

**Uninformative blocks** (under 30 after P4, kept in the pooled figure, D139):

| block | presences |
|---|---:|
| Northern Basin and Range | 15 |
| Snake River Plain | 7 |
| Sierra Nevada | 7 |
| Columbia Plateau | 6 |
| Central Basin and Range | 6 |
| Central California Valley | 1 |
| Wyoming Basin | 0 |
| Colorado Plateaus | 0 |
| NW Glaciated Plains | 0 |
| NW Great Plains | 0 |

**Level I** (full / A / B):

| level I | presences | full | A | B |
|---|---:|---:|---:|---:|
| 6 | 6,594 | 0.839 | 0.830 | 0.833 |
| 7 | 8,958 | 0.880 | 0.885 | 0.883 |
| 10 | 34 | 0.760 | 0.738 | 0.775 |
| 11 | 38 | 0.943 | 0.941 | 0.940 |
| 9 | 0 | n/a | n/a | n/a |

### Side runs (reported beside, no verdict; configurations reused from the main run, P7 point 9)

| run | presences | background | AUC full | full minus A | full minus B |
|---|---:|---:|---:|---|---|
| M2 side run (mixed and uncertain genera in) | 17,261 | 500,000 | 0.8815 | +0.0039 (+0.0022 to +0.0059) | +0.0023 (+0.0007 to +0.0038) |
| licence track (CC0 and CC BY, T6's `cc` surface) | 1,586 | 192,593 | 0.8344 | +0.0194 (+0.0082 to +0.0306) | +0.0082 (−0.0005 to +0.0167) |
| comparison group (*Laetiporus*) | 606 | 500,000 | 0.8670 | +0.0232 (+0.0104 to +0.0376) | +0.0153 (+0.0053 to +0.0267) |

The licence track keeps the same background draw (P3 point 5). 307,407 of the 500,000 cells have
no value on the CC surface (its frame is smaller) and are dropped, counted. The track's held effort
is 0.7264.

### Area of applicability (P8, D141)

- **Threshold.** CAST's rule on the cross-validated training DI gives a threshold of **0.1982**.
  - The rule is Q75 + 1.5 IQR, capped at the maximum.
  - Training DI quartiles: 0.043, 0.069 and 0.105. The maximum is 1.690.
  - The mean training distance is estimated from 2,000,000 random pairs, the disclosed departure
    in `aoa.py`.
- **Weights:** each habitat band's gain in the final full model (in `fit_report.json`). Effort is
  excluded.
- **Cells:** of 6,967,248 eligible cells, **16,478 are outside** (code 2, transparent) and 6,950,770
  are inside.
  - Of the inside cells, **3,212,655 lie in weather cells outside T6's effort frame**. That is
    shading extended from searched forest to similar forest where nobody reported a fungus (P6's
    stated meaning).
  - Of the outside cells, 7,052 are in the frame and 9,426 are not.

## Timing (step 3's stop rule)

- **One outer fold, timed first** (`timing.json`): base model, block 112, 505,126 training points,
  80 inner fits plus the final fit, **646 s**. The projection was **18.7 h** of fits, which is under
  the 24 h stop, so the run went ahead. The bootstrap took 37 s per difference. The area of
  applicability took 30 s to fit and is projected at 0.06 h to query every eligible cell.
- **Actual: 51,072 s (14.2 h)** for the full run, from 2026-10-16T11:56Z to 2026-10-17T02:07Z.

  | step | time |
  |---|---|
  | A | 2.1 h |
  | B | 2.8 h |
  | base | 4.0 h |
  | eight add-one runs | 22 min |
  | full | 4.3 h |
  | final model, area of applicability, side runs, map pass, writers | 37 min |

  It took less than projected because `c16`, the fastest configuration, was nearly always chosen
  for the final fits. The timing used weights before the scale fix. After the fix, a fold of the
  base model took about 10.5 minutes.

## Outputs (on `/mnt/work/Zynergy/forecast-data/t7/pnw-2026-10-17/`; never in the repository, never on the flash drive)

| file | bytes | sha256 |
|---|---:|---|
| `relative_habitat_pnw.tif` (float32 raw score at the held effort, NaN where masked) | 18,513,600 | `c186977db309b5356889cfe1eebfc369e451e1651a87d727f4388540da096ff6` |
| `applicability_pnw.tif` (uint8 codes 0 to 6) | 1,078,617 | `07baec5f0990a116b7ec7512aaa993215f689ceac6a5f4571083bf05ed539c67` |
| `block_report.csv` | 2,380 | `5c8f8fcf671c2ee8a98932c8a2429b6ab153e3087e6e16d6dc85953f44dab1dc` |
| `block_report.json` | 27,108 | `eca3ebab368578793b45667aa58c7ec0abc6fd02bb24e36ac297ab304c10b1fa` |
| `mask_map.png` (500 m pixels, five equal-count classes, codes 2 to 6 in greys, frame outline, level III lines; **not opened**) | 2,248,375 | `bb0f0df8f4aabbd14be5ca95f347a7f5e31b3a2fe69391b722be45a3d0cdfc44` |
| `manifest.json` | 132,985 | `f041714ea402ffea6b8b5b58027b5d3d7cf904824f1864ab65c61048ca8449d5` |

The folder is named by the UTC date at writing, 2026-10-17, because the run crossed midnight UTC.

**The output window is the box's master-grid window**, 5,048 by 5,089 cells
(`pnw.pnw_window`). The writers' wording check passed on every label and tag.

**Attribution:**
- **Included:** the tile tags filtered to what was read, plus FungalTraits, the GBIF download DOI and
  CEC level III.
- **Left out:** SCANFI, because no Canadian value was read.

A smoke pass with 2 configurations, a tenth of the background and 50 resamples wrote
`/mnt/work/Zynergy/forecast-data/t7/smoke-2026-10-16/`. That pass is not a result and nothing in
this report comes from it.

## Premises that were wrong, and what was changed

1. **Weight scale (fixed in `41f9c79`, test first).**
   - **What the smoke pass showed:** the comparison group's model B predicted exactly what model A
     predicted.
   - **Cause:** the comparison group is one M3 unit, so its weights summed to 2 over 500,000
     points. LightGBM's `min_sum_hessian_in_leaf` and its L2 penalty act on the weights' own scale,
     so almost no split was allowed. The main run (total weight about 90: 45 units on each side) was affected less, but
     was affected.
   - **The fix:** `model.train` now rescales weights to a mean of 1. Every M3 and P3 share is
     unchanged, and so are the weighted AUC and the tuning log loss.
   - **The test:** the new one failed on the unfixed code and passes now.
   - **The abandoned run:** the full run that had started at `dccb1f4` was stopped before its first
     model finished, and its cache was deleted.
   - **The timing:** it was measured before this fix.
2. **The add-one runs reuse "the full model's" configuration (P7 point 7).** That is circular,
   because the full model is defined by the add-one results. I read it as **the base model's
   per-fold configuration**, the model each band is added to. The full model was then tuned anew
   (a fourth tuned model). The side runs reuse the full model's per-fold configurations, as P7
   says.
3. **The verify report's "25 level III blocks"** is a headline count. Its own list names 26, with
   Colorado Plateaus included. D139's 18 forested blocks stand (V9 report).

## Decided beyond scope (stated so they can be overruled)

- **Effort per presence** comes from its 250 m cell centre's weather cell, as for background. The
  223 presences where that differs from the record's own weather cell are counted.
- **D144 rule 4 (30 to count alone)** applied to the presences that enter the fit, not to every box
  presence.
- **The final all-data model** used for the map, the importance weights and the comparison
  correlation: its configuration was chosen by inner grouped 4-fold over all 24 blocks, the same
  procedure as each fold.
- **The licence track** dropped background cells with no CC-surface value instead of drawing anew.
- **Code 2 (outside the area of applicability)** is set only on eligible cells, and its score is
  NaN.
- **Output folder** `pnw-<UTC date>`.

## What is not checked

- **The mask map image was not opened or viewed** (nothing is displayed, M8). Its classes and lines
  are as the code writes them, unseen.
- **The rasters were not opened in any viewer.** Their codes were counted as they were written.
- **No independent reviewer** has read the code or the run (D18). The T7 build itself has no filed
  D18 review on origin, as far as I know (not checked this session).
- **The optimism from selecting bands on the same held-out blocks** (item 6) is not measured.
- **Spatial autocorrelation beyond one weather cell.** The weather-cell interval is the ruled one,
  and the block interval includes zero.
- **Whether a wider tuning grid would change the result** (item 7).
- **The licence track's background** is smaller and from a smaller frame, so its comparison to the
  main run is not like for like.
- **The 2,000,000-pair estimate** of the mean training distance against the exact value at this
  size: checked on 300 points only, in the build.
- **CI** was not run for this branch, and its result was not read.
- **LightGBM's determinism across thread counts.** Everything ran at 4 threads, and a rerun at
  another count may differ.
