# T7 re-fit report: the PNW habitat map with the road band as access, judged against P10b

Hazel Cairnwright (coder), written 2026-10-18 UTC for the planner (Rowan Waymark).
- **Dispatch:** `docs/dispatch/2026-10-17-t7-refit.md` (branch `t7-strengthen-plan`, c608b8c), Phase 2.
- **The owner's go:** "2 yes go ahead" (Forager RECORD -1188), started through the planner (-1189).
- **The rulings applied:** D156 to D158 (-1182, -1187).

This run passed -1030's second point of no return for the re-fit. **The third is not passed: nothing is shown or published.** The mask map image and the rasters were not opened.

- **Code:** branch `t7-refit` at `0560dae`, the commit the output manifest records. The worktree was clean at that commit when the run started.
- **Run:**
  - transient user unit `t7-refit.service`, started 2026-10-17T11:48:56Z;
  - first log line 11:49:08Z, done 2026-10-18T02:15:20Z, **51,983 s (14.4 h)**;
  - Result=success, exit status 0;
  - MemoryMax 5 GiB, no swap, Nice 10, 4 threads, beside t6b-night;
  - peak 2,954 MB (`peak_rss_mb` in the report).
- **Evidence:** `docs/audits/2026-10-17-t7-refit/`:
  - `fit_report.json`, which holds every figure below;
  - `block_report.csv`;
  - `output_manifest.json`;
  - `table_meta.json`;
  - `fit_log.txt` and `fit_out.txt`;
  - `unit_status.txt`;
  - `map_comparison.py` and `.json`.
- **Flags:** OBSERVED means this run wrote it. READ means a file says so. INFERRED means my reasoning.

## Verdict

**P10b fails** (D145). Conditions 1 and 4 pass. Conditions 2 and 3 fail. OBSERVED, `fit_report.json` `p10b`.

| condition | figure | point | 95% interval | wholly above zero |
|---|---|---:|---|---|
| 1 | full minus B, pooled held-out AUC, interval clustered by level III block, all 24 blocks | +0.00379 | +0.00105 to +0.00924 | **yes** |
| 2 | full minus A, within one weather cell, interval from level III block resampling (D145 as amended) | −0.00722 | −0.02570 to +0.01614 | **no** |
| 3 | host-specific contrast: mycorrhizal gain (full minus A, +0.00488) minus saprotroph gain (+0.00209), one block draw for both | +0.00279 | −0.00196 to +0.01054 | **no** |
| 4 | specimens above matched background, AUC minus 0.5, whole box (4,014 specimens, 40,140 background), block interval | +0.19615 | +0.06645 to +0.28547 | **yes** |

Every interval comes from 1,000 resamples, seed 20260918.

**Reported beside, with no verdict:**
- **P10 (D140) passes.** With weather-cell intervals:
  - full minus A is +0.00488 (+0.00276 to +0.00724);
  - full minus B is +0.00379 (+0.00210 to +0.00545);
  - over the 17 forested blocks, both also pass.
- **Condition 3 over the 13 shared forested blocks:** +0.00301 (−0.00156 to +0.01022).
- **Condition 4, interior sub-box:** 390 specimens and 3,900 background points, +0.10333 (−0.15708 to +0.23985).

### Which interval the log prints for condition 2

The planner asked about the line in `fit.log` that reads "within one weather cell … full minus A −0.00722 [−0.02327, +0.00794]". **That interval resamples weather cells.** It is `within_cell_figures`, through `metrics.within_cluster_auc_difference`, and the report stores it as `within_weather_cell_no_verdict`. **It is not the interval D145 requires.**

The required interval resamples level III blocks, with rows weighted by their block's draw count (`metrics.within_cluster_auc_difference_rows_resampled`). In the report it is `within_weather_cell_block_clustered_no_verdict` and `p10b.conditions.2_…`, reading **−0.00722 (−0.02570 to +0.01614)**. The point is the same in both, and both intervals include zero, so the verdict does not depend on the choice. The log prints only the weather-cell version, and the block version is in the JSON alone. That gap in the log is mine; it should print both.

## What changed from 2026-10-16, and what it does and does not say (read before deciding anything)

| pooled held-out AUC, all blocks | 2026-10-16 | re-fit |
|---|---:|---:|
| A (effort; now effort and road distance) | 0.87728 | **0.88782** |
| B (A plus conifer and broadleaf cover) | 0.87880 | 0.88891 |
| base | 0.87961 | 0.89054 |
| full | 0.88146 | **0.89270** |
| full minus A | +0.00419 | +0.00488 |
| within one weather cell: A | 0.4939 | **0.6481** |
| within one weather cell: full | 0.5479 | 0.6409 |
| within one weather cell: full minus A | +0.0540 | **−0.0072** |

The 2026-10-16 within-cell values are READ from `docs/audits/2026-10-17-t7-part-a/condition2-by-block/figures_from_cache.json`.

1. **The road band carries the within-cell signal habitat had.**
   - On 2026-10-16, within one weather cell, where effort is one value, the full model ranked pairs at 0.548 against effort's 0.494, and condition 2 passed (+0.0540, block interval +0.0160 to +0.0639).
   - With road distance beside effort, A alone ranks those pairs at 0.648, and the habitat bands add nothing on top (−0.0072).
   - Inside a weather cell, what the habitat bands seemed to know is mostly how near a road a place is. OBSERVED for the figures; INFERRED for the reading.
2. **The pooled gain over A did not shrink: it grew a little,** from +0.0042 to +0.0049. The habitat bands still separate presences from background across weather cells. But condition 2 says they do not within one, so that gain sits between cells, where it can still be confounded with whatever else differs between cells. INFERRED.
3. **Condition 1 now passes, but it rests on band selection.**
   - Base minus B, the habitat model before any band was selected, is +0.00163 with a block interval of −0.00131 to +0.00670, which includes zero (weather-cell interval −0.00008 to +0.00329).
   - The full model adds the three bands kept by the add-one step: *Lithocarpus* (tanoak), *Chrysolepis* (chinquapin) and *Arbutus* (madrone). They were selected on the same held-out blocks condition 1 is then scored on, so condition 1 carries optimism that was not measured (as on 2026-10-16, item 6 of that report).
   - All three are southwestern Oregon and northern California broadleaf hosts. *Larix* is no longer kept: its lower bound is −0.000004.
4. **Condition 4 passes, with caveats that point the other way.**
   - The specimens are mostly old: 712 of the 6,026 kept records are from 2000 on (Phase 1 report).
   - 72% of kept records come from one herbarium, the University of Washington's.
   - The background is matched on road distance but not on collecting stations or decade.
   - 2,012 of 6,026 kept specimens are not scorable (their own cell has no map value).
   - **The interior sub-box, which is the question part D was asked, does not pass:** +0.103, interval −0.157 to +0.240, on 390 specimens.
5. **Condition 3 fails, and the wood-rot comparison still gains more than the mycorrhizal group.**
   - The saprotroph group's gain is +0.0021 against the mycorrhizal group's +0.0049, and the contrast's interval includes zero.
   - *Laetiporus* (chicken of the woods) gains +0.0141 over A (interval +0.0005 to +0.0290), almost three times the mycorrhizal group's gain.
   - So the habitat bands are not shown to help the mycorrhizal group more than groups that do not depend on the same hosts.
6. **Block by block.** Of the 14 informative blocks (30 or more presences), full is above A in 8 (7 on 2026-10-16) and above B in 11 (9). It is below A in:
   - Klamath Mountains, 0.817 against 0.824;
   - Wasatch and Uinta, 0.862 against 0.864;
   - Columbia Mountains/Northern Rockies, 0.840 against 0.849;
   - Canadian Rockies, 0.843 against 0.849;
   - Coastal Range, 0.912 against 0.916;
   - Willamette Valley, 0.877 against 0.879.

   **At level I it still loses in Marine West Coast Forests**, where 8,958 of the 15,624 presences are: 0.885 against A's 0.886 and B's 0.886. It wins in Northwestern Forested Mountains (6,594 presences): 0.859 against 0.850 and 0.851.
7. **By year** (beside, no verdict). Full is below A in 2016 (0.696 against 0.750; 55 presences) and in 2017 (0.920 against 0.924), and equal in 2021. It is above A in the other eight years.
8. **Tuning ran to the edge of the grid again.**
   - Every outer fold of B, base and full chose `c16`, the most regularised configuration.
   - A chose `c02` in 16 of 24 folds.
   - The final all-data model chose `c04` (500 rounds, 50 points per leaf), not `c16`. INFERRED: a grid reaching further toward simpler models might choose differently.
9. **The licence track** (CC0 and CC BY records, 1,586 presences) has full minus B +0.0083 with a block interval of −0.0019 to +0.0308, which includes zero.

## Side runs (configurations reused from the main fit, P7 point 9; no verdict)

| run | presences | AUC full / A / B | full minus A (weather-cell interval) | full minus B, block interval | within-cell full minus A, block interval | seconds |
|---|---:|---|---|---|---|---:|
| M2 side run | 17,261 | 0.8935 / 0.8887 / 0.8901 | +0.0048 (+0.0031 to +0.0069) | +0.0034 (+0.0008 to +0.0085) | −0.0051 (−0.0248 to +0.0083) | 699 |
| licence track | 1,586 | 0.8469 / 0.8337 / 0.8385 | +0.0131 (+0.0044 to +0.0221) | +0.0083 (−0.0019 to +0.0308) | −0.0027 (−0.0379 to +0.0166) | 242 |
| comparison group (*Laetiporus*) | 606 | 0.8634 / 0.8493 / 0.8556 | +0.0141 (+0.0005 to +0.0290) | +0.0078 (−0.0114 to +0.0211) | +0.0031 (−0.0512 to +0.0387) | 646 |
| saprotroph main (condition 3) | 9,591 | 0.9222 / 0.9202 / 0.9192 | +0.0021 (+0.0008 to +0.0034) | +0.0030 (+0.0020 to +0.0055) | −0.0069 (−0.0164 to +0.0132) | 682 |
| saprotroph side | 14,163 | 0.9218 / 0.9201 / 0.9196 | +0.0017 (+0.0007 to +0.0029) | +0.0022 (+0.0008 to +0.0045) | −0.0009 (−0.0162 to +0.0201) | 682 |
| trails side check (`dist_any_m` in place of roads) | 15,624 | 0.9105 / 0.9055 / 0.9077 | +0.0049 (+0.0025 to +0.0084) | +0.0028 (+0.0015 to +0.0058) | +0.0040 (−0.0098 to +0.0155) | 696 |

- The trails check carries 13,010 rows with no trail value (the Umatilla and Wallowa-Whitman forests, D150), left as NaN.
- With trails in, the pooled AUCs are higher across the board, and the habitat gain over A is about the same.
- Within one weather cell, full minus A is +0.0040 there against the main run's −0.0072. Both intervals include zero.

## The map

Outputs are in `/mnt/work/Zynergy/forecast-data/t7/refit/outputs/`. They are never in the repository, never on the flash drive, and not opened.

| file | bytes | sha256 |
|---|---:|---|
| `relative_habitat_pnw.tif` (float32 raw score, effort held at 1.4407 and road distance at 258.3 m; NaN where masked) | 24,264,312 | `504d59b31f2272c6b99490b00d934322dd3744fff56e705c202dd1083fd99e90` |
| `applicability_pnw.tif` (uint8 codes 0 to 6) | 1,076,671 | `ee8b9e447731edc9f916129c4371acef12012707012a266591587c71c422e323` |
| `block_report.csv` | 2,377 | `ceaa6ed8bfc49742fab33890c372d291c76c8d8135380ce8a02c6a99d5b5a50c` |
| `block_report.json` | 55,668 | `d858a21f5318debfaceb5d4e5076d10feb3b26065ecd4ea7976e038fee6e81bd` |
| `mask_map.png` (**not opened**) | 2,295,745 | `07f6486c8769b6a043695c4260af1b8ab5e189e07b8b261bcb93f79798dc38d7` |
| `manifest.json` | 133,860 | `af0fc2dd5c5868773da1a41d5231abdcf1aab16c8d5a1ee95e86392434b648ec` |

- **Label and attribution.** The label is "relative habitat, PNW pilot, not shown". The access layer's credit line is in the attribution.
- **P6.** The ranking is identical at effort's 25th and 75th percentiles (shift 2.4295 for every cell), and at road distance's 25th and 75th percentiles over the background draw, 97 m and 702 m (shift −1.1102 for every cell). OBSERVED.
- **Area of applicability.** It uses the 13 habitat bands; effort and road distance are excluded.
  - The threshold is 0.1746.
  - 16,738 of 6,967,248 eligible cells are outside it (16,478 on 2026-10-16).
  - 3,212,602 inside cells lie in weather cells outside T6's effort frame.
- **The mycorrhizal map against the *Laetiporus* map:** rank correlation 0.280 over shaded cells (0.230 on 2026-10-16).

### What the map now ranks highest, against 2026-10-16

From `map_comparison.json`: the 6,941,779 cells shaded in both maps, both scores at their held values. OBSERVED.

- **Overall agreement.** The two maps' rank correlation is **0.912**, and **58%** of the re-fit's top tenth of cells were also in the 2026-10-16 top tenth. The map moved, but not wholesale.
- **Where the top tenth is.** Both maps' top tenth is interior mountain conifer forest: Columbia Mountains/Northern Rockies and the Idaho Batholith carry 38% of it now, against 44% before. North Cascades (2026-10-16: not in the top six blocks; now 12%) and Cascades (6.6% → 10.8%) gain. Blue Mountains (10.1% → 8.3%) and Middle Rockies (9.1% → below the top six) lose.
- **Farther from roads.** The top tenth's median road distance rose from 593 m to **793 m**, and its share of cells more than 1 km from a road from 41% to 45%. Over all shaded cells the median is 305 m.
- **The trees.** The top tenth holds more true fir (*Abies* share 0.31 → 0.34) and hemlock (*Tsuga* 0.06 → 0.10), less Douglas-fir (*Pseudotsuga* 0.16 → 0.13) and pine (0.23 → 0.21), with higher canopy cover (47% → 51%) and slightly lower soil pH (5.85 → 5.75).

## Mechanism prediction (written in the Phase 1 report, before Phase 2) against the result

| predicted | result | |
|---|---|---|
| A rises clearly, by more than the +0.004 the habitat bands added last time | A 0.8773 → 0.8878 (+0.0105) | right |
| A's within-cell AUC rises most | 0.494 → 0.648 | right |
| Full minus A shrinks | +0.0042 → +0.0049, a slight rise | **wrong** |
| Condition 2 shrinks the most | +0.0540 → −0.0072, gone | right |
| Condition 1 stays inside zero | passes, +0.0038 (+0.0010 to +0.0092) | **wrong** |
| Condition 3 hard to call, wide interval; access absorbs more of the saprotroph gain, so the contrast rises | saprotroph gain small (+0.0021), contrast +0.0028 with an interval including zero | partly right: wide, not shown above zero |
| The map moves toward forest far from roads | top tenth's median road distance 593 → 793 m | right |
| …and away from lowland and urban-edge forest near roads | the 2026-10-16 top tenth was already interior mountain forest, so there was little lowland to move from | **premise wrong**: I described the old map without reading it |

The wrong half of the mechanism is the pooled one. INFERRED: the road band absorbed differences within cells, where effort could not reach. But B and full rose with A by about the same amount (B +0.0101, full +0.0112), so the between-cell habitat signal, which drives the pooled and block-clustered figures, was left largely in place, and the three selected broadleaf bands lifted full a little further above B.

## What is not checked

- **The mask map image and the rasters were not opened** (nothing is displayed, M8). Codes were counted as written.
- **The optimism from selecting bands on the same held-out blocks** is not measured, and condition 1 depends on it (item 3).
- **Spatial structure finer than a block, or coarser than a weather cell**, is not tested beyond the intervals given.
- **Whether a wider tuning grid would change the result** (item 8).
- **Condition 4's background** is matched on road distance only, not on collecting stations, decade or herbarium.
- **No independent reviewer has read this run.** The dispatch's finish line calls for two reviews by Sorrel Tally, on other models.
- **LightGBM's determinism across thread counts.** Everything ran at 4 threads.
- **The rasterio `NotGeoreferencedWarning` in `fit_out.txt`.** It appears once, from the mask-map step. The same warning appeared in the trial; I infer it is the PNG written without georeference, and did not check.
- **The transient unit's start and exit timestamps** were gone from systemd when I read it (`unit_status.txt` keeps Result=success and exit status 0). The times above come from the log and from my start record (-1189).

## Decided beyond scope

- `map_comparison.py`, a read-only comparison of the judged run's cached scores with this run's, to answer what the map ranks highest. It reads `t7/fit/` (the judged run's work dir) and writes nothing there.
- **This report's evidence is committed by hand,** copied from the work dir, apart from `fit_report.json` and `block_report.csv`, which the script wrote.
