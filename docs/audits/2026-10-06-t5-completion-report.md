# T5 completion report: host trees as a genus share of canopy, and the BC and Washington seam

Branch `t5-host-trees`, unmerged. It was cut from main `ad64fef` and merged main `74c7f3b`, with T4,
before Part 2 began. Written 2026-10-06 (UTC) by the T5 coder session (D38). The documents it rests
on:

- Dispatch: `docs/dispatch/2026-10-06-t5-host-trees.md`.
- Amendment 1: `docs/dispatch/2026-10-06-t5-host-trees-amendment-1.md` (Forager RECORD -587).
- Rulings: D83 to D87.
- Part 1: `2026-10-06-t5-source-survey.md`.
- Verify first: `2026-10-06-t5-verify-report.md`, including its appended section 7.

Not merged (D40). It waits for the independent review (D18).

## 1. What landed

| Commit | What |
| --- | --- |
| `0192dfd` | Part 1 source survey and its index row |
| `cf4d2ae` | Merge of main `74c7f3b`. The index conflict was on appended rows only, and every row from both sides is kept |
| `f1ea5e6` | Amendment 1 filed; D83 to D87 |
| `de579a1` | Verify-first report and the TreeMap strip probe |
| `f30c0ee` | `crown_cover.py` and `seam.py`, with tests (each seen failing at collection before its module existed) |
| `c247c12` | Verify report section 7: the westmost transect longitude, and the verdict rule replaced before any value was read |
| `b7a04ac` | `t5_layer.py` and `scripts/t5_build.py`, with synthetic end-to-end tests |
| `59246a1` | TreeMap window read past the raster's north edge (the first real cut failed on it; the new test reproduced the failure first) |
| `536224b` | Woodland-surrogate test and the revert runner |
| `b953609` | One regrid pass per source (same values; the first real build was stopped for speed) |
| `97af4fd` | Tests for the reverts that did not bite in the first run; two runner checks added |
| `88760cd` | Request records in `docs/pulls/`, register rows for TreeMap 2023 and BIGMAP's D83 reading |
| `01590ba` | Build evidence: revert results, transects, summaries, master hashes, canopy check |

Code: `src/forager_forecast/crown_cover.py`, `seam.py`, `t5_layer.py`, `scripts/t5_build.py`.
Tests: `tests/test_crown_cover.py`, `test_seam.py`, `test_t5_layer.py`.

## 2. Data (gitignored `data/t5`, a symlink to the owner's flash drive)

- **TreeMap 2023**: `RDS-2026-0038.zip`, 5,240,617,359 bytes, downloaded 11:15:12 to 11:21:54 UTC.
  Its sha256 `348264eb...abb7` equals the catalogue's. The raster was extracted on the flash drive
  only. The tree table is streamed from the zip.
- **SCANFI v2, 2025**: ten windowed reads over HTTP of the species crown-closure layers, 190 s, about
  18 MB in total.
- Request records: `docs/pulls/t5-treemap2023-strip.request.json` and
  `docs/pulls/t5-scanfi-v2-2025-strip.request.json`. They carry the citations, the Archive's terms
  as quoted (D84), the zip's sha256, pixel windows and file hashes.
- Register rows were appended for TreeMap 2023 and for BIGMAP's D83 reading.
- Nothing was written to internal disk beyond the repository and `/tmp` test output. No other folder
  on the drive was touched.

## 3. What was built

A 250 m master-grid strip, 48.70 to 49.30 N by 122.80 to 120.95 W (window `-1839250, 1254250,
-1696750, 1356750`), in `data/t5/master_scale_{0.7,1.0,1.3}/`:

- `host_trees_strip.tif` (float32): total canopy cover %, valid fraction, source (1 TreeMap,
  2 SCANFI), and share bands for *Pseudotsuga*, *Tsuga*, *Picea*, *Abies*, *Pinus*, *Quercus*,
  conifer and broadleaf.
- `host_trees_strip_flags.tif` (uint8): one flag per share band. 0 means no value, 1 TreeMap,
  2 SCANFI, 3 Canada and not available in SCANFI (D85).
- Both files carry both citations, the derived-data notice (D84) and the rulings in their tags.

Hashes for scale 1.0 are in `2026-10-06-t5-build/master_sha256.txt`.

At scale 1.0 (`2026-10-06-t5-build/summary_scale_1.0.json`):

| | US (TreeMap) | Canada (SCANFI) |
| --- | --- | --- |
| Cells in the strip | 72,479 | 72,040 |
| Cells passing D74's half-area rule | 72,478 | 72,040 |
| Cells with a share (cover of at least 10%) | 47,160 | 56,306 |
| Mean share, *Pseudotsuga* | 0.080 | 0.202 |
| Mean share, *Tsuga* / *Abies* | 0.315 / 0.334 | not available |
| Mean share, conifer / broadleaf | 0.801 / 0.199 | 0.791 / 0.209 |

TreeMap facts:
- 1,512 plots in the window, every one with tree rows.
- 1,242 live trees took a surrogate crown width under the rule in verify report section 2. The
  surrogates were 14 species, listed in the summary; the class default (quaking aspen) went to
  ash, cottonwood, birch, cherry, dogwood, willow, buckeye, crab apple and chinkapin.

## 4. The Verify: transects across 49 N

The plan is as stated before any value was read (verify report section 4, with section 7's
corrections): 25 transects, 1 km windows, and a null-quantile verdict. Results at scale 1.0
(`2026-10-06-t5-build/transects.json`):

| Variable | Transects with a border window | B = median \|border step\| | Threshold (null P95) | Median \|within\| US / CA | Mean signed step (CA − US), 95% CI | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Total canopy cover (%) | 25 | 14.4 | 12.6 | 8.1 / 8.2 | +0.9 [−6.8, +7.8] | **Known artifact** |
| *Pseudotsuga* share | 7 | 0.087 | 0.072 | 0.038 / 0.056 | +0.087 [−0.021, +0.197] | **Known artifact** |
| Conifer share | 7 | 0.020 | 0.059 | 0.012 / 0.016 | +0.022 [−0.017, +0.081] | No step |
| Broadleaf share | 7 | 0.020 | 0.059 | 0.012 / 0.016 | −0.022 [−0.081, +0.017] | No step |

*Tsuga*, *Picea*, *Abies*, *Pinus* and *Quercus* cannot be tested, because they are not available on
the Canadian side (D85).

How to read the two artifacts. They are written up here with their size, and nothing was tuned:

- **Total cover.** The border steps are larger in size than steps inside either country, but they
  have no consistent sign: the mean is +0.9 points, with an interval that spans zero. The two sides
  measure cover differently:
  - SCANFI's crown closure;
  - our crown-width cover, which leaves out trees under 5 in.

  On the strip's plots, our cover runs a median **10.9 points below TreeMap's own CANOPYPCT**
  (Pearson r = 0.83, IQR −19.1 to −4.2; `2026-10-06-t5-build/canopy_check.out.txt`). Land use along
  the line (a cleared boundary vista, roads and farms) may add real steps. That is inferred and was
  not checked.
- ***Pseudotsuga* share.** Canada reads higher by a median 0.087, but only 7 of 25 transects have a
  share on both sides, and the interval on the signed mean includes zero. The step is real by the
  stated rule, and weak as evidence either way.
- **The conifer and broadleaf totals**, which both sides carry for every host list (D85), show no
  step beyond within-country variation.
- **Only 7 transects carry shares.** The other 18 have a window under 10% cover on one side or the
  other (cleared lowland in the Fraser Valley and Whatcom County, inferred from the transects'
  longitudes, not checked on a map). The threshold was not lowered to gain transects.

**Sensitivity to the surrogate rule:**
- Every surrogate crown width was scaled by 0.7 and by 1.3. The verdicts are unchanged: B moves by
  at most 0.0022 for *Pseudotsuga* (0.0894, 0.0875, 0.0853) and 0.0002 for conifer.
- US cells with a share go from 46,734 to 47,466.

## 5. Tests and revert checks

- **Suite**: 275 passed before T5 code (after the merge), and **303 passed after**. Test functions
  went from 171 to 199. `__pycache__` was cleared and `PYTHONDONTWRITEBYTECODE=1` set for every run.
  `ruff check` and `ruff format --check` are clean.
- **Revert checks: 19**, run by `2026-10-06-t5-build/revert.py.txt`, which is T4's strict runner:
  - it saves a copy and restores from it, and confirms the restored file equals HEAD;
  - it refuses a run with collection or import errors;
  - it confirms the interpreter sees the edit.

  Results are in `revert_results.json`. **17 bite**, each with a failure message specific to its
  own edit. For example, "no overlap correction" fails only the equation 1-2 test with
  `5.588 == 5.435`, and "verdict against the median" fails the no-step rate test with `83/200`.
  The two that cannot bite were labelled so in the runner before it ran:
  1. Filling Canada's unavailable genera from the US share: the US layers are already NaN north of
     49 N, so the edit changes nothing. The flag-dropping and Pinus-supplied reverts do bite.
  2. **D74's half-area rule.** Under the centre-side rule a cell's own side covers about half its
     area or more, so the rule almost never binds. On real data it removed **1 cell of 145,519**.
     It is a check that can barely fail here, and it is recorded rather than dressed up.
- **The first revert run** had 5 of 17 not biting. Three were real gaps:
  - the 10% threshold, because the test's sparse cell had exactly zero cover;
  - the TreeMap north-of-49 mask, because the synthetic raster had the same plot on both sides;
  - the cell-side rule, because no test touched a cell just north of 49 N.

  Tests for each were added (`97af4fd`), and the second run bites on all three. Two of them fail on
  the same assertion line (`assert np.False_`), so the message does not by itself name which edit
  it was. The edit is named by the runner.

## 6. Not checked or not verified

- The surveyed boundary against the 49th parallel (inferred to differ by up to a few hundred
  metres). Which side a cell falls on uses the parallel.
- Which species SCANFI puts in "other coniferous" and "broadleaf" (inferred from the readme, which
  does not say).
- Whether the cleared-land reason for the 18 transects without shares is right (inferred, no map
  view).
- The pro-rata split of overlap-corrected cover between genera (inferred from Crookston and Stage's
  random-placement assumption, verify report section 2).
- No tile archive was made, as Part 2 does not ask for one. No raster was looked at in a viewer.
- The Bechtold widths were not checked against any field crown measurement. The only external check
  is TreeMap's own CANOPYPCT (section 4), which our cover undershoots.
- TreeMap includes trace imputed Californian species in the strip (blue oak, for example). They are
  carried as given.

## 7. For the owner

1. **Two known artifacts** at the border: total cover, with no consistent sign, and the Douglas-fir
   share (Canada +0.087 median, n = 7). Accept them as recorded, or ask for a follow-up. The obvious
   candidates are TreeMap's own CANOPYPCT as the US total, and FVS crown-width equations or
   saplings, to close the 10.9-point cover gap. Each is a change to D87's formula and needs your
   word.
2. **The readings in verify report section 6**:
   - *Pinus*, *Picea* and *Abies* are not available in Canada (whole genus, not the partial sums);
   - the surrogate rule;
   - the 10% threshold;
   - SCANFI 2025.
3. **The host-genus sources** found (D85): Pilz et al. 2003 for *Cantharellus* in the Pacific
   Northwest (Douglas-fir, hemlock, spruce, fir, pine; oak only in California and the East), and
   Burdsall and Banik 2001 for *Laetiporus* (conifers, and *Quercus* among hardwoods). The dispatch's
   oak line for PNW chanterelles is not supported by the first.
4. **Decision rows used**: D83 to D87, within the D83 to D89 range the dispatch allowed.

## 8. Appended 2026-10-06: Amendment 2, with TreeMap's own canopy as the US total (D88, D89)

Sections 1 to 7 above stand as written. This section records Amendment 2
(`docs/dispatch/2026-10-06-t5-host-trees-amendment-2.md`, Forager RECORD -588) and what it changed.

**The field.**
- TreeMap's data dictionary (`TreeMap2023_CONUS_Data_Dictionary.pdf`, in the publication zip) lists
  `CANOPYPCT` as "Live canopy cover (percent)", source "From Forest Vegetation Simulator". It is
  read from the raster attribute table, `TreeMap2023_CONUS.tif.vat.dbf`.
- The dictionary does not say whether overlap is accounted for. The publication's metadata says plot
  cover was calculated "using the StrClass keyword in the Forest Vegetation Simulator (Dixon 2002,
  Crookston and Stage 1999)". Crookston and Stage define StrClass's stand total as "Percent canopy
  cover, accounting for overlap". So `CANOPYPCT` is **canopy cover with overlap** (inferred from
  those two texts; neither states it on its own).
- It covers all live trees, including those under 5 in, which the tree-list split leaves out.

**The change** (`680bca4`):
- US total cover is now `CANOPYPCT`.
- A genus's cover is `CANOPYPCT` x its tree-list share; D87's split is unchanged.
- In the strip, 22 of 1,512 plots (2,219 of 4,969,059 forest pixels) have canopy but no tree of 5 in
  or more. They count toward total cover but are left out of the shares, never counted as zero of
  every genus.
- The first build stays reproducible (`us_total="tree_list"`). Its outputs are kept on the drive as
  `master_tree_list_scale_*` and `transects_tree_list.json`. The committed `transects.json` and
  `summary_scale_*.json` in `2026-10-06-t5-build/` are those first-build files.
- Rule, seed and windows are unchanged; nothing else was tuned.

**Transects, old against new** (scale 1.0; new files `transects_treemap_canopy.json` and
`summary_treemap_canopy_scale_*.json`):

| Variable | US total | Transects | B, median \|border step\| | Threshold | Median \|within\| US / CA | Mean signed (CA − US) [95% CI] | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Total cover (pts) | tree list (first build) | 25 | 14.4 | 12.6 | 8.1 / 8.2 | +0.9 [−6.8, +7.8] | artifact |
| Total cover (pts) | **TreeMap CANOPYPCT** | 25 | **15.0** | **14.2** | 8.1 / 8.2 | **−5.9 [−14.1, +1.8]** | **artifact** |
| *Pseudotsuga* share | tree list | 7 | 0.088 | 0.072 | 0.038 / 0.056 | +0.087 [−0.021, +0.197] | artifact |
| *Pseudotsuga* share | **CANOPYPCT** | 7 | **0.083** | 0.072 | 0.041 / 0.056 | +0.087 [−0.014, +0.192] | **artifact** |
| Conifer share | tree list | 7 | 0.020 | 0.059 | 0.012 / 0.016 | +0.022 [−0.017, +0.081] | no step |
| Conifer share | **CANOPYPCT** | 7 | **0.017** | 0.059 | 0.009 / 0.016 | +0.020 [−0.018, +0.079] | no step |
| Broadleaf share | tree list | 7 | 0.020 | 0.059 | 0.012 / 0.016 | −0.022 [−0.081, +0.017] | no step |
| Broadleaf share | **CANOPYPCT** | 7 | **0.017** | 0.059 | 0.009 / 0.016 | −0.020 [−0.079, +0.018] | no step |

Reading:
- **Both artifacts remain.** They stay recorded as known artifacts, as Amendment 2 allows.
- **Total cover**: the step's size barely moves (14.4 to 15.0 against a threshold of 14.2). Its sign
  now leans US-high: with TreeMap's higher canopy, the mean is −5.9, and the interval still spans
  zero.
- **Shares**: they move only through the per-pixel weighting, and the verdicts do not change.
- **Cells with a share**: US cells rise from 47,160 to 49,424, because more cells now pass the 10%
  threshold. Still only 7 transects have shares on both sides.
- **Sensitivity**: at surrogate width scales 0.7 and 1.3, the *Pseudotsuga* B is 0.0831 at both and
  the verdicts are unchanged.

**Decision rows**:
- D88 records the US total, with the field, its units and its overlap reading.
- D89 records the owner's acceptance of the four readings: *Pinus*, *Picea* and *Abies* wholly not
  available in Canada; the surrogate rule; the 10% threshold; SCANFI 2025.
- That fills the range the dispatch allowed (D83 to D89).

**Tests and revert checks.**
- Tests first: the new tests failed with `build_master() got an unexpected keyword argument
  'us_total'` before the change.
- Suite: **307 passed**, with test functions going from 199 to 203. Ruff is clean.
- Revert runner, now with 23 checks (`revert_results_d88.json`):
  - **21 bite**, and the same 2 as before cannot bite.
  - The four D88 checks:
    - "US total back to the tree list" fails with `42.71 == 70.0`.
    - "genus cover left as tree-list cover" fails with `0.610 == 1.0`.
    - "canopy with no split counted as no genus" is stopped by the regrid's own guard ("layers of
      one source must share their no-data pattern") before any share test runs.
    - "plot without CANOPYPCT accepted" fails later, with a `KeyError` and not the intended message.
  - Both of the last two still fail loudly, but not at the assertion written for them.
- The not-available flag check's anchor was updated to follow the D88 flag code (`04bf880`).

## 9. Appended 2026-10-06: Amendment 3, the D92 build and the matched null (D90, D91, D92)

Sections 1 to 8 above stand as written. This section records Amendment 3
(`docs/dispatch/2026-10-06-t5-host-trees-amendment-3.md`, Forager RECORD -594), which answers the
review (`2026-10-06-t5-review.md`). Evidence is in `2026-10-06-t5-amendment-3/`.

**How this section was produced.** Two earlier sessions on this amendment were stopped by machine
restarts, the second by an out-of-memory kill of a build process at 3.9 GB while a Gradle suite also
ran. This session started from `171e3b6` (nothing newer on the remote, worktree clean) and trusted
none of their output on the drive:
- The TreeMap cut was re-run with the current code. All three files (`treemap_plots.tif`,
  `treemap_plot_covers.csv`, `treemap_request.json`) came out byte-identical to both cuts the earlier
  sessions left (sha256 `5cb0f6a9`, `729a80c9`, `1d6be31c`).
- The SCANFI total window matches its request record in `docs/pulls/` (sha256 `ceb2d79f`), and the
  ten class windows match theirs.
- The leftover `stale_master_d92_scale_0.7_from_0642` and `stale_recut_from_0632` folders on the drive
  were not used. No `master_d92_*` folder existed before this session's builds.
- Each scale was built in its own process (`scale=S`, added at `a1634ec`), one after another, under a
  6 GB memory cap with no swap, as the only heavy job on the machine.

| Step | Peak memory (max RSS) | Wall time |
| --- | --- | --- |
| TreeMap re-cut | 0.85 GB | 14 s |
| D92 build, scale 1.0 | 5.00 GB | 496 s |
| D92 build, scale 0.7 | 5.00 GB | 477 s |
| D92 build, scale 1.3 | 5.00 GB | 481 s |
| Transects, three scales | 0.12 GB | 7 s |
| SCANFI sum against total (re-run) | 1.09 GB | — |
| Revert runner, 29 checks | 0.16 GB | 285 s |
| Full suite | 0.18 GB | 34 s |

**D92: SCANFI's own total.** Before the switch, the ten-class sum was compared with SCANFI's total
crown closure on the strip's Canadian side (`scanfi_sum_vs_total.out.txt`, re-run this session and
identical):
- 10,995,751 pixels; 24,467 are no data in both, with no disagreement between the masks.
- On all 10,971,284 compared pixels, the sum equals the total exactly (difference 0 at the minimum,
  maximum, P1 and P99). The mean is 35.83 for both.
- So, on this strip, D92 changes nothing in the values. On the master grid the D92 strip and the
  Amendment 2 strip have identical `total_cover_pct` on all 72,040 Canadian cells, and identical
  Canadian shares (`strip_d92_vs_a2.out.txt`). The build now names its Canadian total in the
  `ca_total` tag; the Amendment 2 strip carries no such tag.

**D91: capped diameters.** From the cut's request record (`treemap_request.json`, scale 1.0):
- **1,516 live trees** of 5 in or more are beyond the largest Table 1 diameter for the species whose
  coefficients they use, and take the width at that diameter. The review's estimate was about 1,500.
- **0 trees** with a non-positive width remain. Before D91, 29 were dropped without a count (28
  western redcedar, 1 Douglas-fir; review F2).
- The counts are recorded at scale 1.0 only. The cap depends on diameter alone, so the capped count
  is the same at every scale (inferred from `crown_cover.py:190-195`, not counted at 0.7 and 1.3).
- Effect on the strip (scale 1.0, against the Amendment 2 strip, which was built before D91): no US
  cell changes its total cover or its defined cells. US shares change on part of the 49,424 cells
  with a share: Douglas-fir on 16,910 cells, at most 0.028, mean 0.0003; conifer and broadleaf on
  about 18,500 cells, at most 0.019; *Abies* and *Tsuga* the most, at most 0.21 and 0.13, mean 0.006
  and 0.004. Those two are not tested at the border (D85).

**D90: the matched null.** The null for each variable is now drawn from the same transects as its
border statistic B. Same seed (20260918), same 25 transects (longitudes identical in all three
builds' files), same windows, same 95th percentile.

**Every build so far, at scale 1.0.** "Old null" is the rule as filed (verify report section 7):
null over 23 (US) and 24 (Canada) transects for the shares, against B over 7 (review,
`rerun_transects.out.txt`). "D90 null" is matched: 7 and 7 for the shares, 25 and 25 for total cover.
The first two builds under the D90 null are the earlier session's files
`transects_tree_list_d90.json` and `transects_treemap_canopy_d90.json`, run on the stored layers.

| Variable | Build | Null | Transects (B) | B | Threshold | Mean signed (CA − US) [95% CI] | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Total cover (pts) | first (tree list) | old | 25 | 14.4 | 12.6 | +0.9 [−6.8, +7.8] | artifact |
| Total cover (pts) | first (tree list) | D90 | 25 | 14.4 | 12.6 | +0.9 [−6.8, +7.8] | artifact |
| Total cover (pts) | Amendment 2 (CANOPYPCT) | old | 25 | 15.0 | 14.2 | −5.9 [−14.1, +1.8] | artifact |
| Total cover (pts) | Amendment 2 (CANOPYPCT) | D90 | 25 | 15.0 | 14.2 | −5.9 [−14.1, +1.8] | artifact |
| Total cover (pts) | **Amendment 3 (D91, D92)** | **D90** | 25 | **15.0** | **14.2** | **−5.9 [−14.1, +1.8]** | **artifact** |
| *Pseudotsuga* share | first | old | 7 | 0.088 | 0.072 | +0.087 [−0.021, +0.197] | artifact |
| *Pseudotsuga* share | first | D90 | 7 | 0.088 | 0.120 | +0.087 | no step |
| *Pseudotsuga* share | Amendment 2 | old | 7 | 0.083 | 0.072 | +0.087 [−0.014, +0.192] | artifact |
| *Pseudotsuga* share | Amendment 2 | D90 | 7 | 0.083 | 0.120 | +0.087 | no step |
| *Pseudotsuga* share | **Amendment 3** | **D90** | 7 | **0.083** | **0.120** | **+0.087 [−0.012, +0.189]** | **no step** |
| Conifer share | first | old | 7 | 0.020 | 0.059 | +0.022 [−0.017, +0.081] | no step |
| Conifer share | first | D90 | 7 | 0.020 | 0.066 | +0.022 | no step |
| Conifer share | Amendment 2 | old | 7 | 0.017 | 0.059 | +0.020 [−0.018, +0.079] | no step |
| Conifer share | Amendment 2 | D90 | 7 | 0.017 | 0.066 | +0.020 | no step |
| Conifer share | **Amendment 3** | **D90** | 7 | **0.017** | **0.066** | **+0.020 [−0.018, +0.078]** | **no step** |
| Broadleaf share | first | old | 7 | 0.020 | 0.059 | −0.022 [−0.081, +0.017] | no step |
| Broadleaf share | first | D90 | 7 | 0.020 | 0.066 | −0.022 | no step |
| Broadleaf share | Amendment 2 | old | 7 | 0.017 | 0.059 | −0.020 [−0.079, +0.018] | no step |
| Broadleaf share | Amendment 2 | D90 | 7 | 0.017 | 0.066 | −0.020 | no step |
| Broadleaf share | **Amendment 3** | **D90** | 7 | **0.017** | **0.066** | **−0.020 [−0.078, +0.018]** | **no step** |

The CI column is left as the mean only for the earlier D90 rows; the CI does not depend on the null,
and is the old row's above it.

Reading:
- **The *Pseudotsuga* verdict changes from artifact to no step**, in every build, at every scale.
  The reason is the null alone: B is 0.083 (0.088 in the first build) under the old threshold of
  0.072 and the matched threshold of 0.120. Nothing about the data changed. Under the old rule a
  median of 7 border steps was compared with a threshold read from 24 within-country rows, which the
  review measured as about 1 false alarm in 6 rather than 1 in 20.
- **Total cover stays a known artifact.** Its B and null were already over 25 transects each, so D90
  does not touch it, and D92 does not change a value on this strip.
- **Conifer and broadleaf stay no step**; their threshold rises from 0.059 to 0.066.
- **D91 moves no tested B at three decimals.** The full files differ only in US within-country
  figures (the largest, the US 95th-percentile within step, by 0.0041) and the signed mean.
- **Sensitivity** (scales 0.7 and 1.3, Amendment 3, D90): *Pseudotsuga* B 0.0831 against 0.1199 at
  both, no step; conifer B 0.0173 and 0.0176 against 0.0661, no step. Under the old null the first
  build's *Pseudotsuga* was an artifact at all three scales (B 0.0894, 0.0875, 0.0853), and still is
  by that rule; under D90 none is.
- Still only 7 of 25 transects carry shares on both sides. US cells with a share: 49,424; Canadian:
  56,306, the same at all three scales.

**Files.** `summary_d92_scale_{0.7,1.0,1.3}.json`, `master_d92_sha256.txt`,
`build_d92_scale_*.log.txt`, `transects_d92_d90.json`, `transects_d92.log.txt`,
`strip_d92_vs_a2.py.txt` and its `.out.txt`, `revert_results_a3.json`. The strips themselves are on
the flash drive as `master_d92_scale_*`; the first build's and Amendment 2's folders are kept beside
them.

**Tests and revert checks.**
- Suite before and after this session's work: **314 passed** both times (210 test functions by a
  grep of `def test_` over `tests/`). The only code change this session is the build script's
  `scale=` option, which no test covers. Ruff check and format are clean.
- Revert runner (`2026-10-06-t5-build/revert.py.txt`: saved-copy restore, `__pycache__` cleared,
  `PYTHONDONTWRITEBYTECODE=1`, refuses collection errors or a run where the interpreter does not
  see the edit): **29 checks, 27 bite, and the same 2 cannot by construction.** Every run was
  citable (no collection error, edit seen), and every file was restored byte-identical to HEAD.
- **The six Amendment 3 checks had not run before.** The runner as committed at `2927f22` stopped
  on its first check, because D91 had renamed the variable in the quadratic-term anchor
  (`dbh_in` to `d`). The anchor was updated at `27d253e`; no other check was changed. The six,
  each failing with a message specific to its edit:
  - review F4, US share against the cover total: `assert False` in
    `test_a_cell_mixing_split_and_unsplit_canopy_takes_its_share_from_the_split_part`;
  - D91, no diameter cap: `assert -8.3287 == 13.8041` and `assert 38.6385 == 26.4892`;
  - D91, non-positive widths not counted: `assert 0 == 1`;
  - D92, total back to the ten-class sum: `assert 0.0 == 40.0` and `assert 80.0 == 85.0`;
  - D90, US null over every transect: `assert 24 == 7`; Canadian: `assert 7 == 25`. Both are on the
    null's row count in the unequal-counts test, not on its false-alarm rate.
- The D88 check "canopy with no split counted as no genus" still fails at the regrid's guard before
  any share assertion, as section 8 recorded.

**Not checked or not verified.**
- That the Amendment 3 tests were written before the code and failed first: that was the earlier
  session's work (`3cde1e2`, `d235993`), and its red runs are not recorded in the repository. This
  session only confirmed, by revert, that each test fails without its change.
- The capped and non-positive counts at scales 0.7 and 1.3 (see above).
- Spatial correlation's effect on the matched null's false-alarm rate (the review's caveat stands).

## Correction, 2026-10-06, appended by the D27 to D29 coder session (review notes A1 to A3)

Appended under D41 by the coder session on branch `dq-tables-d27-d29`, on the Forager planner's
instruction to fold in the T5 Amendment 3 review's record findings A1 to A3
(`2026-10-06-t5-amendment-3-review.md`, "Findings"). Nothing above this section is edited. Each figure
below was read in this session from the committed files named; none is copied from the review alone.

**A1. The first build's *Pseudotsuga* B is 0.087, not 0.088.** The value in
`2026-10-06-t5-amendment-3/transects_tree_list_d90.json` (scale 1.0, `border_median_abs`) is
0.08747893772670068. Rounded to three places that is 0.087. Section 9 gives 0.088 in its table (the
first build's "old" and "D90" rows, lines 330 and 331) and in the Reading bullet (line 351), which also
disagrees with the section's own sensitivity bullet (0.0875, line 362). Section 8's table (line 219)
has the same slip. No verdict changes: 0.087 is above the old threshold 0.072 (artifact under the old
null) and below the D90 threshold 0.120 (no step), as with 0.088.

**A2. The two F5 slips that had no note.** The T5 review (`2026-10-06-t5-review.md`, F5) named five.
The Pilz page numbers and the rulings tag were corrected before; 0.088 is A1 above. The other two:
- **Line 204, "2,219 of 4,969,059 forest pixels".** That count is the whole cut, including 8,347
  forest pixels north of 49 N. South of 49 N it is **2,209 of 4,960,712**, as the review observed
  (`2026-10-06-t5-review.md:151-153`). Not re-measured in this session; the strip is on the flash
  drive, which this session did not read.
- **Register timing.** The TreeMap register row (`DATA_REGISTER.md:27`, commit `88760cd`, 05:19:54
  local) landed after TreeMap was first used: probed at 04:46 and built by 05:18. The licence itself
  was recorded in D84 at 04:18, before the download finished, so no data was used without a recorded
  licence. Only the register row came late. Times as the review gives them
  (`2026-10-06-t5-review.md:159-162`); the commit time of `88760cd`, 2026-10-06 05:19:54 −0700, was re-read here and matches.

**A3. The interval does depend on the null, a little.** Line 346-347 says "the CI does not depend on
the null, and is the old row's above it". `seam.py:108-109` draws the bootstrap from the same
generator after the null's draws, so a null over a different number of rows leaves the generator in
a different state and moves the interval. The earlier D90 rows' intervals, read from the committed
files (scale 1.0, `border_mean_signed_ci95`):

| Variable | Build | Old null [95% CI] (section 9) | D90 null [95% CI] |
| --- | --- | --- | --- |
| *Pseudotsuga* share | first (tree list) | [−0.021, +0.197] | [−0.0196, +0.1939] |
| *Pseudotsuga* share | Amendment 2 (CANOPYPCT) | [−0.014, +0.192] | [−0.0121, +0.1889] |
| Conifer share | first | [−0.017, +0.081] | [−0.0174, +0.0815] |
| Conifer share | Amendment 2 | [−0.018, +0.079] | [−0.0179, +0.0787] |
| Broadleaf share | first | [−0.081, +0.017] | [−0.0815, +0.0174] |
| Broadleaf share | Amendment 2 | [−0.079, +0.018] | [−0.0787, +0.0179] |
| Total cover (pts) | first | [−6.8, +7.8] | [−6.76, +7.82] |
| Total cover (pts) | Amendment 2 | [−14.1, +1.8] | [−14.13, +1.77] |

Files: `transects_tree_list_d90.json` (first build) and `transects_treemap_canopy_d90.json`
(Amendment 2), both in `2026-10-06-t5-amendment-3/`. Total cover's null was already over the same 25
transects as B, so D90 does not change its interval. The interval is not part of any verdict, so no
verdict changes.
