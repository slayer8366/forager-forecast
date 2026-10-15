**Supersedes `2026-10-11-t7-pnw-pilot-habitat.md` (never dispatched), which stays unchanged beside it.**

# Dispatch: T7 for the PNW pilot, a habitat map for mycorrhizal mushrooms as a group, verify and propose first

**Verify first and report by message. Every modelling choice is proposed and ruled before any count of
the outcome is read and before anything is fitted. No fit until the owner has ruled and the planner
says go. No GBIF request, no climate pull, no Open-Meteo request, no merge (D40).**

Written on 2026-10-15 (UTC, about 04:30) by a planning writer for the Forager planner session, on
Forager RECORD -1025 ("Rewrite the T7 habitat plan for mycorrhizal mushrooms as a group"), documents
only. Base: forager-forecast `origin/main` at `a79d667` (the merge of `merge-2026-10-15`, Forager
RECORD -1021). Forager RECORD read at `records-after-173` `28d4b83c` (entries -806 to -812, -828,
-832, -913, -914, -1017, -1021, -1023, -1025). The flash drive, `/mnt/work` and the D26 and T6
folders were listed (names, sizes, dates; no values read) at about 04:10 UTC on 2026-10-15.
**Every cite is a premise to re-check. Anything here that names what exists on disk was true when
listed and may have moved since.**

This file rewrites the T7 dispatch drafted on 2026-10-10 for chanterelles and chicken of the woods.
What changed and why is in "What changed from the chanterelle plan" at the end; the citations that
had gone stale are listed there too.

**Writer (D38):** a coder session on this laptop, in its own worktree (suggested
`~/Zynergy/forager-forecast-t7-myco`). **Branch:** `t7-mycorrhizal-habitat`, cut from forecast main
`a79d667` or later (D126). **Review (D18).** **Merge (D40).** **Decision rows:** the next free number
after D126, checked against every origin branch before the first is written.

## The machine: read this first

This laptop has 11 GB of RAM (5 GB available at 04:10 UTC on 2026-10-15, `free -g`). The owner's order
for forecast work (Forager RECORD -1017, -1021) is: the habitat map's open questions, then the
continental layers restart (T6b), then this week's forecast. So T7 may share the processor with the
T6b restart and the weekly forecast run, and the planner schedules Forager app builds around them.
Whether app builds still run on this laptop at all is not checked here.

One heavy job at a time. Every heavy command runs under
`systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0 <command>` (the T6b dispatch's
rule). The verify steps below are light (listing, metadata, small reads); say before running anything
over about 1.5 GB or more than a few minutes of CPU, and wait for the planner's go.

Disk at 04:10 UTC on 2026-10-15 (`df -h`): the flash drive 6.0 GB free (it had 15 GB on 2026-10-10),
`/mnt/work` 23 GB, `/` 12 GB. Say where outputs go before writing any, with an estimate of their size.

## Goal

TASKS.md, T7 (`docs/planning/TASKS.md:80-85` on main):

> **T7. Habitat model, first version**
> - Depends on: T4, T5, T6
> - Also depends on (added 2026-10-06, D100): T6b, so the model is fitted on continental layers, not the test areas T4 and T5 built
> - Does: fit presence-background models for both groups with the effort covariate, then predict with effort held constant and compute the area of applicability.
> - Verify: a spatial block validation report by ecoregion and a mask map.

**The target has changed.** The owner, verbatim (Forager RECORD -913): "I think it would be worthwhile
having a map focused on mycorrhizal mushrooms for now. It's already geared in that direction and this
is something that can benefit more than foragers". Asked what it should show, the owner chose
"Habitat: where mycorrhizal fungi can grow (Recommended)" (offered: weekly forecasts for several
mycorrhizal species; both, habitat first). What -913 sets: "A habitat map, not a weekly forecast, of
where host trees and soils suit mycorrhizal mushrooms as a group, for foresters, ecologists and land
managers as well as foragers. It builds on the drafted T7 habitat dispatch ... widened from
chanterelles to the mycorrhizal group." -913 also says "scope only, not a go-ahead".

The positioning, verbatim (Forager RECORD -914): "Other apps focus on burn morels for their maps, and
we can approach it from the mycorrhizal angle". -914 adds: "Unverified by the planner: what other apps
actually map. A prior-art check belongs in the habitat dispatch." That check is V15 below.

So T7's "both groups" (TASKS.md:83) is read here as **the mycorrhizal group, plus a control if the
owner keeps one** (open decisions M1 to M5). This reading changes what SPEC and TASKS say T7 does and
needs its own decision row before the build (M6). Until that row exists, the reading is a premise
the owner has stated in scope only.

**The inputs are D121's lean start** (`DECISIONS.md:11`, owner's words "Go with the lean start",
Forager RECORD -789): "habitat, host trees (T5/T6b genus fractions with the conifer and broadleaf
totals), soil pH, and the NALCMS land and water mask; ... observation, the T6 effort layer. Any
further input (terrain, SSURGO, POLARIS, burn perimeters or others) enters only if a model with it
beats the same model without it on held-out years under the D33 evaluation, and that comparison is
reported." T7 uses no weather. **The host-genus bands were chosen for chanterelles**, not for the
mycorrhizal group: the T5 verify report's host sources are Pilz et al. 2003 for *Cantharellus* in the
PNW and Burdsall and Banik 2001 for *Laetiporus* (`docs/audits/2026-10-06-t5-verify-report.md:85-97`),
and the bands are `HOST_GENERA = ("Pseudotsuga", "Tsuga", "Picea", "Abies", "Pinus", "Quercus")` plus
conifer and broadleaf totals (`src/forager_forecast/crown_cover.py:155-156`). Hosts of other
mycorrhizal genera (birch, aspen and poplar, larch, beech among them; from memory, unverified) have no
band of their own and reach the model only through the broadleaf and conifer totals. That is open
decision M7.

**The area of applicability** is the mask SPEC needs: R1, "Every scored cell carries a sighting
chance, an uncertainty and an in-or-out applicability flag" (`SPEC.md:61`); R5, "cells outside the
area of applicability are transparent" (`SPEC.md:72`). The method on record is the CAST package's
area of applicability, "distance to training data in predictor space" (`EVIDENCE.md:56`,
`RESEARCH_LOG.md:56`). It is a source to read, not a rule; the method is proposal P8.

**What the output is, and is not.** The habitat output is relative habitat at 250 m. D12: "The 250 m
raster is relative habitat shading inside each cell and carries no percent." R8 (`SPEC.md:78`): "The
250 m raster is labelled relative habitat and shows no percent." Nothing T7 writes carries a percent,
the words "sighting chance", or any term D58 forbids. The group contains deadly genera if it is drawn
from a trait list (*Amanita*, for one; from memory). SPEC keeps "Species identification and edibility
advice" out of scope (`SPEC.md:25`), so nothing T7 writes names a genus as edible or suggests it.

**Why a pilot.** RECORD -806, the owner: "Real forecast, PNW only, ASAP"; -807: "The PNW can be our
pilot run so we know how it works before we commit to the entire country". D123 (`DECISIONS.md:9`)
changes D100 "for this first fit only". Part of T7's job is to measure how this step behaves (time,
memory, data gaps, what the validation says) before the continent is committed to. Those
measurements are evidence, below.

## The box, and why

**Decided: 40.0 to 49.0 N, 125.0 to 111.0 W, by cell centre**, the T6b PNW box (`PNW_BOX`,
`src/forager_forecast/pnw.py:30`). The owner, verbatim (Forager RECORD -832): "Test map's box, after
the 8 tiles (Recommended)" (offered: T1's area; the union box). Carried over unchanged (A2 below):
none of the reasons depended on which mushrooms are modelled.

- Its habitat layers are complete. The 8 Canadian tiles have landed: the D18 review's pass 5 found
  all 10 tiles of the night run (the 8, plus 256_-27_20 and 256_-28_20) with ok trees lines and
  hashes that match (`docs/audits/2026-10-11-t6b-pnw-layers-review.md:55-62`, `:233-252`). Listed
  on the drive on 2026-10-15: each of the 8 has `trees_<tile>.tif` and `trees_flags_<tile>.tif`, and
  `tiles/trees/` holds 2,025 whole tree tiles. The rebuilt mosaic's summary reads
  `cells_in_tiles_not_computed_yet: 0` and `cells_pending_canada: 0`
  (`docs/audits/2026-10-10-t6b-pnw-run/seam-after-10-tiles/mosaic-and-seam.out.txt`).
- The weather pull's union box (40 to 49.5 N, 111 to 125 W, D123) covers it.
- It holds 25 CEC level III ecoregions (5 level I) by 0.1° cell centres, against 12 (3 level I) in
  T1's box (`docs/audits/2026-10-10-pnw-first-fit-verify-report.md:231-233`).

What it costs:
- **It is not T1's box** (42.0 to 49.5 N, 121.0 to 125.0 W, `src/forager_forecast/t1_design.py:35`).
  The 49.0 to 49.5 N strip stays outside T7.
- **It takes in deserts.** The largest ecoregions are Northern Basin and Range (1,531 centres) and
  Central Basin and Range (1,277) (verify report `:232`). For a mycorrhizal group this is sharper
  than it was for chanterelles: almost any model separates sagebrush steppe from forest, so a
  box-wide score can look good while saying nothing about which forests suit the group. P7 must say
  how the validation keeps that from flattering the result.

## Inputs: where each lives, and its state

`DRIVE` is `/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data`.
**Observed** means listed or its metadata read on 2026-10-15; **read** means a file or record says so;
nothing below was opened for values.

| Input | Where | State | Rule |
|---|---|---|---|
| Records | `~/Zynergy/forager-forecast-d26/data/d26/downloads/0012112-260928105237408.zip`, 1,434,032,123 bytes | present (observed). sha256 equal to its DOI record (verify report `:189`, observed there, not re-hashed here). All US and Canada fungi, so every mycorrhizal genus is already in it: no new GBIF request is needed for the group | D26, D71, D72 |
| Record filters for habitat | `src/forager_forecast/records/filters.py`, `r6_audit_steps()` (`:176-182`), uncertainty at most 250 m (`:42`) | merged code. R6 survivors over D26, T1's PNW box, all fungi: 133,488 (observer key) (`docs/audits/2026-10-06-d28-date-rule/survivors_0012112/pass_r6.json`, read by the 2026-10-10 writer, not re-read). **No per-group figure for the mycorrhizal group exists in any filed table**, and none for the T6b box | SPEC R6, D27, D97, D98 |
| Taxon fields | `src/forager_forecast/records/occurrence.py:52-65` (`COLUMNS_READ`) | the loader reads `acceptedTaxonKey` and `genusKey`, not the genus **name**, family or order. A membership list of genus names needs the download's own name-to-key pairs (V16), read offline, not GBIF's matching API | D27, D44 |
| Group membership list | none | **does not exist.** Its source, version and licence are open decision M1 | SPEC constraints (`SPEC.md:84`, `:90`) |
| Soil pH, 0 to 30 cm | `DRIVE/t6b/tiles/soil/`, 89 files | done continent-wide (89 files observed) | D74, D80, D81 |
| Host trees, whole tiles | `DRIVE/t6b/tiles/trees/trees_256_*.tif` plus `trees_flags_256_*.tif` | 2,025 whole tiles (observed; 2,015 before the PNW night run, plus its 10). Bands `TREE_BANDS` (`src/forager_forecast/t6b_layers.py:97`) | D84 to D92, D112, D115, D116, D119, D120, D122 |
| The PNW render | `DRIVE/pnw/mosaic/trees_pnw.tif`, `soil_pnw.tif` | **rebuilt** after the Canadian tiles (file times 2026-10-10 15:18 local; summary in `seam-after-10-tiles/mosaic-and-seam.out.txt`). Its summary counts shares for Pseudotsuga, Tsuga, conifer and broadleaf only, so it is a picture, not T7's input (inferred from the summary, bands not read here). Read the tiles | RECORD -835, -838 (cited by the OMS briefing, not read here) |
| Study-area mask | `DRIVE/t6b/mask.tif` | present (observed) | D111, D113, D117 |
| NALCMS land cover 2020, 30 m | `DRIVE/t6b/sources/nalcms/` | present (observed). Used only inside the tree layer (D112; `scripts/t6b_run.py:73`, `scripts/pnw_checks.py:38`). **Decided: a mask only, not an input** (A4) | D112, D121, RECORD -832 |
| Ecoregions | `DRIVE/t6b/sources/terr_ecoregions_v2_level_iii_shapefile/` | present (observed). Level III is the validation block (D125) | D111, D117, D125 |
| Effort surface | `~/Zynergy/forager-forecast-t6/data/t6/{all,cc,counts}/` | present (observed). Ten sha256 equal to `docs/audits/2026-10-06-t6-fit/stored_surface_sha256.txt` (verify report `:191`, observed there). Read through `EffortSurface.read` (`src/forager_forecast/effort.py:633`); `effort()` raises `NoEffortValue` outside the 43,035-cell frame or the 573 weeks (`:618-624`) | D101 to D109; D107 leaves "the level at which T7 holds effort constant" to T7 |
| Master grid and regrid | `grid.py`, `regrid.py`, `t4_layer.py`, `t6b_*.py` | merged on main | D74, D115 |
| Weather | not used by T7 | | |

## Pilot-scoped deviations

Each is quoted from the rule it bends. The pilot takes it for this first fit only; the continental fit
keeps the rule.

1. **D100**, TASKS.md:82: "T6b, so the model is fitted on continental layers, not the test areas T4
   and T5 built". The pilot fits on one box, under D123 (`DECISIONS.md:9`), "for this first fit
   only". V3 checks that D123 reaches this T7.
2. **SPEC.md:15**: "One continental pipeline: static habitat layers on a 250 m equal-area grid". Bent
   in extent only. **D5**, "North America is one pipeline and one grid", is kept.
3. **TASKS.md:84 and D125.** Block validation by level III ecoregion inside one box tests transfer
   between neighbouring ecoregions, not across the continent. 25 level III blocks under 5 level I;
   seven hold under 100 cell centres and Colorado Plateaus holds 1 (verify report `:231-233`).
4. **Not a pilot deviation but a scope change: TASKS.md:83, "for both groups", and SPEC.md:13-14,
   "Phase 1 groups: chanterelles ... and chicken of the woods ... as the control".** The target is
   now the mycorrhizal group (RECORD -913). SPEC's own header says "Changes to Decisions or
   Requirements need a new row in DECISIONS.md first" (`SPEC.md:3`), and START_HERE's fixed term
   "Forager group" means "A genus-level group such as chanterelles" (`START_HERE.md:43`), which a
   group of many genera is not. This is open decision M6. T7 does not build until it is ruled.
5. **SPEC.md:20**: "Validation by ecoregion and held-out year". Kept in form; T7's layers are static.
   Say how held-out years enter, if at all.
6. **D18** (`DECISIONS.md:106`): "A dependent task does not start until its prerequisite's review is
   filed." **Now met for the box's layers:** the review is filed on main
   (`docs/audits/2026-10-11-t6b-pnw-layers-review.md`): no blocking finding, three should-fix (S1 to
   S3) and six notes. S1 (the seam could run on only 6 of 25 transects) was overtaken by the seam
   re-run on all 25 after the 2 extra tiles (`seam-after-10-tiles/mosaic-and-seam.out.txt`; OMS
   briefing `:454-458`). Whether S2 and S3 have been fixed is not checked here (V6).

**Kept, not bent:** D5's gate and D12's meaning; R6 (no record above 250 m reaches habitat
training); R8 (no percent at 250 m); D31's rule that a tuning grid is written into the repo before any
fit, and its seed 20260918; D121 (no layer beyond the lean set without a held-out comparison); D58.

## Verify before building, report by message

Confirm or correct each premise, with a file and line or a command and its output. A premise that
fails is a finding, not something to fix quietly.

- **V1. Base.** `git fetch origin`; name the base you cut from (main `a79d667` or later, D126) and
  confirm with `git merge-base --is-ancestor` that it holds T6b's code, D121 and D123. At writing,
  every tip named in RECORD -1021, plus `cfbf50d`, `aec605d`, `a8f85b9`, `dd28648`, `9e24e67` and
  `04f0302`, is an ancestor of `a79d667` (observed). If main has moved, say what moved.
- **V2. Decision rows.** Confirm D122 is the SCANFI edge ruling and D123 the pilot ruling
  (`DECISIONS.md:10`, `:9`), that D125 and D126 are on your base as filed with this dispatch, and that
  no origin branch holds a different row with any number you are about to use.
- **V3. The pilot ruling reaches this T7.** Quote D123's scope words ("the first model is a Pacific
  Northwest pilot ... for this first fit only") and RECORD -806's order ("then T7 to T9 on the
  PNW"), and say whether they cover a habitat map for the mycorrhizal group or only the chanterelle
  chain they were written for. If you read them as not covering it, stop.
- **V4. The box's tiles.** Confirm on the drive that each of the 8 Canadian tiles has a whole tree
  file and flags with an ok manifest line, and that no study cell in the box carries flag 4
  "pending" (the review's pass 5 says so as of 2026-10-10; re-check, do not cite).
- **V5. Every tree band, both sides.** D85 and D89: Tsuga, Quercus, Pinus, Picea and Abies are "not
  available" on the Canadian side. Count, in the box, the cells with each share defined, by side
  (the mosaic summary has 7,087,659 cells with a Pseudotsuga share and 6,991,082 with a Tsuga share;
  say whether the gap is the Canadian side). A share missing on one side is a modelling choice (P4),
  not something to fill.
- **V6. The T6b review's open items.** Say whether S2 and S3 of
  `docs/audits/2026-10-11-t6b-pnw-layers-review.md` (`:91-112`) were fixed, and on which commit. Do
  not fix them; they belong to T6b. Confirm the seam verdicts after the re-run (total cover a known
  artifact on 23 transects with a border step; the Douglas-fir, conifer and broadleaf shares no step
  on 7) from `seam-after-10-tiles/`, and say how T7 handles the total-cover artifact (P4).
- **V7. Soil in the box.** Confirm the soil tiles over the box, the count of cells with a mean (the
  rebuilt mosaic's summary reads 16,248,227 of 16,674,133), and that `ph_mean_0_30cm` and its valid
  fraction are read under D74.
- **V8. NALCMS.** Confirm no master-grid NALCMS layer exists, that water and unmapped pixels are no
  data in the tree layer (D112), and that the study area is `mask.tif`. Under A4 nothing new is
  built for it.
- **V9. Presences, the group.** This step runs only after the owner has ruled M1 and M2 (which taxa
  count). Before any presence is counted, commit (a) the membership list as ruled, with its source,
  version and sha256; (b) the record list (R6 steps from `filters.py`); (c) the box test by cell
  centre; (d) the minimum presences per level III block below which a block is "uninformative", fixed
  now under D125 (D33 used 30 positives per fold; say whether that carries over and why); (e) the
  minimum records per genus below which a genus is reported but not weighted on its own, if M3 is
  ruled for equal weighting. Then count presences per genus, for the group, per year, per side and
  per ecoregion at levels III and I. Name the duplicate key and why (D27: a key with taxon counts two
  genera seen by one person on one day as two records; say what that means for a group presence).
  Read the group total against the all-fungi R6 total for the same box.
- **V10. Effort frame.** Count the box's 0.1° cells, and how many are outside the effort frame (so
  `effort()` refuses them). Say what that means for background points there. No made-up value.
- **V11. Cell keying across scales.** A 250 m master-grid cell and a record each map to a 0.1°
  weather cell by `cells.cell_for` (D46, D63, D64). Confirm the mapping from the master grid's
  ESRI:102008 cell centre to latitude and longitude, and its ties, on a fixture.
- **V12. Ecoregion assignment.** Confirm the level III file, its licence as stated at source (D113's
  practice; DATA_REGISTER's CEC ecoregions row reads "CC BY 4.0 where CEC is the author"), and that a
  cell's ecoregion is read at its centre, as D117 does for the mask.
- **V13. Size and memory.** About 16.7 million study cells in the box. Estimate the predictor table's
  memory for the proposed background sample and the predict pass over every cell, against the 5 GB
  cap, from one trial window. Say whether prediction must stream by tile.
- **V14. Licences of what the output reads.** List each source the habitat raster reads and its
  licence as stated at source (DATA_REGISTER.md; D84, D112, D113), the membership list's source
  included, so the output's attribution names exactly what it read (the planner's call in RECORD
  -822).
- **V15. Prior art: what other foraging apps and public maps show (RECORD -914).** Before any
  proposal, check what other mushroom-foraging apps' maps actually show, and what public mycorrhizal
  habitat or distribution maps already exist. Read only public pages (store listings, product
  pages, help pages, published papers); no account, no purchase, no download. For each: what the map
  shows (burn perimeters, host trees, predicted species, user finds, other), at what scale, from
  what data as the page states it, whether it shows a percent or a chance, and the date read. In
  the report, **describe products generically** ("a paid foraging app's burn-morel map"), never by
  name; papers and datasets are cited normally. Two research maps to look for, both from memory and
  unverified: a 2019 global map of the share of forest held by trees that partner with
  ectomycorrhizal fungi, and a 2025 global atlas of underground mycorrhizal fungal diversity from
  soil DNA. GlobalFungi (soil DNA, CC BY 4.0) is already in DATA_REGISTER.md. Say whether -914's
  premise ("Other apps focus on burn morels for their maps") holds, and what, if anything, already
  maps mycorrhizal habitat at a forest-stand scale in North America. This is research for framing;
  it adds no layer (D121) and changes no rule.
- **V16. Genus names to keys, offline.** Confirm the D26 download carries the genus name beside
  `genusKey` (and family and order, if M2's options need them), so a membership list of names can be
  joined to records without GBIF's matching API. Count the group's records that have a family but no
  genus (identified only to family), by family, without reading any location.
- **V17. The membership source, read at source.** For the source the owner rules under M1, open its
  page and record: the version or release, the licence as stated at source, how it assigns a
  lifestyle (by genus, by species, with or without a confidence), and how it marks mixed or uncertain
  genera. Do not fetch the list itself until the owner has ruled M1 and the planner says go; then
  fetch it once, record its sha256, and file a DATA_REGISTER row before it is used (`SPEC.md:84`).

## Propose before fitting (the owner rules)

Send these as one list, each with a recommendation, a reason and a source, **before any count of the
outcome beyond V9's presence totals and before any fit**. This is how T6 ran (D101 to D108).

- **P1. Groups, as ruled.** The membership list (M1, M2), the weighting (M3), and the control (M4),
  with V9's counts for each. Say what the control is meant to show for a habitat model: a
  non-mycorrhizal group whose habitat model should not simply reproduce the mycorrhizal one.
- **P2. Presences.** The record list, key and box from V9. Whether presences are thinned to one per
  250 m cell (or per some other unit), how a cell with several genera counts under the ruled
  weighting, and why.
- **P3. Background.** How background points are drawn (count, seed 20260918 per D31, where from),
  and how effort enters: as a covariate per D107, a weighting of the background by effort, or
  both. Name the source for the choice (`EVIDENCE.md:55`, Simmonds et al. 2020: "Integration alone
  does not fix spatial bias. A bias covariate or spatial term is needed"). Say whether background is
  drawn from all fungal outings (a target-group background, which T6's outings already are) or from
  the study area at random.
- **P4. Covariates.** Exactly which bands from D121's set, how a share undefined below 10% canopy
  (D89 (3)) or "not available" in Canada (D85) is handled, and how total cover's seam artifact is
  handled. The host bands were chosen for chanterelles (M7); say what that leaves out for the group.
  Any covariate beyond D121's set is out of scope; propose it as a later comparison, not now.
- **P5. Model family and package.** Name it, why, and the exact pinned version (uv). LightGBM is
  already pinned at 4.7.0 (`pyproject.toml:17`; START_HERE.md session log `:82`); say whether its use
  here differs.
- **P6. Effort held constant.** The level at which effort is held constant for prediction (D107 left
  it to T7): a box-wide value, a per-band value, or another. State what the habitat output then
  means in one plain sentence a forester would read correctly.
- **P7. Validation.** Blocks are level III ecoregions with a level I summary beside (D125); the
  minimum from V9 (d). Folds, the metric or metrics, the comparison models, the bootstrap and its
  seed, and how the deserts are kept from flattering the score. At least two comparison models:
  effort only, and host-tree totals only (conifer plus broadleaf cover), so the report shows whether
  the full model adds anything beyond "where the forest is". A score within forested blocks is
  reported beside the whole-box score. The tuning grid is written into the repo before any fit (D31).
- **P8. Area of applicability.** The method (the CAST approach on record, or another), the threshold
  rule, fixed before any prediction is read, and what a masked cell shows (R5: transparent).
- **P9. Outputs.** File names, format and location: the relative-habitat raster on the master grid
  for the box, the applicability mask, the block report, a mask map image, and a manifest with input
  hashes (the membership list's included), code commit, seed and configuration (the D107 pattern).
  No percent, no "sighting chance", no edibility wording on any 250 m output (R8, `SPEC.md:25`).
- **P10. The bar for showing it (M8).** If the owner wants the habitat map shown to anyone later,
  propose the test it must pass, fixed before the fit, in the same form as D5: for example, the full
  model beats both comparison models on pooled held-out blocks with a bootstrap interval that
  excludes zero. Nothing from this dispatch is shown anywhere either way.

**Stops:** V1, V2 and V3 before anything else; M1, M2 and M6 ruled before V9; V4 before any fit; any
proposal that needs a new rule; any count that falls under a minimum fixed in V9; any memory estimate
over the cap.

## Build (after the rulings and the planner's go)

- **Tests first**, through the real entry points: the box and side tests; the membership join (a
  fixture record of a listed genus is in, one of an unlisted genus is out, one identified only to
  family is handled as M2 rules, and the list's sha256 is checked before use); the presence list (R6
  count of records above 250 m in the training table is zero, SPEC R6's own check); the cell keying;
  the effort refusal path; the block assignment; the applicability mask on a synthetic case where the
  answer is known; and a leakage test that no presence in a held-out block is used in its fold's fit.
- **The strict revert runner** (saved-copy restore, `__pycache__` cleared,
  `PYTHONDONTWRITEBYTECODE=1`, refuse a run with compile or import errors or where the interpreter
  does not see the edit; after each revert confirm the forward change is present). Full suite before
  and after, under the cap.
- **The fit and prediction**, one heavy job at a time, yielding to the jobs named under "The machine".
- **The Verify as TASKS.md states it**: the block validation report by ecoregion, and the mask map.

## Evidence required

- Commits, each pushed, with hashes. Tests seen failing before the code they cover; each revert's
  failure message specific to its own edit, and the build log free of errors before it is cited.
- V1 to V17 answered, each with a file and line or a command and its output. V15 as a table, products
  described generically.
- The membership list as committed (or its pointer and sha256 if it is too large), with every genus's
  record count in the box, and the records left out under M2 counted by reason.
- The presence counts per genus and for the group, per year, side and ecoregion, with the group total
  read against the all-fungi R6 total for the box.
- The block report: per block, presences, background points, the metric and its interval, and
  "uninformative" where the minimum is not met. The pooled figure and how it was pooled. The level I
  summary beside it. The two comparison models' scores beside the full model's.
- The mask map image and the count of cells in and out of the applicability area, per side and per
  ecoregion.
- Output files with sha256 and sizes; the manifest.
- **The pilot measures** (RECORD -807): wall time and peak memory for presence count, predictor
  extraction, fit, predict and mask; disk used; every guard that fired and every cell or record
  refused, counted. Scaled to the continent by cell count, marked as an estimate.
- A report in `docs/audits/` with its index row, and TASKS.md and START_HERE updated, with the four
  disclosure sections: confirmed vs inferred, could not determine, premises that were wrong, decided
  beyond scope.

## Abort conditions

Stop, report, and wait. Do not work around any of these.

- The base does not hold T6b's code, D121 and D123 (V1), or D123 does not reach this T7 (V3).
- M1, M2 or M6 is not ruled when V9 is reached.
- The membership source's licence is not stated at source (`SPEC.md:90`).
- A study cell in the box reads "pending" at fit time (V4).
- D26's zip or T6's stored surface no longer matches its filed sha256.
- A count falls under a minimum fixed before it was read (V9).
- Memory over the 5 GB cap on the trial window, or the laptop's other jobs need the processor
  (yield; do not fight for it).
- Any record above 250 m found in the training table.
- A leakage test fails.
- The work would need a rule changed, a layer added beyond D121, a new download other than the
  ruled membership list, or a T6b tile rewritten.
- Two failed attempts on the same failure: stop guessing and report the data.

## Do not touch

- No GBIF request (the matching API included), no Copernicus or Open-Meteo request, no secret (D36).
- No edit to a filed record (D41); no edit to another branch's DECISIONS rows; no merge (D40).
- Nothing on the pilot's branches or the zynergy-site repo. T7's output is not put on the live map
  or any other public page (M8).
- T6b's tiles, manifest, runner and run are read-only. Do not start, pause or stop a T6b section.
- Nothing in the Forager app repo. No forbidden term (D58), no "probability" or "chance" outside
  D12's defined term, and no edibility wording.
- No product named in any file or message (V15).

## What follows, one line each

- **T8** (trigger and joint challenger) and **T9** (calibration and gate) were written for the
  chanterelle sighting chance; where they get a habitat input from now depends on M5.
- **T10** (nightly job) and **T11** (vector companion and map client) are unchanged by this
  dispatch.
- **The continental habitat fit** follows the pilot (D100, D123), on the layers the T6b restart
  completes.

## Earlier decisions: carried, changed or dropped

These were answered in RECORD -832 for the chanterelle plan (A1 to A5), or open there (O4, O7).

- **A1 (was O1), the two D122 rows: no longer applies.** Settled on main: D122 is the SCANFI edge
  ruling and D123 the pilot ruling (`DECISIONS.md:9-10`); RECORD -1021: "No renumbering".
- **A2 (was O2), the box: carries over unchanged.** "Test map's box, after the 8 tiles
  (Recommended)" (RECORD -832). Its reasons are about layer completeness, the weather box and the
  number of ecoregions, none about which mushrooms; its condition is now met (V4 re-checks).
- **A3 (was O3), the groups: needs re-asking.** "Chanterelles and chicken of the woods
  (Recommended)" (RECORD -832) answered a question about chanterelles; the target is now the
  mycorrhizal group. Whether chicken of the woods stays as the control is M4, and where chanterelles
  go is M5.
- **A4 (was O5), NALCMS: carries over unchanged.** "A mask only (Recommended)" (RECORD -832). How
  water and land are masked does not depend on the target.
- **A5 (was O6), D18 for the T6b layers: carries over, now fulfilled.** "Review now, alongside
  (Recommended)" (RECORD -832). The review is filed on main with no blocking finding (deviation 6
  above). It reviewed the layers, which are the same whatever the target.
- **O4, the ecoregion level: decided, D125.** The owner, verbatim (RECORD -1023), after the planner's
  explanation of level III (about 25 regions in the PNW box) against level I (about 5) and the
  recommendation "Level III, with a Level I summary alongside it": "Yes to all". What -1023 sets:
  "Level III ecoregions are the validation blocks; the minimum presences per block is fixed before
  any count is read; blocks under it are marked uninformative and kept in the pooled figure; a Level
  I summary is reported beside. T9's publishing level is not decided by this."
- **O7, the base branch: decided, D126.** RECORD -1023: "O7 (base branch) is answered by the merge in
  -1021: forecast main a79d667 holds T6b's code, D121 and the pilot ruling D123." The merge order the
  old dispatch recommended is moot.

## Open decisions for the owner

Each needs a word before T7 starts. Written plainly; the recommendation is the planner's to relay.

- **M1. Which mushrooms count as "mycorrhizal", and where the list comes from.** Mycorrhizal
  mushrooms partner with tree roots. The map needs a fixed list of which kinds count. Options:
  (a) **a published fungal-traits list that labels each genus by how it lives**, keeping the
  mushroom-forming genera labelled as partnering with tree roots; a fixed, dated copy is kept with a
  fingerprint (sha256), and the list changes only by a new decision row. (b) A hand list of
  well-known forager genera (chanterelles, boletes, milk caps, russulas, hedgehogs and the like).
  (c) Whole families instead of genera. **Recommended: (a)**, with the source opened and its licence
  read before it is used (V17). It is the only option that someone outside the project can check and
  repeat, which matters for foresters and ecologists; (b) is shorter but is our own judgement and
  would leave out many genera the map claims to cover; (c) sweeps in families that mix lifestyles.
  Note: a full list includes deadly genera. The map shows habitat only, never edibility.
- **M2. What to do with mushrooms whose lifestyle is uncertain or mixed, and with records named only
  to family.** Some genera are not clearly root partners (morels are one example often given; from
  memory, unverified), and some records stop at family. Options: (a) **leave them out of the main
  map and run the model once more with them in, reported beside**; (b) put them in; (c) rule each one
  by hand. **Recommended: (a)**. The main map then rests only on clear cases, and the side run shows
  whether the unclear ones change anything, so nobody has to guess.
- **M3. How the different mushrooms are weighed, which decides what the map means.** Options:
  (a) every record counts once; the map then leans toward the kinds people photograph most, so it
  says "where mycorrhizal mushrooms get reported". (b) **Each genus counts equally**, with genera
  below a minimum number of records (fixed before counting) reported but not weighted on their own;
  the map then says "where conditions suit many kinds of mycorrhizal mushrooms". (c) A separate model
  for each genus, combined afterwards; the clearest meaning, but many times the work and too few
  records for most genera in one box. **Recommended: (b)**, because it matches "mycorrhizal mushrooms
  as a group" (RECORD -913) and keeps one popular genus from defining the map.
- **M4. Whether to keep a comparison group (re-asking A3).** Chicken of the woods rots wood rather
  than partnering with roots. Options: (a) **keep chicken of the woods as the comparison**: if its
  habitat map looks the same as the mycorrhizal one, the model is mostly learning "where the forest
  is", which is worth knowing; (b) use all wood-rotting mushrooms as the comparison; (c) no
  comparison. **Recommended: (a)**. It is already counted and named in earlier rulings (D109), and it
  costs one more fit.
- **M5. Where chanterelles go.** The old T7 fed a chanterelle habitat layer into the weekly sighting
  chance (T8, T9). Options: (a) **this T7 fits the mycorrhizal group (and the comparison) only; the
  same code fits chanterelles alone when T8 and T9 are dispatched**; (b) fit chanterelles in the same
  run now; (c) drop chanterelles from the weekly forecast plan. **Recommended: (a)**. It keeps this
  task to what the owner asked for "for now", and nothing waits on a chanterelle habitat layer until
  T8 is written. (c) is a larger scope question than this dispatch should raise on its own.
- **M6. Recording the change of target.** The spec still names chanterelles and chicken of the woods
  as the phase 1 groups (`SPEC.md:13-14`), T7 says "both groups" (`TASKS.md:83`), and "forager group"
  is fixed to mean one genus (`START_HERE.md:43`). Options: (a) **file a decision row recording
  RECORD -913's scope (a habitat map for the mycorrhizal group) and a new fixed term, "mycorrhizal
  group", kept separate from "forager group"**, then bring SPEC and TASKS in line by appended notes;
  (b) treat it as a pilot-only deviation and leave the spec as it is. **Recommended: (a)**. The spec
  is what every later task reads; leaving it saying chanterelles would mislead the next one.
- **M7. Host trees the layers do not have.** The tree layers name Douglas-fir, hemlock, spruce, fir,
  pine and oak, chosen for chanterelles; other mycorrhizal hosts (birch, aspen, larch among them)
  count only inside the general conifer and broadleaf totals. Options: (a) **use the layers as they
  are, say plainly in the report what is missing, and add host genera later only if a model with them
  beats one without (D121)**; (b) add host genera to the T6b layers before fitting (a T6b rerun and a
  delay). **Recommended: (a)**. It keeps the pilot on finished, reviewed layers; the comparison in
  (a) is how D121 says new layers earn a place.
- **M8. Whether, and on what test, the habitat map is ever shown.** The weekly forecast may be shown
  only after it beats a seasonal calendar (D5). A habitat map has no calendar to beat. Options:
  (a) **nothing from this task is shown; the coder proposes a pass bar (P10), fixed before the fit,
  and the owner decides later whether it was met**; (b) show it labelled experimental once fitted;
  (c) show it only alongside the weekly forecast after T9. **Recommended: (a)**. It holds the map to
  the same standard as the forecast ("Trust is in operability, not promises", D60) without deciding
  today whether foresters see it.

## What changed from the chanterelle plan

- **Target:** chanterelles with chicken of the woods as control, to the mycorrhizal group (RECORD
  -913), with the control and chanterelles' place re-asked (M4, M5) and the group's definition new
  (M1 to M3).
- **New premises:** V15 (prior art, RECORD -914), V16 (genus names to keys offline), V17 (the
  membership source at source).
- **New proposals:** P10 (a pass bar); P7 gains two comparison models, effort only and host-tree
  totals only.
- **Decided since:** O4 (D125) and O7 (D126); A1 no longer applies; A5 fulfilled by the filed review;
  the 8 Canadian tiles have landed and the seam has been re-run on all 25 transects.
- **New stops:** M1, M2 and M6 before V9; a membership source without a stated licence.

**Citations re-checked against main `a79d667`**, corrected where stale (the old file is unchanged):

1. TASKS.md T7: cited as `origin/d121-lean-start:docs/planning/TASKS.md:80-85`; now on main at the
   same lines, `docs/planning/TASKS.md:80-85`.
2. D121: cited as `DECISIONS.md:8` at `aec605d`; on main it is `DECISIONS.md:11`.
3. D18: cited as `DECISIONS.md:103`; on main `:106`.
4. Host bands: cited as `crown_cover.py:156-157` on `t6b-continental-layers` (correct at `cfbf50d`);
   on main `src/forager_forecast/crown_cover.py:155-156`.
5. NALCMS path: cited as `t6b_run.py:72` (correct at `cfbf50d`); on main `scripts/t6b_run.py:73`.
6. LightGBM pin: cited as `START_HERE.md:75`; the pin is `pyproject.toml:17`, and the session-log row
   that records it is `START_HERE.md:82`.
7. `filters.py` `r6_audit_steps()`: cited `:176-180`; the function's step list runs `:176-182`
   (holds, widened to the full list).
8. The PNW render: "built 2026-10-09 05:39 PDT, before Canada"; rebuilt 2026-10-10 15:18 local after
   the 10 Canadian tiles (drive listing; `seam-after-10-tiles/mosaic-and-seam.out.txt`).
9. The 8 Canadian tiles: "pending"; landed (review `:55-62`, drive listing).
10. The 49 N seam: "no verdict while Canada was pending"; re-run on all 25 transects, total cover an
    artifact, the three shares no step (`seam-after-10-tiles/`).
11. D18 for T6b: "no independent review found"; filed,
    `docs/audits/2026-10-11-t6b-pnw-layers-review.md`.
12. Base: "no single branch held all three"; main `a79d667` holds them (V1).
13. Tree tiles: "2,015 tiles plus flags"; 2,025 now (drive listing).
14. Drive free space: 15 GB on 2026-10-10; 6.0 GB on 2026-10-15. RAM available: 7 GB in the verify
    report; 5 GB at writing.
15. Held as cited: `pnw.py:30`, `t6b_layers.py:97`, `t1_design.py:35`, `effort.py:633` and
    `:618-624`, `filters.py:42`, `scripts/pnw_checks.py:38`, `SPEC.md:15`, `:20`, `:61`, `:72`, `:78`,
    `EVIDENCE.md:55-56`, `RESEARCH_LOG.md:56`, the verify report's `:189`, `:191`, `:231-233`, `:236`,
    `:267-268` (file unchanged since `dd28648`), `2026-10-10-t6b-scanfi-edge-and-pace.md:78-80`, the
    T2 report's `:206` and `:232`.

**Not done, for the planner:** D41 says "a dispatch closed without being acted on carries a dated
closeout note appended inside it". The old T7 file was left unchanged as instructed, so it carries no
such note; this file's first line and its index row say it is superseded. Whether to append the note
is the planner's call.
