# Review: T6b's soil and host-tree layers for the PNW box (40 to 49 N, 111 to 125 W), under the standing protocol (D18)

- **Reviewed:** `origin/t6b-continental-layers` at `cfbf50d` (t6b-scanfi-edge merged per Forager
  RECORD -828), plus the runner change the night run actually uses, `origin/t6b-pnw-scanfi` at
  `4ac4cab` (`--tiles`, not merged into t6b-continental-layers at the time of writing).
- **Commissioned by:** Forager RECORD -832 ("Review now, alongside (Recommended)").
- **Rulings read:** D74, D80, D81, D84 to D92, D111 to D120, D122
  (`docs/planning/DECISIONS.md:8-47` at `cfbf50d`). D121 is not on this branch.
- **Data:** read in place on the flash drive,
  `/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b/`. Nothing was
  written to the drive. Reviewer scripts and outputs are in `2026-10-11-t6b-pnw-layers-review/`;
  the scripts are byte-identical to what ran, saved as `.py.txt`; to re-run one, copy it to `.py`
  beside `recompute.py` (two of them import it) and run from the repository root.
- **Reviewer:** a Claude session separate from every T6b builder. Worktree
  `~/Zynergy/forager-forecast-t6b-pnw-review`, branch `t6b-pnw-review`, own `.venv`. I did not
  touch the running `t6b-night` unit, its checkout `~/Zynergy/forager-forecast-scanfi-edge`, or
  any other worktree. CPU: reviewer jobs ran at nice 19 on small windows only.
- **Conventions:** "read" = opened in this session; "observed" = command output in this session;
  "inferred" is marked. Line cites are to `cfbf50d` unless they name another commit.

## Pass 0: pre-registration (committed before any manifest line or tile value was read)

**Box tile list, from the mask only** (`box_tiles.py`, `box_tiles.json`). Study and side rules are
restated in the script from D113, D115 item 1 and D117, not imported. Observed: 296 tree tiles
hold box study cells (273 US only, 20 with both sides, 3 Canada only); 8 soil tiles;
16,571,590 US and 102,543 Canadian study cells in the box. The total, 16,674,133, equals the
figure in `2026-10-09-pnw-monday-completion-report.md` section 5, and the 102,543 equals section
12's, so the two counts agree from independent code. The 8 tree tiles holding Canadian box cells
are exactly the 8 named on the night run's `--tiles` (observed from `ps`, 2026-10-10 20:20 UTC).

**Samples, seed 20261011** (`prereg.py`, `prereg.json`), drawn from the mask alone:
- Hash sample: 6 of the 273 US-only tree tiles, 4 of the 20 US-half tiles, 3 of the 8 soil
  tiles, and every file of the 8 Canadian tiles once they land.
- Spot cells: 3 soil cells, 3 US tree cells and 2 Canadian tree cells, drawn at random from box
  study cells; plus one cell fixed by hand at 47.705 N, 116.79 W (Coeur d'Alene Lake's north
  shore, a guess at a shore cell; whether it is one is read from NALCMS during the recompute).
- Tolerances, fixed now: soil mean and quantiles 0.01 pH, valid fractions 0.005; trees as D115
  item 4 (cover 0.1 points, shares 0.001, valid fraction 0.001, source and flags exact). My
  recompute uses exact polygon clipping, not a point sampler, so the fraction tolerance is tighter
  than the ten-cell rule's 0.02 for soil.
- Manifest checks (no hashing): every box tile has a latest unit line with status ok that names
  files; no failed or deferred line is the latest line of a unit counted done; every file named
  exists.

## Verdict after passes 1 to 4 (2026-10-10, about 20:50 UTC; the 8 Canadian tiles not yet landed)

**Holds for the US side of the box, with no blocking finding.** The code does what D74, D80, D81,
D84 to D92, D111 to D120 and D122 say, as far as the box exercises them. The manifest's claims
for every box tile hold. Ten cells recomputed independently from the source rasters agree with
the stored tiles to float32 rounding (largest difference 1.3e-5 points of cover). Three
should-fix findings and six notes follow. The Canadian 102,543 cells are not reviewed yet (pass
5): at the time of writing the night run had done 26 of its 88 SCANFI layer units and was
paused by its PAUSE file at 13:22:57 -07:00 (manifest's last section line).

## Update after pass 5 (2026-10-10, about 22:20 UTC): the Canadian tiles

The night run resumed at 13:57 -07:00 with **10** tiles: the 8, plus 256_-27_20 and 256_-28_20, which
the planner added after S1 (observed in the run's `--tiles`). It finished at 15:08:41 -07:00 with
every unit done: scanfi-layers 84 ok in this start (110 in all) and trees 10 ok, 0 deferred, 0
failed. The evidence commit is `04f0302` on `origin/t6b-pnw-scanfi`. **The verdict holds for the
Canadian cells too.** S1's remedy (a) is now in place for the data, but the seam check has not been
re-run: the PNW mosaic on the drive is still the 05:39 -07:00 build. S2 and S3 stand.


### Blocking

None.

### Should-fix

**S1. After tonight's 8 tiles, the 49 N seam check can run on 6 of its 25 transects, not 25.**
(`seam.py:43-70`, `scripts/pnw_checks.py:558-575`; reviewer `seam_tiles.out.txt`.)
- Observed: the north samples of transects 0 to 18 (121.00 to 122.23 W) fall in tree tiles
  256_-27_20 and 256_-28_20; those of transects 19 to 24 (122.30 to 122.64 W) in 256_-29_20.
- 256_-27_20 and 256_-28_20 are US-half tiles whose Canadian cells all lie north of 49 N, so
  outside the box, so not among the 8 tiles of `--tiles` (their box Canadian count is 0 in
  `box_tiles.json`). After tonight they are still pending.
- So a re-run of the seam check after tonight gets a border step on at most transects 19 to 24,
  which run through the Fraser Valley farmland around Abbotsford and Langley (inferred from the
  coordinates, not read from a map layer). T5's verdict rule (`seam.py` docstring, D90) was fixed
  for 25 transects; a median over 6 is a different and much weaker check.
- What it means for T7: the box's own Canadian cells are on southern Vancouver Island and the
  Gulf Islands (inferred: Canadian cells in the box exist only west of 122.80 W, where the
  polygon decides, `t6b_mask.py:214-221`). No land seam joins them to US cells, so no seam check
  as written can ever test them against the US side. The cross-border consistency of the cells T7
  will use is unchecked by design, not just pending.
- Options (for the planner, not chosen here): run the 2 more tiles 256_-27_20 and 256_-28_20
  (22 SCANFI units, about 7 minutes at the measured pace) so the seam runs as written; or accept
  a 6-transect seam labelled as such; or record that the box's Canadian cells have no seam check.

**S2. A tree tile's Canadian values are taken from the SCANFI layer files on their existence, not
on the manifest.** (`scripts/t6b_run.py:218-220` in `tree_unit` and `:304-307`, `layers_ready`.)
- The trees stage offers a Canadian tile once all eleven `scanfi_<layer>_<tile>.npz` files exist,
  and `tree_unit` reads them. It does not check that each has an ok manifest line or that its
  hash matches; the tree tile's own manifest line names neither the eleven files nor their hashes
  (`fill_canadian_cells`, `t6b_layers.py:832-842`, records only the US-half file's hash).
- That a file without a line exists is not hypothetical: `2026-10-10-t6b-scanfi-edge-and-pace.md`
  ("Found along the way") records `scanfi_balsamFir_256_38_33.npz` on the drive with no manifest
  line. Its values are whole (written as `.partial` and renamed, `t6b_layers.py:600-606`), so
  this is a provenance gap, not a wrong value.
- Fix (small): `layers_ready` asks `done_units` for the eleven units, and the tree tile's line
  records the eleven npz hashes, as D119 already does for the US-half file.

**S3. The edge check cannot be re-run as written once the 8 tiles land.**
(`scripts/pnw_checks.py:121-180`.)
- For a window holding Canadian cells it recomputes with `tree_tile_us_half` (pending Canadian
  cells), but `_stored` (`:87-105`) now finds the whole file first. Five of the 17 border corners
  touch the 8 tiles ((-7936, 5120), (-7680, 4864), (-7680, 5120), (-7680, 5376), (-7424, 5120),
  from `check-rules.md`), so a re-run would report differences that are the check's, not the
  data's.
- And no edge check has yet compared Canadian cells across a tile edge. The layer route's tiling
  invariance is tested on synthetic data (`tests/test_t6b_layers.py:381`), not on the drive.

### Notes

- **N1. The tiles' `rulings` tag stops at D115.** `t6b_layers.py:89-90`; every soil and tree
  tile written since D116 carries a `rulings` list without D116, D117, D119, D120 or D122, which
  do apply to them. The D120 report chose this so no finished tile's tags differ
  (`2026-10-09-pnw-monday-completion-report.md`, section 12). Provenance only; values unchanged.
- **N2. Unit lines of the scanfi-layers stage carry the SCANFI layer's name in `layer`, not
  `scanfi-layers`.** `t6b_run.py:231-236` writes `"layer": layer` then `**result`, and
  `scanfi_layer_tile` returns its own `layer` (`t6b_layers.py:607`). Observed: 717 lines read
  `"layer": "balsamFir"`. Nothing reads it for done-ness (`done_units` keys on `unit`).
- **N3. A filtered section's `units_done_before` counts the whole manifest, not its own units.**
  `t6b_run.py:209` and `:306`. Observed in tonight's section line: `units_total` 88,
  `units_done_before` 709 (the continental balsamFir units). The commit message built from it
  (`scripts/t6b_run.py:386-391`) reads correctly; the JSON field misleads.
- **N4. NALCMS is looked up with NAD83 coordinates labelled EPSG:4326.** `t6b_layers.py:358`.
  NALCMS is on WGS 84 (its CRS, read). The difference is at most about a metre or two against
  30 m pixels (inferred, not measured); my recompute used pyproj's own NAD83 to WGS 84 step and
  got the same water pixel counts on the shore cell below.
- **N5. A whole SCANFI layer already on the drive is reused without its hash being checked.**
  `scripts/t6b_run.py:256-258`. Checked here for douglasFir.tif only: its sha256 equals its
  request record's (`5b09622f...`).
- **N6. The D122 `failed` path has never fired on real data.** The manifest holds 0 failed and
  0 deferred unit lines (`manifest_check.out.json`). The edge tile that raised on 2026-10-10 left
  no line (the old code ended the run). The path is covered by tests
  (`tests/test_t6b_run.py:204`), not by the run.

## Pass 1: each layer against its decisions

Read at `cfbf50d`, and `4ac4cab` for the runner's `--tiles`.

| Ruling | What the row says | Where the code does it | Holds |
|---|---|---|---|
| D80 | pH 0 to 30 cm, weights 5, 10, 15 over 30 | `soilgrids.py:37`, `:71-78` (no data at any depth is no data); `t6b_layers.py:212` blends native pixels, then regrids | Yes; recomputed (pass 4) |
| D81 | Q0.05 and Q0.95 blended the same way, labelled approximate; display carries the mean only | `t6b_layers.py:212` (all three statistics), band notes `:237-240`, `t4_layer.py:92-97`; PNW display reads `ph_mean_0_30cm` only (`scripts/pnw_build.py:86`) | Yes |
| D74 | a value only where at least half the cell is valid; fraction kept | soil `t6b_layers.py:224-225`; trees `:661-668`; `MIN_VALID_FRACTION` 0.5 (`t4_layer.py:82`) | Yes |
| D84 | TreeMap 2023 CONUS; cited in every derived raster | read at `scripts/t6b_run.py:230`; citation in tags `t6b_layers.py:688-699` | Yes |
| D85, D89 (1) | Canada: genera SCANFI cannot supply flagged not available | `t5_layer.py:105-110`; `t6b_layers.py:675-682` (Pseudotsuga, conifer, broadleaf from SCANFI; Tsuga, Picea, Abies, Pinus, Quercus flag 3) | Yes (code); Canadian data in pass 5 |
| D86, D113 | Alaska, Hawaii, Puerto Rico, USVI and Mexico masked | `t6b_mask.py:92-108` (country codes 3 and 4 never in study, `:224-230`); pixels there blank (`t6b_layers.py:348`) | Yes |
| D87, D88 | US total = CANOPYPCT; genus = CANOPYPCT x tree-list share | `t6b_layers.py:410-428` | Yes; recomputed |
| D89 (2), D91, D116 | surrogate coefficients; d.b.h. capped at the fitted maximum; unlisted genera by FIA code, never hosts | `crown_cover.py:170-201`, `:230-262` | Yes; recomputed with my own implementation |
| D89 (3) | a share only where total cover is at least 10% | `t6b_layers.py:664`, `t5_layer.py:48` | Yes; recomputed |
| D90 | the transect null (seam) | `seam.py` docstring; PNW use in S1 above | Not exercised (no border step yet) |
| D92 | Canada's total = SCANFI's own closure; shares from the ten classes over their sum | `t6b_layers.py:627-630` (layer route), `:501-506` (window route), shares `:676` | Yes (code); data in pass 5 |
| D111, D117 | Arctic ecoregions out; a centre in no ecoregion polygon out | `t6b_mask.py:111-127`, `:224-230` | Yes; my restated rule gives the same study counts on all 293 box tiles (pass 2) |
| D112 | water and NALCMS-unmapped are no data, not no crown; soil unchanged | `t6b_layers.py:355-367`, blank `:412`, `:494`, `:595`; 127 (the file's declared no-data, read) is treated as unmapped too | Yes; a shore cell recomputed (pass 4) |
| D113 | CEC political lines, cell centre | `t6b_mask.py:92-108`, `_burn` (`:130`) by centre | Yes |
| D114 | sections, stop time, PAUSE | `t6b_run.py:109-114`, `:265-288` | Yes; tonight's section stopped on PAUSE (manifest) |
| D115 item 1 | 49 N inside the band 122.80 to 95.15 W, 48 to 50 N; polygon elsewhere; pixels by their own centre | `t6b_mask.py:214-221`; pixels `t6b_layers.py:330-352` | Yes |
| D115 item 5 | positions from the full raster's origin | `regrid.py:104-126`; used at `t6b_layers.py:215`, `:597` | Yes (tested on synthetic tiles, and by the pnw-monday edge check on the US side) |
| D118 | SCANFI whole, one layer at a time, free space checked, deleted after | `scripts/t6b_run.py:245-301`; `--tiles` keeps the layers (`4ac4cab`, `scripts/t6b_run.py:311` there) | Yes, with N5; the `--tiles` change was asked for by RECORD -828 |
| D119 | US half now, Canadian cells pending, filled later without touching the US cells | `t6b_layers.py:750-842`; runner `scripts/t6b_run.py:193-235`, `:337-356` | Code yes; the "unchanged" claim is checked on real files in pass 5 |
| D120 | a no-country pixel outside TreeMap is no data; a US pixel outside is still refused | `t6b_layers.py:396-401` | Yes |
| D122 | past the SCANFI edge is no data; count recorded; a unit's error fails that unit | `t6b_layers.py:535-611`; `t6b_run.py:147-183` | Yes; none of the 8 PNW tiles reaches the edge (edge audit section 4) |

## Pass 2: the manifest against the files

`manifest_check.py.txt`, `manifest_check.out.json`, `manifest_counts.py.txt`,
`manifest_counts.out.json`. The manifest was read once at 2026-10-10 about 20:25 UTC (1,718,736
bytes, sha256 `17757f3a...`, 2,964 lines, 2,931 unit lines).

- **Every box tile listed.** All 273 US-only tree tiles have a latest `trees` line, status ok,
  naming two files that exist; all 20 mixed tiles a latest `us-half:` line, ok, with files; all 8
  soil tiles an ok line with a file. 0 problems. The 3 Canada-only tiles have no line, as
  expected before tonight.
- **Counts.** The manifest's per-tile study counts (US, and Canadian pending for US halves) equal
  my mask counts on all 293 tiles that have a line: 0 mismatches. This could have failed: it
  compares the pipeline's side rule with mine, restated.
- **Hashes, the pre-registered sample (seed 20261011).** 23 of 23 files match their manifest
  sha256: 12 files of the 6 US-only tiles, 8 of the 4 US-half tiles, 3 soil tiles.
- **No unit with an error counted done.** Status counts over all 2,931 unit lines: every line is
  ok (balsamFir 717, blackSpruce 8, broadleaf 8, douglasFir 2, soil 89, trees 2,015,
  trees-us-half 92). 0 failed, 0 deferred, 0 ok lines without files in the box. So the check that
  an error is never counted done had no error to catch (N6); what it does show is that `done_units`
  (`t6b_run.py:61-73`) requires status ok and a hash match, read.

## Pass 3: the pnw-monday checks

| Check | What it compared, on what sample | Could it fail | After D120 | After tonight |
|---|---|---|---|---|
| Tree tile edges | 32 windows of 64 x 64 cells at fixed corners (`check-rules.md` section 1); stored tiles against a recompute by the same pipeline code. 29 computed, 117,760 cells after D120 | Yes, but only for tiling dependence: it shares every input and every line of code with the run, so it tests D115 item 5, not correctness. The window-relative regrid it guards against was shown to differ in the last bits (T6b verify report, section 3) | Re-run after D120: 29 of 32 exact (report section 12). Holds | US cells: holds, provided the fill copies them unchanged (checked in pass 5). Canadian cells: never compared, and the check cannot be re-run as written (S3) |
| Soil tile edges | 11 windows, 10 computed, 40,960 cells, fresh SoilGrids fetches | Yes, same scope as above | Soil untouched by D120. Holds | Untouched. Holds |
| Ten fixed cells | 2 of 10 in the box, both US: coast-oregon (256_-33_12) and border-us-selkirks (256_-23_19, a US half). Independent recompute | Yes; it had a negative control (`tests/test_pnw_checks.py`) | Neither is a D120 tile. Holds | Neither tile is among the 8. Holds, and still says nothing about Canada |
| 49 N seam | T5's 25 transects on the PNW mosaic | Could not give a verdict: the Canadian side was pending | Still no verdict | At most 6 of 25 transects (S1) |

## Pass 4: independent recompute (US side and soil)

`recompute.py.txt` and its outputs; `supplement_us.py.txt`; `soil_remote.py.txt`. My code imports
from the pipeline only the published tables in `crown_cover.py` (Bechtold 2004 coefficients,
counts and fitted maxima; T5's genus lists and class defaults). Shared inputs I did not
re-derive: `mask.tif` (the CEC polygons burned by the pipeline).

**Soil, 3 pre-registered cells** (`recompute_soil.out.json`): mean, Q0.05 and Q0.95 agree to
within 5e-7 pH and the valid fractions to within 3e-6 (one cell is 0.827 valid, so the no-data
path is exercised), against tolerances of 0.01 and 0.005.

**Soil, back to ISRIC** (`soil_remote.out.json`): the 27 stored native windows behind the 3 cells
(9 layers each) hash to their request records, and each of the cells' 108 native pixels, read
again from ISRIC's own VRTs over the network (`files.isric.org/soilgrids/latest/data/phh2o/`),
equals the stored pixel. So the soil chain is checked from the producer's file to the tile.

**Host trees, 4 pre-registered US cells** (`recompute_us.out.json`): all agree. But the sample was
weak: 3 of the 4 have 0% cover (sagebrush steppe and, for the hand-picked "shore" cell, NALCMS
class 17, urban: my guess missed the lake), so only one cell (256_-32_9, 58.68% cover, all eight
shares) tested the shares, and none tested water.

**Supplementary sample** (`supplement_us.out.json`), rule written after seeing that weakness and
before any of these cells' tile values was read (seed 20261012, stated in the script's
docstring): one cell whose screening points mix NALCMS water and land, two cells on forest
plots. 240 draws.
- Water cell, 48.639 N, 115.285 W (256_-21_18): 11 of 89 TreeMap pixels on NALCMS water. Valid
  fraction 0.93859 against stored 0.93859 (difference 2.3e-7); cover 31.4542 (4.7e-6); shares
  within 1e-7.
- 48.692 N, 120.333 W, in US-half tile 256_-27_19 (so D119 on real data): cover 28.2752, all
  shares within 4e-7.
- 43.027 N, 121.447 W: cover 28.8249, Pinus share 1.0, within 2e-7.
- Flags: source 1 and every flag 1 where a share is defined; 0 where cover is 0. As D89 (3).

**Largest difference over all 10 cells:** 1.3e-5 points of cover (256_-32_9), against 0.1.

## Pass 5: the 10 Canadian tiles

`canadian_tiles.py.txt` and `canadian_tiles.out.json` (all 10 tiles, no sampling);
`recompute_ca.py.txt` and `recompute_ca.out.json`. The manifest was read after the section's last
line (3,025 unit lines; 0 failed and 0 deferred anywhere).

- **Lines and hashes.** All 10 tiles have a latest `trees` line, status ok. Their 20 files hash to
  it. All 110 SCANFI layer units (11 by 10) have an ok line, and their 110 npz files hash to it.
  None records `past_scanfi_edge_pixels`, as the edge audit predicted.
- **Counts.** Each line's Canadian study count equals my mask count (`box_tiles.json`
  `tile_study_ca`), for example 18,981 for 256_-29_20, 59,441 for 256_-27_20 and 41,773 for
  256_-28_20.
- **D119's "unchanged", on real files.** These are the 7 tiles with a US half: the 5 of the 8, plus
  256_-27_20 and 256_-28_20.
  - Each US-half file still hashes to its own manifest line.
  - Each whole file's `us_cells_from` tag names that hash.
  - Every non-pending cell of the whole file equals the US-half file on all 11 value bands and 8
    flag bands: 0 cells differ.
  - No pending value (4) is left in any whole file's source band or flag band.
  - So the pnw-monday edge and ten-cell results on US cells carry over unchanged to these tiles.
- **Independent recompute, 2 pre-registered Canadian cells.** They come from the whole SCANFI files:
  att_closure for the total, and the ten classes for the shares (D92).
  - 48.816 N, 124.224 W (256_-31_20): cover 58.1041 against stored 58.1041 (difference 8.8e-6).
    Douglas-fir 0.39524, conifer 0.61905, broadleaf 0.38095, each within 4e-7.
  - 48.959 N, 123.860 W (256_-30_20): cover 47.8701 (1.5e-6). Douglas-fir 0.64523, within 1e-7.
  - Flags on both: 2 for Pseudotsuga, conifer and broadleaf; 3 (not available, D85, D89 (1)) for
    Tsuga, Picea, Abies, Pinus and Quercus; source 2.
  - Neither cell touches water or the SCANFI edge. A Canadian shore cell was not sampled, so D112
    on the SCANFI side is covered by the code read and the synthetic test
    (`tests/test_t6b_layers.py:292`), not by a real cell.
- **Not checked:** the att_closure whole file's hash against its request (4.2 GB; skipped to keep
  the drive and processor free). The values recomputed from it agree with the tiles, which shows
  the tiles were built from this file, not that the file is SCANFI's.

## What this review could not check

- **The 49 N seam after tonight.** It needs the PNW mosaic rebuilt (`scripts/pnw_build.py
  mosaic`, which writes to the drive), so it was not run here. Once it is rebuilt, the 25
  transects can all get a border step (S1, remedy (a)).
- **Canadian cells across a tile edge** (S3).
- **The mask's polygons.** `mask.tif` was taken as given: my study and side rules are restated, but
  the CEC polygons were not re-burned.
- **Soil and US cells beyond the 13 recomputed,** and tiles outside the hash sample (beyond the 10
  Canadian tiles, all checked).
- **The test suite** was not run, to keep the processor free for the model fit.
- **Old manifest lines.** 37 unit lines carry no `status` key. `done_units` reads them as ok
  (`t6b_run.py:65`). All 37 are soil lines, inferred to predate the field. Two are box soil tiles,
  2048_-4_2 and 2048_-3_2, and both were in the hash sample and matched (pass 2). Observed.
