# Dispatch: T7 for the PNW pilot, the habitat model, verify and propose first

**Verify first and report by message. Every modelling choice is proposed and ruled before any count of
the outcome is read and before anything is fitted. No fit until the owner has ruled and the planner
says go. No GBIF request, no climate pull, no Open-Meteo request, no merge.**

Written on 2026-10-10 (UTC, about 20:15) by a planning writer for the Forager planner session, on
Forager RECORD -828 ("Write the T7 habitat-model plan"), for dispatch on 2026-10-11. The file name
carries the dispatch date the planner gave. Base: forager-forecast `origin/main` at `36cc647`, read
together with these unmerged branch tips: `d121-lean-start` `aec605d` (D121),
`t6b-continental-layers` `cfbf50d` (T6b code, D111 to D120, the SCANFI D122),
`pnw-pilot-t1` `a8f85b9` (the pilot D122), `pnw-first-fit-verify` `dd28648` (the verify report),
`pnw-pilot-scoring` `9e24e67`. Forager RECORD read at `records-after-173` `9f6f2e02` (entries -806 to
-828). Data folders were listed (not read for values) at about 20:05 to 20:10 UTC on 2026-10-10.
**Every cite is a premise to re-check. Anything in this file that names what exists on disk was true
when listed and may have moved since.**

**Writer (D38):** a coder session on this laptop, in its own worktree (suggested
`~/Zynergy/forager-forecast-t7-pnw`). **Branch:** `t7-pnw-pilot`, base to be confirmed (open decision
O7). **Review (D18).** **Merge (D40).** **Decision rows:** none until the duplicate D122 is resolved
(open decision O1); then the next free number.

## The machine: read this first

This laptop has 11 GB of RAM (7 GB available when the verify report measured it, section 5) and is
shared, today, by three jobs that come before this one:

- **The pilot's T1 weather fit and scoring** (`pnw-pilot-t1`, RECORD -827: the full model expected
  about 12:00 to 13:00 UTC Sunday 2026-10-11), then the random-date comparison and D33 (3) and (4)
  (RECORD -828).
- **T6b's PNW box tiles** (RECORD -828): a tile filter for `scanfi-layers`, the 5 missing SCANFI
  layers (9.02 GB), the 8 Canadian tiles, then the trees stage for them. RECORD -828: it "yields the
  processor to the pilot's weather fit".
- **Forager app builds**, which the planner schedules.

So: one heavy job at a time, and T7 is last in line. Every heavy command runs under
`systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0 <command>` (the T6b dispatch's
rule). The verify steps below are light (listing, metadata, small reads); say before running anything
over about 1.5 GB or more than a few minutes of CPU, and wait for the planner's go.

## Goal

TASKS.md, T7 (`origin/d121-lean-start:docs/planning/TASKS.md:80-85`):

> **T7. Habitat model, first version**
> - Depends on: T4, T5, T6
> - Also depends on (added 2026-10-06, D100): T6b, so the model is fitted on continental layers, not the test areas T4 and T5 built
> - Does: fit presence-background models for both groups with the effort covariate, then predict with effort held constant and compute the area of applicability.
> - Verify: a spatial block validation report by ecoregion and a mask map.

**The inputs are D121's lean start** (`DECISIONS.md:8` at `aec605d`, owner's words "Go with the lean
start", Forager RECORD -789): "habitat, host trees (T5/T6b genus fractions with the conifer and
broadleaf totals), soil pH, and the NALCMS land and water mask; ... observation, the T6 effort layer.
Any further input (terrain, SSURGO, POLARIS, burn perimeters or others) enters only if a model with it
beats the same model without it on held-out years under the D33 evaluation, and that comparison is
reported." T7 uses no weather; the trigger is T8.

**The area of applicability** is the mask that SPEC needs: R1, "Every scored cell carries a sighting
chance, an uncertainty and an in-or-out applicability flag" (`SPEC.md:61` at `aec605d`); R5, "cells
outside the area of applicability are transparent" (`:72`). The method on record is the CAST
package's area of applicability, "distance to training data in predictor space" (EVIDENCE.md:56,
RESEARCH_LOG.md:56). It is a source to read, not a rule; the method is a proposal item below.

**What the output is, and is not.** The habitat output is relative habitat at 250 m. D12: "The 250 m
raster is relative habitat shading inside each cell and carries no percent." R8 (`SPEC.md:78`): "The
250 m raster is labelled relative habitat and shows no percent." Nothing T7 writes carries a percent,
the words "sighting chance", or any term D58 forbids.

**Why a pilot.** RECORD -806, the owner: "Real forecast, PNW only, ASAP"; -807: "The PNW can be our
pilot run so we know how it works before we commit to the entire country". -806's order: "T1 ...
first; the PNW box's Canadian SCANFI tiles ahead of the continent; then T7 to T9 on the PNW". So part
of T7's job is to measure how this step behaves (time, memory, data gaps, what the validation says)
before the continent is committed to. Those measurements are evidence, below.

## The box, and why

**Proposed: 40.0 to 49.0 N, 125.0 to 111.0 W, by cell centre**, the T6b PNW box (`PNW_BOX`,
`origin/t6b-continental-layers:src/forager_forecast/pnw.py:30`). The owner confirms or picks
another (open decision O2).

Why this one:
- It is the only box whose habitat layers are, or are about to be, complete. Every US study cell in
  it has its tree tile (RECORD -785; the render's `mosaic.json` reads `cells_in_tiles_not_computed_yet:
  0`). Its 102,543 Canadian cells sit in 8 tiles that T6b is filling now (RECORD -828; the 8 tiles are
  named in `docs/audits/2026-10-10-t6b-scanfi-edge-and-pace.md:78-80` on `t6b-scanfi-edge`).
- The weather pull's union box, 40 to 49.5 N, 111 to 125 W (RECORD -812), covers it, so T8 on the same
  box needs no second pull.
- It holds 25 CEC level III ecoregions (5 level I) by 0.1° cell centres, against 12 (3 level I) in
  T1's box (verify report section 4, `dd28648`, lines 226-233). Block validation by ecoregion needs
  blocks.
- It is the area the owner has already shown (the 2026-10-09 test map and images, RECORD -783).

What it costs:
- **It is not T1's box.** T1 and the live pilot map use 42.0 to 49.5 N, 121.0 to 125.0 W
  (`t1_design.py:35`). The strip from 49.0 to 49.5 N (Lower Mainland and more of Vancouver Island) is
  outside this box, and its Canadian cells are in tiles that are **not** among the 8 being filled. How
  many more tiles that strip would need was not determined here.
- **It takes in deserts.** The largest ecoregions are Northern Basin and Range (1,531 centres) and
  Central Basin and Range (1,277) (verify report :231-233). Background points there are easy to tell
  from chanterelle habitat, which can make a habitat model look better than it is where it matters.
  The proposal must say how the validation keeps that from flattering the result.

## Inputs: where each lives, and its state

`DRIVE` is `/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data` (the flash
drive; 15 GB free at 20:08 UTC, `df`). `/mnt/work` had 13 GB free. **Observed** means listed or its
metadata read here; **read** means a file or record says so; nothing below was opened for values.

| Input | Where | State | Rule |
|---|---|---|---|
| Records | `~/Zynergy/forager-forecast-d26/data/d26/downloads/0012112-260928105237408.zip`, 1,434,032,123 bytes | present (observed). sha256 equal to its DOI record (verify report :189, observed there, not re-hashed here) | D26, D71, D72 |
| Record filters for habitat | `records/filters.py`, `r6_audit_steps()` (main, `:176-180`), uncertainty at most 250 m (`:42`) | merged code. Over D26, R6 survivors in T1's PNW box, all fungi: 133,488 (observer key) (`docs/audits/2026-10-06-d28-date-rule/survivors_0012112/pass_r6.json`, read). **Per group, in either box: not in any filed table I found.** The last per-group figures are on the superseded T2 download: PNW Cantharellus 600, Laetiporus 715 after the last step (`2026-09-18-t2-credentialed-run-report.md:206, :232`, download 0005714), under the old date and duplicate rules. Indicative only | SPEC R6, D27, D97, D98 |
| Soil pH, 0 to 30 cm | `DRIVE/t6b/tiles/soil/soil_2048_*.tif`, 89 files, 6 bands each (`ph_mean_0_30cm`, two approximate quantiles, three valid-fraction bands) | done continent-wide (RECORD -802: "soil 89/89"; 89 files observed) | D74, D80, D81 |
| Host trees, whole tiles | `DRIVE/t6b/tiles/trees/trees_256_*.tif` plus `trees_flags_256_*.tif` | 2,015 tiles plus flags (observed; RECORD -802: "trees 2015/2015"). Bands `TREE_BANDS` (`t6b_layers.py:97`): `total_cover_pct`, `valid_fraction`, `source`, and shares of Pseudotsuga, Tsuga, Picea, Abies, Pinus, Quercus, conifer, broadleaf (`crown_cover.py:156-157`, on `t6b-continental-layers`) | D84 to D92, D112, D115, D116 |
| Host trees, US halves of border tiles | `DRIVE/t6b/tiles/trees_us_half/` | 92 (observed; RECORD -802). Canadian cells carry flag 4 "pending" | D119, D120 |
| Host trees, the box's 8 Canadian tiles | 256_-31_21, 256_-30_21, 256_-32_20, 256_-31_20, 256_-30_20, 256_-29_20, 256_-31_19, 256_-30_19 | **pending.** At 20:08 UTC none had a whole tree file and none a SCANFI layer file; 5 had US-half files, 3 are Canada-only (observed). T6b fills them under RECORD -828 | D118, D122 (SCANFI edge), D85, D89 |
| The PNW render | `DRIVE/pnw/mosaic/trees_pnw.tif` (10 bands), `soil_pnw.tif` (2 bands), 250 m, ESRI:102008 (metadata read) | built 2026-10-09 05:39 PDT, **before** Canada. Its tree file holds only Pseudotsuga, Tsuga, conifer and broadleaf shares, so it is a picture, not T7's input. Read the tiles, or rebuild a mosaic with every band | RECORD -772 to -785 |
| Study-area mask | `DRIVE/t6b/mask.tif`, 2 bands: country (0 none, 1 US 48 and DC, 2 Canada, 3 Alaska Hawaii PR USVI, 4 Mexico) and ecoregion (0 in no polygon, 1 Tundra or Arctic Cordillera, 2 other) | done (metadata read) | D111, D113, D117 |
| NALCMS land cover 2020, 30 m | `DRIVE/t6b/sources/nalcms/NA_NALCMS_landcover_2020v2_30m.tif` | present. Used today only inside the tree layer, where class 18 water and value 0 are no data (D112; `t6b_run.py:72`, `scripts/pnw_checks.py:38`). **No master-grid NALCMS layer exists** (`git grep -i nalcms` over src and scripts on `t6b-continental-layers`) | D112, D121 (open decision O5) |
| Ecoregions | `DRIVE/t6b/sources/terr_ecoregions_v2_level_iii_shapefile/` (CEC level III, v2) | present (observed) | D111, D117 |
| Effort surface | `~/Zynergy/forager-forecast-t6/data/t6/{all,cc}/` (`cell_level.csv`, `year_level.csv`, `season.csv`, `day_type.csv`, `effort_manifest.json`) | present (observed). Ten sha256 equal to `docs/audits/2026-10-06-t6-fit/stored_surface_sha256.txt` (verify report :191, observed there). Read through `effort.EffortSurface.read` (`effort.py:633`, main); `effort(cell, week)` raises `NoEffortValue` for a cell outside the 43,035-cell frame or a week outside the 573 (`:618-624`) | D101 to D109; D107 leaves "the level at which T7 holds effort constant" to T7 |
| Master grid and regrid | `grid.py`, `regrid.py`, `t4_layer.py` (main); T6b code on `t6b-continental-layers` (unmerged) | merged for T4; T6b code unmerged | D74, D115 |
| Weather | not used by T7 | | |

## Pilot-scoped deviations

Each is quoted from the rule it bends. The pilot takes it for this first fit only; the continental fit
keeps the rule.

1. **D100**, TASKS.md:82: "T6b, so the model is fitted on continental layers, not the test areas T4
   and T5 built". The pilot fits on one box. The pilot D122 (`origin/pnw-pilot-t1`, DECISIONS.md)
   changes this clause "for this first fit only". Premise V3 checks that it reaches T7.
2. **SPEC.md:15**: "One continental pipeline: static habitat layers on a 250 m equal-area grid". Bent
   in extent only. Same master grid, same layer code, same rules. **D5**, "North America is one
   pipeline and one grid", is kept.
3. **T7's Verify, "a spatial block validation report by ecoregion"** (TASKS.md:84). It can run, but
   inside one box it tests transfer between neighbouring ecoregions, not across the continent. In the
   proposed box that is **25 level III ecoregions under 5 level I** (verify report :231); in T1's box,
   12 under 3. Seven of the 25 hold under 100 cell centres, and Colorado Plateaus holds 1. How many
   hold any chanterelle presence under R6 is not known until counted, so the number of usable blocks
   is a verify item (V9), and the level is open decision O4.
4. **T7's Does, "for both groups"** (TASKS.md:83). Bent only if the owner rules chanterelles only
   (open decision O3).
5. **SPEC.md:20**: "Validation by ecoregion and held-out year". Kept in form; T7 itself has no year
   split, since its layers are static. Say how held-out years enter, if at all.
6. **D18** (DECISIONS.md:103): "A dependent task does not start until its prerequisite's review is
   filed." No independent review of the T6b continental layers was found by the verify report (:266-
   269), and none was found for this dispatch either: no file under `docs/audits/` on any origin
   branch has both "t6b" and "review" in its name (searched 2026-10-10 about 20:20 UTC). The reviews
   on record cover `t6b-pnw-monday` only, and are recorded in Forager RECORD -786 and -788, not as a
   filed review here. T7 on those layers bends D18 unless one is filed, or the
   owner accepts it labelled unreviewed (open decision O6).

**Kept, not bent:** D5's gate and D12's meaning (pilot D122: "unchanged"); R6 (no record above 250 m
reaches habitat training); R8 (no percent at 250 m); D31's rule that a tuning grid is written into the
repo before any fit; D121 (no layer beyond the lean set without a held-out comparison); D58.

## Verify before building, report by message

Confirm or correct each premise, with a file and line or a command and its output. A premise that
fails is a finding, not something to fix quietly.

- **V1. Base.** `git fetch origin`; name the base you cut from and confirm it holds T6b's code,
  D121 and the pilot D122 (`git merge-base --is-ancestor`). Today no single branch holds all three:
  `d121-lean-start` lacks both D122s, `t6b-continental-layers` lacks D121, `pnw-pilot-t1` lacks D121
  and T6b. That is open decision O7; stop until the planner names the base.
- **V2. The D122 collision.** Two different rows are numbered D122: the SCANFI edge ruling on
  `t6b-scanfi-edge` and `t6b-continental-layers` (RECORD -805), and the pilot ruling on
  `pnw-pilot-t1`, `pnw-pilot-scoring` and `pnw-pilot-t1-review` (RECORD -806 to -812). The pilot row
  says "Numbered after D121", so it did not see the other. Confirm by `git show <branch>:docs/
  planning/DECISIONS.md`. Write no D-row until it is resolved (O1). Cite either by branch and RECORD
  number meanwhile.
- **V3. The pilot ruling reaches T7.** Quote the pilot D122's scope words and RECORD -806's order
  ("then T7 to T9 on the PNW"), and say whether they cover T7 or only T1. If only T1, stop.
- **V4. The 8 Canadian tiles.** Confirm on the drive that each now has a whole tree file and flags,
  that its manifest line is `ok`, and that no study cell in the box still carries flag 4 "pending".
  Until then, nothing is fitted on the box (open decision O2 covers a US-only start).
- **V5. Every tree band, both sides.** Confirm which bands carry values in the Canadian cells. D85 and
  D89: Tsuga, Quercus, Pinus, Picea and Abies are "not available" on the Canadian side. Count, in the
  box, the cells with each share defined, by side. A share used as a covariate that is missing on one
  side is a modelling choice to propose (P4), not to fill.
- **V6. The 49 N seam.** T5 found total cover "a known artifact" at the seam and the Douglas-fir,
  conifer and broadleaf shares "no step" (TASKS.md:18; D90). The PNW seam check gave "no verdict"
  while Canada was pending (RECORD -785). Say whether that check has now been run with the Canadian
  side, and its result. Do not run it yourself unless the planner says so; it belongs to T6b.
- **V7. Soil in the box.** Confirm the soil tiles over the box, the count of cells with a mean (the
  render read 16,248,227 of 16,674,133, `mosaic.json`), and that you read `ph_mean_0_30cm` and its
  valid fraction under D74.
- **V8. NALCMS.** Confirm no master-grid NALCMS layer exists. Say what using "the NALCMS land and
  water mask" (D121) would need under each reading of O5: as a mask, already applied through D112 and
  `mask.tif`; or as a land-cover covariate, a new regrid with its own class rule and check.
- **V9. Presences.** Before any presence is counted, commit (a) the record list (R6 steps from
  `filters.py`), (b) the box test by cell centre, (c) the minimum number of presences per group and
  per validation block below which a block is "uninformative" (D33 used 30 positives per fold; say
  whether that carries over and why). Then count presences per group, per year, per side and per
  ecoregion at levels III and I. Name the duplicate key used and why (D27: event or observer).
- **V10. Effort frame.** Count the box's 0.1° cells, and how many are outside the effort frame (so
  `effort()` refuses them). Say what that means for background points there. No made-up value
  (D107's `NoEffortValue`).
- **V11. Cell keying across scales.** A 250 m master-grid cell and a record each map to a 0.1° weather
  cell by `cells.cell_for` (D46, D63, D64). Confirm the mapping from the master grid's ESRI:102008
  cell centre to latitude and longitude, and its ties, on a fixture.
- **V12. Ecoregion assignment.** Confirm the level III file, its licence as stated at source (D113's
  practice), and that a cell's ecoregion is read at its centre, as D117 does for the mask.
- **V13. Size and memory.** The box at 250 m is about 16.7 million study cells (`mosaic.json`).
  Estimate the predictor table's memory for the proposed background sample and the predict pass
  over every cell, against the 5 GB cap, from one trial window. Say whether prediction must stream by
  tile.
- **V14. Licences of what the output reads.** List each source the habitat raster reads and its
  licence as stated at source (DATA_REGISTER.md; D84, D112, D113), so the output's attribution names
  exactly what it read (the planner's call in RECORD -822).

## Propose before fitting (the owner rules)

Send these as one list, each with a recommendation, a reason and a source, **before any count of the
outcome beyond V9's presence totals and before any fit**. This is how T6 ran (D101 to D108).

- **P1. Groups.** Chanterelles (Cantharellus) and chicken of the woods (Laetiporus), or chanterelles
  only (O3). Give V9's counts for both.
- **P2. Presences.** The record list, key and box from V9. Whether presences are thinned to one per
  250 m cell (or per some other unit), and why.
- **P3. Background.** How background points are drawn (count, seed 20260918 per D31, where from), and
  how effort enters: as a covariate per D107, a weighting of the background by effort, or both. Name
  the source for the choice (EVIDENCE.md:55, Simmonds et al. 2020: "Integration alone does not fix
  spatial bias. A bias covariate or spatial term is needed").
- **P4. Covariates.** Exactly which bands from D121's set, how a share undefined below 10% canopy
  (D89 (3)) or "not available" in Canada (D85) is handled, and how total cover's seam artifact is
  handled. Any covariate beyond D121's set is out of scope; propose it as a later comparison, not now.
- **P5. Model family and package.** Name it, why, and the exact pinned version (uv). If it is
  LightGBM, it is already pinned at 4.7.0 (START_HERE.md:75); say whether its use here differs.
- **P6. Effort held constant.** The level at which effort is held constant for prediction (D107 left
  it to T7): a box-wide value, a per-band value, or another. State what the habitat output then means
  in one plain sentence.
- **P7. Validation.** Blocks (ecoregion level, O4), folds, the metric or metrics, the comparison model
  (for example a model with effort only, or a null), the bootstrap and its seed, and how the deserts
  are kept from flattering the score (for example a score within forested blocks reported beside the
  whole-box score). The tuning grid is written into the repo before any fit (D31).
- **P8. Area of applicability.** The method (the CAST approach on record, or another), the threshold
  rule, fixed before any prediction is read, and what a masked cell shows (R5: transparent).
- **P9. Outputs.** File names, format and location on the drive: the relative-habitat raster on the
  master grid for the box, the applicability mask, the block report, a mask map image, and a manifest
  with input hashes, code commit, seed and configuration (the D107 pattern). No percent, no "sighting
  chance" on any 250 m output (R8).

**Stops:** V1, V2 and V3 before anything else; V4 before any fit; any proposal that needs a new rule;
any count that falls under the minimum fixed in V9; any memory estimate over the cap.

## Build (after the rulings and the planner's go)

- **Tests first**, through the real entry points: the box and side tests, the presence list (R6 count
  of records above 250 m in the training table is zero, SPEC R6's own check), the cell keying, the
  effort refusal path, the block assignment, the applicability mask on a synthetic case where the
  answer is known, and a leakage test that no presence in a held-out block is used in its fold's fit.
- **The strict revert runner** (saved-copy restore, `__pycache__` cleared,
  `PYTHONDONTWRITEBYTECODE=1`, refuse a run with compile or import errors or where the interpreter
  does not see the edit; after each revert confirm the forward change is present). Full suite before
  and after, under the cap.
- **The fit and prediction**, one heavy job at a time, yielding to the pilot's T1 work and T6b.
- **The Verify as TASKS.md states it**: the block validation report by ecoregion, and the mask map.

## Evidence required

- Commits, each pushed, with hashes. Tests seen failing before the code they cover; each revert's
  failure message specific to its own edit, and the build log free of errors before it is cited.
- V1 to V14 answered, each with a file and line or a command and its output.
- The presence counts per group, year, side and ecoregion, with the total read against the filed
  survivor count for the box (133,488 all-fungi R6 survivors in T1's box is the one filed figure;
  for the proposed box, say what it is checked against).
- The block report: per block, presences, background points, the metric and its interval, and
  "uninformative" where the minimum is not met. The pooled figure and how it was pooled.
- The mask map image and the count of cells in and out of the applicability area, per side and per
  ecoregion.
- Output files with sha256 and sizes; the manifest.
- **The pilot measures** (RECORD -807; verify report section 4's table): wall time and peak memory
  for each of: presence count, predictor extraction, fit, predict, mask; disk used; every guard that
  fired and every cell or record refused, counted. Scaled to the continent by cell count, marked as
  an estimate.
- A report in `docs/audits/` with its index row, and TASKS.md and START_HERE updated, with the four
  disclosure sections: confirmed vs inferred, could not determine, premises that were wrong, decided
  beyond scope.

## Abort conditions

Stop, report, and wait. Do not work around any of these.

- The base cannot hold T6b's code, D121 and the pilot ruling together (V1), or the pilot ruling does
  not reach T7 (V3).
- A study cell in the box still reads "pending" at fit time (V4).
- D26's zip or T6's stored surface no longer matches its filed sha256.
- A count falls under the minimum fixed before it was read (V9).
- Memory over the 5 GB cap on the trial window, or the laptop's other jobs need the processor (yield;
  do not fight for it).
- Any record above 250 m found in the training table.
- A leakage test fails.
- The work would need a rule changed, a layer added beyond D121, a new download, or a T6b tile
  rewritten.
- Two failed attempts on the same failure: stop guessing and report the data.

## Do not touch

- No GBIF request, no Copernicus or Open-Meteo request, no secret (D36).
- No edit to a filed record (D41); no edit to another branch's DECISIONS rows; no merge (D40).
- Nothing on `pnw-pilot-t1`, `pnw-pilot-scoring`, `pnw-pilot-t1-review`, or the zynergy-site repo.
  T7's output is not put on the live map. The map's next data drop is the weather model (RECORD
  -817, -825).
- T6b's tiles, manifest, runner and run are read-only. Do not start, pause or stop a T6b section.
- Nothing in the Forager app repo. No forbidden term (D58), and no "probability" or "chance" outside
  D12's defined term.

## What follows, one line each

- **T8** (trigger and joint challenger): windows with randomisation checks on the union box's
  weather, after T1's pilot result; its own dispatch.
- **T9** (calibration and gate): calibrate to R3 and compute skill per ecoregion; D5's gate decides
  what is shown.
- **T10** (nightly job): the live weather route, after the Open-Meteo rain gap (RECORD -819, -820) is
  understood.
- **T11** (vector companion and map client): D55 and D56's shapes, checked on a real phone.

## Open decisions for the owner

Listed separately so none is decided inside the build. Each needs a word before the step it gates.

- **O1. The two D122 rows.** One number holds two rulings on different branches (V2). One must be
  renumbered by a new row when the branches meet. Which, and when? (Planner's to propose; it changes
  no ruling.)
- **O2. The box, and whether to wait for Canada.** (a) 40 to 49 N, 111 to 125 W, after the 8 Canadian
  tiles are in (recommended above); (b) the same box, US cells first, Canada added after (faster;
  the first fit would not cover southern Vancouver Island and Delta); (c) T1's box, 42 to 49.5 N, 121
  to 125 W, so habitat and the live map line up (needs Canadian tiles north of 49 N that are not
  being filled; their number is not determined); (d) the union, 40 to 49.5 N (as (c), plus the
  deserts).
- **O3. Both groups or chanterelles only.** TASKS.md says both; the pilot's T1 is chanterelles only.
  Chicken of the woods is the control (SPEC). The superseded T2 counts suggest a few hundred R6
  records each in the PNW; V9 gives the real ones.
- **O4. Which ecoregion level validation uses.** Nothing on record says which level R2 and T9 mean
  (verify report :235-237). Level III gives more, smaller blocks with few presences each; level I
  gives 5 blocks in the proposed box (3 in T1's).
- **O5. What D121's "NALCMS land and water mask" means.** A mask only (already applied through D112's
  water rule and the study mask), or a land-cover covariate (a new layer, its class rule, its check).
- **O6. D18 for the T6b layers.** File an independent review of the T6b continental layers in the box
  before T7 fits on them, or let T7 proceed labelled unreviewed, with the review to follow.
- **O7. The base branch.** No branch holds T6b's code, D121 and the pilot ruling together (V1). The
  planner names the base, or merges the needed branches first under D40. Suggested: cut from
  `t6b-continental-layers` and merge `d121-lean-start` and the pilot's DECISIONS row in, once O1 is
  settled.
