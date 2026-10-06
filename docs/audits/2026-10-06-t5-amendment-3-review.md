# Review: T5 Amendment 3 (D90 to D92, Forager RECORD -594), a short follow-up under the standing protocol (D18)

- **Reviewer:** an independent session that did not build T5 or the amendment. I read the repository
  and the stored outputs, not the builder's chat.
- **Base:** `origin/t5-host-trees` at `0c0c726`, confirmed after `git fetch origin`. Scope is the
  commits after `02d4f19` that implement Amendment 3: `3056e9d` (merge of the first review) through
  `0c0c726`.
- **Branch:** `t5-review-a3`, a worktree cut from `0c0c726`, with `core.hooksPath` set to `.githooks`.
- **The amendment as ruled:** Forager `RECORD.md` entry `2026-09-28-594`, read on
  `origin/records-after-173`. The dispatch is filed as
  `docs/dispatch/2026-10-06-t5-host-trees-amendment-3.md`.
- **Machine limits:** this laptop has crashed twice from running out of memory, and an app Gradle job
  ran beside this review. So no strip was rebuilt. I re-ran only light steps (each under 1.1 GB):
  the suite, ruff, the transects from the stored strips, the SCANFI comparison, and two reviewer
  revert runs. I checked `free -h` before each step. The flash drive was mounted, and I read it only.
- **Conventions:** "observed" means I ran it here. "Read" means I read it in a file at a line.
  "Inferred" is labelled where it appears. Evidence files are in `2026-10-06-t5-amendment-3-review/`.

## Verdict

**The amendment holds.** All three of the owner's answers are built as ruled, and nothing else was
tuned. The verdict table in section 9 matches the stored outputs on every verdict, B and threshold,
with one exception: a carried-over rounding slip. The findings are record-level and change no
result:
- **A1.** Section 9 repeats F5's 0.088 instead of correcting it.
- **A2.** Three of the five F5 slips have no correcting note, although RECORD -594 says the F5 slips
  are corrected by appended notes.
- **A3.** Section 9 says the bootstrap interval does not depend on the null. It does, slightly.
- **A4.** No test read D92's real file name. I closed that gap with one added test, which bites.

Under the matched null (D90), the *Pseudotsuga* share is **no step** in every build and at every scale
(B 0.083 against 0.120 at scale 1.0). Total cover stays a **known artifact** (B 14.97 against 14.16).
Conifer and broadleaf are **no step**.

## The items checked in particular

**1. D90 builds the null from exactly the border step's transects. Holds.**
- `seam.py:93` sets `ok = np.isfinite(border)`. `seam.py:100-101` index both within arrays by that
  same `ok`, and the null is drawn from those rows. B is taken over the same `ok`.
- Observed on the stored strips (`rerun_transects_a3.out.txt`):
  - for every share, `null_rows_us/ca = 7/7` with `n = 7`;
  - for total cover, `25/25` with `n = 25`;
  - under the filed rule, the same samples give 23/24 rows for the shares.
- **The test fails under the old rule with unequal counts.** It is
  `test_with_7_border_steps_against_24_within_rows_the_verdict_still_fires_rarely`
  (`tests/test_seam.py:98-114`). My revert put both nulls back to every transect at once, which is
  the filed rule. It fails on the **false-alarm rate**: `assert (28 / 200) <= 0.1`
  (`revert_a3_review_results.json`, check 1).
- The builder's two reverts each changed one side only. They failed only on the row-count assertion
  at `:114`, because the other side's matched threshold still sets the maximum. Mine shows that the
  rate assertion at `:113` bites too.
- The margin is 0.14 against 0.10 over 200 seeded trials. The test is deterministic, so this is not
  a flake risk. It is narrower than the review's 0.165, measured over 400 trials.
- **A small dead branch.** `seam.py:100-101` fall back to the unmatched null when the within array is
  1-D (`... if wus.ndim == 2 else wus`). The only production caller, `seam.py:169`, passes 2-D arrays,
  and so does every test caller (`tests/test_seam.py:74, 94, 111, 119`). So this branch never runs.
  Nothing to fix now. If a 1-D caller ever appears, it would silently get the old rule.

**2. The cap uses each species' own Table 1 maximum, and no tree is dropped. Holds.**
- **The table against the paper.** All 53 entries of `BECHTOLD_2004_DMAX` (`crown_cover.py:102-110`)
  equal the stem-diameter maximum in Bechtold 2004 Table 1 (`dmax_vs_table1.out.txt`: 0 mismatches,
  and the Table 1 n of each row matches `BECHTOLD_2004_N` for the same code).
  - The source is the PDF text the first review read (`pdftotext`, PDF sha256 `68b67c0e…909b`).
  - The 19 entries the first review had typed independently also agree.
  - My first pass matched rows by n alone. It mis-paired the three n that occur twice (28, 37 and
    164). That was my script's error, not the code's. The committed script matches rows by Table 1's
    code order, with n as a cross-check.
- **Which species' maximum.** `crown_cover.py:190` caps at the maximum of `used`, the species whose
  coefficients are applied. For a surrogate that is the coefficient species: an Oregon ash takes
  quaking aspen's 19.9 in.
  - This is the builder's reading of "the species' … fitted range" in the planner's text. A surrogate
    has no Table 1 row of its own, and D91 states the reading in words.
  - It is consistent with the owner's "Cap at the fitted size". I flag it only because it is a
    reading.
  - My revert read the cap from the tree's own species instead. It bites:
    `test_a_surrogate_is_capped_at_its_coefficients_species_range` fails with
    `assert 38.6385 == 26.48921`.
- **No tree is dropped.**
  - `crown_cover.py:236` counts a non-positive width before it skips the tree.
  - After the cap, no tree of 5 in or more can reach that branch. Equation 3's minimum over
    [5.0 in, Table 1 max] is positive for all 53 coefficient sets; the smallest is 3.30 ft, for
    lodgepole pine (`width_floor.out.txt`). So the counter is a guard, reachable only through the
    monkeypatched test.
  - The cut's request record on the drive says `capped_trees` 1,516 and `nonpositive_width_trees` 0,
    and all three summaries carry the same figures. The first review's estimate, about 1,500, covered
    19 species.
  - My revert stopped the capped trees from being counted. It bites:
    `test_a_diameter_beyond_the_fitted_range_takes_the_width_at_the_largest_fitted_diameter`,
    `assert 0 == 1`.

**3. D92 reads the right SCANFI layer, and the request is recorded. Holds, with one test added (A4).**
- **The layer.** `scanfi_url` (`t5_layer.py:126-127`) maps `att_closure` to
  `SCANFI_att_closure_2025_v2_20260119.tif`. That is the name the first review read in the v2 readme
  as "Total crown closure (%)" (`2026-10-06-t5-review.md`, F3). I did not re-read the readme: that
  would be a fetch.
- **The request.** `docs/pulls/t5-scanfi-v2-2025-total-strip.request.json` records that URL, its
  ETag, Last-Modified, the pixel window and the sha256.
  - It equals the drive's `scanfi_total_request.json` byte for byte (observed).
  - The drive's `scanfi_att_closure.tif` hashes to the recorded `ceb2d79f…0402`.
  - Its pixel window equals all ten class windows, and every class file matches its own recorded
    sha256.
- **Where the total is used.** `_scanfi_layers` (`t5_layer.py:501`) takes the closure layer as the
  cover. Shares keep the ten-class split against its sum, as D92 says.
- **The sum against the total, independently.** I ran my own comparison on the whole window, not
  only the Canadian side:
  - 22,001,746 pixels;
  - identical no-data masks;
  - the sum equals the total on all 10,976,781 compared pixels (difference 0, mean 35.83);
  - this confirms `scanfi_sum_vs_total.out.txt`, which restricts to centres at 49 N and north
    (10,971,284).
  - So on this strip D92 changes no value, and the "closure with no class cover" path at
    `t5_layer.py:501` meets 0 real pixels. Only the fixture exercises it
    (`tests/test_t5_layer.py:311`).
- **Two labels in the total-only request are wrong** (`t5_layer.py:383, 388`). It says
  `"dataset": "SCANFI v2, species crown closure (%)"` and lists all ten `classes`, although it fetched
  only the total layer. The `layers` array and `total_layer` are right. Cosmetic; not changed.

**4. The verdict table in section 9 matches the stored outputs. Holds on every verdict, B and
threshold, except A1 and A3.**
- **The strips.** The three `master_d92_scale_*` strips on the drive hash to
  `master_d92_sha256.txt` (6 of 6).
- **The transects.** I re-ran them under HEAD's code on all nine stored strips (three builds, three
  scales). They reproduce `transects_d92_d90.json`, `transects_tree_list_d90.json` and
  `transects_treemap_canopy_d90.json` field for field, and the drive's copies equal the committed
  ones (`rerun_transects_a3.out.txt`).
- **The old-rule rows.** I re-computed them from the same samples (`rerun_transects_a3.out.txt`
  section 3): thresholds 0.07178 for *Pseudotsuga*, 0.05898 for conifer and broadleaf, and 23/24 rows.
  They match.
- **The sensitivity bullet.** The first build is an artifact at all three scales under the old null,
  and nothing is under D90 (`old_rule_scales.out.txt`). It matches.
- **D91 moves no tested B at three decimals.** Observed: *Pseudotsuga* 0.08313 in both the
  Amendment 2 build and the D92 build.
- **Exceptions:** A1 (the first-build *Pseudotsuga* B) and A3 (the claim about the interval).

**5. The decision rows quote the owner verbatim against RECORD -594. Holds.**
- The quotes in D90, D91 and D92 (`docs/planning/DECISIONS.md:8-10`) are "Fix the rule, record both
  (Recommended)", "Cap at the fitted size (Recommended)" and "Use SCANFI's own total (Recommended)".
  RECORD -594 has the same three strings.
- The IDs fit -594's allocation (D90 to D92; D93 and D94 spare). Main `fe0993a` holds D100 and
  nothing between D83 and D99, so there is no ID collision.

**6. Nothing was tuned beyond the three changes. Holds.**
- The `src/` diff `3056e9d..0c0c726` touches `seam.py` (D90), `crown_cover.py` (D91 and its
  counters) and `t5_layer.py` (D92, the counters passed through, the rulings tag F5 asked for, and
  `fetch_scanfi`'s new `layers` parameter).
- None of these changed: seed, quantile, windows, transect longitudes, surrogate scales, the 10%
  threshold, the half-area rule, the strip, or the surrogate rule.
- `scripts/t5_build.py` gains the build names and a `scale=` option, which the report says no test
  covers.

## Protocol checks

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Terms | Holds | No "probability", "calibrated" or relative-habitat percent in the diff (grep) |
| 2 | Decisions | Holds | The code matches D90 to D92 as worded. D91's surrogate reading is stated in the row (item 2) |
| 3 | Fixed choices | Holds | Item 6. The verdict rule changed by the owner's ruling, not after a result was tuned, and old and new are both recorded |
| 4 | Scope | Holds | Only the three changes, their counters, the F5 rulings tag and a build-script option |
| 5 | Record | **Gap (A1, A2)** | D90 to D92 added as rows. Index row, TASKS and START_HERE updated. The verify report is corrected by appended section 8, not edited. Three F5 slips have no note |
| 6 | Data hygiene | Holds | No data in git (the large-file hook passed on my commit). The total layer is SCANFI v2 under the licence already registered (`DATA_REGISTER.md:14`); no new source |
| 7 | Claims carry evidence | Holds, with A3 | Section 9 cites files throughout and marks what was not checked |
| 8 | Revert checks | Holds | Below |
| 9 | Headline numbers re-run | Holds | Item 4, from the stored strips. The strips themselves were not rebuilt (machine limit) |
| 10 | Gaps | Listed | Below |

### Revert checks

These were observed with my strict runner (`revert_a3_review.py.txt`).
- **How the runner works:**
  - it restores from a copy it saved, never from git;
  - it deletes `__pycache__` and sets `PYTHONDONTWRITEBYTECODE=1`;
  - it gives each run a fresh JUnit XML;
  - it refuses any run with collection errors, and any run where a separate interpreter does not see
    the edit in the imported source.
- **Every run was citable,** and every file was restored byte-identical to its saved copy and to HEAD.

| Edit | Result | Message |
| --- | --- | --- |
| D90: both nulls over every transect (the filed rule) | Bites | `assert (28 / 200) <= 0.1` in the unequal-counts test |
| D91: cap read from the tree's own species | Bites | `assert 38.6385 == 26.48921` in the surrogate-cap test |
| D91: capped trees not counted | Bites | `assert 0 == 1` in the cap test |
| D92: the total layer's URL names another file, before my test | **Did not bite** | 16 passed |
| The same, after my test (`revert_a3_review_2_results.json`) | Bites | `assert False` in `test_scanfis_total_is_read_from_its_own_published_file` |

- Each failure is one this edit can cause.
- The D90 revert's message is on the rate, and no other edit's message is.
- I did not re-run the builder's 29-check runner. I read `revert_results_a3.json`: 29 checks, 27 bite.
  Its six Amendment 3 messages are each specific to their edit, as section 9 says.

## Findings

**A1. Section 9 repeats F5's 0.088 instead of correcting it (record).**
- The first-build *Pseudotsuga* B is 0.08748, which is 0.087 (observed:
  `transects_tree_list_d90.json`; old rule, `rerun_transects_a3.out.txt`).
- Section 9 gives 0.088 in two table rows and in the Reading bullet
  (`2026-10-06-t5-completion-report.md:330, 331, 351`). That is the slip F5 named in section 8's
  table (`:219`).
- The same section's sensitivity bullet gives 0.0875 (`:362`), so the section disagrees with itself.
- No verdict changes.
- **Proposed:** a dated note appended after section 9. I did not edit the report.

**A2. Three of F5's five slips have no correcting note (record).**
- RECORD -594: "The F5 slips are corrected by appended notes."
- Two were corrected:
  - the Pilz page numbers, by verify report section 8;
  - the rulings tag, in code (`t5_layer.py:112`, test at `tests/test_t5_layer.py:449-451`).
- Three have no note:
  - 0.088 (now A1);
  - "2,219 of 4,969,059 forest pixels" (`completion report:204`; 2,209 of 4,960,712 south of 49 N,
    per the review);
  - the register-timing drift (`DATA_REGISTER.md:27`).
- Neither the completion report nor section 9's "Not checked" mentions them.
- **Proposed:** one appended note covering all three.

**A3. "The CI does not depend on the null" is not quite right (record).**
- `seam.py:108-109` draw the bootstrap from the same generator, after the null's draws. So a null with a
  different row count leaves the generator in a different state, and the interval moves.
- Observed:
  - first build, old [−0.021, +0.197] against D90 [−0.0196, +0.1939];
  - Amendment 2, old [−0.014, +0.192] against D90 [−0.0121, +0.1889].
- So the blank interval cells for the earlier D90 rows are not "the old row's above it"
  (`completion report:346-347`).
- The interval is not part of the verdict, so no verdict changes.
- **Proposed:** an appended note with the D90 intervals from the committed JSON files.

**A4. No test read D92's real file name. Closed here.**
- Every fetch test passes its own `source_for`, so a wrong total-layer name passed all 16 tests in
  `test_t5_layer.py` (revert above).
- Under the protocol's small-gap rule I added `test_scanfis_total_is_read_from_its_own_published_file`
  (`tests/test_t5_layer.py:246-251`). It pins the readme's file name, and it bites.
- The suite went from 314 passed (observed at `0c0c726`) to 315 passed.

## Gaps (check 10) and what I did not check

- **Not rebuilt:** no strip, and not the TreeMap cut. The memory limit ruled them out. The strips'
  hashes, the transects and the summaries' counts were checked against the drive; the build itself
  was not reproduced.
- **The 1,516 capped trees** were not recounted from the tree table. Only the request record and the
  review's 19-species estimate were compared.
- **The readme was not re-read.** The meaning of `att_closure` as "Total crown closure (%)" rests on
  the first review's reading of it, plus the file name.
- **Test order.** Whether the Amendment 3 tests were red before the code is not recorded; section 9
  says so. The reverts show that each test bites now.
- **Spatial correlation.** Its effect on the matched null's false-alarm rate is still unmeasured, as
  the first review's caveat said.
- **D92's effect elsewhere.** It changes nothing on this strip. Whether SCANFI's classes sum to its
  total elsewhere (for T6b's continental run) is unknown.

## For the owner

1. **Merge.** The amendment holds as ruled. A1 to A3 are record notes the builder (or you) can append
   before or after the merge; none changes a verdict. This review branch carries one added test (A4)
   and should go in with the amendment.
2. **The result in one line:** at 49 N, only total cover shows a step beyond the within-country null;
   the Douglas-fir share's earlier "artifact" came from the unmatched null alone.
3. **Merging into main `fe0993a` conflicts in three record files.** I did not resolve them:
   - `docs/audits/README.md`, at the end of the index. Main adds the T6b/D100 row; the branch adds the
     T5 rows. Keep every row.
   - `docs/planning/DECISIONS.md`, at the top of the table. Main adds D100; the branch adds D83 to D92.
     Keep all of them, D100 first, because the table is newest first.
   - `docs/planning/TASKS.md`. Main has "T5 to T11 | Not started" plus a T6b row; the branch has the
     T5 row plus "T6 to T11". The resolution is the branch's T5 row, then "T6 to T11", then main's
     T6b row.
   - D100 runs T5's host-tree layer continent-wide. D92's equality of the sum and the total is shown
     only for this strip.
   - This review's own index row extends the README conflict; it does not add a new one.
