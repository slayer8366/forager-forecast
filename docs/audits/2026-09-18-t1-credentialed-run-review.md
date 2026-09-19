# T1 review: the credentialed run, download and count tables

**Date:** 2026-09-18 (machine local time, UTC-7).
**Type:** review under docs/dispatch/2026-09-18-review-protocol.md, ordered by D32 (DECISIONS.md on
main, "the credentialed-run commits on T1 (four) and T2 (three) are reviewed before anything else
of theirs merges").
**Reviewed:** branch t1-calendar-smoke-test, commits 34933e8..691bef3, five commits:
ade7ce6 (loader, filters, count script, 21:05:11), 8c45daa (DOI record and renderer, 21:13:45),
f04c209 (report and filed dispatch, 21:19:38), 09ce2ef (index, session log, TASKS cell, 21:20:00),
691bef3 (DOI record note, 22:00:00). The report under review is
docs/audits/2026-09-18-t1-credentialed-run-report.md. Everything before 34933e8 was reviewed in
docs/audits/2026-09-18-t1-review.md and is not re-reviewed here.
**Reviewer base commit and branch:** t1-credentialed-run-review cut from 691bef3, tree clean. This
review is the first commit on that branch. `git fetch origin t1-calendar-smoke-test` at the start
and again before this commit: the tip was 691bef3 both times; it did not move. origin/main moved
during the review from 218a7df to ef6c82a (the D30 header and D31 corrections folded in); that
touches no file this review compares against.

The reviewer is a separate agent session from the builder and read the repo, not the builder's
chat. The reviewer holds no GBIF credentials and did not enter the worktree that holds the
download zip, so nothing was re-run on the file itself; check 9 says what was re-derived instead.
Every claim below names a file and line, a commit, a URL opened today, or a command whose output is
quoted, or is marked inferred. Line numbers for the report refer to the file at 691bef3.

## Summary

Nothing in the five commits contradicts a decision row as it stood when the run was made (D13 to
D23 on the branch), a fixed term, or a fixed choice. The predicate GBIF stored is equal to the file
fixed at ac12f55, and every filter function is byte-unchanged since that commit. The row accounting
adds up, the four source-stage counts reconcile to the earlier search-API preview to the record,
the suite, lint and format reproduce, the revert check bites, and every live figure the reviewer
could reach (download metadata, dataset list, one preview count) matches the report. Two items go
to the owner, neither a contradiction of a row: the account's username appears in the committed
report, quoted from Cowork's report (check 4), and the dispatch file this run filed is not on main,
so the "byte-identical to main" premise the reviewer was given could not be checked (check 5). Four
rulings made after the run (D26, D28, D29, D33) now ask for things this run did not produce; they
are listed under check 10 as gaps, not drift.

## Drift checks

### 1. Terms. Holds.

- The label the protocol's check 1 names ("fruiting probability") appears in none of the twelve
  files the diff touches except the two planning files where it was already banned:
  `git diff 34933e8..691bef3 --name-only | xargs grep -n -i -E 'fruiting probability|probabilit|calibrat|relative habitat'`
  returns START_HERE.md:8, 14, 34, 35 and TASKS.md:77, 79, all pre-existing text outside the diff
  hunks. Nothing in src, tests, scripts, the report, the DOI record or the dispatch.
- "percent" in the report appears at lines 313, 314, 328 and 394, all about record fractions
  (licence share, usable share), never about relative habitat.
- "sighting chance" is not used in the new code, and the report says why (report 423: no chance
  is estimated here).
- No em dash in any touched file (`grep -P '\x{2014}'` returns nothing).

### 2. Decisions. Holds against D13 to D23; four later rulings supersede choices, recorded under check 10.

Compared against the branch's own DECISIONS.md (ends at D23) and against D24 to D34 on main
(`git show origin/main:docs/planning/DECISIONS.md`).

- D13 (target-group negatives, GBIF download with a DOI): the run made one GBIF download and no
  substitute; no design was coded. `git diff 34933e8..691bef3 --name-only | grep '\.py$' | xargs
  grep -n -i -E 'lightgbm|open_meteo|archive-api|pseudo|sample|random|fit\(|urlopen|requests\.'`
  returns nothing.
- D19, D21, D25 (Open-Meteo pinning): no archive request was made; the report says so (report 37)
  and the grep above finds no request path in the new files.
- D22 (private, no licence file): `git ls-files | grep -i licen` still returns nothing.
- D27 (taxon in the duplicate key): records.py:96 keys on `(taxon_key, lat_tenths, lon_tenths,
  event_date)`, which is D27's event key. Holds before D27 was written.
- D28 (stricter date rule stands provisionally): records.py:76-83 is the stricter rule, unchanged
  since ac12f55, and the report measures both rules (report 334-350). D28 also asks the counts
  report for a day-of-month table by dataset; absent, ruled after the run, check 10.
- D29 (licence gate): the by-licence table is present (report 298-313). D29 also asks for a
  constituent dataset list with licence and count filed next to each DOI; absent, ruled after the
  run, check 10. Nothing derived from any record is shipped: no output beyond count tables exists.
- D26 (one geometry-selected archive download for T1 and T2): this run's SIMPLE_CSV download is
  the "first download" D26 keeps as provisional and superseded. Not drift by this run, which
  followed the dispatch's "predicate already fixed on the branch. Do not change it now"
  (dispatch line 32). The DOI record's `superseded_by` is `null` and its `why_provisional` names
  only the business-account redo, not the D26 supersession; check 10.
- The report's owner item 3 (report 391) reads D26 as "moot in one direction" because T2's
  download is a separate archive. D34 accepted D26 as written, so that reading was not adopted.
  A proposal-level remark, not a built thing; recorded so nobody cites it as the ruling.
- D33 (3) asks the counts report to split the uncertainty step into no-stated-uncertainty and
  above-the-limit; the report lists that split as not checked (report 405-407). Ruled after the
  run, check 10.

### 3. Fixed choices. Holds.

The check that matters most here. Three comparisons and a timeline.

- Predicate. `git diff --stat ac12f55 691bef3 -- src/forager_forecast/gbif/t1_fungi_two_boxes_2015_2025.json`
  is empty; `git log ac12f55..691bef3 -- <that file>` lists no commit. Parsed as JSON and compared:
  file at ac12f55 == file at 691bef3 == `request.predicate` in the public download record
  (`curl -s https://api.gbif.org/v1/occurrence/download/0005709-260916113435855`, opened today)
  == the predicate in docs/pulls/t1-fungi-two-boxes-2015-2025.doi.json. All four equal (Python
  `==` on the parsed objects, observed). Kingdom 5, HUMAN_OBSERVATION, YEAR 2015 to 2025,
  HAS_COORDINATE true, two polygons at the dispatch's box limits.
- Boxes, year range, thresholds, windows. `git diff --stat ac12f55 691bef3 --
  src/forager_forecast/t1_design.py src/forager_forecast/cells.py` is empty. The records.py diff
  (`git diff 34933e8..691bef3 -- src/forager_forecast/records.py`) adds the `license` field, the
  `T1_FILTER_STEPS` tuple, `SOURCE_STAGE` and `apply_t1_filters_observed`, and rewrites
  `apply_t1_filters` as a delegate; it touches no line of `drop_uncertain_coordinates` (65-73),
  `is_default_date` (76-83) or `keep_one_per_taxon_cell_day` (90-100). The step list in
  T1_FILTER_STEPS (107-113) is the same five names in the same order as the loop it replaced.
- Timeline. The download was created 2026-09-19T03:57:12Z (20:57:12 local) and succeeded
  04:10:34Z (21:10:34 local), from the public record. ade7ce6, which holds the loader, the filter
  refactor and the count script, was committed at 21:05:11 local, after the request and before
  any row of the file existed on the machine. So the code the counts ran through was fixed before
  a count could be seen. 8c45daa (21:13:45) and everything after it post-date the download's
  success. 8c45daa holds the DOI record (with the zip's sha256, so the zip had arrived) and the
  renderer, and the renderer carries the second reading of the premise, "years with at least 100"
  (t1_render_tables.py:9-10, 61). Cannot tell whether the count run had finished before 21:13:45
  (the run takes 2:08, report 213). That threshold is a way of reading a count, changes no
  count, no filter and no box, and D33 (1) has since fixed the reading; recorded so the timing is
  on file.
- The count script pre-sorts rows by box and year and runs the filters once per box and year
  (t1_count_table.py:79-116). The report's claim that this is exact (report 359-362) holds:
  every step is per record except the duplicate step, whose key holds the event date
  (records.py:96), and the two boxes share no 0.1 degree cell (they are 37 degrees of longitude
  apart, t1_design.py unchanged). Inferred from the code, not re-run.

### 4. Scope. Gap, on one do-not-touch item; holds on everything else.

- The dispatch said pull, count, verdict on the premise, stop. No model fit, no sampler, no
  weather: check 2's grep. The diff touches twelve files (`git diff --stat 34933e8..691bef3`):
  two source modules, two scripts, two test files, the DOI record, the report, the filed
  dispatch, one index row, one session log row, one TASKS.md cell. Nothing else.
- DECISIONS.md, SPEC.md and the Fixed terms table: `git diff --stat 34933e8..691bef3 --
  docs/planning/DECISIONS.md docs/planning/SPEC.md` is empty; START_HERE.md's diff is one
  appended session log row.
- The password. `git diff 34933e8..691bef3 | grep -nE 'GBIF_USER|GBIF_PWD|GBIF_EMAIL'` finds the
  three names only as names (report 76-78, 92, 100; the dispatch; the DOI record's
  `submitted_with`). A grep of the diff for `password|passwd|pwd=|Basic [A-Za-z0-9+/=]{10,}|
  Authorization|token|@[a-z0-9.-]+\.(com|org|net)` finds the word "password" in prose only, no
  header value, no base64 string, no email address. The 70-byte file's contents appear nowhere.
  The one authenticated command shown (report 92) takes the password from the environment. The
  public download record carries no `creator` and no `notificationAddresses` (observed, both
  keys absent from `request`), so the DOI page leaks neither. Holds.
- **The gap.** Report line 52 reads: "The username is `b.wann`, not an organisation name". That
  is the value of GBIF_USER, committed to the repo in a report, quoted from Cowork's report. The
  dispatch's do-not-touch names the password only ("The password is never printed, logged,
  committed or pasted into a report", dispatch 43), and its verify-first item 2 says "Do not
  print any value" about the credentials file, which the builder honoured (report 73-83 prints
  names only). The reviewer was told to treat all three values as credentials. The repo is private
  (D22) and a GBIF username is not a secret in the way a password is, so this is a gap for the
  owner's reading, not drift. Proposed fix, owner's call: append a dated note to the report
  (never edit line 58) saying whether the username may stay on record; if not, the line stays
  in history regardless, so the useful action is a rule for future reports rather than a
  rewrite. The reviewer did not change the report.
- Downloads one at a time: the report says T2 was requested only after T1 SUCCEEDED (report
  123); the T2 branch is outside this review, so that is read, not observed.

### 5. Record. Holds, with one wrong premise and two small gaps.

- Rows appended, not edited. docs/audits/README.md: one row appended at line 27. START_HERE.md:
  one session log row appended at line 69. TASKS.md: the T1 status cell (line 11) rewritten in
  place, from the blocked wording to the counts-reported wording; that is how the T1 review
  (check 5) treated the same cell and how TASKS.md is used. DECISIONS.md and SPEC.md untouched.
  691bef3 appends two keys to the DOI record, one of them dated
  (`integrity_check_2026-09-18`), and edits nothing that was there.
- Report header carries the base: report 7-9, "branch t1-calendar-smoke-test at 34933e8 (the T1
  review) over main f96d557", with ade7ce6 and 8c45daa named.
- The DOI record marks the download provisional: `"status": "provisional"` with `why_provisional`
  naming the test account and the redo, `superseded_by: null`, the full request stored beside
  it (docs/pulls/t1-fungi-two-boxes-2015-2025.doi.json:3-4, 16-62, 66). The dispatch's three
  test-account rules (dispatch 27-28) are each met: query beside the DOI, provisional mark, and
  no count pinned in a test (`grep -rn -E "1195034|1,195,034|3425|1226|2748|142238|447164"
  tests src` returns only gbif_download.py:7, a docstring quoting the earlier predicate-search
  count).
- **Wrong premise, reported as a finding.** The reviewer was asked to confirm the filed dispatch
  is byte-identical to the one on main with `git diff origin/main -- docs/dispatch/2026-09-18-t1-t2-credentialed-run.md`.
  That file is not on origin/main at 218a7df or at ef6c82a (`git rev-parse origin/main:<path>`
  fails, "exists on disk, but not in 'origin/main'"). It exists on origin/t1-calendar-smoke-test
  and origin/t2-record-audit as the same blob, 9ceb685 (`git rev-parse <branch>:<path>` on every
  remote branch). So the two branches filed one identical text, and the report's own claim
  (report 155, "filed byte-identical to the owner's upload (`cmp`)") is against an upload that is
  not in any repo and cannot be checked from here. Cannot tell on the upload; holds on the two
  branches agreeing.
- Small gap, closed by this header: the index row and session log row name 34933e8, ade7ce6,
  8c45daa and f04c209, and cannot name 09ce2ef or 691bef3 (the row's own commit and one after).
  This review's header names all five, as the T1 review did for its three.
- Small form point, not fixed because a row is never rewritten: the new index row's file column
  reads `docs/audits/2026-09-18-t1-credentialed-run-report.md` where every earlier row uses a
  backticked path relative to docs/audits/. Both resolve.

### 6. Data hygiene. Holds, with a register gap now owned by D29.

- `git ls-files` at 691bef3 lists 63 files. The only JSON files are the pre-existing evidence
  file, the predicate, and the DOI record (69 lines). No CSV, zip, parquet or anything under
  data/: `git ls-files | grep -E '^data/'` is empty. `git check-ignore -v data/t1` names
  .gitignore:6.
- Largest tracked files: uv.lock 41,201 bytes, then the T1 completion report 32,207, the lag
  atlas HTML 29,734, the report under review 26,711.
- `./scripts/check-large-files.sh --all` printed `63 file(s) checked, none over 1048576 bytes`,
  exit 0. The report's figure of 61 (report 181) was taken at 8c45daa, where `git ls-tree -r
  691bef3^^^ | wc -l` is 61; f04c209 added the report and the dispatch. Counts per commit: 55,
  59, 61, 63, 63, 63.
- Licence. The by-licence table is in the report (298-313) and in the run's counts_by_license.csv
  (not in git, by design). Three licences, no empty value, CC BY-NC at 92 and 89 percent of the
  usable Cantharellus records (re-computed: 1,127/1,226 = 91.9, 2,436/2,748 = 88.6). Nothing is
  shipped or published: the run produced count tables and nothing else. DATA_REGISTER.md's GBIF
  row still reads "Per record" (main, line 20); D29 now asks it to point at a per-DOI dataset
  list, which does not exist yet (check 10).

## Evidence checks

### 7. Claims carry evidence. Holds, with a short list.

File-and-line references spot-checked and found accurate: simple_csv.py:1-18 (docstring on what
a row lacks), 67-106 (`parse_event`), 141-148 (genus key by name match); records.py:76-83
(`is_default_date`, "T00:00" equals 00:00:00), 116-136 (the delegate); gbif_download.py:99-124
(`submit_download_request`); t1_count_table.py:1-15 (one box at a time); .gitignore:6. The
"read, observed, inferred" labels are used throughout (report 13-15 states the rule, and the
tables carry a Source column).

Arithmetic re-done from the printed tables (a script over the report text, observed):

- Every stage row's eleven years sum to its printed total, in all four tables, and no year
  increases from one stage to the next.
- 250,269 + 935,156 = 1,185,425 loadable; 1,185,425 + 0 + 9,609 = 1,195,034 = totalRecords.
  9,604 + 1 + 4 = 9,609.
- Preview reconciliation: 3,425 + 0, 250,269 + 4, 5,503 + 42, 935,156 + 9,605 equal 3,425,
  250,273, 5,545, 944,761, which are the T1 completion report's preview table (that file, lines
  83-86). All four to the record, as claimed.
- The eight licence rows each sum to their total.
- The default-date step drops 7, 164, 2 and 403 in the four tables; the measured table (report
  340-345) gives 7 + 0, 157 + 0 (+7), 2 + 0, 396 + 5 (+2): 562 of 567 date-only, 5 at 00:00, 9
  Cantharellus. All as printed.
- Premise table: PNW final years 3, 8, 12, 29, 79, 111, 122, 97, 98, 345, 322 give 11 with any,
  4 at or above 100, smallest 3; East 12, 28, 65, 196, 203, 323, 502, 220, 571, 319, 309 give 11,
  8, smallest 12. As printed.

Claims that do not hold as printed, or carry no evidence the reviewer could reach:

- Report 328: "the PNW's usable records are 27 percent of the 2015 to 2018 preview counts". The
  numbers on the page give 52 of 181 (26 + 31 + 53 + 71), which is 28.7 percent, so 29. The
  sentence's point (those four years are thin) is unaffected. Not edited; a later note can
  supersede it.
- Report 179: "46 files already formatted". The reviewer sees 48. Cause found this time: ruff's
  resolver includes 49 paths here, the 24 Python files plus pyproject.toml and 24 Markdown files
  (`ruff format --check . -v`, "Included path via `include`"), so the figure grows by one for
  every Markdown file added, and f04c209 added two. The same effect explains the T1 review's 39
  versus 40, which it left undetermined.
- Observed by the builder only, no output quoted and not reproducible without the file: the
  clock-time shape "T00:00" on rows 4 to 6 (report 169-171); the zip's sha256 and `unzip -t`
  (DOI record 11, 67); the elapsed 2:08.51 and 454,040 kB (report 213); the nine-row positive
  control's printed line (report 203-207); the T2 download's state.
- Report 137: the download licence "CC BY-NC 4.0 (the most restrictive licence among the
  records, inferred from GBIF's practice)" is marked inferred, correctly; the public record's
  `license` field agrees.

### 8. Revert check. Holds.

A different edit from the builder's two, so this is a third line proven to be guarded.

- Saved a copy: `cp src/forager_forecast/simple_csv.py /tmp/t1review_simple_csv.py.bak`, sha256
  467268dc...92d65 recorded.
- One-line edit at simple_csv.py:142: `row.get("kingdom", "").strip() == FUNGI_KINGDOM_NAME`
  replaced by `True`, so the genus name alone decides Cantharellus. `git diff --stat`: one file,
  one line.
- Ran only the module: `uv run pytest -q tests/test_simple_csv.py`. `1 failed, 26 passed in
  0.13s`, no collection or import error. The failure is
  `tests/test_simple_csv.py:96 ... assert record_from_row(row(kingdom="Animalia")).genus_key is
  None`, `AssertionError: assert 9623860 is None`, with the Record printed showing
  `kingdom: 'Animalia'` and `genus_key=9623860`. Only removing the kingdom condition makes an
  Animalia row carry the Cantharellus key, so the message is specific to the edit. The two
  earlier assertions in that test (genus Laetiporus, genus empty) still passed, as they should.
- Restored with `cp` from the saved copy, not from git. `sha256sum -c` printed `OK`;
  `grep -c 'and True$'` printed 0; `git status --short` and `git diff --stat` empty; the module
  then passed, `27 passed in 0.10s`.

The builder's two revert checks (report 188-199) are described with edit-specific messages
(`'inside a T1 box' != 'source'` for the removed source call; `DID NOT RAISE UnloadableRow` on
the three cross-day cases). Not re-done; the descriptions name failures only those edits produce.

### 9. Headline numbers re-run. Holds for everything reachable; the counts on the file cannot be re-run from here.

From the clean tree at 691bef3 (`git status --short` empty),
`~/.local/bin/uv sync --locked --all-groups`, then:

```
uv run ruff check .            -> All checks passed!               (report: same)
uv run ruff format --check .   -> 48 files already formatted       (report: 46; explained in check 7)
uv run pytest -q               -> 83 passed in 3.59s               (report: 83 passed in 1.08s)
./scripts/check-large-files.sh --all -> 63 file(s) checked, none over 1048576 bytes (report: 61 at 8c45daa)
```

Live, without credentials, all public endpoints, opened today:

- `GET https://api.gbif.org/v1/occurrence/download/0005709-260916113435855`: doi
  10.15468/dl.hdkjmn, status SUCCEEDED, created 2026-09-19T03:57:12.022+00:00, modified
  04:10:34.821+00:00, totalRecords 1195034, numberDatasets 15, size 163662303, license
  by-nc/4.0, eraseAfter 2027-03-19T03:57:11.907+00:00, request.format SIMPLE_CSV,
  request.sendNotification true. Every one equals the DOI record and the report's download table.
  The stored predicate equals the branch file (check 3).
- `GET .../download/0005709-260916113435855/datasets?limit=50`: 15 datasets whose numberRecords
  sum to 1,195,034. The three largest: iNaturalist research-grade 948,169; the New Jersey
  2007-201x fungi dataset (fca5e616) 156,744; Mushroom Observer 86,698; then the 2018 New Jersey
  dataset (2b169d34) 1,877. This is the dataset half of the D29 list, obtainable without the
  file; the licence half needs one `GET /dataset/{key}` each, not done here.
- One search-API count from the preview table:
  `occurrence/search?taxonKey=9623860&hasCoordinate=true&basisOfRecord=HUMAN_OBSERVATION&decimalLatitude=42.0,49.5&decimalLongitude=-125.0,-121.0&year=2015,2025&limit=0`
  returned count 3425, and the same for year=2015 returned 26. Both equal the preview table and
  the report's PNW Cantharellus source row (3,425; 26 for 2015).
- `curl -sIL` on the download link: 302 to occurrence-download.gbif.org, then 200 with
  content-length 163662303 and `etag: "9c149df-65bce2b6609d0"`. 0x9c149df is 163,662,303, so the
  tag is size and mtime, not a content hash: the 691bef3 note holds.

Not re-run, because the zip sits in another session's worktree the reviewer must not enter: the
count run itself (every number below the source stage), the row accounting, the unloadable-row
reasons, the licence table, the default-date measurement and the positive control. What stands
in for it: the source-stage counts equal an independent live count (above), the accounting
identity closes on the printed numbers, and every stage total and licence row sums (check 7).
The numbers below the source stage rest on the builder's run and the code reviewed in check 3.

## Gaps

### 10. What the dispatch asked for that the report does not evidence, what is marked not checked, the premise, and what D26 now requires. Gap, mostly by rulings made after the run.

Asked by docs/dispatch/2026-09-18-t1-t2-credentialed-run.md and evidenced: the four verify-first
items, the DOI with its query, the counts by box, year, filter step and licence, the premise
verdict, the large-file guard, a Conventions line, a not-checked list. All present. Not evidenced
from the repo: the `cmp` against the owner's upload (check 5), and "Request downloads one at a
time" beyond the report's word (check 4).

Marked not checked by the report (398-412), all still open: whether the 9,604 year-only rows are
the New Jersey dataset's convention (the public dataset list confirms fca5e616 is the New Jersey
2007-201x dataset with 156,744 records in this download, which is consistent with the report's
9,330 but does not answer the question); whether date-only first-of-month rows are defaulted
dates; the uncertainty step's split; the notification email; two simultaneous requests; CI on
this branch (no pull request, so no run); the T2 download's contents.

The premise, under both readings, as D33 now settles it: the report shows both (report 318-332)
and calls the literal reading met in both boxes, the stricter reading met in the East only. D33 (1)
rules the premise "met in both boxes, with the Pacific Northwest recorded as thin: its useful data
is 2019 to 2025". The report's numbers support that ruling exactly: PNW 2019 to 2025 hold 1,174 of
the 1,226 usable records, 2015 to 2018 hold 52. No fold restriction was made (D33 (2)), and none
is in the code.

What later rulings now ask of this run's download, none of them drift and none yet done:

- D26: this download is kept as provisional and superseded. When the geometry-selected archive
  download exists, its two-box subset must contain every record key from this download's
  1,195,034 rows or explain each missing key, with the differences reconciled in a report. The
  DOI record needs a superseding entry then; today `superseded_by` is `null` and `why_provisional`
  names only the business-account redo. Proposed fix, for the session that runs the archive
  download: append to the DOI record, do not edit the existing keys.
- D28: a day-of-month table for date-only records, by dataset. Not in this report. datasetKey is
  one of the file's 50 columns (report 375-377), so it can be produced from this download.
- D29: a constituent dataset list with licence and record count filed next to the DOI, and the
  Data register's GBIF row pointed at it. The dataset half is public (check 9); the licence half
  is one request per dataset.
- D33 (3): the uncertainty filter split into no-stated-uncertainty and above-the-limit, and the
  5,000 m sensitivity run. The report lists the split as not checked.
- D31: seed 20260918 and the 20-configuration grid. Nothing here draws or fits, so nothing to
  check yet; the grid is not yet written into the repo.

One further item the reviewer adds, unverified: scripts/t1_count_table.py:55 reads
`except KeyError, ValueError:` with no parentheses. That parses on the pinned Python 3.14.4 (the
suite imports it, and `ast.parse` on the file succeeds here). From memory, not checked: that form
was added in Python 3.14 and is a syntax error on 3.12, which D20 names as the fallback. If the
fallback is ever exercised, this line is the first thing to break. Not changed, because it is code
under review and the fallback has not been invoked.

## What the reviewer changed

This file, and one row appended to docs/audits/README.md, in one commit on branch
t1-credentialed-run-review over 691bef3. Nothing in src, tests, scripts, the report, the DOI
record, or any planning file. No pull request opened, no merge. Commit hash: in the final message
to the launching session.

## Conventions

Checked in this repo at 691bef3: docs/dispatch/2026-09-18-review-protocol.md for the ten checks,
the verdict words and the output form; docs/audits/README.md for the index row form and the
append-only rule; docs/audits/2026-09-18-t1-review.md for the header fields and the shape of a
revert check write-up; the Forager CLAUDE.md rules on revert checks (save a copy, restore from it
and never from git, check for collection errors before reading failures, confirm the tree is clean
afterwards), on citing a figure with its scope, and on reading a check's sample before citing it.
Followed all of them. The reviewer entered no other worktree, read no credentials file, and made
no authenticated request. "Sighting chance" is not used because no chance is estimated; the label
check 1 searches for appears in this file only inside check 1. No em dashes.

## Not checked

- Anything on the download zip itself: every number below the source stage, the sha256, `unzip -t`,
  the row shapes, the positive control. The file is in a worktree this reviewer may not enter.
- The `cmp` of the filed dispatch against the owner's upload; the upload is not in any repo.
- The builder's two revert checks; one different revert was done instead.
- The T2 branch and its report, beyond the fact that it carries the same dispatch blob.
- Cowork's credentials report and the credentials file: not opened, by instruction. The report's
  account of them (report 43-86) is read, not observed.
- The per-dataset licences behind the D29 list.
- Whether GBIF limits concurrent downloads; the report could not find it in the docs page either.
- CI on the runner: no run exists for this branch.
- Python 3.12 against t1_count_table.py:55; the system Python here is 3.14.4.
- The notification email GBIF sent.
