# T1 review: credentialed run, download and count tables

**Date:** 2026-09-18
**Type:** review under docs/dispatch/2026-09-18-review-protocol.md.
**Reviewed:** branch t1-calendar-smoke-test at 691bef3 over main f96d557. Five commits after
34933e8 (the previous T1 review): ade7ce6 (SIMPLE_CSV loader, observed filter run, count-table
script, 29 tests), 8c45daa (DOI record, table renderer), f04c209 (the run report and the filed
dispatch), 09ce2ef (index row, session log row, TASKS.md cell), 691bef3 (two keys appended to
the DOI record). The report under review is
docs/audits/2026-09-18-t1-credentialed-run-report.md.
**Reviewer base commit:** 691bef3, tree clean, local equal to origin/t1-calendar-smoke-test after
`git fetch`. This review is the next commit on the same branch.
**Supersedes:** nothing. The previous review (docs/audits/2026-09-18-t1-review.md) stands; its
open items are listed under check 10 where they are still open.

The reviewer is a separate agent session from the builder and read the repo, not the builder's
chat. Every claim below names a file and line, a commit, or a command whose output is quoted, or
is marked inferred. Line numbers for the report refer to the file at f04c209, which is unchanged
at 691bef3. The reviewer read nothing under ~/Labs or ~/.config, made no GBIF download request,
and used no credentials; the one GBIF call was a public unauthenticated GET of the download
record.

## Summary

All ten checks hold. Every headline number reproduces: the count script re-run on the same zip
in a fresh output directory produced byte-identical CSVs, and all 34 table rows in the report
equal the renderer's output; the DOI record equals GBIF's public download record field for
field; both revert checks fail with the builder's exact messages and restore cleanly; the
nine-row positive control, rebuilt from the report's description, gives the report's numbers.
Nothing built contradicts a decision row, a fixed term or a fixed choice, and the five filter
functions are byte-unchanged since the previous review. Four small items for the record, none a
contradiction: one percentage in the report does not follow from its own table (27 versus 29),
`scripts/t1_count_table.py:55` uses syntax that is a SyntaxError on the Python 3.12 fallback D21
names, a docstring at `gbif_download.py:105-106` now states a decayed claim, and the new index
row departs from the form of the ten rows above it. The owner items the report raises (PNW
thinness, the default-date rule, the licence gate) are the owner's and are set out under check
10 with the previous review's still-open items.

## Drift checks

### 1. Terms. Holds.

- `git grep -n -i "fruiting probability"` outside docs/planning and docs/dispatch returns
  README.md:27 (which bans the phrase) and the previous review's check 1 (which describes this
  search). Nothing in the five commits.
- `git grep -n -i "probability" -- src tests scripts '*.json' pyproject.toml` returns nothing.
  `git grep -n -i "calibrat" -- src tests scripts` returns nothing.
- "percent" in the report appears at lines 313, 314, 328 and 394, all fractions of records,
  never of relative habitat. "relative habitat" appears in none of the twelve changed files.
- No em dash in any of the twelve files `git diff 34933e8..HEAD --name-only` lists
  (`grep -P "\x{2014}"` over them returns nothing).
- No chance is estimated in this run, so "sighting chance" has no new occurrence to check; the
  existing ones (cell_weeks.py:5, cells.py:3) are untouched.

### 2. Decisions. Holds, with two small items outside any row.

- D19 and D21: no Open-Meteo request was made in this run (report 37, "no weather was pulled";
  the twelve changed files contain no archive URL, `git grep archive-api` over them is empty).
- D22: the licence question stays open. The report measures the CC BY-NC share (lines 302-316)
  and hands it to the owner (owner item 4, line 394); nothing in code rules a licence in or out.
  `git ls-files | grep -i licen` still returns nothing.
- D20 and D21, Python 3.14 with 3.12 as the fallback. The code runs on 3.14.4 (83 passed). One
  item: `scripts/t1_count_table.py:55` reads `except KeyError, ValueError:`, the unparenthesised
  form that Python 3.14 accepts. Observed:
  `~/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12 -c "import ast;
  ast.parse(open('scripts/t1_count_table.py').read())"` raises `SyntaxError: multiple exception
  types must be parenthesized` on 3.12.14, while 3.14.4 parses it. This is not a contradiction
  of D21 (pyproject.toml:9 pins `requires-python = "==3.14.*"`, so the fallback is not in use),
  but the fallback D21 records would not run the count script as written. Proposed fix, one
  line: `except (KeyError, ValueError):`. Not done by the reviewer: it is the builder's code.
- A decayed claim in a docstring, for the record rather than any row: `gbif_download.py:105-106`
  still says "Not run in T1: no credentials existed on the machine". The function ran in this
  task and returned the key (report 130, 143-145; DOI record line 64). Proposed fix: replace
  the sentence with the run date and key. Not done by the reviewer, same reason.
- D23: nothing in the five commits touches zynergy-site or reads from the pack branch.

### 3. Fixed choices. Holds.

Compared the dispatch, the code, the request GBIF stored and the commit times.

| Fixed choice | Where it stands | Match |
| --- | --- | --- |
| Predicate, unchanged since ac12f55 | `git log --oneline -- src/forager_forecast/gbif/t1_fungi_two_boxes_2015_2025.json` lists one commit, ac12f55 | yes |
| Request GBIF stored equals the branch file | `GET /occurrence/download/0005709-260916113435855` (public), `request.predicate == json.load(predicate file)` printed True; also equal to the DOI record's `request.predicate` | yes |
| Boxes, years, uncertainty threshold | `git diff 34933e8..HEAD -- src/forager_forecast/t1_design.py` is empty | yes |
| The five filter functions | `git diff 34933e8..HEAD -- src/forager_forecast/records.py`: `keep_inside_boxes`, `keep_years`, `drop_uncertain_coordinates`, `is_default_date`, `drop_default_dates`, `keep_one_per_taxon_cell_day` have no changed line; the diff adds the `license` field (records.py:33-35), the `T1_FILTER_STEPS` tuple (107-113) with the same five names in the same order the old inline tuple had, and the observe hook (116-131) | yes |
| Format SIMPLE_CSV with the license column kept | GBIF record `request.format` SIMPLE_CSV; file header has 50 columns with `license` at column 43 (`unzip -p ... \| head -1 \| tr '\t' '\n'`) | yes |

- Order of events, from the record rather than the report: the download was created at
  2026-09-19T03:57:12Z (20:57 local) and completed at 04:10:34Z (21:10 local); the zip's mtime
  is 21:11; the loader and count script were committed at ade7ce6, 21:05:11 -0700 (`git log
  --date=iso`). So the loader's rules (refuse a range across days, refuse a year-only value,
  match Cantharellus on the genus name) were committed before the file existed on this machine.
  Inferred from those timestamps; the builder could not have read a row of the download before
  GBIF finished it.
- The 9,609 rows the loader refuses are counted beside the tables (report 216-246), not added
  as a sixth filter step. That is the right side of this check: adding a step after seeing the
  data would be a filter change (report 363-366 says the same).
- The default-date widening flagged by the previous review (check 3 there) is unchanged in code
  (records.py:76-83) and is now measured rather than decided (report 334-352): 562 of the 567
  drops at that step turn on the widening, 9 of them Cantharellus. Still the owner's yes or no;
  see check 10.

### 4. Scope. Holds.

- `git diff --stat 34933e8..HEAD` lists twelve files: two source modules, two scripts, two test
  files, the DOI record, the filed dispatch, the report, the index, the session log and
  TASKS.md. Nothing else. None of the six code files imports lightgbm or any model; no fit path
  was added.
- Do-not-touch list, item by item:
  - The password. `git grep -n GBIF_PWD` returns the variable name in code, tests, docs and the
    DOI record only (sixteen lines, listed by the reviewer); no tracked file contains a value.
    The report's quoted commands (73-95) name `$GBIF_PWD`, never a value. Whether the builder's
    session logged it anywhere outside the repo the reviewer cannot tell and did not look.
  - No search-API substitute. The counts come from the zip: scripts/t1_count_table.py:72-100
    opens the member and streams its rows; the search API appears in the report only as the
    earlier preview it compares against (222-234).
  - Predicate, boxes, year range, window list: see check 3.
  - DECISIONS.md, Fixed terms, SPEC.md: `git diff 34933e8..HEAD -- docs/planning/DECISIONS.md
    docs/planning/SPEC.md docs/planning/DATA_REGISTER.md` is empty; START_HERE.md's diff is one
    appended row (line 69).
  - No data in git: check 6.
- "One at a time." The T1 record's `modified` is 2026-09-19T04:10:34Z and the T2 branch's DOI
  record (origin/t2-record-audit:docs/pulls/gbif-fungi-north-america-2015-2025.doi.json,
  `created_utc`) is 04:11:37Z, 63 seconds after T1 succeeded. Two records, both in git, agree
  with the report's account (37-39, 121-124).
- Stopped where told: no model, no sampler, no weather (report 37). The report ends with owner
  items rather than the "Then build" work of the T1 dispatch.

### 5. Record. Holds, with three form items.

- DOI record: 691bef3 appends two keys (`integrity_check_2026-09-18`, `gbif_erases_after`) and
  changes no existing key (`git diff 09ce2ef..691bef3`, three insertions, one deletion which is
  the comma on the previous last line). Append, not edit.
- docs/audits/README.md: one row appended at line 27. docs/planning/START_HERE.md: one row
  appended at line 69. TASKS.md: one cell, the T1 status (line 13). The previous review's rows
  are untouched.
- Header: the report names its base (line 7, "34933e8 over main f96d557") and its code commits
  (line 8). The DOI record names the predicate's commit (line 63).
- Form item 1: the index row at README.md:27 gives its File as
  `docs/audits/2026-09-18-t1-credentialed-run-report.md`, without backticks and with the
  directory prefix; the ten rows above it (17-26) each use a backticked path relative to
  docs/audits. Not edited, per the append-only rule (README.md:13). Noted so the next row
  returns to the form.
- Form item 2: the report at lines 8-9 says the report is "the next commit" and the record rows
  "one more", and then a further commit 691bef3 followed. `git grep 691bef3 09ce2ef -- docs`
  returns nothing, so neither the index commit nor the DOI amendment is named anywhere in the
  record. This review's header names all five hashes, as the previous review did for its three.
- Form item 3: the filed dispatch docs/dispatch/2026-09-18-t1-t2-credentialed-run.md has no
  index row of its own; README.md:3-4 says the index records "the dispatches they answer", and
  three dispatch files have rows (t0b, review-protocol, filing-d21-d23) while four do not (t0,
  t1, t2, t3, `grep -c` of each basename in the index). The convention is mixed, so this is not
  called a gap; it is recorded so the owner can choose one form. The reviewer did not add a row:
  the report's "byte-identical to the owner's upload (`cmp`)" claim (line 155) cannot be
  checked from the repo, so a row would carry the builder's word.

### 6. Data hygiene. Holds.

- `git ls-files data | wc -l` is 0. `git ls-files | wc -l` is 63.
  `./scripts/check-large-files.sh --all` printed `63 file(s) checked, none over 1048576 bytes`.
  Largest tracked: uv.lock 41,201 bytes, then the T1 completion report 32,207, the atlas HTML
  29,734, this run's report 26,711. The report's "61 file(s) checked" (line 181) was at 8c45daa,
  before the report and dispatch were tracked; 61 + 2 = 63.
- `git check-ignore -v` names `.gitignore:6:data/` for the zip and for
  data/t1/counts/summary.json. The zip on disk is 163,662,303 bytes (`ls -l`), sha256
  6468a43137d4f1da0379d0e6e5574d0cc5d3ab8e72d2ae50b140cac464a41683 (`sha256sum`), member
  734,590,434 bytes (`unzip -l`), `unzip -t` reports no errors: all four equal the DOI record
  lines 10-13 and its integrity note at line 67.
- Licence: DATA_REGISTER.md:20 (GBIF downloads, "Per record", Verified) existed at f96d557,
  before the request. The per-record split is now measured (report 302-311); the register's
  flag cell is unchanged, and the previous review's note that T3 owns register verification
  still applies. The report's line 137 marks "most restrictive licence among the records" as
  inferred, correctly: GBIF's public record carries the download licence and no statement of
  how it was chosen.
- `ruff format --check .` printed `48 files already formatted` here against the report's 46
  (line 179); `ruff check --show-files .` lists 23 files and `find` counts 24 `.py` files. The
  cause of the count is not determined, as it was not for the previous review's 40 versus 39;
  neither run found an unformatted file.

## Evidence checks

### 7. Claims carry evidence. Holds, with a short list.

File-and-line citations checked with `cat -n` and found accurate: gbif_download.py:99-124
(`submit_download_request`); simple_csv.py:1-18 (the module docstring's two decisions), 67-106
(`_parse_instant` and `parse_event`), 141-148 (the genus-name match); records.py:76-83
(`is_default_date`), 116-136 (`apply_t1_filters_observed` and the delegating
`apply_t1_filters`); scripts/t1_count_table.py:1-15 (the one-box-at-a-time docstring);
.gitignore:6; DOI record line 63 (predicate source). Counts: `pytest --collect-only` gives 27
cases in tests/test_simple_csv.py and 2 in tests/test_records_observed.py (report 153); the
suite is 83 (report 180). File facts: 50 header columns with `license` at column 43 (report
135); data rows 3 to 6 of the file carry `T00:00` with no seconds (report 169 says rows 4 to 6;
the reviewer's `head -7 | tail -6` shows the form on file lines 4 to 7, which is the same rows
counted from the header). The techdocs page fetched here is 34,293 bytes and contains none of
the seven phrases the report lists (line 119-121), each `grep -o -i -c` returning 0. The T2
report on origin/t2-record-audit names fca5e616 as the New Jersey fungi dataset at its lines 281
and 289 (report 240). data/t1/counts/diagnostics.txt lines 1-14 hold the 42 Cantharellus
year-only rows, the 9,330 and 274 datasetKey split, and every cell of the default-date table
at report 340-345.

Claims the reviewer could not check, and how they stand:

- Everything read from ~/Labs and ~/.config (report 43-100: Cowork's report and its four
  differences, the file's mode and three names, the 200 and 401, `count: 0`). Barred to the
  reviewer by rule. The download's existence under the account is shown by the public record
  (check 9), which is the strongest fact those steps lead to.
- "Filed byte-identical to the owner's upload (`cmp`)" for the dispatch (line 155). The upload
  is not in the repo.
- The notification email and the account's inbox (report 146-147, 408): not observed by the
  builder either, and stated so.
- The nine-row positive control (report 203-207) is not in the repo. The reviewer rebuilt it
  from the description (one row each: kept in PNW, other fungus kept, kept in East, outside both
  boxes, month-only date, missing uncertainty, first-of-month at 00:00:00, duplicate of the
  first row, a 2021 date-only row) and ran the script: `total_rows 9, loadable 7, outside 1,
  unloadable 1, accounted 9`, and PNW 2020 Cantharellus `4, 4, 4, 3, 2, 1` down the six stages.
  Reproduces.

Figures that do not follow from the report's own tables:

- Line 328, "the PNW's usable records are 27 percent of the 2015 to 2018 preview counts". From
  the tables at 256-263, usable 3 + 8 + 12 + 29 = 52 and preview 26 + 31 + 53 + 71 = 181, which
  is 28.7 percent. No reading of the tables gives 27. The conclusion ("thin") does not move.
  The other percentages check: 1,127 of 1,226 is 91.9 and 2,436 of 2,748 is 88.6 (lines
  313-315, "92" and "89").
- Line 133, "Succeeded 2026-09-19T04:10:34Z". GBIF's public record has no `succeeded` field;
  its `modified` is 04:10:34.821Z and `status` is SUCCEEDED, and the DOI record's
  `succeeded_utc` is that `modified` value. A fair reading, stated here so the field name is on
  record.
- Line 146, "The request body GBIF echoes back has `sendNotification: true` and the
  notification address". The public record's `request` has `sendNotification: true` and no
  `creator` or `notificationAddresses` key; it also carries `type: OCCURRENCE` and two empty
  extension lists the DOI record's `request` omits. Inferred: the authenticated response the
  builder saw carried the address and the public one strips it. The DOI record's choice not to
  store the address (line 64) loses nothing the public record shows.

"Inferred" and "observed" are used where they should be (lines 13-15, 83, 98, 137).

### 8. Revert check. Holds. Both re-done.

Each with a copy in /tmp, `sha256sum` recorded before the edit, a one-line `sed`, only the
affected test file run, the log grepped for import and collection errors before reading the
failures, restored with `cp` from the copy (never from git), `sha256sum -c`, `grep -c
REVERT-MARK` = 0, `git status --short` empty, then the file's tests and the full suite.

1. records.py:125, `observe(SOURCE_STAGE, current)` replaced by `pass  # REVERT-MARK`.
   `uv run pytest -q tests/test_records_observed.py`: `1 failed, 1 passed`, 0 import or
   collection errors. The failure is at tests/test_records_observed.py:45:
   `AssertionError: assert ['inside a T1...cell and day'] == ['source', 'i...cell and day']`,
   `At index 0 diff: 'inside a T1 box' != 'source'`. That is the report's message (lines
   194-196) to the character, and the only edit that removes the source stage from the front of
   the observed list is the one made. Restored: `src/forager_forecast/records.py: OK`, `2
   passed`.
2. simple_csv.py:104, the same-day condition replaced by `if False:  # REVERT-MARK`.
   `uv run pytest -q tests/test_simple_csv.py`: `3 failed, 24 passed`, 0 import or collection
   errors, each failure `Failed: DID NOT RAISE UnloadableRow`, on the three cross-day range
   cases (`2020-09-15/2020-09-16`, `2020-09-01/2020-09-30`, `2025-10-04/2025-10-05`). That is
   the report's message and count (197-199). Restored: `src/forager_forecast/simple_csv.py:
   OK`, then `83 passed in 1.44s` for the whole suite.

The forward change was confirmed present after both restores: sha256 equal to the pre-edit
hash, which is the committed file's.

### 9. Headline numbers re-run. Holds. Everything reproduces.

From the clean tree at 691bef3:

```
uv run ruff check .          -> All checks passed!               (report: same)
uv run ruff format --check . -> 48 files already formatted        (report: 46, check 6)
uv run pytest -q             -> 83 passed in 1.49s                (report: 83 passed in 1.08s)
/usr/bin/time -v uv run python scripts/t1_count_table.py \
    data/t1/downloads/0005709-260916113435855.zip /tmp/t1-review-counts
                             -> exit 0, wall 2:25.00, max RSS 454,272 kB
                                (report: 2:08.51, 454,040 kB)
```

- Row accounting printed by the script: total_rows 1,195,034; loadable_rows_inside_boxes
  1,185,425; rows_outside_boxes 0; unloadable_rows 9,609; accounted 1,195,034. Equals report
  216-220 and data/t1/counts/summary.json.
- The three CSVs the script wrote are byte-identical to the builder's (`cmp` on
  counts_by_box_year_step.csv, counts_by_license.csv, unloadable_rows.csv, each "identical");
  summary.json differs only in the `zip` path argument.
- `uv run python scripts/t1_render_tables.py /tmp/t1-review-counts`: every table row in the
  report between lines 250 and 330 (the four stage-by-year tables, the license table and the
  premise table, 34 rows) is in the renderer's output, and `diff` of the two sorted row sets
  shows only the renderer's three unloadable-row lines, which the report carries at 238-242 in
  a wider table with the same three counts (9,604; 1; 4).
- Premise arithmetic re-read from the tables: PNW final 1,226 over 11 years with any, 4 years
  at or above 100 (111, 122, 345, 322), smallest 3 in 2015; East final 2,748, 11 years, 8 at or
  above 100, smallest 12 in 2015. The default-date step's drops are 164 (162,122 to 161,958) and
  403 (490,909 to 490,506), equal to the date-only plus 00:00 columns at 340-345 (7 + 157 + 0;
  2 + 396 + 0 + 5). 562 = 567 - 5, and 9 = 7 + 2 Cantharellus. All as at 347-349.
- Preview comparison (report 225-230) checked per year against the T1 completion report's
  table at its lines 81-86: the East Cantharellus differences are 8, 8, 8, 10, 8 in 2015 to
  2019 and 0 after, summing to 42; PNW Fungi differs by 2 in 2023 and 2 in 2024, 4; East Fungi
  differs by 1,867, 1,866, 1,866, 2,140, 1,866 in 2015 to 2019, 9,605. The unloadable rows are
  all in 2015 to 2019, which is consistent with 9,604 of them being year-only dates from one
  dataset.
- DOI record against `curl -s https://api.gbif.org/v1/occurrence/download/0005709-260916113435855`
  (public, no credentials): key, DOI 10.15468/dl.hdkjmn, licence URL, `size` 163,662,303,
  `totalRecords` 1,195,034, `numberDatasets` 15, `created` 03:57:12Z, `modified` 04:10:34Z,
  `eraseAfter` 2027-03-19T03:57:11.907Z, `status` SUCCEEDED, `request.format` and
  `request.sendNotification`, and `request.predicate` all equal the DOI record's fields (each
  comparison printed True). The local zip's size and sha256 equal the record (check 6).

## Gaps

### 10. What the dispatch asked for that the report does not evidence. Holds for the T1 half; the stop is the dispatch's stop.

Asked and evidenced: the download with the fixed predicate and the licence column (check 3);
the count tables by box, year and step, and by license (check 9); the premise verdict under both
readings (report 318-332); the DOI with its query, marked provisional (DOI record lines 3-4,
16-62); the large-file guard result (report 181); one at a time (check 4); the Conventions line
and the not-checked list (report 398-424); stopped before any model.

Evidenced by the report's word only, because the reviewer is barred from the sources: Verify
first items 1 to 3 (Cowork's report, the credentials file, the 200 and 401). Item 4 (test-account
rules) is evidenced in the repo: the DOI record's status and `superseded_by` fields, and
`grep -rn -E "1195034|1,195,034|3425|1226|2748" tests src` re-run here returns only the
gbif_download.py:7 docstring, not a test.

Not evidenced, by design or by scope:

- The "Person only" items (which email the account uses; the CAPTCHA and terms checkbox) are
  the owner's.
- The T2 half (its tables, the hand-check CSV) is on branch t2-record-audit and is not this
  review's scope.
- The fixed tuning budget is still not written down anywhere on this branch (`git grep -n -i
  "tuning budget" -- src tests scripts` returns only t1_design.py:5, the docstring that says it
  must not change once a result is seen; no value is recorded). Carried from the previous
  review's check 10; it is now one step away, since modelling is what waits on the owner.
- CI has not run on this branch: .github/workflows/ci.yml:6-8 triggers on push to main and on
  pull requests, and no pull request is open. The three commands pass locally (check 9).

Owner items now open on this branch, all of them the report's or the previous review's, none
touched by the reviewer:

1. The premise reading for the PNW (report owner item 1): 1,226 usable records over 11 years,
   but 3, 8, 12 and 29 in 2015 to 2018; leave-one-year-out would hold out 3 positives in 2015.
   The literal reading holds; the stricter one does not.
2. The default-date rule (report owner item 2; T1 completion report owner item 4): 9
   Cantharellus and 553 other records turn on the widening.
3. The licence gate (report owner item 4): 89 to 92 percent of usable Cantharellus records are
   CC BY-NC; the register row still reads "Per record".
4. D24, D25, D26 (report owner item 3), unchanged since the previous review.
5. From the previous review, still open: `scripts/verify-open-meteo-historical-fields.sh` sends
   requests D21 forbids; the Open-Meteo register row still reads "Terms to confirm".
6. New here, small: the 3.12 fallback cannot parse scripts/t1_count_table.py:55 (check 2); the
   docstring at gbif_download.py:105-106 is stale (check 2); the "27 percent" at report 328 is
   28.7 (check 7).

Marked not checked by the report (400-412) and still open: whether the year-only rows are the
New Jersey dataset's convention; whether date-only first-of-month rows are defaulted dates; the
uncertainty step's split between missing, obscured and merely above 1,000 m; the notification
email; two simultaneous download requests; CI; the T2 download's contents.

## What the reviewer changed

This file, and one row appended to docs/audits/README.md, in one commit on
t1-calendar-smoke-test. Nothing in src, tests, scripts, the report, the DOI record, the filed
dispatch, or any planning file. The scratch outputs (/tmp/t1-review-counts, the two module
copies, the rebuilt synthetic zip, the fetched GBIF record and techdocs page) are outside the
repo and are not kept. Commit hash: in the final message to the launching session.

## Conventions

Checked in this repo at 691bef3: docs/dispatch/2026-09-18-review-protocol.md for the ten checks,
the verdict words and the output form; docs/audits/README.md for the index row form (backticked
path relative to docs/audits) and the append-only rule; docs/audits/2026-09-18-t1-review.md for
the header fields and section order; the Forager CLAUDE.md rules on revert checks (save a copy,
restore from it and never from git, check the log for import and collection errors before
reading failures, confirm the forward change is present afterwards), on citing a figure with
its scope, and on reading a check's sample before citing it (the count run's accounting line
and the `cmp` of its outputs against the builder's). Followed all of them. "Sighting chance" is
not used here because no chance is estimated; the banned label appears in this file only inside
check 1's description of the search. No em dashes.

## Not checked

- Anything under ~/Labs or ~/.config, by rule: Cowork's report, the credentials file, the
  login codes, `count: 0` before the request.
- Any authenticated GBIF endpoint. The one GBIF call was the public download record. No
  download was requested.
- The dispatch file against the owner's upload (not in the repo).
- The notification email.
- The T2 branch beyond two reads by `git show`: the T2 run report's lines naming fca5e616, and
  the T2 DOI record's `created_utc`.
- The cause of 48 versus 46 in `ruff format --check`.
- CI on the runner; no run exists for this branch.
- Whether the 9,604 year-only rows would carry a day in the DWCA's verbatim.txt (the report's
  own first not-checked item; the T2 archive is on the other branch).
- The uncertainty step's drops by cause (missing, obscured, above 1,000 m); the report says the
  T2 run report has a split at 250 m, not re-read here.
- The Python 3.12 fallback beyond parsing one file; no test was run under 3.12.

Renamed 2026-09-20 under D35. This document is a builder self-check, not a review under D18. The review of record is at docs/audits/2026-09-18-t1-credentialed-run-review.md.
