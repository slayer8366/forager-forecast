# T7 re-fit, Phase 1: road band as access, condition 3, specimen records, P10b wired, trial run

Hazel Cairnwright (coder), 2026-10-17. Dispatch: `docs/dispatch/2026-10-17-t7-refit.md` (branch `t7-strengthen-plan`, c608b8c). Forager RECORD: intent -1183; the owner's go for Phase 1 -1184 ("Yes, start the coder on phase 1 of the re-fit"). Branch `t7-refit` from t7-build `5c1a9df` (checked against the remote first), draft PR #5 into t7-build, unmerged.

**Phase 2 has not run. No full fit has run.** The trial run's figures prove that the plumbing works, and nothing more. They are not reported as results.

Evidence is in `docs/audits/2026-10-17-t7-refit-phase1/`:
- `tests_over_stubs.txt`
- `revert_checks.py` and `.txt`
- `table/`
- `smoke/`
- `specimens/`
- `access_by_band.py` and `.json`
- `timing/`

## What was built

- **The table** (`t7_fit.py table --access`). It holds the three access bands, read through `predictors.read_tile`'s access path. The access file is checked by sha256 against part B's manifest (`7748fe0b…`).
  - The table was rebuilt into `t7/refit/`.
  - Every existing array equals the judged run's table: cell ids, features, weather keys, blocks, input hashes, codes and per-block counts.
  - Across the 6,967,248 eligible cells, `dist_road_m` has no NaN. `dist_trail_m` and `dist_any_m` are NaN on 218,175 cells, the two forests (D150), and are never filled.
- **The road band in every model that carries effort.** That covers A, B, base, the add-ones and full (`model.ladder_with_access`). It is never a candidate.
  - Access joins effort's interaction group (`lgb_params`).
  - Access is held on the map at the median of `dist_road_m` over the background draw (`predict_held`, `map_columns`).
  - Access is excluded from the area of applicability (`habitat_features`, `area_of_applicability`).
  - P6's check is run for access too, at its quartiles over the background draw, with effort held.
  - The monotone direction must be passed (`--access-monotone`). A model with access and no direction refuses to build.
- **Side runs** reuse the main fit's per-block configurations (P7 point 9). They are the M2 side run, the licence track, the comparison group, the saprotroph main and side runs, and the trails side check (`dist_any_m` in place of `dist_road_m`, NaN kept).
- **Condition 3** (`metrics.host_specific_contrast`):
  - each group's gain is its full model's held-out AUC minus its model A's;
  - the contrast is the mycorrhizal gain minus the saprotroph gain;
  - the interval comes from one resampling of whole level III blocks per draw, applied to both groups (seed 20260918);
  - it is reported over all blocks, and over the shared forested blocks with no verdict.
- **P10b in `fit_report.json`** (`p10b_figures`). The report carries the verdict and each condition's figure, with P10 (D140) beside them marked "no verdict".
- **The map's output folder** is now named on the command line (`--out`), and the judged run's folders are refused.
- **Specimens** (`t7/specimens.py`, `scripts/t7_specimens.py`): the predicate, the filters, the archive checks and the counts.

## Tests first, revert checks, suite

- **Tests over stubs.** 19 tests in `tests/test_t7_refit.py` all failed over the stubs (`tests_over_stubs.txt`):
  - 17 on `NotImplementedError`;
  - the interaction-group test on its assertion (`[[0, 1, 3], [2]] != [[0, 1], [2, 3]]`);
  - the refusal test on "DID NOT RAISE".
- **One test-data fix, disclosed.** The map test's synthetic rows lacked the cover-share columns that every table carries. I fixed that test data after the first implementation run. It was a fault in the test data, not in the rule, and revert r9 shows the fixed test bites.
- **Revert checks.** All nine reverts failed, each on the test or tests its own edit can break, with an edit-specific message (`revert_checks.txt`):

  | revert | what it undid |
  |---|---|
  | r1 | access put back among the habitat inputs' group |
  | r2 | A without access |
  | r3 | access back in the area of applicability |
  | r4 | each group drawing its own resample |
  | r5 | no dataset licence filter |
  | r6 | the uncertainty limit raised to 5 km |
  | r7 | the pending condition 4 no longer guarding the verdict |
  | r8 | the judged folders no longer refused |
  | r9 | access on the map not held |

  How the runner worked:
  - each revert ran in its own scratch worktree and local branch, deleted afterwards;
  - the compile and import log was read first, and the code imported was confirmed to be the scratch tree's;
  - each file was restored from a saved copy, never from git, and the forward text was confirmed present.

  `ruff format` reformatted the runner after its first run. I re-ran the committed version, and its results are identical except for object addresses.
- **Suite.** 727 tests, 0 failures, 0 errors, 0 skipped, read from the JUnit XML. That is 708 at the base plus my 19. ruff check and format are clean.
- **Environmental issue.** The suite ran with `--basetemp` on `/mnt/work`, because `/tmp` (tmpfs) has 1.5 GB free. With the default temp folder, `test_t6b_host_genera.py`'s 2 GB free-space guard fails four tests. That is environmental, and nothing was changed for it.

## The specimen download

- **Requests.** One request, key `0032050-260928105237408`, DOI **10.15468/dl.5mvzg2**. The account is D26's: its download `0012112-…` is in that account's list. The account now lists exactly one download made today.
- **Fetch.** One fetch. The first wait stopped on a transient DNS failure while reading the status, before any file was fetched. The poll now retries status reads only, and the second wait fetched the file.
- **The file.** 122,622,731 bytes, sha256 `28efb80e2d1e662c5dd389308ef608dd4a5760c60ca1178237249bb76d8634ad`. It is read-only under `t7/specimens/`.
- **Checked against the aggregator.** The size, 256,778 records and 212 datasets all equal the aggregator's record.
- **Predicate:**
  - kingdom Fungi (key 5);
  - `PRESERVED_SPECIMEN`;
  - has coordinate;
  - no geospatial issue;
  - the box.

  The taxon filter is my call (see the calls section).
- **Licences.** By dataset: 94 CC BY, 67 CC0 and 51 BY-NC, which are out. The aggregator gives the download as a whole BY-NC, its most restrictive dataset.
- **Outcomes:**

  | outcome | records |
  |---|---:|
  | dataset licence not CC0 or CC BY | 75,922 |
  | no stated uncertainty | 63,256 |
  | uncertainty over 1 km | 86,196 |
  | not in the main run | 25,378 |
  | **kept** | **6,026** |

  The kept set is CC0 1,650 and CC BY 4,376. 4,338 of the kept records are from the University of Washington Herbarium. The kept file's sha256 is `c9e8c66f…`.
- **Counts of kept records** (`specimens/specimen_counts.json`):
  - **By block:**

    | block | records |
    |---|---:|
    | Puget Lowland | 1,631 |
    | Coastal Range | 1,244 |
    | Cascades | 950 |
    | North Cascades | 841 |
    | Columbia Mountains | 258 |
    | Klamath | 188 |
    | Idaho Batholith | 140 |
    | Blue Mountains | 116 |
    | Willamette | 115 |
    | Eastern Cascades | 101 |
    | Columbia Plateau | 99 |
    | Middle Rockies | 89 |
    | Canadian Rockies | 58 |
    | Wasatch/Uinta | 28 |
    | 7.1.5 (Canada) | 27 |
    | others | 23 |
    | outside every block | 118 |

  - **By decade:** the 1990s have the most (1,208), then the 1970s (1,053) and the 1960s (859). 2000 on has 712; 100 have no year.
  - **By uncertainty:**

    | uncertainty | records |
    |---|---:|
    | up to 100 m | 226 |
    | 100 to 250 m | 443 |
    | 250 to 500 m | 2,216 |
    | 500 to 1,000 m | 3,141 |

  - **By P4 cell code:** 1 (in): 4,031; 4 (no shares): 1,053; 5 (no pH): 749; 0: 126; 6: 35; 3 (Canada): 32.
  - **Interior sub-box:** 751 records. The searches report's "about 2,620" counted all Agaricomycetes at 1 km, with every licence. 390 of the 751 are in cells with code 1, and 340 in cells with code 4.
  - **Effort frame:** 5,744 records have a weather cell in T6's frame, and 282 do not.
- A DATA_REGISTER row is added.

## The trial run (`--smoke`, `--access-monotone 0`; plumbing only)

- **Setup.**
  - Work dir `t7/refit-smoke/`, holding symlinks to the re-fit table.
  - Outputs in `t7/refit-smoke/outputs/`.
  - It took 1,330 s, with a peak of 2,676 MB, under the memory cap beside t6b-night.
  - The log is `smoke/fit_log.txt`.
- **Every piece ran and wrote its section:**
  - the ladder with access in every model;
  - all six side runs, including the trails check, which had 1,362 NaN access rows, kept;
  - condition 3, with **13 shared forested blocks**, which matches -1173;
  - P10b, with condition 4 shown as "pending: data exist, scoring not yet ruled";
  - P10 beside it, no verdict;
  - P6 for effort and for access, ranking the same at both;
  - the area of applicability excluding effort and access;
  - the map and the manifest, labelled "relative habitat, PNW pilot, not shown".
- The access credit line is in the attribution.
- The mask image was not opened.

## Phase 2 estimate

- **Timing step** (`timing/timing.json`): the base model with access, block 112, 505,126 training points, 80 inner fits plus the final fit, **711.5 s**.
  - The judged run's fold after its weight fix was about 630 s, so this one takes about 13% longer.
  - The script's projection is 21.1 h. Its formula overestimated last time: it gave 18.7 h, and the run took 14.2 h.
- **Estimate.** Scaling the judged run's actual 14.2 h by 1.13, and adding three more side runs (about 30 min) and condition 3's bootstraps (a few minutes), gives **about 16.5 h, within 16 to 21 h**, at 4 threads beside t6b. This is inferred.
- **Trails side check:** about 3 × 24 untuned fits × 8.8 s, roughly 11 minutes, plus its intervals; about 20 to 25 minutes in all. That is under the hour, so it is not a stop.
- **Disk:** 4.9 GB free on `/mnt/work` now. The re-fit work dir holds 653 MB, and Phase 2 adds perhaps 100 MB.

## Mechanism prediction for Phase 2 (written before Phase 2)

- **Model A** (effort and access) rises clearly.
  - Within weather cells, presences sit nearer roads than background: the median is nearer in 1,366 cells and farther in 494 for the mycorrhizal group (`access_by_band.json`, descriptive).
  - Effort at 0.1° cannot see this; the road band can.
  - I expect A's pooled AUC to rise by more than the habitat bands added last time (+0.004), and its within-cell AUC (0.494 last time) to rise most of all.
- **Full minus A** shrinks.
  - Part of the habitat gain last time was probably access-correlated forest, as the fit report inferred in item 4. That part moves into A.
  - Condition 2 (within-cell full minus A, +0.054 last time) shrinks the most, because within one cell the road band now ranks pairs that only habitat could rank before.
  - I expect condition 1 (full minus B, block-clustered) to stay inside zero, as on 2026-10-16 (inferred).
- **Condition 3** is hard to call.
  - The saprotroph group shows an even steeper road gradient (ratio 2.11 under 50 m, 0.10 over 5 km), against 1.92 and 0.19 for the mycorrhizal group. So access should absorb more of that group's former habitat gain.
  - That would raise the contrast, but its interval spans 13 to 24 blocks with four dominant ones, so I expect it to be wide.
- **The map.**
  - Access is held at one value, so the ranking is habitat only.
  - The habitat ranking should shift away from the lowland and urban-edge forest near roads, where last time habitat and access were confounded, and toward forest far from roads.
  - The area of applicability is unchanged in kind.

## Open items (evidence and options; none is picked)

### 1. The access band's monotone direction

The trial ran at 0 for plumbing only. That is not a choice.

- **Evidence** (`access_by_band.json`, descriptive; no model fitted):
  - **Mycorrhizal group:** the presence-to-background weight ratio by road distance is 1.92 (under 50 m), 1.54, 1.11, 0.83, 0.45 (0.5 to 1 km), 0.49 (1 to 2 km), 0.41 and 0.19 (over 5 km). It falls throughout, with one small rise at 1 to 2 km.
  - **Saprotroph group:** 2.11 down to 0.10, falling throughout.
  - ***Laetiporus*:** it falls to 0.62 at 0.5 to 1 km, then is flat to rising, about 0.9 to 1.0, beyond 1 km.
- **Options:**
  - **(a) −1, falling with distance.**
    - It matches "access like effort": more reports near roads.
    - It stops the access term from soaking up a far-from-road habitat preference. Under the constraint, any rise with distance has to come through habitat, so habitat keeps credit for remote forest.
    - Cost: the 1 to 2 km bump, and the *Laetiporus* shape, are flattened.
  - **(b) 0, unconstrained.**
    - It fits whatever shape the data has.
    - Risk: within effort's group, the access term can learn a rise far from roads that is really habitat, such as remote old forest. The map holds access constant, so that signal would be taken out of the habitat ranking, not kept in it.
  - **(c) +1.** It contradicts every group's data above, and I list it for completeness.

### 2. Condition 4's scoring

These are owner-level choices, and nothing for them is built.

- **(i) How a 1 km record meets a 250 m map:**
  - (a) the map's value at the record's own cell;
  - (b) the mean of the map over the cells within its stated uncertainty;
  - (c) the maximum over that disc.

  Option (a) is simplest but treats 1 km points as exact: 3,141 of the 6,026 kept records are 0.5 to 1 km. Option (b) matches the uncertainty honestly, but smooths. Option (c) favours the map, being optimistic for any wide disc.
- **(ii) Background.**
  - (a) The fit's own background draw. It is effort-frame cells, while specimens are not from platform effort.
  - (b) A new uniform draw of eligible cells over the same blocks. This tests habitat against everywhere.
  - (c) A draw matched to the specimens' access distribution. Herbarium collecting is road- and station-biased, so (a) and (b) would reward the map for any road correlation the map retains. (c) costs a decision on how to match.

  Whatever the choice, only cells with code 1 inside the area of applicability have a map value. 4,031 of the kept records are in code 1 cells; 1,995 are not and would drop.
- **(iii) Which records.**
  - (a) The whole box: 6,026, of which 4,031 are scorable. It is dominated by the University of Washington Herbarium and the western lowlands.
  - (b) The interior sub-box only: 751, of which 390 are in code 1 cells. This answers the searches report's question, the interior, with a small sample.
  - (c) Both, one with a verdict and one beside it.

  Age is a further choice: most records predate the tree layers by decades (only 712 are from 2000 on). A year cut is possible but was not asked for.

### 3. Condition 4's state in the verdict

This is a call beyond the dispatch, for ruling. The specimens exist, so under D145 condition 4 is required. Until its scoring is ruled, I made the report's verdict never read "pass": it reads "incomplete: conditions 1 to 3 pass; condition 4 not yet evaluated". `metrics.p10b` itself is unchanged.

- **Option:** keep this.
- **Option:** treat condition 4 as absent until ruled, which is `p10b`'s None meaning "no usable data". I'd advise against this: it would read "pass" on conditions 1 to 3 alone.

## Confirmed, inferred, not determined

- **Confirmed (read or run):**
  - the base at 5c1a9df on the remote;
  - the newest decision row is D155;
  - the fit read no access before;
  - effort was the only held feature, monotone +1 and in its own group (`model.py` at base, lines 28 to 47);
  - `metrics.p10b` was wired into no run;
  - the saprotroph main run has 9,591 entering presences (trial log);
  - there are 13 shared forested blocks;
  - D26's account;
  - the access file's hash;
  - the new table equals the judged one;
  - the download equals the aggregator's record.
- **Inferred:** the Phase 2 time; the mechanism prediction; what each open option would do.
- **Not determined:**
  - whether LightGBM's NaN handling in the trails check biases that run;
  - the access gradient's shape inside blocks rather than pooled;
  - how many kept specimens duplicate a platform record (none by basis, D26 being human observations; vouchers unknown).

## Premises that were wrong

- **The map's output folder.** The dispatch's Phase 2 assumes the fit writes outside the judged folders. The script named the map folder `t7/pnw-<UTC date>`, so a non-smoke run on 2026-10-17 UTC would have written into the judged run's `t7/pnw-2026-10-17/`. It is now `--out`, guarded. Phase 2's map folder needs naming; I'd propose `t7/refit/outputs/`.
- **Disk.** It was 6.4 GB free at the dispatch. It is 4.9 GB now, after the re-fit table (653 MB), the download (118 MB) and the trial (76 MB). That is above the 2 GB stop.

## Calls beyond the dispatch (for the planner to accept or reject)

1. **The taxon filter: kingdom Fungi** (256,778 records, lichens included), filtered locally to the main-run genera through the same `Join`. A class or phylum filter could miss list genera (the list spans Pezizomycetes, Eurotiomycetes, Leotiomycetes and Agaricomycetes).
2. **Both dataset and record licence** must be CC0 or CC BY. The dispatch named the dataset licence.
3. **The table was rebuilt into `t7/refit/` in Phase 1**, with all three access bands, rather than copied in Phase 2. The trial ran on symlinks to it.
4. **The `fit` command is now the re-fit.** It needs an access table and a direction. The judged run's code stays at 5c1a9df.
5. **The map's folder is `--out`,** with the judged folders refused and an existing folder refused if it holds files.
6. **The verdict guard for a pending condition 4** (open item 3).
7. **Every side run carries the road band.** That includes the licence track and *Laetiporus*, since they reuse the main fit's configurations. The trails check carries `dist_any_m`.
8. **Condition 3's blocks** are drawn from the union of both groups' blocks (24, the shared background). The 13-block figure subsets both groups to the forested blocks with 30 or more presences in each.
9. **Model names** keep the keys "A: effort only" and "B: forest only", for cache and report compatibility, though A is now effort and access. `fit_report.json` lists every model's features under `model_features`.
10. **Descriptive access evidence** was read from the training table (no fit) to support open item 1.
11. **The trial ran at monotone 0**, and the timing step also at 0, for plumbing and cost only.
12. **Decision rows.** None was written. Rows from D156 wait for the rulings on the open items. **The audits index needs a row** for this report and its evidence; the planner owns it.

## Not checked

- No full fit; Phase 2 has not run.
- The mask image and rasters were not opened.
- The DWCA's per-record `license` was trusted as the aggregator's interpretation, beside each dataset's EML licence.
- CI was not run on the branch.
- Determinism across thread counts.
- Whether the 1 to 2 km bump in the mycorrhizal ratio is a real shape or noise; no interval was computed.
