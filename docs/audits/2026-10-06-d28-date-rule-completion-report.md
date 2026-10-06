# D28's final date rule: completion report (midnight count, D97, D98)

Answers `docs/dispatch/2026-10-06-d28-date-rule.md`. Written 2026-10-06 (UTC) by the coder session on
this laptop (D38), branch `d28-date-rule`, worktree `~/Zynergy/forager-forecast-d28`. Base: `origin/main`
`41005c1` plus the dispatch `df3456e` (checked with `git fetch origin` at the start of this session).
**Not merged (D40). Waits for the independent review (D18).** No download, no credentials, no secret, no
model fit, no edit to a filed record, nothing in the Forager app.

Conventions: "read" means opened in this session, "observed" means command output in this session, and
"inferred" is marked as such.

## For the owner, in short

- **Midnight on the 1st is not special for any source.** Only iNaturalist has enough midnight records to
  test. Midnight is rare for it on every day: 657 of 2.1 million timed records. 30 of those fall on the
  1st, against about 22 expected, and that is within chance at the level fixed beforehand. The 1st is not
  even its busiest midnight day (the 19th has 88).
- **Your rulings are applied.** "Keep the 1st (Recommended)" (RECORD -601, now D97) and "Drop the check,
  keep them (Recommended)" (RECORD -605, now D98). The date step in both lists now keeps every dated
  record.
- **Survivors over D26's download:**

| List (own key) | Before (provisional rule) | Keep the 1st only (tables' "keep all") | Now (D97 + D98) |
|---|---|---|---|
| T1 (event key) | 591,324 | 591,779 | **591,783** |
| R6 (observer key) | 1,249,009 | 1,249,709 | **1,249,718** |

The step from "keep all" to "now" is the midnight records:
- **T1:** 5 more records reach the duplicate step, and 4 of them survive.
- **R6:** 10 more reach it, and 9 survive.

Against the old provisional rule, that is 459 more survivors in T1 and 709 in R6. That is under 0.1% of
each list.

## Part 1: the midnight count

**The measure, committed before any count was read.** `2026-10-06-d28-midnight-measure.md`, commit
`00d23f6` at 12:24:18 −0700. No midnight count had been read before it was committed:
- The run started 19:28:18 UTC, which is 12:28:18 −0700 (`2026-10-06-d28-midnight/run.json`).
- The one midnight figure already on record was the whole-download total of 30. The measure says so.

What the measure fixes:
- **Population:** every record the loader types, by dataset.
- **Midnight:** exactly 00:00:00 as written. This is the clock half of the old rule.
- **Expected:** the 1st's share of midnight records should be **12/365.2425** (3.29%) if the 1st is like
  the other days. That is the other days' rate carried over to the 1st.
- **Test:** D95's style. At least 300 midnight records, a one-sided exact binomial test, 0.01 split
  (Bonferroni) over the datasets tested, and "clear" also needs the 95% lower end at twice expected.
- **Shown but not used in any verdict:** the share against 1/30, the any-day midnight share, and the
  dataset's own day-1 share among its timed records that are not at midnight.

**Code:** `src/forager_forecast/records/midnight.py`, with tests in `tests/test_records_midnight.py`
(`23c6f17`). The script is `scripts/d28_midnight_table.py` (`62d0dde`).

**Input checked:**
- The zip's sha256 `c0d5f6a1…b26c` equals `docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json`
  (observed). It was read in place and not extracted.
- Rows read: 2,493,578, the DOI record's total.
- Records with a clock time plus date-only records: 2,124,793 + 359,158 = 2,483,951. That equals the
  loaded count.
- Midnight records on the 1st: 30, the figure filed in the D27 to D29 report.
- The run took 2 min 29 s with a peak of 28 MB.

**The table.** Only datasets with any record carrying a clock time are shown. The other 18 are entirely
date-only. All rows, with every day's count, are in `2026-10-06-d28-midnight/midnight_by_dataset.json`
and `midnight_table.md`.

| Dataset | Timed | Midnight, any day | Midnight on the 1st | Days 2-31 | Share on the 1st | × expected | 95% range | p | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| iNaturalist | 2,123,100 | 657 (0.03%) | 30 | 627 | 0.0457 | 1.39 | 0.0310 to 0.0645 | 0.047 | not special to the 1st |
| NABU\|naturgucker | 18 | 18 (100%) | 0 | 18 | 0 | 0 | | | too few to test |
| Six others | 4 to 1,141 each | 0 | 0 | 0 | | | | | too few to test |
| All datasets (not a verdict) | 2,124,793 | 675 | 30 | 645 | 0.0444 | 1.35 | 0.0302 to 0.0628 | 0.062 | |

The verdict wording fixed in the measure was "midnight is common on every day". For iNaturalist it means
"not concentrated on the 1st"; midnight itself is rare there. That wording issue was disclosed to the
planner with the table.

**How many of the 30 can move a survivor:** 5 reach the date step in T1 and 10 in R6, all iNaturalist.
The other 25 or 20 leave earlier, at other filters.

**Revert checks, 7 of 7 bite** (`2026-10-06-d28-midnight-revert.py.txt`, results in `-revert-results.jsonl`,
`cd82036`):

| # | One edit | Fails, with its message |
|---|---|---|
| V1 | expected share 1/30 | 3: `0.0333 == 12/365.2425`, and the p-value and ratio off |
| V2 | midnight ignores seconds | 2: only the `00:00:00.500` and `00:00:01` cases |
| V3 | Bonferroni over every dataset | 1: `0.002 == 0.0025` |
| V4 | clear judged on the share | 1: `'midnight on the 1st is special' == 'small excess on the 1st'` |
| V5 | reach ignores the filters | 1: `t1, 4 == 2` |
| V6 | date-only counted as timed | 1: `(6, 3, 2) == (5, 3, 2)` |
| V7 | tail from k + 1 | 2: the p-value, and the split's verdict |

## Part 2: the rule applied

**Rulings filed:** D97 ("Keep the 1st (Recommended)", RECORD -601) and D98 ("Drop the check, keep them
(Recommended)", RECORD -605, citing `394c6c1`). Both are new rows; no row was edited. **D99 is not used**:
the dispatch reserved D97 to D99, and two rows were enough.

**The change** (`records/filters.py`, `1aed9a2` and `23520a1`):
- The date step in `t1_steps()` and `r6_audit_steps()` now applies `drops_no_dated_record`, which keeps
  every record the loader could date.
- **The step stays in both lists, renamed and dropping nothing.** T1's step is now "date kept as given
  (D97, D98)" and R6's is now `date_kept_as_given`. Every run's step table therefore shows the ruling,
  with 0 dropped.
- **Decided beyond the dispatch's text:** I kept the step rather than removing it. Removing it would hide
  the ruling from the counts, and the D28 tools would have nowhere to swap a rule in (`with_date_rule`,
  the midnight table). The reason is in the function's docstring.
- `is_default_date` stays, as the D28 tables' "drop all" candidate (`DROP_ALL`).
- `date_step_position` finds the date step by the new predicate.

**Tests first, through `Pipeline` with each list:**
- `669b0f8` (red): 11 failing for the expected reasons. Date-only and midnight records on the 1st were
  still dropped, and the old step names were still in place (`2026-10-06-d28-date-rule/red_part2_filters.txt`).
- Green in `1aed9a2`.

**Tests changed because they asserted the provisional rule, now retired.** I'm listing these so nobody
reads them as tests weakened to get a pass:
- `test_records_date_quality.py`: "drop all is the provisional rule already in the step lists" became
  "...and the step lists now keep every date". It now asserts survivors {1, 2, 3, 4, 5} for the lists,
  and still {4, 5} under `DROP_ALL`.
- `test_records_duplicate_keys.py`: the T1 stage name.
- `test_records_midnight.py`: two lookups of the date step now use `date_step_position` and
  `drops_no_dated_record`.

**Knock-on fixes:**
- **`scripts/t2_render_tables.py` now refuses a stage it does not know.** Without this, a count CSV
  written before the R6 rename would print 0 for the renamed stage, silently. This is the same class of
  problem as the D26 review's finding 4. The test was red first, and the hand revert check P6 bites.
- **`scripts/d27_d28_tables.py` pass 1 now puts the provisional rule back explicitly**
  (`with_date_rule(t1_steps(), DROP_ALL)`), so the script still reproduces its filed run. This was not
  re-run. The change is one line and has no test.
- **`scripts/t2_count_table.py` was not changed.** It runs the current R6 list, so a re-run now applies
  D97 and D98, as intended.

**Frozen T1 evidence was not edited.** `records/t1_record.py` and its tests are untouched; `git diff
41005c1 -- src/forager_forecast/records/t1_record.py` is empty.

**Revert checks, 6 of 6 bite** (`2026-10-06-d28-date-rule/revert.py.txt` and `revert_results.jsonl`,
`f0590dc`, with P6 by hand in `d5b7542`). The runner:
- saves the file's bytes and makes one edit;
- confirms a fresh interpreter sees the edited source;
- runs four test files with a fresh JUnit XML;
- refuses on errors or an exit other than 1;
- restores from the saved bytes, never from git, and checks the restore is identical.

`git diff` was empty after the run.

On its first attempt the runner refused to start: its import check still named `midnight.py`. It caught
that itself, and nothing ran on the wrong file.

| # | One edit | Fails |
|---|---|---|
| P1 | date-only on the 1st dropped again | 8: only the date-only-on-the-1st cases, plus the fixture counts |
| P2 | midnight on the 1st dropped again | 6: only the midnight-on-the-1st cases |
| P3 | T1 list keeps `is_default_date` | 7: only T1 cases |
| P4 | R6 list keeps `is_default_date` | 8: only R6 cases |
| P5 | date step found by the old predicate | 6: `no default-date step to replace (found 0)` |
| P6 | renderer's stage refusal off | 1: `DID NOT RAISE SystemExit` |

**Survivors over D26's download** (`scripts/d28_survivors.py`, `2026-10-06-d28-date-rule/survivors_0012112/`).
The pass function is the D27 to D29 one, which checks every row is accounted for and that the tally in the
list's own key equals the pipeline's survivors overall and by region.
- The sha256 was checked first.
- The run took 6 min 31 s with a peak of 1.11 GB, one process (`/usr/bin/time -v`).

| | T1 | R6 |
|---|---|---|
| Date step: before, dropped | 655,655, 0 | 1,341,858, 0 |
| Duplicate step reads | 655,655 = 655,650 (keep all) + 5 | 1,341,858 = 1,341,848 + 10 |
| Survivors, own key | **591,783** = 591,779 + 4 | **1,249,718** = 1,249,709 + 9 |
| Survivors, other key | observer 612,120 (keep all 612,116, +4) | event 1,207,287 (keep all 1,207,278, +9) |
| By region, own key | PNW 144,145, East 447,638 | PNW 133,488, East 413,518, outside 702,712 |

**Why +4 and +9 rather than +5 and +10.** Adding a record to the duplicate step adds at most one survivor,
and adds none when its key is already present. So exactly one of T1's 5 shares an event key, and exactly
one of R6's 10 shares an observer key. That one either matches a record already at that step or another
midnight record. Which record it is was not traced.

**T1 by region:** keep-all's PNW is 144,048 + 97 = 144,145, the same as now. Its East is 447,276 + 358 =
447,634, now 447,638. So the 4 midnight survivors are all in the East box (observed by subtraction).

## Suites

- Before Part 1 (`df3456e`): 357 passed.
- After Part 1: 372.
- After Part 2: **375 passed**.
- `ruff check` and `ruff format --check` are clean (observed).

## Not verified, or not done

- **Which midnight record fails to survive in each list** was not traced; it needs a further pass.
- **The binomial test's independence assumption** does not hold for real dates. Midnight counts by day
  range from 3 to 88 for iNaturalist. That makes the test flag more readily, never less. Inferred, not
  measured.
- **The midnight test is one-sided**, so a shortage on the 1st reads as "not special".
- **`d27_d28_tables.py` after its one-line change** was not re-run (33 min).
- **`midnight_table.md`**: I escaped the pipe characters inside three dataset titles after the run. The
  JSON is as written.
- **The midnight measure's code tests were written after the code**; the revert checks show they bite.
- Review (D18) and merge (D40) are not done, as instructed.
