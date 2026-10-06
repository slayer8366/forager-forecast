# Independent review (D18) of D28's final date rule (midnight count, D97, D98)

Reviews branch `d28-date-rule` at `48c78c7` (confirmed with `git fetch origin` at the start: `origin/d28-date-rule`
= `48c78c7ddae1`, `origin/main` = `41005c1f1026`, which is also the merge base). Written 2026-10-06 (UTC) by a
reviewer session on this laptop that did not build the task, on branch `d28-review` in worktree
`~/Zynergy/forager-forecast-d28-review` (core.hooksPath `.githooks`). Protocol: `docs/dispatch/2026-09-18-review-protocol.md`
(origin/main), checks 1 to 10. Read: the dispatch `docs/dispatch/2026-10-06-d28-date-rule.md`, the measure
`2026-10-06-d28-midnight-measure.md`, the `2026-10-06-d28-midnight/` outputs, the completion report
`2026-10-06-d28-date-rule-completion-report.md`, every commit `df3456e..48c78c7`, D97 and D98, and Forager RECORD
-601, -602, -605 and -606 (`git -C ~/Zynergy/Forager show origin/records-after-173:RECORD.md`).

**Conventions:** "read" means opened in this session; "observed" means command output in this session; "inferred"
is marked. File:line cites are at `48c78c7` unless another commit is named.

## Verdict

**Holds.** Every headline number was re-derived by my own code in one pass over D26's download and is equal: the
midnight table, both lists' survivors under the old rule, "keep all" and the ruling, by region and in both keys,
and the d27_d28 script's pass 1 after its one-line change. The measure was committed before the run. D97 and D98
quote the owner word for word. The three existing tests the report names were each forced by the ruling, and none
was weakened. The same holds for six further changed tests in `test_records_filters.py`, which the report doesn't
list. Three of my own revert checks bite. **Nothing for the owner.** Three small findings are for the planner
(F1 to F3). I closed one small gap in my own commit (G1).

## What I re-derived (observed)

Script: `2026-10-06-d28-date-rule-review/reviewer_recount.py.txt` (`dcfb33a`). Output:
`reviewer_recount_0012112.json`, log `reviewer_recount_run.log.txt`. It's one process and one pass, run
19:52:30 to 19:56:30 UTC, 3 min 59 s, peak 852 MB, exit 0. `free -h` before the run showed 8.3 GiB available, and
nothing else heavy was running.

- **Input.** The zip's sha256 was checked in the script before reading: `c0d5f6a1…b26c`, equal to the DOI record.
  I read `occurrence.txt` out of the zip in place and didn't extract it. Rows: 2,493,578. Unloadable: 9,604 + 23.
- **Independence.** The script doesn't import `records/midnight.py`, `records/date_quality.py`'s tests or stats,
  the `scripts/d28_*` scripts, or the new date-step functions. It uses the loader, the non-date predicates,
  `region_of` and the two key functions. `git diff 41005c1..48c78c7` is empty on `occurrence.py`, `counts.py` and
  `t1_design.py`; in `filters.py` only the date step changed. The stats are scipy (`binomtest`, beta quantiles).
  Midnight was also counted a second way, by a regex over the raw `eventDate` text, with no loader involved:
  **0 disagreements** with the loader's `event_time == 00:00:00`. Every midnight record in the 1st trace is
  written `…T00:00`, with no seconds.

| Figure | Filed | Mine |
|---|---|---|
| iNaturalist: timed, midnight any day, on the 1st | 2,123,100; 657; 30 | 2,123,100; 657; 30 |
| iNaturalist: share, × expected, p (one-sided), 95% CP | 0.0457; 1.39; 0.047; 0.0310 to 0.0645 | 0.04566; 1.3898; 0.04694; 0.03102 to 0.06455 |
| iNaturalist: busiest midnight day / quietest | 19th, 88 / 3 (report :17, :195) | 19th, 88 / 3 |
| NABU\|naturgucker: timed, midnight, on the 1st | 18, 18, 0 | 18, 18, 0 |
| Other timed datasets with any midnight | none (6 datasets) | none (8 timed datasets in all) |
| Pooled: timed, midnight, on the 1st, p | 2,124,793; 675; 30; 0.062 | 2,124,793; 675; 30; 0.0619 |
| Midnight on the 1st reaching the date step, T1 / R6 | 5 / 10 | 5 / 10 |
| T1 event key: drop all / keep all / now | 591,324 / 591,779 / 591,783 | 591,324 / 591,779 / 591,783 |
| T1 now by region (event) | East 447,638, PNW 144,145 | East 447,638, PNW 144,145 |
| T1 observer key now | 612,120 (keep all 612,116) | 612,120 (612,116) |
| R6 observer key: drop all / keep all / now | 1,249,009 / 1,249,709 / 1,249,718 | 1,249,009 / 1,249,709 / 1,249,718 |
| R6 now by region (observer) | outside 702,712, East 413,518, PNW 133,488 | same |
| R6 event key now | 1,207,287 (keep all 1,207,278) | 1,207,287 (1,207,278) |
| Records reaching the duplicate step, T1 / R6, now | 655,655 / 1,341,858 | 655,088 + 562 + 5 = 655,655 / 1,341,108 + 740 + 10 = 1,341,858 |

Only one dataset had M ≥ 300, so the Bonferroni level is 0.01 / 1, and p = 0.0469 is not under it. The verdict
"not special to the 1st" therefore follows from the measure as fixed.

**The +4 and +9, traced.** It's the same record in both lists: **gbifID 3466077871** (iNaturalist,
`2021-10-01T00:00`, East box). Its key, the event key in T1 and the observer key in R6, is already held by a
"keep all" survivor, **gbifID 3466153817**, and no other midnight record shares it. The midnight record has the
lower gbifID, so under D65 (3) it **replaces** 3466153817 as that key's survivor rather than adding one. The count
moves by 4 and 9, and the survivor set also changes by that one swap. The other 4 (T1) and 9 (R6) midnight
records each have a key of their own. This settles the report's open item (completion report :176-179, :193).

## The drift checks

1. **Terms: holds.** `git diff 41005c1 48c78c7` adds no "fruiting probability", no "probability" or "calibrated",
   and no percent on relative habitat (grep, observed).
2. **Decisions: holds.** D97 and D98 are new rows at the top of `docs/planning/DECISIONS.md`. The branch removes
   no line anywhere under `docs/` (`git diff … -- docs/ | grep '^-[^-]'` is empty), so D28 and D65 are not
   edited. D97's supersede clause quotes D28 as filed (DECISIONS.md:72). D98's quotes D65 (2) as filed (:35).
   - **The owner's words, checked against the RECORD:**
     - D97's "Keep the 1st (Recommended)" is -601.
     - D98's "Keep the midnight check (Recommended)" is -601.
     - D98's "Yes, measure it first" is -602.
     - D98's "Drop the check, keep them (Recommended)" is -605.
     - All four are verbatim. The declined options in -601 and -605 are reflected in D97 and D98's
       alternatives.
   - **The rule applied is what -605 sets:** "No first-of-month or midnight drop remains in the date step".
3. **Fixed choices: holds.**
   - **Order of commits and run.** The measure was committed at `00d23f6`, 2026-10-06 12:24:18 −0700 (19:24:18
     UTC). The code `23c6f17` followed at 19:26:52, and the run started at 19:28:18 UTC
     (`2026-10-06-d28-midnight/run.json`, `run_time.txt`). Results were committed at `394c6c1`, 19:31:10.
   - **The measure is unchanged since it was fixed.** `git log` on the measure file shows only `00d23f6`. The
     constants in `records/midnight.py:31-33` and the imported `FAMILY_LEVEL` match the measure:
     12/365.2425, M ≥ 300, 2× expected, 0.01 Bonferroni.
   - **Edits to `midnight.py` after the run.** `midnight.py` was changed once after the run (`1aed9a2`), and
     only in how it finds the date step (`filters_before_date_step`). That changes no count. Its 5 / 10 reach
     equals mine.
   - **A cite checked.** The measure's cite `records/filters.py:87-89` is right at `41005c1`.
   - **Cannot tell** whether anyone opened `tables_0012112/day_of_month_by_dataset.csv`, which is on main and
     carries a per-dataset midnight-on-the-1st column, before `00d23f6`. The measure says it was not. The fixed
     choices don't depend on per-dataset counts (p0 is a calendar share, and the floor of 300 is D95's).
4. **Scope: holds.**
   - **Nothing on the do-not-touch list was touched:** no download, no fit, no secret, no filed record edited, no
     merge, and nothing in Forager.
   - **Frozen T1 evidence (D67, D68) is untouched.** `git diff 41005c1 48c78c7` is empty on `t1_record.py`,
     `t1_simple_csv.py`, `scripts/t1_count_table.py`, `scripts/t1_render_tables.py`,
     `tests/test_records_t1_record.py` and `tests/test_records_t1_observed.py`.
   - **Order of Part 1 and Part 2.** Part 2's red commit `669b0f8` (19:34:21 UTC) already quotes RECORD -605, so
     the ruling preceded it (inferred from the commit's content). The RECORD's own timestamps can't order these
     events: -601 to -606 read 20:40Z to 22:35Z, later than this review's own run clock (19:56Z, `date -u`).
     That is F3.
   - **Two things decided beyond the dispatch's text: within scope.**
     - **The date step was kept with 0 drops** (`filters.py:81-94`). The dispatch says to "change the shared
       date step … to the ruled rule", which reads as the step staying. I judge it hides nothing:
       `drops_no_dated_record` returns `False` unconditionally (`filters.py:94`), and every loaded record is
       dated, since undatable rows are counted before the first filter (D66). The step therefore shows 0 drops
       by construction. My recount puts every record that clears the non-date filters into the duplicate step
       (the table above).
     - **What the kept step does cost** is F1.
     - **The renderer's stage refusal.** I judge it a sound knock-on: without it, an R6 CSV written under
       `default_first_of_month_date` would render that stage as 0, silently. It refuses only names outside
       `STAGES` (`t2_render_tables.py:40-46`). As a consequence, re-rendering the filed pre-D97 T2 outputs with
       this renderer now refuses. That is the intended behaviour, and it is noted for whoever tries it.
5. **Record: holds.**
   - **Rows and headers.** Each new file in `docs/audits/` has an index row (`README.md`, three rows added),
     and TASKS.md and START_HERE.md have rows added, none edited. The reports carry their base (`41005c1` +
     `df3456e`).
   - **D99 is unused.** It is stated (report :98-99).
6. **Data hygiene: holds.** The largest added file is `midnight_by_dataset.json` at 508 lines, which is
   aggregates. The pre-commit large-file hook passed on every commit of mine. No data or download is in git.

## The evidence checks

7. **Claims carry cites: holds, with one gap (F2).** The figures I compared are above. The report keeps read,
   observed and inferred apart, and it marks the independence-assumption remark as inferred.
8. **Revert checks: holds.**
   - **The builder's runs.** 7 of 7 (Part 1) and 6 of 6 (Part 2) are recorded. Each recorded failure names
     the case its edit touches: I read both `jsonl` files and `revert.py.txt`. The builder's runner restores
     from saved bytes and refuses exit codes other than 1, which covers collection errors (exit 2).
   - **My runner.** `2026-10-06-d28-date-rule-review/reviewer_revert.py.txt` follows the strict design:
     - it restores from a saved copy and never from git;
     - it clears `__pycache__`, with `PYTHONDONTWRITEBYTECODE=1`;
     - it checks, by sha256, that a fresh interpreter reads the edited source;
     - it refuses a missing XML, any error, an exit other than 1, or fewer cases than the unedited run (117);
     - after all checks it confirms the targets' sha256 equal their pre-run values.
   - **My results** (`reviewer_revert_results.jsonl`): the unedited run had 117 cases, all passing. All three
     checks bite:

| # | One edit | Failed (of 117), all attributable to the edit |
|---|---|---|
| R1 | `drops_no_dated_record` drops every record on the 1st, any time | 12: the six date-step cases on the 1st (date-only, midnight, **and 13:24:27**), the mixed run (`[4] == [1, 2, 3, 4]`), the two fixture-count tests, and `{1,2,3,4,5}` |
| R2 | `t2_render_tables.py`: `if unknown_stages and False:` | 1: `DID NOT RAISE SystemExit` (the builder's P6, now under a strict runner) |
| R3 | `is_default_date` loses `if day != 1: return False` | 6: DROP_ALL now drops the 14th, so `{4} == {4, 5}` (×4), and my G1 test `{3} == {1, 2, 3}` (×2) |

   The forward state was intact afterwards: `filters.py` `944057e3…`, `t2_render_tables.py` `26d3ffce…`, both
   equal to their pre-run values. The failure sets name only cases each edit can cause, so this was not a stale
   run.
9. **Headline numbers re-run: holds.** These are my own code over the same zip (above), not a re-run of the
   builder's scripts. I did not re-run `scripts/d28_survivors.py` or `scripts/d28_midnight_table.py` themselves.
10. **Gaps.** Everything the dispatch asked for is evidenced:
    - Part 1: the measure first, the table, then a stop for the ruling.
    - Part 2: D97, D98, the step changed in both lists, tests through `Pipeline` with each list, survivors at
      the midnight-ruled variant, the revert runner, the suite before and after, and the frozen evidence
      untouched.

    What the report marked not done:
    - the trace, now closed above;
    - the `d27_d28_tables.py` re-run, now closed below for its pass 1.

## The three changed existing tests the report names, and six it doesn't

- **`test_records_date_quality.py:229-235`.** The old assertion was "DROP_ALL's survivors equal the lists'
  survivors", which is false under D97 and D98, so the change was forced. The replacement asserts both exact
  sets: `{1,2,3,4,5}` for the lists and `{4,5}` under DROP_ALL. It is stronger, not weaker.
- **`test_records_duplicate_keys.py:94`.** Only the stage name changed, which was forced. `entered == 8` and
  both survivor counts are unchanged; the fixture has no date-only or midnight record on the 1st, so none should
  move.
- **`test_records_midnight.py:97` and `:183`.** Both lookups of the date step changed, forced by
  `is_default_date` leaving the lists. The assertions are unchanged. The `:183` test still requires a
  `ValueError` when the date step is removed.
- **Also changed, in `669b0f8`, and not listed in the report (F2):**
  - **The two step-name tests** (`test_records_filters.py:60`, `:69`): forced.
  - **`test_first_of_month_without_a_real_time_is_dropped`**, replaced by
    `test_the_date_step_keeps_every_dated_record` (`:147-164`), which asserts each case kept, with the step's
    `(before, dropped) == (1, 0)`.
  - **The three fixture-count tests** (`:251-257`, `:266-267`, `:290`, `:296`): the expected survivors grew
    from `[1, 7]` to `[1, 5, 7]` and from `[1]` to `[1, 5]`, and the chained before/after counts were updated
    consistently. These are forced, and the counts are still asserted exactly.
  - **One thing lost** in the replacement: direct coverage that the retired predicate keeps midnight and
    date-only records on days other than the 1st. That is G1.

## d27_d28_tables.py's one-line change

This is pass 1, `with_date_rule(t1_steps(), DROP_ALL)`, at `scripts/d27_d28_tables.py:119-125`.

- **The numbers reproduce (observed).** My recount ran exactly that pipeline, with the repo's own `Pipeline`, on
  the same stream through a generator tap. Its result equals the filed `pass_t1_drop_all.json`: survivors
  591,324 (East 447,276, PNW 144,048), and the date step 655,655 before with 567 dropped. Every earlier step's
  count is equal too.
- **The labels don't (F1).** The other eight passes go through the same `with_date_rule`, so by reading they
  reproduce their counts too. I didn't run them.

## Findings

- **F1 (minor, for the planner): a swapped-in rule now runs under the ruling's name.**
  - **Cause.** `with_date_rule` keeps the step's name (`date_quality.py:252-253`, docstring "names unchanged").
    That name is now "date kept as given (D97, D98)" (T1) or `date_kept_as_given` (R6).
  - **Effect.** Every D28 candidate pass labels a step that drops records with the ruling's name. Observed:
    pass 1 reports "date kept as given (D97, D98)" with 567 dropped. A re-run of `d27_d28_tables.py` would
    write that label into all nine `pass_*.json` files, where the filed run has "not a default date (first of
    month at 00:00:00)". The counts reproduce and the labels mislead.
  - **Proposed fix:** let `with_date_rule` take the step name from the rule (for example, the rule's own label).
    This changes output labels, so I left it unfixed.
- **F2 (minor, record): the report's list of changed existing tests is incomplete.**
  - **What's missing.** The report's list (`completion-report.md:118-125`) leaves out the six existing tests in
    `test_records_filters.py` changed in `669b0f8`, listed above. They are framed as "tests first" instead.
  - **What it means.** None was weakened, but the report's own reason for the list ("so nobody reads them as
    tests weakened") applies to them as well.
  - **Proposed fix:** an appended note to the report. I didn't edit the filed report.
- **F3 (minor, for the planner, Forager side): RECORD timestamps are not on the clock.**
  - **What's wrong.** RECORD -601 to -606 carry `Timestamp`s from 20:40Z to 22:35Z. That is later than the UTC
    clock at the time of this review (19:52Z to 19:56Z, `date -u`) and than the forecast commits they describe
    (for example, -605 cites `394c6c1`, committed 19:31:10Z).
  - **Effect.** They can't be used to order the owner's rulings against the commits. Here the commit content
    did the ordering.
  - **Proposed fix:** a superseding note in the Forager record.
- **Cosmetic, not a finding:**
  - `date_step_position`'s error still says "no default-date step to replace" (`filters.py:191`).
  - The report's "keep-all's PNW is 144,048 + 97" (:181) means drop-all's PNW plus 97. The arithmetic is right.

## Closed here

- **G1.** A test was added, `test_drop_all_drops_only_the_1st_and_keeps_midnight_and_date_only_on_other_days`
  (`tests/test_records_date_quality.py`, t1 and r6). It goes through `Pipeline` with each list, and R3 shows it
  bites. Suite 375 → **377 passed**. `ruff check` and `ruff format --check` are clean (observed, after a
  comment re-wrap made after the revert run; the re-wrap changes no code).

## Not checked

- I did not re-run the builder's `scripts/d28_survivors.py` or `scripts/d28_midnight_table.py`, or
  `d27_d28_tables.py` beyond its pass 1. Its other eight passes are checked by reading only.
- Whether `day_of_month_by_dataset.csv` was opened before the measure was committed (cannot tell; see check 3).
- The builder's red output (`red_part2_filters.txt`) was read, not reproduced.
- The ordering of the owner's ruling against Part 2, beyond the content of `669b0f8` (F3).

## Merge

- **Into main `41005c1`.** `41005c1` is the merge base of `d28-date-rule` (and of this branch), so a merge is a
  fast-forward with no conflicts. `git merge-tree --write-tree origin/main origin/d28-date-rule` reports none.
- **With T6 afterwards.** `origin/t6-observation-layer` (one commit off `41005c1`, its dispatch) also appends to
  `docs/audits/README.md`. Merging it after this branch conflicts there (`git merge-tree` observed: CONFLICT in
  `docs/audits/README.md`). The fix is to keep every row.
- **This review's own index row** sits at the end of `README.md` as well, so the same applies.
- **Nothing else is touched by both.** No other record file (`DECISIONS.md`, `TASKS.md`, `START_HERE.md`) is
  changed by both branches.
