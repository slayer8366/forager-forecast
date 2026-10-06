# D26 shared download: completion report

Answers `docs/dispatch/2026-10-06-d26-shared-download.md`. Written 2026-10-06 (UTC) by the coder
session on the credentials machine (D38), branch `d26-shared-download`, worktree
`~/Zynergy/forager-forecast-d26`. Base `origin/main` `ad64fef`, re-checked unmoved before the build.
The verify-first report is `2026-10-06-d26-verify-report.md`; its two stops were answered by the owner
through the Forager planner session (Forager RECORD -576), and that answer was the go.

**One GBIF download was requested and fetched once:** key `0012112-260928105237408`, DOI
`10.15468/dl.8jxmeb`, 2,493,578 records, provisional (test account). No Climate Data Store or
Open-Meteo pull, no model fit, no merge, nothing in the Forager app repository. No secret appears
here (D36). The account named by the request is the test account of the owner's GBIF credentials
report; its username and email are not recorded here.

"Read" means opened in this session; "observed" means command output from this session;
"inferred" is marked. Evidence is in `docs/audits/2026-10-06-d26-build/`: every script that ran, saved
as `.py.txt` and byte-identical to what ran from `/tmp/claude-1000/d26/`, with its JSON output.

## What landed

| Commit | What |
|---|---|
| `64ffb20` | D68 to D71, and the 109 to 117 test-count correction appended to the D32 follow-up completion report, with an index row |
| `6b8a1ab` | Verify-first report and evidence (`2026-10-06-d26-verify/`); two stops |
| `4b6a837` | D72, the owner's answer to stop 1, narrowing D71: GADM tag, else `country` where the tag is missing; the combined predicate's count |
| `8483d08` | Tests first, red: 8 failing, 211 passing |
| `49efa99` | Build, green: `d26_predicate`, `download_status`, `fetch_download` in `records/gbif_download.py`; count region renamed `outside_t1_boxes` |
| `e061a43` | Red-run tail, nine revert checks, the one-shot submit script |
| `ac93ab2` | Baseline counts at this commit over 0005714 and 0005709; the acceptance script's dry run |
| `964c40e` | The download's record, `docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json` |
| this commit | Acceptance check and count comparison evidence, this report, index row, TASKS.md, START_HERE.md |

## The build

- **`d26_predicate()`** (`records/gbif_download.py`): the T1 template's five filters, taken from
  `expected_t1_predicate()` so they cannot drift (kingdom 5, HUMAN_OBSERVATION, years 2015 to 2025,
  HAS_COORDINATE), then `or(GADM_LEVEL_0_GID in [USA, CAN], and(isNull GADM_LEVEL_0_GID, COUNTRY in
  [US, CA]))` (D72). No `CONTINENT`, no licence filter.
- **`download_status(key)`** reads GBIF's public download record. **`fetch_download(key, dir,
  expected_size)`** streams the zip to a `.part` file, refuses an existing target (fetch once),
  checks the byte size against GBIF's record, removes the partial file on any failure, and returns
  the size and this machine's sha256. Neither uses credentials.
- **Region rename:** `counts.REST_OF_NORTH_AMERICA = "rest_of_north_america"` became
  `OUTSIDE_T1_BOXES = "outside_t1_boxes"` (accepted by the planner). **A rename only: what is counted
  does not change.** `region_of` returns it for every record outside both boxes exactly as before.
  `scripts/t2_render_tables.py` follows. T2's filed tables keep the old label. Note: `filters.py`
  already has a function `outside_t1_boxes` (the T1 box step's test); the two names agree in meaning.
- `submit_download_request` was not changed. It ran once, from `submit_once.py.txt`, which reads
  `~/.config/forager-forecast/gbif.env` into a dict for `credentials_from_env`, prints only the
  request body without personal fields and the key, and refuses to run again once a key file exists.
  No curl was used with credentials. Plain unauthenticated `curl` fetched GBIF's public docs and the
  predicate converter during verify.

## Tests and revert checks

- **Red first** (`8483d08`, observed): 8 failed, 211 passed. Failures: `AttributeError` for
  `d26_predicate` (3 tests), `download_status`, `fetch_download` (2), `counts.OUTSIDE_T1_BOXES`, and
  the count-table test's `assert 0 == 2` at `outside_t1_boxes`.
- **Green** (`49efa99`): **219 passed**, **123 test functions** (`^def test_` summed over `tests/`,
  observed; base 117). `ruff check` and `ruff format --check` clean.
- New tests run through the real entry points: `request_template(d26_predicate())` equals the full
  literal request; the predicate's keys are exactly the six named, with no `CONTINENT` and no
  `LICENSE`; its first five predicates equal the T1 template's; status and fetch are driven with stub
  openers, never the network.
- **Nine revert checks** (`revert.py.txt`, results in `revert_results.jsonl`). Each makes one edit,
  restores from a byte copy saved before editing (never from git), and confirms the restored file is
  byte-identical to that copy, so the forward change is present. A run whose exit code is not 0 or 1,
  or whose JUnit XML reports errors, is refused. **All nine ran with 0 errors, all bit, and each
  failure belongs to its own edit:**

| Revert | Fails |
|---|---|
| fallback's `isNull` guard removed | the exact-request test (dict differs) |
| `CONTINENT` filter added | exact request; "D26: never select by the continent field" |
| `LICENSE` filter added | exact request; "D61: records of every licence" |
| one T1 filter dropped (`[:5]` to `[:4]`) | exact request; key set lacks HAS_COORDINATE; template-unchanged test |
| fetch size check removed | "DID NOT RAISE RuntimeError" |
| fetch-once guard removed | "DID NOT RAISE FileExistsError" |
| partial file not removed | "no partial file is left behind" |
| status URL wrong | the status test's URL assertion |
| region label back to `rest_of_north_america` | count table: `0 == 2` at `outside_t1_boxes` |

The first check's failure is a generic dict comparison, but only the exact-request test fails and it
compares the predicate, so it can only come from that edit. After the runner: `git status` clean, 219
passed (observed).

## The download

- Combined predicate on GBIF's predicate search at 06:49 UTC, before the request: **2,493,578**, and
  every record of both T1 boxes (252,822 and 945,486, the same as the boxes with no area filter)
  (`../2026-10-06-d26-verify/combined.json`).
- Requested 2026-10-06T06:52:19Z. The download endpoint accepted the `or`/`isNull` predicate. One
  background loop checked `download_status` every four minutes and exited on SUCCEEDED at 07:40:36Z
  (GBIF's `modified` 07:39:31Z). It was never queued past 60 minutes.
- GBIF's record (`gbif_download_record_0012112.json`): totalRecords **2,493,578**, size
  **1,434,032,123** bytes, 26 datasets, licence CC BY-NC 4.0, eraseAfter **2027-04-06**.
- Fetched once to `data/d26/downloads/` (gitignored): 1,434,032,123 bytes, equal to the record;
  `unzip -t` clean; sha256 `c0d5f6a1a775ddb902f73ca2c1978946c056a4f326beb7e13349677c0f72b26c`
  (this machine's). Members: occurrence.txt 3,398,020,752, verbatim.txt 2,031,723,255,
  multimedia.txt 1,361,560,562 bytes. **Not extracted.** Every reader opens the zip in place.
- The request GBIF stored equals `d26_predicate()` exactly (observed, Python equality), with
  `format` DWCA, the backbone `checklistKey`, and GBIF's defaults (type OCCURRENCE, empty extension
  lists).
- Record: `docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json`, in the 0005714 record's form,
  `status: provisional`, `superseded_by: null`.
- Free disk after the fetch: 4.52 GB (observed).

## The acceptance check (D26)

Input: 0005709 read from `~/Zynergy/forecast-data/gbif/0005709-260916113435855.zip` (sha256
`6468a431…1683`, equal to its DOI record, observed). That is the planner's copy. The original under
the T1 worktree was removed by the planner on the owner's word after the copies were verified. Its
DOI record's `local_copy` is not edited.

**Box subset of the new download** (`t1_design.box_of` on the coordinates as reported, edges
inclusive; `acceptance.py.txt`, `acceptance_0012112.json`):

| | PNW | East | Total |
|---|---|---|---|
| Rows of 0005709 (all inside the boxes) | | | 1,195,034 distinct gbifIDs |
| Box subset of 0012112 | 252,822 | 945,486 | 1,198,308 |
| 0005709 keys found in that subset | | | **1,194,729** |
| 0005709 keys found elsewhere in 0012112 (outside boxes, or no coordinates) | | | **0** |
| 0005709 keys **missing** from 0012112 | 93 | 212 | **305** |
| Subset rows not in 0005709 | 2,642 | 937 | 3,579 |

Check: 1,195,034 − 305 + 3,579 = 1,198,308.

**The 305 missing keys, grouped.** Each was looked up on GBIF's public occurrence API
(`explain_missing.py.txt`, `missing_explained.json`, 07:47 to 07:51 UTC): **all 305 return 404, so
GBIF no longer holds them.** All 305 are iNaturalist Research-grade Observations
(`50c9509d…`), 207 US and 98 CA, from every year 2015 to 2025, all last interpreted 2026-09-11 in
0005709. Why iNaturalist withdrew them (deleted by the observer, or no longer research grade) cannot
be told from GBIF. One reason group: **removed from GBIF since 0005709 (later snapshot).** No key is
missing for a filter, geography or step reason.

**The untagged question (verify report, section 10).** Of 0005709's 1,195,034 keys, **29,792 have no
GADM tag** in the new download. All are present, through D72's country fallback. The new download's
box subset has 29,904 untagged rows in all (PNW 2,769 CA + 6,442 US; East 9,576 CA + 11,117 US), the
same 29,904 the verify report counted on GBIF's index. So 112 of them are not in 0005709. In
0005714 (2026-09-19), 29,556 of 0005709's keys were already untagged (`acceptance_dryrun_0005714.json`),
so the missing tag is not new.

**0005714 against 0005709, in passing.** The same script with 0005714 as input found 242 of
0005709's keys missing from 0005714 and 0 rows of 0005714's box subset outside 0005709. All 242 are in
the new download's box subset, and there **all 242 have an empty `continent` and no GADM tag** (196 US,
46 CA; `continent_242.json`). These are D26's stated reason for leaving the continent field, now
counted to the record.

## Counts: both step lists over the new download, against 0005714 and 0005709

All runs read the zips in place at this branch's code. The 0005714 runs at this commit reproduce the
D32 follow-up completion report's figures exactly (T1 list 588,870 survivors, R6 list 1,273,198;
observed). The frozen T1 path over 0005709 gives PNW 142,238 and East 447,163, as D69 records.

### Decomposition

Every record is in both DWCA downloads ("common", 2,482,173 keys), only in 0005714 (67,335) or only
in 0012112 (11,405) (`decompose.py.txt`, `decompose.json`). The filter steps are per record, so their
per-class counts add up exactly to the pipeline's. The 9,627 unloadable rows (9,604 non-day dates,
23 ranges across days) are the same count in both, and all of them fall in the common class.

- **Only in 0005714 (67,335): the narrower geography, and the later snapshot.**
  - 66,577 have neither a US/CA `country` nor a USA/CAN tag: Mexico at least 45,896, Costa Rica 8,319,
    Puerto Rico 3,008 (from the 40 largest country and tag pairs), Guatemala, Panama, Honduras, Greenland, the Caribbean and the rest of D47's
    exclusions.
  - 55 have `country` US but a GADM tag of Greenland (34) or Mexico (21). D72 lets the tag decide.
  - 703 carry a USA/CAN tag or are untagged US/CA: 552 US|USA, 135 CA|CAN, 14 US untagged, 2 CA
    untagged. The 60 lowest keys of the 758 US/CA ones, looked up, all return 404
    (`only_old_explained.json`). The rest are inferred to have been removed likewise (not looked up).
- **Only in 0012112 (11,405): the later snapshot, plus D72's fallback.** All are US or CA: 9,754
  tagged USA/CAN, 1,651 untagged. They include the 242 continent-empty box records above (selection,
  D26/D72). The rest are inferred to be records added to or re-matched in GBIF since 2026-09-19 (not
  checked individually).
- **Common keys whose fields changed between snapshots:** T1 list: −5 at the uncertainty step, −1 at
  the obscured step, +6 reach the duplicate step. R6 list: −12 at the uncertainty step, +12 reach the
  duplicate step. The later snapshot reinterpreted these records.

### T1 step list (`t1_steps`), records left after each step

| Step | 0005709, frozen T1 path (D67, no obscured step) PNW / East | 0005714 unified PNW / East | 0012112 unified PNW / East |
|---|---|---|---|
| inside a T1 box (loadable) | 250,269 / 935,156 | 250,165 / 935,018 | 252,818 / 935,881 |
| year 2015 to 2025 | 250,269 / 935,156 | 250,165 / 935,018 | 252,818 / 935,881 |
| not user-obscured | (no such step) | 233,471 / 883,150 | 235,906 / 883,930 |
| uncertainty ≤ 1,000 m | 162,122 / 490,909 | 162,121 / 490,908 | 164,261 / 491,394 |
| not a default date | 161,958 / 490,506 | 161,957 / 490,505 | 164,097 / 490,991 |
| one per taxon, cell and day | 142,238 / 447,163 | 142,038 / 446,832 | **144,048 / 447,276** |

0012112 against 0005714, totals, with each difference split by class (only_new − only_old + common):

| Step | 0005714 | 0012112 | Difference | Explained by |
|---|---|---|---|---|
| inside a box (after) | 1,185,183 | 1,188,699 | +3,516 | +3,821 new (3,579 since 0005709 and the 242 continent-empty) − 305 removed |
| obscured dropped | 68,562 | 68,863 | +301 | 319 − 17 − 1 |
| uncertainty dropped | 463,592 | 464,181 | +589 | 664 − 70 − 5 |
| default date dropped | 567 | 567 | 0 | 1 − 1 |
| reaching the duplicate step | 652,462 | 655,088 | +2,626 | 2,837 − 217 + 6 |
| duplicate dropped | 63,592 | 63,764 | +172 | the duplicate step joins records; the inputs above changed, so it is not decomposed |
| survivors | 588,870 | 591,324 | +2,454 | the above |

0012112 against 0005709: the entry counts reconcile exactly. PNW 250,269 − 93 removed + 2,642 new =
252,818; East 935,156 − 212 + 937 = 935,881. Both downloads hold 9,609 unloadable rows inside the
boxes; that they are the same rows is inferred, not checked. **After the box step the two are not
comparable step by step.** The frozen path has no obscured step and uses its own Record, key and
loader (D67, D68, D69), and the unified list cannot read SIMPLE_CSV (D67). This is the comparison
the D32 follow-up report could not make on one download, and it stops here for that reason.

### R6 audit step list (`r6_audit_steps`, via `scripts/t2_count_table.py`)

| Step | 0005714 | 0012112 | Difference | Explained by |
|---|---|---|---|---|
| rows read | 2,549,508 | 2,493,578 | −55,930 | 11,405 − 67,335 |
| cannot be loaded | 9,627 | 9,627 | 0 | same reasons, same counts, all in the common class |
| source | 2,539,881 | 2,483,951 | −55,930 | as rows read |
| user_obscured dropped | 156,543 | 155,988 | −555 | 1,385 − 1,940 + 0 |
| coordinate_uncertainty dropped | 1,015,248 | 986,105 | −29,143 | 3,657 − 32,788 − 12 |
| default_first_of_month_date dropped | 811 | 750 | −61 | 4 − 65 + 0 |
| reaching the duplicate step | 1,367,279 | 1,341,108 | −26,171 | 6,359 − 32,542 + 12 |
| duplicate dropped | 94,081 | 92,099 | −1,982 | joins records; not decomposed |
| survivors | 1,273,198 | 1,249,009 | −24,189 | the above |

The R6 audit list has no area step, so the outside-box region in its count table is now the US and
Canada (`outside_t1_boxes`).

## ±180 longitude

The download has no record at |longitude| ≥ 179.9 (verify report, section 7). Three Aleutian
records sit at 178.66 E. `cells.py`'s two ids for one meridian are not reached by this data.

## Not verified

- Why GBIF carries no GADM tag on about 2.4% of US and Canada records. D72 makes it harmless here.
- Why iNaturalist withdrew the 305 missing keys. GBIF's 404 does not say.
- 703 of the 758 US/CA keys only in 0005714: only the 60 lowest were looked up.
- The 11,405 keys only in 0012112, other than the 242: inferred to be new or re-matched records,
  not checked one by one.
- That the 9,609 unloadable in-box rows of 0005709 and 0012112 are the same rows.
- The duplicate steps' differences are stated, not decomposed.
- The unified T1 list over 0005709 (not possible under D67).
- The D32 follow-up report's "1 per box" difference at the T1 uncertainty step between the frozen
  path and the unified list. It reappears here (162,122 against 162,121; 490,909 against 490,908) and
  is not attributed. Inferred: an obscured record at 1,000 m or less, which only the frozen path
  keeps.
- The business-account redo of this request (release checklist).
