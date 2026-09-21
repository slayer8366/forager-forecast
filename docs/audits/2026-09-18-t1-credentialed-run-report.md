# T1 credentialed run: credentials proven, download requested, count tables produced, stopped

**Date:** 2026-09-18 (machine local time, UTC-7). GBIF's own timestamps below are UTC and fall on
2026-09-19.
**Type:** run report for docs/dispatch/2026-09-18-t1-t2-credentialed-run.md, the T1 half. The T2
half is reported on branch t2-record-audit in docs/audits/2026-09-18-t2-credentialed-run-report.md.
**Base:** branch t1-calendar-smoke-test at 34933e8 (the T1 review) over main f96d557, which was
still origin/main when this was written. Code commits ade7ce6 and 8c45daa; this report is the next
commit; the index row, session log row and TASKS.md cell follow in one more.
**Supersedes:** nothing. It answers "Verify first" item 1 of the T1 dispatch, which the T1
completion report (f9890ad) left at "neither confirmed nor disproved".

Every claim below names a file and line, a commit, a URL opened today, or a command whose output
is quoted, or is marked inferred. Observed means this session saw the output; read means a
document was opened; inferred is marked as such.

---

## The short version

- **The credentials are real and work.** The file the owner's Cowork session described exists at
  the stated path with mode 600 and the three names, outside every repository, and one
  authenticated request to GBIF returned HTTP 200 while a made-up user returned 401.
- **The T1 download exists.** DOI **10.15468/dl.hdkjmn**, key 0005709-260916113435855, 1,195,034
  records, requested with the predicate fixed at ac12f55 and unchanged, format SIMPLE_CSV with
  the license column kept. The request GBIF stored equals the branch's predicate file. It is a
  **provisional** DOI from a test account (Cowork's report; "Test account rules" below).
- **The count tables are below**, by box, year and filter step for Cantharellus and for all fungi,
  and by license. Every row of the file is accounted for: 1,185,425 loadable rows inside a box,
  9,609 rows with no single-day date, 0 outside the boxes, sum 1,195,034, equal to the download's
  totalRecords. The source-stage counts equal the T1 completion report's search-API preview to
  the record once the unloadable rows are added back.
- **The premise holds under its literal reading in both boxes and is thin in the PNW.** Usable
  Cantharellus records after every filter: PNW 1,226 over 11 years, East 2,748 over 11 years. In
  the PNW only four years reach 100 and 2015 to 2018 hold 3, 8, 12 and 29. Whether that is "at
  least 8 years" in the sense the dispatch meant is the owner's reading; both readings are shown.
- **Stopped here.** No model was fit, no sampler ran, no weather was pulled. The T2 download was
  requested only after the T1 download had succeeded (one at a time, as instructed) and was
  still running when this report was written; it is reported on its own branch.

## Verify first, as answered

### 1. Cowork's report, found and read in full

`find ~ -name gbif-credentials-report.md` returned one file,
/home/zynergy-labs/Labs/gbif-credentials-report.md (4,638 bytes, mode 600, next to
gbif-credentials.sh, 4,256 bytes; neither inside a git repository). Read in full. Its four
stated differences from the dispatch it worked from:

1. Cowork did not create the account; the owner registered, running a script Cowork supplied,
   so no password passed through an agent.
2. The username is `b.wann`, not an organisation name; owner's decision, closed.
3. The password is under 24 characters and owner-chosen (inferred by Cowork from the 70-byte file
   size), accepted for a throwaway test account.
4. No password manager entry; Cowork did not check whether one is set up.

Its unchecked items, as listed there: whether the owner accepted GBIF's terms and data user
agreement; whether an account already existed for the email; whether the password is in a
browser's saved logins; whether a download request succeeds (this report answers that: yes);
whether GBIF can transfer a download between accounts (moot, downloads will be redone); and the
forager-forecast repo itself, which Cowork could not see. Its "owner-reported" items, not
observed by Cowork: the username, the 200 on login, the folder and file modes.

Where the report and this dispatch disagree: nowhere on where the credentials live or what they
are named. The report adds one instruction the dispatch does not have, to load the file by
sourcing it rather than splitting lines on `=`, because a value may be quoted. Followed. The
report also says the account is a **test account** and gives three rules for it. Followed; see
"Test account rules".

### 2. The credentials file, checked without printing a value

```
$ stat -c '%a %U %n' ~/.config/forager-forecast/gbif.env
600 zynergy-labs /home/zynergy-labs/.config/forager-forecast/gbif.env
$ cut -d= -f1 ~/.config/forager-forecast/gbif.env      # names only, values never read here
GBIF_USER
GBIF_PWD
GBIF_EMAIL
$ cd ~/.config/forager-forecast && git rev-parse --show-toplevel
fatal: not a git repository (or any of the parent directories): .git
```

Observed. The `cut` splits on `=` only to list the names on the left of it; no value was printed
or used from that command. The folder is `drwx------`, 70 bytes in the file, both as Cowork
reported. The file sits under ~/.config, which is under no repository or worktree
(`git rev-parse` fails there).

### 3. One authenticated request, and a negative control

```
$ set -a; . ~/.config/forager-forecast/gbif.env; set +a
$ curl -s -o /dev/null -w '%{http_code}' -u "$GBIF_USER:$GBIF_PWD" https://api.gbif.org/v1/user/login
200
$ curl -s -o /dev/null -w '%{http_code}' -u "no-such-user-zz:x" https://api.gbif.org/v1/user/login
401
```

Observed. The password reached curl through the environment and appears in no command, log or
file this session wrote. Before any request the account had no downloads:
`GET /occurrence/download/user/$GBIF_USER?limit=10` (authenticated) returned `count: 0`.

### 4. Test account rules, applied

Cowork's report says the business will use a new account later and every download will be
redone under it, not moved. Its three rules and where each is met:

- **Store the query next to each DOI.** docs/pulls/t1-fungi-two-boxes-2015-2025.doi.json (8c45daa)
  holds the DOI, the key, the full request (format, sendNotification, predicate) and the path of
  the predicate file it came from. The creator and notification address are not recorded there.
- **Mark the DOI provisional.** The same file has `"status": "provisional"`, says why, and has an
  empty `superseded_by` for the business account's DOI to fill. The old entry stays.
- **Pin no record counts in any test.** No test on this branch contains 1195034, 3425, 1226 or
  2748 (`grep -rn -E "1195034|1,195,034|3425|1226|2748" tests src` returns only the docstring of
  gbif_download.py, which quotes the T1 report's predicate-search count and is not a test). The
  new tests run on synthetic rows only.

### 5. GBIF's concurrent-download limit: not confirmed, so one at a time

https://techdocs.gbif.org/en/data-use/api-downloads was fetched (34,293 bytes) and searched for
"concurrent", "simultaneous", "at a time", "at once", "limit", "per user" and "three downloads";
none of those phrases appears in its text. The dispatch's from-memory claim that GBIF limits
simultaneous downloads per account is therefore neither confirmed nor refuted here, and the
dispatch's fallback was followed: the T2 request was submitted only after the T1 download
reported SUCCEEDED.

## The download

| Field | Value | Source |
|---|---|---|
| Key | 0005709-260916113435855 | returned by `submit_download_request` (gbif_download.py:99-124), observed |
| DOI | 10.15468/dl.hdkjmn | GET /occurrence/download/0005709-260916113435855, saved as data/t1/downloads/0005709-260916113435855.metadata.json |
| Created | 2026-09-19T03:57:12Z | same |
| Succeeded | 2026-09-19T04:10:34Z (13 minutes) | same |
| totalRecords | 1,195,034 | same; equals the predicate-search count in the T1 completion report |
| Format | SIMPLE_CSV | same; `license` is column 43 of the file's 50 (header read with `unzip -p ... | head -1`) |
| Datasets | 15 | same, `numberDatasets` |
| Download licence | CC BY-NC 4.0 (the most restrictive licence among the records, inferred from GBIF's practice; the per-record split is in the license table) | same, `license` |
| Zip | 163,662,303 bytes, sha256 6468a431...a41683 (full hash in the DOI record) | `ls -l`, `sha256sum`, observed |
| Member | 0005709-260916113435855.csv, 734,590,434 bytes | `unzip -l`, observed |
| Predicate equal to the branch file | True | `d["request"]["predicate"] == json.load(open(PREDICATE_PATH))`, observed |
| Local copy | data/t1/downloads/, gitignored (`git check-ignore -v` names .gitignore:6) | observed |

The request was built and posted by the branch's own `submit_download_request` with credentials
from `credentials_from_env(os.environ)`, which was the one function the T1 report listed as never
exercised against the real endpoint. It returned the key on the first call. The request body
GBIF echoes back has `sendNotification: true` and the notification address, so the account's
email received GBIF's notice; nothing in this session read it.

## What landed

| Commit | Change |
|---|---|
| ade7ce6 | records.py: `license` field on Record (default ""), `T1_FILTER_STEPS`, `SOURCE_STAGE`, `apply_t1_filters_observed`; `apply_t1_filters` delegates to it. simple_csv.py: `read_rows`, `parse_event`, `record_from_row`, `UnloadableRow`, `missing_columns`, `is_cantharellus`. tests/test_simple_csv.py (27 cases), tests/test_records_observed.py (2). scripts/t1_count_table.py |
| 8c45daa | docs/pulls/t1-fungi-two-boxes-2015-2025.doi.json; scripts/t1_render_tables.py |
| next | docs/dispatch/2026-09-18-t1-t2-credentialed-run.md, filed byte-identical to the owner's upload (`cmp`), and this report |
| last | index row, session log row, TASKS.md T1 cell |

What the loader decides, because a SIMPLE_CSV row does not carry it (simple_csv.py:1-18):

- **genus_key.** SIMPLE_CSV has no genusKey column (T1 completion report, "GBIF's Simple download
  format"). `record_from_row` fills `Record.genus_key` with the Cantharellus key when the row's
  kingdom is Fungi and its genus is Cantharellus, else None (simple_csv.py:141-148). Every
  Cantharellus count below is by that genus-name match.
- **eventDate.** A Record needs one calendar day. `parse_event` (simple_csv.py:67-106) accepts a
  day, a day with a clock time (with or without seconds, a Z, or an offset), and a range whose
  two ends fall on the same day. It raises `UnloadableRow` with a reason for an empty value, a
  year-only or month-only value, and a range across days. The run script counts those rows by
  reason and box (unloadable_rows.csv); nothing is guessed and nothing is silently dropped.
- The file's clock times are of the form `T00:00` without seconds (observed on rows 4 to 6 of the
  file); `time.fromisoformat("00:00")` equals `time(0, 0, 0)`, so `is_default_date`
  (records.py:76-83) treats them as the dispatch's 00:00:00.

## Evidence

### Lint, tests, guard

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 46 files already formatted
uv run pytest -q               -> 83 passed in 1.08s     (54 before this run, 29 new)
./scripts/check-large-files.sh --all -> 61 file(s) checked, none over 1048576 bytes
git ls-files data | wc -l      -> 0
```

The pre-commit hook printed "none over 1048576 bytes" on each of the two code commits
(observed in the commit output).

### Revert checks, restored from saved copies

Each: `cp` the module to /tmp, `sha256sum` recorded, one line changed with `sed`, the affected
test file run, `cp` back from /tmp (never from git), `sha256sum -c`, `grep -c REVERT-MARK` = 0,
full suite re-run (83 passed). Neither reverted build had an import or collection error.

1. records.py, `observe(SOURCE_STAGE, current)` removed. tests/test_records_observed.py:
   `AssertionError: assert ['inside a T1...cell and day'] == ['source', 'i...cell and day']`,
   `At index 0 diff: 'inside a T1 box' != 'source'`. The failure names the missing source call.
2. simple_csv.py, the same-day check on ranges disabled (`if False:`). tests/test_simple_csv.py:
   3 failed, 24 passed, each `Failed: DID NOT RAISE UnloadableRow`, the three cross-day range
   cases. Only this edit lets a cross-day range through.

### Positive control for the run script

On a nine-row synthetic zip built to hit every branch (one row per: kept in PNW, other fungus
kept, kept in East, outside both boxes, month-only date, missing uncertainty, first-of-month at
00:00:00, duplicate of the first row, a 2021 date-only row), scripts/t1_count_table.py printed
`total_rows 9, loadable 7, outside 1, unloadable 1, accounted 9` and the PNW 2020 Cantharellus
column read 4, 4, 4, 3, 2, 1 down the six stages, each drop the row built to cause it.

### The real run

```
uv run python scripts/t1_count_table.py data/t1/downloads/0005709-260916113435855.zip data/t1/counts
Elapsed (wall clock): 2:08.51    Maximum resident set size: 454,040 kB    exit 0
```

Row accounting (data/t1/counts/summary.json):

| Rows in file | Loadable, inside a box | Outside both boxes | Unloadable | Sum | Download totalRecords |
|---|---|---|---|---|---|
| 1,195,034 | 1,185,425 | 0 | 9,609 | 1,195,034 | 1,195,034 |

Against the T1 completion report's search-API preview (its "Verify first" item 1 table), which
was taken before any download existed:

| Box, group | Preview | Source stage here | Unloadable rows in that box and group | Source + unloadable |
|---|---|---|---|---|
| PNW, Cantharellus | 3,425 | 3,425 | 0 | 3,425 |
| PNW, all fungi | 250,273 | 250,269 | 4 | 250,273 |
| East, Cantharellus | 5,545 | 5,503 | 42 | 5,545 |
| East, all fungi | 944,761 | 935,156 | 9,605 | 944,761 |

All four agree to the record. The unloadable rows are the difference, which is the check the
Forager CLAUDE.md asks for: the sample the count ran on is the whole file, and the part it could
not read is counted, not lost.

### Rows that could not become a Record

| Box | Reason | Rows | Shape and example | Publisher |
|---|---|---|---|---|
| East | eventDate does not name a calendar day | 9,604 | year only, e.g. `2018` | 9,330 from fca5e616 (the New Jersey fungi dataset named in the T2 report), 274 from 2b169d34 |
| East | eventDate spans more than one day | 1 | `2015-06-13/2015-06-14` | |
| PNW | eventDate spans more than one day | 4 | same shape | |

42 of the 9,604 year-only rows are Cantharellus, all in the East box (data/t1/counts/
diagnostics.txt). A year-only record has no week and could not enter the primary design in any
case.

## The count tables

Rendered by `uv run python scripts/t1_render_tables.py data/t1/counts` from
data/t1/counts/counts_by_box_year_step.csv. The first two filter steps re-check what the predicate
already selected and drop nothing, as the T1 completion report predicted.

### pnw, cantharellus

| Stage | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| source | 26 | 31 | 53 | 71 | 222 | 328 | 369 | 280 | 321 | 941 | 783 | 3,425 |
| inside a T1 box | 26 | 31 | 53 | 71 | 222 | 328 | 369 | 280 | 321 | 941 | 783 | 3,425 |
| year 2015 to 2025 | 26 | 31 | 53 | 71 | 222 | 328 | 369 | 280 | 321 | 941 | 783 | 3,425 |
| coordinate uncertainty present and at most 1,000 m | 4 | 8 | 15 | 34 | 89 | 121 | 141 | 132 | 108 | 401 | 378 | 1,431 |
| not a default date (first of month at 00:00:00) | 4 | 8 | 15 | 34 | 88 | 121 | 141 | 126 | 108 | 401 | 378 | 1,424 |
| one record per taxon, cell and day | 3 | 8 | 12 | 29 | 79 | 111 | 122 | 97 | 98 | 345 | 322 | 1,226 |

### pnw, all_fungi

| Stage | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| source | 2,492 | 3,073 | 4,088 | 7,635 | 13,498 | 23,467 | 27,978 | 25,323 | 40,744 | 47,077 | 54,894 | 250,269 |
| inside a T1 box | 2,492 | 3,073 | 4,088 | 7,635 | 13,498 | 23,467 | 27,978 | 25,323 | 40,744 | 47,077 | 54,894 | 250,269 |
| year 2015 to 2025 | 2,492 | 3,073 | 4,088 | 7,635 | 13,498 | 23,467 | 27,978 | 25,323 | 40,744 | 47,077 | 54,894 | 250,269 |
| coordinate uncertainty present and at most 1,000 m | 954 | 1,459 | 2,079 | 3,756 | 7,531 | 13,962 | 18,179 | 17,941 | 27,948 | 30,350 | 37,963 | 162,122 |
| not a default date (first of month at 00:00:00) | 939 | 1,444 | 2,070 | 3,743 | 7,517 | 13,946 | 18,172 | 17,897 | 27,939 | 30,333 | 37,958 | 161,958 |
| one record per taxon, cell and day | 843 | 1,334 | 1,866 | 3,519 | 6,795 | 12,631 | 16,165 | 15,654 | 24,110 | 26,718 | 32,603 | 142,238 |

### east, cantharellus

| Stage | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| source | 179 | 180 | 276 | 492 | 471 | 566 | 817 | 391 | 1,009 | 574 | 548 | 5,503 |
| inside a T1 box | 179 | 180 | 276 | 492 | 471 | 566 | 817 | 391 | 1,009 | 574 | 548 | 5,503 |
| year 2015 to 2025 | 179 | 180 | 276 | 492 | 471 | 566 | 817 | 391 | 1,009 | 574 | 548 | 5,503 |
| coordinate uncertainty present and at most 1,000 m | 13 | 29 | 69 | 207 | 214 | 345 | 522 | 235 | 609 | 330 | 337 | 2,910 |
| not a default date (first of month at 00:00:00) | 13 | 29 | 69 | 207 | 214 | 345 | 522 | 235 | 608 | 330 | 336 | 2,908 |
| one record per taxon, cell and day | 12 | 28 | 65 | 196 | 203 | 323 | 502 | 220 | 571 | 319 | 309 | 2,748 |

### east, all_fungi

| Stage | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| source | 37,811 | 41,061 | 47,372 | 69,323 | 72,499 | 87,402 | 109,818 | 91,612 | 126,875 | 118,720 | 132,663 | 935,156 |
| inside a T1 box | 37,811 | 41,061 | 47,372 | 69,323 | 72,499 | 87,402 | 109,818 | 91,612 | 126,875 | 118,720 | 132,663 | 935,156 |
| year 2015 to 2025 | 37,811 | 41,061 | 47,372 | 69,323 | 72,499 | 87,402 | 109,818 | 91,612 | 126,875 | 118,720 | 132,663 | 935,156 |
| coordinate uncertainty present and at most 1,000 m | 2,827 | 4,641 | 8,164 | 19,815 | 28,045 | 54,948 | 71,183 | 60,078 | 80,673 | 74,385 | 86,150 | 490,909 |
| not a default date (first of month at 00:00:00) | 2,782 | 4,585 | 8,117 | 19,757 | 27,991 | 54,909 | 71,164 | 60,061 | 80,652 | 74,355 | 86,133 | 490,506 |
| one record per taxon, cell and day | 2,602 | 4,262 | 7,582 | 18,486 | 25,648 | 51,044 | 65,159 | 55,456 | 73,612 | 67,699 | 75,614 | 447,164 |

### By license, at the source stage and after the last filter

From data/t1/counts/counts_by_license.csv, which also holds every intermediate stage.

| Box | Group | Stage | CC0_1_0 | CC_BY_4_0 | CC_BY_NC_4_0 | Total |
|---|---|---|---|---|---|---|
| pnw | cantharellus | source | 95 | 238 | 3,092 | 3,425 |
| pnw | cantharellus | one record per taxon, cell and day | 34 | 65 | 1,127 | 1,226 |
| pnw | all_fungi | source | 15,323 | 24,217 | 210,729 | 250,269 |
| pnw | all_fungi | one record per taxon, cell and day | 8,801 | 13,300 | 120,137 | 142,238 |
| east | cantharellus | source | 188 | 1,060 | 4,255 | 5,503 |
| east | cantharellus | one record per taxon, cell and day | 102 | 210 | 2,436 | 2,748 |
| east | all_fungi | source | 37,919 | 219,824 | 677,413 | 935,156 |
| east | all_fungi | one record per taxon, cell and day | 20,991 | 36,065 | 390,108 | 447,164 |

Three licences and no empty value appear in the file. CC BY-NC records are 92 percent of the
usable Cantharellus records in the PNW and 89 percent in the East (1,127 of 1,226; 2,436 of
2,748). The commercial-use question in SPEC.md, which D22 leaves open, bears on almost all of
the usable records.

### The premise

"Each box has at least 1,000 usable Cantharellus records across at least 8 years."

| Box | Usable Cantharellus records (last stage) | Years with any | Years with at least 100 | Smallest year | Verdict, literal reading (total at least 1,000 and at least 8 years with any) |
|---|---|---|---|---|---|
| pnw | 1,226 | 11 | 4 | 3 (2015) | holds |
| east | 2,748 | 11 | 8 | 12 (2015) | holds |

**Confirmed under the literal reading in both boxes.** What the owner should weigh before taking
"holds" at face value: the PNW's usable records are 27 percent of the 2015 to 2018 preview
counts and those four years contribute 52 records in total; leave-one-year-out validation
(dispatch, "Validation") will hold out a test year with 3 positives when it holds out 2015. The
East has at least 100 usable records in eight years. Under a stricter reading, "at least 8 years
each with a useful number of records", the East holds and the PNW does not.

### The default-date rule, measured

The T1 completion report widened the dispatch's rule from "first of month at 00:00:00" to "first
of month with no clock time at all" and left the choice to the owner (its owner item 4). On this
file, among the rows reaching that step:

| Box | Group | Date only | 00:00 clock time | Real clock time (kept) |
|---|---|---|---|---|
| pnw | cantharellus | 7 | 0 | 52 |
| pnw | other fungi | 157 | 0 | 5,375 |
| east | cantharellus | 2 | 0 | 90 |
| east | other fungi | 396 | 5 | 17,264 |

The step's drops (164 in the PNW, 403 in the East, from the tables above) equal the date-only
plus 00:00 columns. Under the dispatch's literal rule the step would drop 5 records in the East
and none in the PNW; the widened rule accounts for 562 of the 567 drops, including all 9
Cantharellus records. Whether date-only first-of-month rows are defaulted dates or ordinary
date-only observations that happen to fall on the first was not tested (see "Not checked"); the
counts are here so the owner can rule on item 4 with the number in view.

## Deviations from the dispatch

- **None on what was run.** Predicate, boxes, year range, format and filters are as fixed at
  ac12f55; the license column was kept; downloads were requested one at a time; the data sit
  under the gitignored data/ folder; the DOI is recorded with its query and marked provisional.
- **The count run holds one box in memory at a time** and runs the filters once per box and
  year (scripts/t1_count_table.py:1-15). That is exact for these filters: the only step that
  joins records, the duplicate step, keys on the event date, so no group crosses a year or a
  box. Stated because a reader of `apply_t1_filters` would expect one call over the whole file.
- **9,609 rows were not filtered** because they could not become a Record (no single-day date).
  They are counted separately rather than shown as a filter step, because the dispatch's filter
  list does not name such a step and adding one would be a filter change after seeing data.
  Their effect on the tables is in the preview comparison above.

## Decisions taken here, and what was rejected

- **The loader refuses rather than guesses** on a date that is not one day (simple_csv.py:67-106).
  Rejected: using GBIF's interpreted year, month, day columns to fill a day for year-only rows
  (they are empty for those rows by construction) or taking the start of a multi-day range as
  the day (a different date under the same field).
- **The publisher key went into the T2 license table, not this one.** T1's table is by box,
  group, stage and license, as the dispatch asks; datasetKey is one of the 50 columns and can be
  added if the owner wants it here. The T2 table has it because the T2 review's licence gate is
  per publisher.
- **`apply_t1_filters` now delegates to `apply_t1_filters_observed`** (records.py:116-136).
  Rejected: a second copy of the step list in the script, which could drift; and an `observe`
  parameter threaded into the existing function, which the Forager CLAUDE.md's building rule
  argues against.

## Owner items

1. **Read the premise table** and say whether "holds" stands for the PNW given 3, 8, 12 and 29
   usable records in 2015 to 2018. Modelling waits on that (dispatch: "Report and stop.
   Modelling waits for the owner").
2. **Rule on the default-date rule** (T1 completion report owner item 4) with the measured
   table above in view: 9 Cantharellus records and 553 other records turn on it.
3. **Weather pull (D24), D25, D26** remain as the T1 completion report left them. D26 is now
   moot in one direction: the T2 download is a separate DWCA request over North America
   (T2 run report), so T1's SIMPLE_CSV and T2's DWCA both exist; whether T1 should later read
   the T2 archive instead is a question for when a model is built.
4. **The licence gate.** 89 to 92 percent of the usable Cantharellus records are CC BY-NC.
   DATA_REGISTER.md's GBIF row still reads "Per record" (T2 review, check 6); the per-publisher
   split is in the T2 run report's license table.

## Not checked

- Whether the 9,604 year-only rows are the New Jersey dataset's convention or a GBIF
  interpretation of a verbatim date the DWCA would show differently. The T2 archive carries
  verbatim.txt and can answer.
- Whether date-only first-of-month rows are defaulted dates. The test would compare the share
  of first-of-month dates among date-only rows with the share among timed rows; not run.
- How the uncertainty step's drops split between missing uncertainty, obscured (about 26 km and
  up), and merely above 1,000 m. The T2 pipeline names the obscured step separately at its own
  threshold, so the T2 run report has the split at 250 m, not at 1,000 m.
- The notification email GBIF sent to the account's address.
- The behaviour of GBIF's download endpoint under two simultaneous requests; not attempted.
- CI on this branch: no pull request is open, so the workflow has not run; the same three
  commands passed locally at 8c45daa and again before this report.
- The T2 download's contents; it was still RUNNING when this report was written.

## Conventions

Checked in this repo at 34933e8: docs/audits/README.md for the index form and the append-only
rule; the T1 completion report and T1 review for the header fields, "The short version" first,
and the read/observed/inferred labels; docs/pulls/ on the T2 branch for where a request record
lives; pyproject.toml for exact pins and ruff settings; .gitignore for data/; the Forager
CLAUDE.md rules on revert checks (saved copy, affected module, build must import, restore from
the copy, verify the tree afterwards), on citing a figure with its scope, and on counting a
check's sample against something outside it (the preview comparison and the row accounting
above). Followed all of them. "Sighting chance" is not used here because no chance is estimated;
the phrase the terms check searches for appears nowhere in the added files. No em dashes.
