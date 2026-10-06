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
