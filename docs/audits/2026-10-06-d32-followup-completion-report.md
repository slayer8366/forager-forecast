# D32 follow-up task: completion report

Answers `docs/dispatch/2026-10-06-d32-followup-unify-filters.md`. Written 2026-10-06 (UTC) by the coder
session on the credentials machine (D38), branch `d32-followup-unify-filters`, worktree
`~/Zynergy/forager-forecast-d32-followup`. Base `origin/main` `1d5bd80`, re-checked unmoved at the
start. The verify step is `2026-10-06-d32-followup-verify-report.md`; this report covers the build after
the owner's answers. **Not merged (D40). Waits for the independent review (D18).** No download, no
weather pull, no model fit. No secret appears anywhere.

## What landed

| Commit | What |
|---|---|
| `1bf444f` | Verify report and its measurement scripts and outputs. Nothing built. |
| `1924d0a` | D64 to D67: the owner's answers to the four stops, relayed by the Forager planner session (Forager RECORD -568), with an index row. |
| `5061338` | `cells.py`: nearest point with exact ties toward +∞, read on the decimal value (D63, D64), and `quarter_cell_for`, the 0.25° ERA5 cell. |
| `1d643c2` | Evidence: T2's pre-D44 key reproduces the published duplicate drop. The revert runner. |
| `39ba0cd` | The unified module and everything moved onto it (below). |
| `5a074e1` | Dated corrections appended to the two handoffs (D41). |
| this commit | This report, its index row, and the build-run evidence. |

What `39ba0cd` contains, against the dispatch's items:

1. **One Record type (D66).**
   - `records/occurrence.py`: `Record`, T1's frozen dataclass with the DWCA fields added.
   - `taxon_key` is `acceptedTaxonKey` (D27).
   - One row loader, `record_from_row`.
   - `OccurrenceLoader`, which counts rows it cannot type, by reason.
   - The row readers move here from `filters.py`.
2. **One filter pipeline, in one module (D65).** `records/filters.py`:
   - `t1_steps()`: box, years, obscured, ≤ 1,000 m, default date, event key.
   - `r6_audit_steps()`: obscured, ≤ 250 m, default date, observer key.
   - One implementation per step. Each list's uncertainty limit comes from its own document.
   - The lowest gbifID survives a duplicate.
   - Both keys use `cell_for`.
   - T2's floor (`weather_cell`) is gone.
   - `counts.py`, `licenses.py`, `cell_weeks.py`, `scripts/t2_count_table.py` and
     `scripts/t2_render_tables.py` use the one Record.
3. **One cell rule** (`5061338`):
   - `cell_for` at 0.1° and `quarter_cell_for` at 0.25°, longitudes −180 to 180.
   - I relied on the delivered files (`grid-positions-d51-report.md:13`, :105), not the research
     note's 0 to 360.
4. **One request builder (D67).**
   - `build_download_request` and `DOWNLOAD_FORMAT = "SIMPLE_CSV"` are deleted.
   - `submit_download_request` sends `request_template(predicate)` plus `creator`,
     `notificationAddresses` and `sendNotification`.
   - **T1's SIMPLE_CSV data is no longer read by the pipeline.** Only the frozen evidence code reads
     it. Reason (D67): SIMPLE_CSV lacks `informationWithheld` and `acceptedTaxonKey`, and D26 makes
     that download provisional.
5. **Stale text.**
   - `records/__init__.py` docstring rewritten.
   - `gbif_download.py:1` docstring rewritten.
   - The duplicate key's docstring and step name were replaced with the module: the step is now
     `duplicate_taxon_observer_cell_day`.
   - `COLUMNS_READ` in `t2_count_table.py` is replaced by the loader's, which includes
     `acceptedTaxonKey`.
   - `t1_record.py:4-5` is frozen, so its stale "has not been requested" is corrected in the header
     above it, not edited.
   - The handoffs are corrected by appended sections (`5a074e1`).
6. **The credential loader's two-of-three case** is asserted
   (`tests/test_records_gbif_download.py`, `test_missing_credentials_are_named_not_guessed`).

**Frozen evidence (D67, and the planner's reading for `t1_record.py`).**
- `t1_record.py`, `t1_simple_csv.py`, `scripts/t1_count_table.py` and `scripts/t1_render_tables.py`
  changed by header comments only (`git diff --numstat`: 11, 4, 6 and 4 lines added, 0 removed).
  Their docstrings are still their docstrings.
- The planner decided `t1_record.py` joins the frozen set, as its reading of D67's intent, open to the
  owner's overruling. I filed no decision row for it; it is recorded here and in the file's header.
- **After D63 the frozen T1 script gives East 447,163, not the published 447,164.** Rerun over
  0005709: PNW 142,238, East 447,163 (`t1_frozen_summary.json`, last step summed from its CSV). The
  last commit that reproduces 447,164 is `1924d0a`, and main `1d5bd80`.

## Verification before building

In the verify report, plus one check the planner asked for. Re-running T2's four steps with the
pre-D44 key (observer|floor cell|day, as at `6560b2d^`) gives:

- a duplicate drop of **538,793**;
- **828,498** survivors.

Both equal the published figures. So D44's taxon fold explains the whole gap to 94,247
(`t2_oldkey_out.json`).

## Tests

- **Suite before:** 97 test functions (147 items), all passing.
- **Suite after:** 109 test functions (213 items), all passing.
- `ruff check` and `ruff format --check` are clean.

Test files:
- New: `tests/test_records_occurrence.py`.
- Rewritten: `tests/test_records_filters.py`.
- Moved to the loader and pipeline: `test_records_counts.py` and `test_records_licenses.py`.
- Extended: `test_cells.py`.
- One-line import change: `test_cell_weeks.py`.
- Edited: `test_records_gbif_download.py`.
- `tests/test_records_t1_*.py` are unchanged and still pass. They test the frozen evidence code.

**One existing expectation changed on purpose.** `test_cells.py` asserted that (47.05, −123.05) gives
−123.1, as Open-Meteo returned on 2026-09-18. D64 rules −123.0. The case moved to the tie test with a
comment saying so. This is a ruled behaviour change, not a weakened assertion.

**Seen failing first:**
- The new cell tie cases, against the old `cell_for`: every negative-side tie failed, and every
  positive-latitude tie passed, as the part 2 report predicts.
- The DWCA submit test failed on the SIMPLE_CSV body.
- The new modules' tests failed at import before the modules existed. Their behaviour-specific failing
  is shown by the revert checks.

**Passed before the change, flagged:** the two-of-three credential assertion. The code already behaved
correctly; the dispatch asked only for the assertion. R12 below shows it can fail.

## Revert checks

Runner: `docs/audits/2026-10-06-d32-followup-verify/revert.py.txt`. Each check:

- makes one edit;
- runs the affected tests;
- restores from a copy saved before the edit, never from git;
- checks the restored file's hash;
- refuses to cite results if collection or import errored. None did.

After all twelve, `git status` was clean with the forward change at `HEAD`.

| # | One edit | Failed | Specific to that edit |
|---|---|---|---|
| R1 | tie rule back to away-from-zero | 12 | Every negative-side tie at both grids, e.g. `lon_tenths: -1233 != -1232` |
| R2 | `Decimal(value)` instead of `Decimal(repr(value))` | 3 | Exactly the D64 decimal ties: `0.05,-0.05`, `47.05,-123.05`, `47.05 / 0.25` |
| R3 | 0.25° grid stepped at 0.1 | 9 | Every quarter-degree case, e.g. `(117.75, -307.75) == (47.0, -123.0)` |
| R4 | obscured step removed from T1's list | 4 | The T1 parametrisations of both obscured tests, the T1 name list, the T1 fixture |
| R5 | midnight on the first no longer default | 2 | Only the `time(0, 0)` first-of-month case, both lists |
| R6 | first seen survives | 3 | Lowest-gbifID test (both lists), and the on_pass test's survivor 4 |
| R7 | floor cell in the observer key | 2 | Nearest-not-floor and the exact-tie test, R6 list only |
| R8 | loader stops counting unloadable rows | 2 | The loader's tally and the count table's `{"coordinates missing or not numbers": 1}` |
| R9 | `taxonKey` instead of `acceptedTaxonKey` | many | The specific one: `assert 9999999 == 5249462`. The rest fail because the fixtures carry no `taxonKey` |
| R10 | R6 limit 1,000 m | 5 | `250.5-True`, and the fixtures whose 300 m and 900 m records are expected dropped |
| R11 | submit body back to SIMPLE_CSV | 1 | The DWCA body test |
| R12 | credentials name only the first missing | 1 | `test_missing_credentials_are_named_not_guessed`, "Regex pattern did not match" |

R12 is inferred to be the two-of-three assertion: under that edit the test's other two assertions
cannot change. The runner's filtered output did not print the input string.

## What changes for real data (item 6)

All runs were read-only over the two zips, whose sha256 match their stored hashes. Times and peak
memory are from `/usr/bin/time -v`.

### T2 download 0005714: old pipeline against the unified R6 audit list

The unified run is `scripts/t2_count_table.py` (4 min 14 s, 750 MB peak). The old run is today's code
before this branch (`t2_out.json`).

| Stage | Old | Unified | Difference, and why |
|---|---|---|---|
| rows read | 2,549,508 | 2,549,508 | |
| cannot be loaded | (none) | 9,627 | D66: 9,604 non-day dates and 23 ranges across days |
| source | 2,549,508 | 2,539,881 | the 9,627 |
| user_obscured dropped | 156,543 | 156,543 | none |
| coordinate_uncertainty dropped | 1,024,875 | 1,015,248 | −9,627. Every unloadable row had been dropped here before, so the "after" is the same 1,368,090 |
| default date dropped | 799 | 811 | +12: D65's parser (`T00:00` without seconds on the first). The 12 are listed in `check_minus_one.json` |
| duplicate dropped | 94,247 | 94,081 | −166 = −165 (D46/D63 cell, measured in the verify report) − 1 (see below) |
| survivors | 1,273,044 | 1,273,198 | +154 = −12 + 166 |

**The −1, checked and not assumed.** Of the 12 records D65 now drops at the date step, exactly one
shares its observer key with a record that passes the date step (`check_minus_one_strict.py.txt`). Under
the old rule that pair cost one duplicate drop; now the record goes at the date step instead. The
survivor rule (D65) changes no count. **No difference is unexplained.**

Under D46 and D63, 1,015,747 of 1,367,291 records entering the duplicate step change cell (verify
report).

### T1

**The unified pipeline cannot be run over T1's download 0005709.** D67 rules that it does not read
SIMPLE_CSV, and the file lacks `acceptedTaxonKey` and `informationWithheld`. What was run:

- **The old T1 pipeline over 0005709**, as frozen: PNW 142,238, East 447,163. Before `5061338` it gave
  447,164, the published figure (verify report). The difference is the one record D63 moves.
- **The unified T1 list over T2's DWCA download**, informative only (2 min 55 s, 359 MB peak).

| Stage (after) | PNW | East | Total |
|---|---|---|---|
| inside a T1 box | 250,165 | 935,018 | 1,185,183 |
| year 2015 to 2025 | 250,165 | 935,018 | |
| not user-obscured | 233,471 | 883,150 | 68,562 dropped |
| uncertainty ≤ 1,000 m | 162,121 | 490,908 | |
| not a default date | 161,957 | 490,505 | |
| one per taxon, cell and day | 142,038 | 446,832 | 588,870 |

That was 2,549,508 rows read, with the same 9,627 unloadable, and 1,354,698 outside both boxes.

**This is two downloads, not one, so these rows are not reconciled against T1's.**
- 0005714 was selected by continent and 0005709 by box. D26 records that the continent field is empty
  on some in-box records.
- The in-box loadable count is 1,185,183 here against 1,185,425 in 0005709.
- Matching them record by record is D26's acceptance check, which needs D26's download.
- The obscured step drops 68,562 in the boxes. At the 1,000 m step the two downloads differ by 1 per
  box (162,121 against 162,122; 490,908 against 490,909). That is consistent with the verify report's
  23 obscured records under 1,000 m continent-wide, **but I have not attributed it**. The downloads
  differ, so the difference could also come from the selection.

## Not verified

- **Real GBIF behaviour of the new request body.** `submit_download_request` has not been run against
  GBIF since this change, and this dispatch forbids it. The DWCA body equals `request_template` plus
  the three personal fields that the 2026-09-19 SIMPLE_CSV request carried.
- **The unified T1 list on one download.** The cross-download comparison above is not a reconciliation.
- The source of the 1-per-box difference at the T1 uncertainty step across downloads.
- The 9,604 non-day dates appearing in both downloads (flagged in the verify report, not checked).
- How T1's 2026-09-19 request was invoked. No production caller exists in the repository, before or
  after.
- Functions with no production caller, reported and not unified:
  - `request_template`: its caller is D26's task.
  - `submit_download_request` and `credentials_from_env`: no caller in `src` or `scripts`.
  - `read_occurrence_table`: tests only.
  - `label_cell_weeks`: tests only.
- Old `summary.json` files from T2's 2026-09-19 run cannot be rendered by the updated
  `t2_render_tables.py`. Its summary keys changed (`*_of_rows_read`, `rows_read`, `unloadable_rows`).
  The previous script is in git history.
- `counts.py` keeps its own copy of the T1 boxes beside `t1_design.BOXES`. Both are read by tests
  against the dispatch's limits. That copy predates this task and is out of its scope.
- Records with an empty `recordedBy` share an observer key, as they did under T2's code. No row rules
  on it, and it is unchanged.
