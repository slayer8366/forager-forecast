# T7 build report: the missing code for the PNW mycorrhizal habitat map, up to the point of no return

Written 2026-10-16 (UTC; evening of 2026-10-15 Pacific) by the T7 build coder for the Forager planner
(Rowan Waymark), on the owner's go (Forager RECORD -1071; the owner, verbatim: "Let's go ahead and
begin building from it in anticipation of approval. The worst case is they say no and we have to
rebuild anyway. At least for now we can make progress so time isn't wasted.").

- **Base.** Branch `t7-build` at `169cd63` (forecast main `b9127e5` plus the merged `t7-proposals`
  `066f91f`). Not merged anywhere (D40).
- **Read.** The T7 plan (`docs/dispatch/2026-10-15-t7-mycorrhizal-habitat.md`), the proposals
  (`docs/audits/2026-10-15-t7-proposals.md`), the T7 verify report, the T6b host-genera review,
  START_HERE, the DECISIONS rows named in the dispatch, Forager's CLAUDE.md, and Forager RECORD
  -1030, -1036, -1049 to -1054, -1061, -1062, -1070, -1071 (read-only, `records-after-173` at
  `56fe3b2a`). **Not read:** the alternatives scoping the planner cited
  (`prompts/preserved/2026-10-15-11-membership-list-alternatives.md`); its requirement reached me
  as the planner's message and is built as worded there.
- **Flags.** OBSERVED = a command here produced it, output committed or quoted; READ = a file or
  page says so; INFERRED; COULD NOT DETERMINE.
- **Hold kept.** No presence or observation record of any group was read, counted, tabulated or
  plotted. From the D26 download only the header line of `occurrence.txt` was read (committed as
  `tests/fixtures/d26_occurrence_header.tsv`; 230 column names). No GBIF, climate or Open-Meteo
  request. No fit on real data. Nothing written on the flash drive. Every test and run under
  `nice -n 10` and `systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0`.

## Commits (all pushed to `origin/t7-build`)

| Commit | What |
|---|---|
| `bcd9cca` | Tests first: 53 tests against stubs, all failing with the stubs' `NotImplementedError` |
| `ee4b94b` | The code: the 13 items, the normalised membership list and the FungalTraits adapter; scipy pinned; tuning grid committed |
| `934f697` | Revert checks (38 of 38 bite) and four strengthened tests |
| `dd55720` | DECISIONS D133 to D142; the normalised list's sha256 recorded |
| this commit | This report and its index row |

## What was built (`src/forager_forecast/t7/`)

Proposals' "New code T7 needs", item by item:

1. **250 m cell to weather cell** (`keying.weather_cells`, `weather_cells_for_window`): the cell
   centre through `t6b_mask.cell_lonlat`, then `cells.cell_for`'s rule, vectorised; any value
   within 1e-6 of a half-way point is decided by `cell_for` itself on its decimal text.
2. **Level III code per cell** (`ecoregions.read_level3`, `burn_level3`): codes 1 to n over the
   file's LEVEL3 identifiers in string order, burned by cell centre as the mask's `_burn` does,
   uint16; the dbf read as UTF-8.
3. **Static effort per weather cell** (`keying.static_effort`): `EffortSurface.effort` summed over
   the 573 frame weeks; a cell outside the frame is listed as refused, never given a value.
4. **Genus and family names** (`names.load_named`): `genus`, `family`, `order`, `taxonRank` beside
   each Record; each row goes through the existing `OccurrenceLoader`, so unloadable rows are
   counted by its reasons. A new path; the loader is unchanged.
5. **The membership join** (`membership.Join`), on the list this project owns (below), its sha256
   checked at load and its fingerprint checked at the join. Main and side runs per M2 (a).
   Comparison group (M4 (a)) by genus name `Laetiporus`.
6. **Presences** (`presences.select_presences`, `thin`, `genus_weights`): R6's step list through the
   shared `Pipeline` (every step counted), the box test by the 250 m cell's centre, the join with
   every outcome counted, then SPEC R6's own check (a record above 250 m reaching the table raises
   `R6Violation`). Thinning one per genus and 250 m cell; M3 (b) weights.
7. **The tile reader** (`predictors.read_tile`): one tree tile with its flags, soil, mask, weather
   keys and level III codes; P4 as ruled (D134, D136, D137); every cell coded 0 to 6 (P9's codes);
   a pending study cell or a tile of another band layout stops the run; tier B left out; shares
   under 0.01 read as 0.
8. **Background** (`background.draw_background`): eligible cells in the frame, without
   replacement, seed 20260918, sorted, sha256 of the list; a short pool is refused; weights sum to
   the presences' total (D133).
9. **Block folds, leakage, tuning** (`folds`): leave one level III block out; every fold checked
   for leakage before the first fit; per-fold tuning by inner grouped 4-fold over training blocks
   by weighted log loss (D31); the 20 configurations committed
   (`docs/audits/2026-10-15-t7-build/tuning_grid.json`, sha256 `7412d906...45cd`); the 15% forested
   cut and the 30-presence minimum (D139).
10. **Weighted AUC and the clustered bootstrap** (`metrics`): the rank-sum AUC with weights, ties
    half; 1,000 resamples of whole weather cells, seed 20260918, interval of a difference; the P10
    test (D140).
11. **Area of applicability** (`aoa`): CAST's method in Python with scipy's KD-tree (see "Premises
    that were wrong" 3 for the source read).
12. **Writers** (`outputs.HabitatWriter`, `write_manifest`): float32 raw score and uint8 code mask
    over the box window, tile by tile, `.partial` then renamed; refused on the flash drive and
    inside the repository; every tag and label checked for a percent, "sighting chance",
    "probability", D58's terms and edibility words; a manifest refused unless it names P9's inputs
    and settings. Default root `/mnt/work/Zynergy/forecast-data/t7`.
13. **Attribution from tile tags** (`outputs.attribution`): the tiles' own `attribution` tags split
    and kept, SCANFI dropped unless a Canadian value was read (under D136, none is).

Also `model.py` (P5, P6, the ladder): LightGBM with `log_effort` in an interaction group of its own
and a rising monotone constraint, T1's determinism settings; `predict_at_effort`; the held effort
as a median; comparisons A and B; the base plus each candidate band (D138).

### The normalised membership list (the planner's design requirement)

Domain code (join, thinning, weighting) reads only this format and knows no published table's
columns. UTF-8, tab-separated, one header row, one row per genus:

| column | meaning |
|---|---|
| `genus` | genus name as GBIF's `genus` column spells it; unique in the file |
| `genus_key` | GBIF `genusKey` if known, else empty |
| `family` | family name or empty; used only for records named to family (M2) |
| `lifestyle` | `ectomycorrhizal`, `wood_rot` or `other` |
| `certainty` | `clear`, `mixed` or `uncertain` |
| `source_id` | the source, its sha256 prefix and the conversion rule version |
| `note` | why the row has its lifestyle and certainty |

`family` is one column beyond the planner's list, because M2 handles records named only to family.
The file's sha256 is checked before a row is read; the join refuses a list whose fingerprint is not
the one it was given. The test
`test_a_hand_made_list_and_an_adapter_made_list_drive_the_same_join_unchanged` drives the same
`Join` from a hand-made synthetic list and from an adapter-made one. The join was never built against
FungalTraits' columns, so nothing was refactored.

FungalTraits reaches the format only through `t7/fungaltraits.py`. Its conversion rule is a
**proposal** (module docstring), not ruled: primary lifestyle ectomycorrhizal with no secondary
lifestyle, no lifestyle comment and a mushroom-forming fruitbody type is "clear"; with a secondary
lifestyle or comment "mixed"; with another fruitbody type "uncertain"; another primary lifestyle
naming ectomycorrhizal in its secondary or comment "mixed"; wood saprotroph is `wood_rot`;
duplicated genera that disagree are "uncertain".

## The FungalTraits fetch

- **URL:** https://repository.up.ac.za/bitstreams/03249ba0-734b-4e0c-be8b-60c7accaa480/download
  (served from `/server/api/core/bitstreams/.../content`), the University of Pretoria repository
  record http://hdl.handle.net/2263/80202 (item `a8309ba3-aa1a-4324-8969-5c7980fa88b6`), file
  `Polme_FungalTraitsTabS1_2020.xlsx`, described there as "Table S1. Traits of genera".
- **Date:** 2026-10-16T02:03:46Z to 02:03:56Z, fetched once (HTTP 200).
- **Checked against the source:** the repository states 1,243,643 bytes and MD5
  `73a66e29b7a786ba884c971b52b5b08f`; both matched (OBSERVED).
- **sha256:** `0092d7fb8bd315b7801cc71e91c7eb889fa07f1e77dade5827b44f093b46bf2a`.
- **Stored:** `/mnt/work/Zynergy/forecast-data/membership/` (read-only file), beside the record's
  metadata as served (`up_item_record.json`, `up_item_bundles.json`) and the repository's licence file
  (`up_deposit_license.txt`). Outside every repository; `.gitignore` now refuses `*.xlsx`, `*.xls`,
  `membership/`, `*FungalTraits*` and `membership_list*.tsv` in case a copy lands here.
- **Licence text seen at that location:** the record's rights field reads "© 2021, Mushroom
  Research Foundation. The original publication is available at
  https://www.springer.com/journal/13225." The item's licence bundle holds the repository's deposit
  licence, which grants the University of Pretoria "the non-exclusive right to reproduce, translate
  ... and/or distribute your submission"; it grants nothing to users. **No open licence is stated**,
  which agrees with RECORD -1036.
- **The normalised list written from it** (adapter run once, no record read):
  `/mnt/work/Zynergy/forecast-data/membership/membership_list_fungaltraits.tsv`, sha256
  `972324a8a1e64c74408e1f6900d6661dd2fa71adb39f9f8ec24a177be40c42ed` (recorded as
  `fungaltraits.NORMALISED_LIST_SHA256`), 10,765 genera from 10,771 rows (6 duplicated names
  merged). Summary of the list, counts only: ectomycorrhizal clear 312, mixed 34, uncertain 3;
  wood_rot clear 1,878, mixed 230; other clear 6,986, uncertain 1,322. These are counts of a trait
  table, not of any record. No genus name from it is in the repository.
- **DATA_REGISTER:** no row filed (`SPEC.md:84`). The source's state is D31's "licence not stated
  at source"; filing that row is for the planner or owner to decide alongside D142.

## Failing first

- `bcd9cca`, before any code: 53 tests, 53 failed, every message `NotImplementedError: T7 build:
  not written yet (tests first)` (OBSERVED, `docs/audits/2026-10-15-t7-build/tests_first.out.txt`,
  from the JUnit XML). Two earlier failures with other reasons were test-side mistakes, fixed before
  that run: `np.round` with an array of digit counts, and an R6 guard test that patched a name the
  stub did not import.
- After the code, two more test-side mistakes, fixed in `ee4b94b`: numpy scalars handed to
  `cells.cell_for` (it reads `repr`), and a capped-threshold example that was not capped (Q75 +
  1.5 IQR of [1, 1, 1, 2] is 1.625; [0, 0, 1, 1] reaches the cap). **`ee4b94b`'s message says
  four**: the other two it names (the rounding and the import) were already fixed in `bcd9cca`.
  The message is wrong on that point; it is not amended.
- Forward: 53 passed (`forward_t7.out.txt`), then 54 with the added level III test.

## Revert checks

Runner `docs/audits/2026-10-15-t7-build/revert_runner.py.txt`, output `revert.out.json`. Rules:
the file copied aside; one exact edit (old text found once); `__pycache__` cleared;
`PYTHONDONTWRITEBYTECODE=1`; a subprocess shows the interpreter sees the edit; all `test_t7_*.py` run
with a fresh JUnit XML; refused on any collection, import, syntax or name error, a missing XML or
errors in it; restored from the saved copy, never git, hashed against it, forward text confirmed;
all files hash as before at the end (OBSERVED: true).

**First pass (not cited as evidence of the final tests):** 33 of 38 failed exactly as predicted.
- Three did not bite:
  - R1, the tie fallback: float rounding lands every exact decimal tie right. Searched every tie
    in -180 to 180 and its neighbouring doubles: 410 of 32,391 differ. The test gained
    -127.85000000000001.
  - R3, level III by centre: the test's 0.02° margins hid the edge cells. Added a metre-exact test.
  - R30, the area of applicability's weighting: only the training side was edited, and new data
    were still weighted. Added a training-side assertion.
- Two failed one more test than predicted, each because of its own edit:
  - R22, the leakage check off, which the outer loop also uses.
  - R25, AUC weights off, which the bootstrap rests on.

  Their predictions were corrected.
- R24 (tuning sees the held-out block) was predicted to fail only after the test was strengthened
  to check that every tuning fit excludes the held-out block.

**Second pass: 38 of 38 fail exactly the predicted tests**, each message specific to its edit:

| Check | Edit | Message (abridged) |
|---|---|---|
| R1 | tie fallback off | `(450, -1278)` against `(450, -1279)` |
| R2 | out-of-frame cell given 0 | the refused cell found in the totals |
| R3 | burn by touch | `[[0, 5, 5, 5]] == [[0, 5, 5, 0]]` |
| R4, R5 | list sha256, join fingerprint unchecked | DID NOT RAISE MembershipListError |
| R6, R7 | mixed genera, family-only records in the main run | "listed mixed"; "family wholly in group" |
| R8 | adapter source sha256 unchecked | DID NOT RAISE SourceMismatch |
| R9, R10 | fruitbody rule, duplicate rule off | the class tables differ |
| R11 | R6 guard off | DID NOT RAISE R6Violation |
| R12 | box test off | `[1, 5, 7] == [1, 7]` |
| R13 | thin by record | the kept list differs |
| R14 | small genera weighted alone | `1.0 == 0.5` |
| R15, R16 | pending, layout checks off | DID NOT RAISE PendingCell, LayoutMismatch |
| R17 | share floor off | `0.0049999... == 0.0` |
| R18 | Canada not masked | Canada cell code 0 against 3 |
| R19 | water code off | code 4 against 6 |
| R20 | draw unsorted | the list differs |
| R21 | short pool not refused | numpy's own ValueError, not NotEnoughBackground |
| R22 | leakage check off | DID NOT RAISE LeakageError; "a point has no held-out prediction" |
| R23 | outer loop skips the check | "a point has no held-out prediction" |
| R24 | tuning on all blocks | held block 1 seen in a tuning fit |
| R25 | AUC ignores weights | 0.5266 against 0.5990; the bootstrap interval collapses |
| R26 | no resampling | interval collapses to the point |
| R27 | P10 ignores forested blocks | `not True` |
| R28 | threshold uncapped | `2.5 == 1.0` |
| R29 | DI not cross-validated | training DI 0; the far-point test fails |
| R30 | training side unweighted | training DI differs from the one-predictor DI |
| R31 | no interaction constraint | KeyError in the params test; the ranking at two efforts differs |
| R32 | no monotone constraint | `[0, 0, 0] == [0, 0, 1]` |
| R33, R34 | flash drive, repository not refused | DID NOT RAISE OutputRefused |
| R35 | wording check off | DID NOT RAISE OutputRefused (two tests) |
| R36 | manifest keys unchecked | DID NOT RAISE OutputRefused |
| R37 | SCANFI kept though unread | the attribution lists differ |
| R38 | rasters written in place | the file exists before close |

Not revert-checked: the xlsx reader's details, `load_named`'s use of the loader, `held_effort`,
`cover_columns`, `ladder` and `kept_candidates` (tested forward only).

## Suite and lint

- Before any change: **604 passed** (252 s).
- After, at `dd55720`: **658 passed** (604 + 54 new), 0 failed, 0 errors, 268 s (OBSERVED, under the 5G cap at nice 10).
- `ruff check .`: all checks passed. `ruff format --check .`: 334 files already formatted at
  `dd55720`.
- pytest basetemp under `.pytest-tmp/` in the worktree (git-ignored).

## The next step, which crosses the point of no return

**V9: the presence count** (RECORD -1030 point 1; the plan's V9; P1 and P2). Running
`names.load_named` over the rows of `occurrence.txt` in
`~/Zynergy/forager-forecast-d26/data/d26/downloads/0012112-260928105237408.zip` (2,493,578
records), then `presences.select_presences` with
`Join(load_list(<list>, NORMALISED_LIST_SHA256), ..., MYCORRHIZAL_GROUP, MAIN_RUN)`, and the same
for the side run and the comparison group, would read every fungal record's taxon names,
coordinates, dates, uncertainty, observer and licence, and count the group's presences per genus,
year, side and block. Once read, the counts fix M1, M2, M3 and the block minimum in practice.

**What must be ruled before it, all still proposals:**
- the adapter's conversion rule, including what counts as mushroom-forming;
- the family-only rule for the side run;
- the thinning unit (one per genus and 250 m cell);
- the per-genus minimum, `PROPOSED_MIN_PRESENCES_PER_GENUS = 30` (V9 (e)), and pooling the genera
  under it.

**Also before it:** the D26 zip's sha256 re-checked against its DOI record (plan abort
conditions); not re-hashed in this build.

**After it, before the fit** (point of no return 2): the effort frame's static effort over the box
(reads T6's stored surface), one pass of `read_tile` over the 296 box tiles (layers only), the
background draw, and one timed trial fold.

## What is untested

- Nothing ran on real layers. `read_tile` is tested only on synthetic 4 x 4 tiles. These are not
  exercised:
  - the real 256-cell tiles and the US-half files (`trees_us_half_*`, not wired in);
  - a soil tile of 2048 cells read through a smaller window;
  - the real mask's offsets;
  - the level III shapefile at full size.
- No end-to-end run joins the pieces: there is no pilot script that streams the box, draws the
  background, fits the ladder, scores and writes. Nothing measures time or memory for the fit or the
  predict pass.
- The mask map image (P9's `mask_map.png`) and the five-class rendering are not built.
- LightGBM 4.7.0 accepts both constraints and keeps the ranking at two effort levels on one
  synthetic model. That is not shown for every configuration of the grid.
- The estimated mean training distance above 5,000 points is checked against the exact one on 300
  points only.
- The adapter was run on the real table once, to write the list. Its classes were not compared
  with any other source.
- CI was not run for this branch by me. Its result on the pushed head was not read.

## Premises that were wrong

1. "DECISIONS.md" (dispatch): the file is `docs/planning/DECISIONS.md`.
2. Proposals, new code 11: "scipy 1.18.1 is in the lock only as LightGBM's dependency
   (`uv.lock:402-403`)". In `b9127e5`'s lock, `lightgbm`, `statsmodels` (dev) and `formulaic` all
   depend on scipy. Lines 402-403 are scipy's own package entry. The pin is unaffected.
3. P8, "by the rule of the published paper, which the build reads and quotes before writing code".
   The publisher's page refused again (HTTP 403), and Europe PMC has no record. What was read
   instead is CAST 1.2.0's source:
   - `R/aoa-helpers.R`, `.di_threshold`: "threshold_quantile <- stats::quantile(trainDI, 0.75)",
     "threshold_iqr <- (1.5 * stats::IQR(trainDI))", "thres <- min(thres, max(trainDI))";
   - `R/trainDI.R`, `trainDist_avrgmean`.

   That is the package's implementation (GPL >= 2; re-implemented, not copied), not the paper.
   One departure is disclosed in `aoa.py`: above 5,000 training points the mean distance is
   estimated from 2,000,000 random pairs.
4. P9 places outputs at `/mnt/work/forecast-data/t7/pnw-<run date>/`. The dispatch placed the
   membership copy under `/mnt/work/Zynergy/forecast-data/`. The writers default to
   `/mnt/work/Zynergy/forecast-data/t7` so the two sit together. That is a choice, below.
5. The P9 mask legend's "canopy under 10%" would trip the build's own wording check (no percent on
   any 250 m output). The legend reads "canopy cover under D89 (3)'s threshold".

## Decided beyond scope

- P9's code 6 is read as "no valid tree pixel at all", meaning a valid fraction of 0. A cell with
  some valid pixels but under half is code 4, as P9's text says.
- The `family` column in the normalised list.
- The comparison group is joined by genus name, not through the list.
- An inner-group assignment by seeded shuffle for the 4-fold tuning.
- The output root above.
- No DATA_REGISTER row.
- Ran the adapter once on the real table to write the list and record its sha256.

## Confirmed vs inferred

- **Confirmed (OBSERVED):**
  - the fetch's size and MD5 against the repository's;
  - the sha256 values;
  - the D26 header columns;
  - tests failing first and passing after;
  - 38 of 38 reverts biting;
  - lint;
  - the suite counts.
- **Inferred:**
  - that float rounding differs from the decimal rule only near ties (searched, not proven);
  - that the proposed adapter rule reads M1's "mushroom-forming".
