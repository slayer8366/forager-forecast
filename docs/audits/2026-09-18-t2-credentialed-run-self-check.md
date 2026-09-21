# T2 credentialed run review: download, count tables and the blocked sample, checked for drift and gaps

**Date:** 2026-09-18
**Type:** review under docs/dispatch/2026-09-18-review-protocol.md, of the run report for the T2 half of
docs/dispatch/2026-09-18-t1-t2-credentialed-run.md.
**Reviewed:** branch t2-record-audit at b4ff6e3, every commit after 02af2c0 (the T2 review): b8bbfa2
stream reader, licence table and count script; 66c96d7 renderer; 2548adc the dispatch filed;
c29af4a the DOI record; 501e24b the run report; 6bd688f index row, session log row and TASKS.md
cell; b4ff6e3 two fields added to the DOI record. Local tip equals origin/t2-record-audit, fetched
at the start. The report names main f96d557 as its base; origin/main is 218a7df at review time,
having taken D24 to D34 (57f0f3a) three minutes after the report commit.
**Reviewer base commit:** b4ff6e3. This review is the next commit on the same branch.
**Supersedes:** none. It answers the items the T2 review (02af2c0) left open where the run report
answers or measures them.

The reviewer read the repo, not the builder's chat: the protocol, the dispatch, the run report, the
previous review, START_HERE.md Fixed terms, DECISIONS.md D19 to D23 on the branch and D24 to D34 on
origin/main, SPEC.md Constraints, the seven commits and every new file. No credentials were read,
no GBIF download was requested, no iNaturalist call was made. Read, observed and inferred are kept
apart. Nothing in this review edits the builder's work.

Every file-and-line citation in the report was checked against `cat -n`; all resolve to the code
they describe. One starts a line late (tests/test_records_licenses.py:34-47; the fixture list opens
at :33), which changes nothing.

---

## The short version

- Every headline number reproduces. The count script re-run on the same zip wrote a summary.json,
  a stage CSV and a licence CSV byte-identical to the builder's (sha256 in check 9), and the 59
  table rows in the report equal the 59 the renderer prints from the re-run. The five withheld
  wordings, their four publishers and the 3,027 Cantharellus share reproduce from the reviewer's
  own pass. The DOI record equals GBIF's public download record field for field.
- The stop on the hand-check CSV is the one SPEC.md Constraints and the dispatch justify, and the
  seed fixed in the report (20260918) is the one D31 fixes on main.
- Two figures in the licence table's residual rows are wrong: "(34 publishers under 1,000 records
  each) 3,253" is 36 publishers and 3,100 records, so the all_fungi source block as printed sums to
  153 more than totalRecords; "(six publishers under 15 records each)" is five. Every named row in
  that table is right, and the CSV sums exactly. A figure, so reported and not fixed.
- The report cites "D26 as written" at a time when no commit held D26; the filed D26 already rules
  the question the report says still needs ruling.
- The script that produced the withheld-wordings table is not in the repo.
- b4ff6e3, which added two fields to the DOI record after the index row was written, is named in
  no record row. This review's index row names it.
- D27, D28 and D29 landed on main after the report and each asks for something this branch does
  not yet have (taxon in the duplicate key, a day-of-month table by dataset, a constituent dataset
  list beside the DOI). Gaps for the next dispatch, not drift: the report predates the rows and
  raised the same questions as owner items.

## 1. Terms: holds

- Over the eleven files in `git diff --name-only 02af2c0..HEAD`: `grep -i "fruiting probabilit"`
  hits only START_HERE.md:14, the pre-existing sentence that forbids the phrase. `grep -i -E
  "probabilit|calibrat"` hits only the pre-existing START_HERE.md and TASKS.md lines (the fixed
  terms table and T9). `grep -i -E "habitat|%"` hits filters.py:34, the R6 quote, unchanged since
  4e247d5, and pre-existing planning lines. No percent on relative habitat anywhere new.
- "percent" in the report is a share of records dropped at a filter step, never a chance.
- "sighting chance" appears in the new files once, report:504, saying it is not used.
- No em dash in any of the eleven files (`grep -P "\x{2014}"`: none).

## 2. Decisions: holds against D19 to D23; three later rows now bind the next step

- D19 and D21: the duplicate step's cell is still the 0.1 degree weather cell (filters.py:38,
  :119); nothing in this range touches it.
- D22: no licence file added. The licence table carries the publisher so the owner can rule per
  publisher (licenses.py:1-8 says why); nothing is ruled in or out in code.
- The report was committed at 21:56:47 local (501e24b); D24 to D34 were committed at 21:59:23
  (57f0f3a) and merged to main at 21:59:54. So the report could not have read them from any commit,
  and they could not have been tuned to what the report says. Read against them now:
  - **D27** (taxon in every duplicate key) supersedes the key the branch runs (filters.py:115-123).
    The report measured that key's effect (42 percent of Cantharellus records reaching the step)
    and did not change it, which is the right order: measure, then the owner rules. Every final
    row of every table in the report moves when the key changes.
  - **D26** (one download selected by geometry, never by the continent field) makes this branch's
    CONTINENT download the one to be superseded. docs/pulls/gbif-fungi-north-america-2015-2025.doi.json:4
    gives the test account as the reason it is provisional and says "the business account will
    redo this exact request"; under D26 the redo is not this exact request.
  - **D28** asks the counts report for a day-of-month table for date-only records, by dataset.
    The report has the eventDate shape table (report:332-339) and the step's drop (799), not that
    table.
  - **D29** asks for the download's constituent dataset list with each dataset's licence and
    record count filed next to each DOI. docs/pulls/ holds the request and the DOI record only.
  - **D31** fixes seed 20260918 for every real draw. The report fixed the same number
    (report:412) before D31 was filed.
- Proposed fix: none for this review to make. The three items are the next T2 dispatch's list.

## 3. Fixed choices: holds

- Predicate: `git diff 4e247d5 HEAD -- docs/pulls/gbif-fungi-north-america-2015-2025.json` is
  empty. GBIF's stored request (check 9) carries that predicate unchanged.
- Thresholds, boxes, groups, steps, sampler: `git diff 02af2c0 HEAD` over counts.py, sampler.py
  and gbif_download.py is empty. filters.py changed at :30 (one import) and :209-225 (the reader
  split into `read_occurrence_rows` over a handle and `read_occurrence_table` delegating to it);
  no constant, step or key changed.
- Order of events, from commit times and file mtimes (observed): b8bbfa2 at 21:05:27 and 66c96d7
  at 21:13:53 local precede the download's SUCCEEDED at 04:40:18Z (21:40:18 local); the count
  outputs under data/t2/counts/ are stamped 21:52; c29af4a (DOI record) at 21:44:43; the report at
  21:56:47. No source file changed after a count was seen.
- The seed for the real draw is fixed in the report before any candidate exists (report:412), in
  text rather than as a constant, with the reason given (report:458-460). D31 accepted the same
  number afterwards.

## 4. Scope: holds

- The eleven files in the diff are the stream reader and licence table, their tests, the two
  scripts, the dispatch filed as received (byte-identical to the T1 branch's copy: `git diff
  origin/t1-calendar-smoke-test HEAD -- docs/dispatch/2026-09-18-t1-t2-credentialed-run.md` is
  empty), the DOI record, the report, and the three record files.
- Do-not-touch: DECISIONS.md, SPEC.md and DATA_REGISTER.md have no diff in the range. The
  predicate, boxes and year range are as check 3 shows. No password material in any committed
  file (`git grep -i -E "authorization|basic [a-z0-9+/=]{8,}|gbif_pwd|password|@..."` over the
  scripts, licenses.py, docs/pulls and the report: the two hits are the sentences saying curl was
  not used because it exposes the password). The DOI record says the notification address is not
  recorded (doi.json:60), and none is.
- No substitute pull. Nothing under data/t2/ is newer than 20:08 except downloads/ and counts/
  (`ls -la`, observed); the sampler's `population_query()` still has no caller outside tests.
- **Is the stop on the hand-check CSV the one the spec and dispatch justify?** Yes. SPEC.md:77-78:
  "Bulk record pulls go through GBIF downloads ... The iNaturalist API is for counts and spot
  checks only." Dispatch:44: "No substitute for GBIF downloads: not the search API, not the
  iNaturalist API." The population (genus-level, two agreeing identifiers, not research grade) is
  not in any GBIF download (T2 completion report, verify-first item 1; re-derived by the T2
  review, check 7). The dispatch's premise that the CSV follows from the download was false when
  the dispatch was written, and the dispatch itself says Claude had not read the repo. The report
  names the premise, names the ruling it waits on, and pulls nothing (report:391-409). That is
  the stop-and-ask case, and the previous review's check 10 reached the same reading.

## 5. Record: holds, with one commit unrecorded

- docs/audits/README.md: one row appended at the end (diff is a single `+` line after the last
  row). START_HERE.md: one session log row appended. TASKS.md: the T2 cell only.
- Report header carries Date, Type, Base and Supersedes. Base names main, branch and every code
  commit. The dated correction note the previous review asked for (check 7, item 1) is present at
  report:379-389, quotes the old wording, gives the date, and says the docstring at filters.py:46-48
  is left for the next edit of that file, which it is.
- **Gap:** b4ff6e3 (22:00:03, two fields added to the DOI record: what integrity check is possible,
  and eraseAfter) landed after 6bd688f wrote the index row, and is named in neither the index row
  ("and the report commit") nor the report's "What landed" table (report:102-109). Proposed fix:
  this review's index row names it; the builder's rows stay as written.

## 6. Data hygiene: holds for git; the licence gate is still open

- `git ls-files data`: nothing. `./scripts/check-large-files.sh --all`: "57 file(s) checked, none
  over 1048576 bytes" (the report says 56, written before its own file was tracked). The largest
  new tracked file is the report at 505 lines; the DOI record is 65 lines. The 1.4 GB zip is
  ignored by .gitignore:6 (`git check-ignore -v`, observed).
- Licences: nothing has been used, so the protocol's rule is not broken. DATA_REGISTER.md:20 still
  reads "Per record" for the GBIF row. The report's licence table gives the per-publisher,
  per-licence counts the previous review asked for; D29 now asks for the constituent dataset list
  with licences beside the DOI, which the zip's own rights.txt (7,243 bytes) and citations.txt
  (11,837 bytes) carry and neither the builder nor this reviewer opened. Proposed fix: the next T2
  dispatch files that list under docs/pulls/ as D29 says, and supersedes the register row.

## 7. Evidence in the report: holds, with five items

Re-derived by the reviewer on 2026-09-18:

| Claim in report | Reviewer's re-derivation |
|---|---|
| Zip 1,475,785,280 bytes, sha256 d0e8e7cd...0ecaaf | `stat`, `sha256sum`: equal, full hash equals doi.json:11 |
| 41 dataset EML files; occurrence.txt 3,561,013,686, verbatim.txt 2,077,868,784, multimedia.txt 1,395,088,270 | `unzip -l`: 41 `dataset/*.xml`; the three sizes equal. The zip also holds rights.txt and citations.txt, which the Members row omits |
| Header 230 columns; the twelve at positions 1, 5, 19, 20, 25, 63, 67, 98, 99, 100, 180, 205 | `unzip -p ... \| head -1 \| tr '\t' '\n'`: 230; all twelve positions equal |
| DOI record fields (report:77-90; doi.json) | `curl -s api.gbif.org/v1/occurrence/download/0005714-260916113435855`: key, DOI, licence URL, created 04:11:37Z, modified 04:40:18Z, eraseAfter 2027-03-19, size, totalRecords 2,549,508, numberDatasets 41, request format DWCA, checklistKey, sendNotification, and the six-clause predicate all equal. GBIF's stored request also carries `type: OCCURRENCE` and two empty extension lists that the committed template does not set; the report's equality claim is scoped to format, checklistKey and predicate, and holds at that scope |
| Step counts, every stage-by-region and year-by-region table (report:191-274) | Identical to the renderer's output from the reviewer's re-run: 59 of 59 rows (check 9) |
| Named licence rows (report:286-322) | All equal to counts_by_license.csv |
| Withheld wordings, publishers, 156,543 total, 3,027 Cantharellus, dataGeneralizations empty on all rows | Reviewer's own pass over occurrence.txt: five wordings with the same counts, four publishers with the same counts, 156,543, 3,027, 0 |
| 42, 17, 39, 14, 6 percent; 16.7; 6.1; 89 percent | 42.35, 16.6, 39.4, 13.9, 5.5; 16.70; 6.14; 89.2. T1's 1,424 to 1,226 and 2,908 to 2,748 are at the T1 run report's lines 262-263 and 284-285 on origin/t1-calendar-smoke-test; 04:10:34Z at its :133; 9,330 at :240 |
| 4,562 of 4,589 and 19,761 of 19,786 iNaturalist at the end | 4,084 + 331 + 147; 18,147 + 1,038 + 576 |
| `grep -rn -E "2549508\|2,549,508" tests` empty | Empty |
| 75 passed, ruff clean, 41 files formatted | 75 passed; "All checks passed!"; 42 files (item 5) |

The five items:

1. **The licence table's residual rows.** report:318, "(34 publishers under 1,000 records each)
   3,253": counts_by_license.csv has 37 all_fungi source rows outside the five named publishers,
   over 36 datasets, summing to 3,100. With the seven named rows (2,546,408) that is 2,549,508
   exactly; with 3,253 the block as printed sums to 2,549,661, which contradicts the report's own
   "Source rows equal the download's totalRecords" one table up. report:305, "(six publishers under
   15 records each) 36": five publishers (2b169d34 12, d1d59f9f 12, e3ce628e 6, 8a863029 4,
   84d26682 2). Every other number in the table equals the CSV. Proposed fix: a dated correction
   note in the successor report quoting both wordings. Not fixed here: a figure in a result.
2. **"D26 as written is overtaken"** (report:475). At the report's commit no commit held D26; the
   only commit that does, 57f0f3a, is 2 minutes 36 seconds later on another branch, and D26's own
   Supersedes cell says a version 1 wording was never filed. The reviewer cannot tell which text
   the report read. The filed D26 already says "selected by geometry and never by the continent
   field" and keeps T1's first download as provisional and superseded, so the ruling the report
   says is needed "before the business-account redo" exists on main. Same class as the previous
   review's launching-message item: a claim about a text not in the repository. Proposed fix: the
   successor cites D26 by the filed text.
3. **The withheld-wordings pass has no script in the repo.** report:348 describes a "second pass
   ... every digit run replaced by N"; `git grep -i -E "normalis|withheld_wordings"` over scripts,
   src and tests finds nothing, and data/t2/counts/withheld_wordings.txt is the only trace. The
   table is right (the reviewer reproduced it), but the record cannot show how. Proposed fix: commit
   the pass as a script, or replace the 40-character prefix tally in t2_count_table.py:85-90, which
   the report itself says over-counts (1,197 prefixes for five wordings), with the normalised one.
4. **The correction note's scope, and the distribution it did not tally.** The note (report:379-389)
   holds: it quotes the old wording, dates itself, and says the exact distribution was not tallied.
   The reviewer tallied it in the same pass, over the 156,510 withheld rows with a numeric
   uncertainty: minimum 1 m, 1st percentile 25,908, median 27,908, 95th 29,631, 99th 112,019,
   maximum 15,382,571 m; 84.7 percent between 26,500 and 28,900 m, 13.2 percent above 28,900 m,
   22 rows at or below 250 m. 33 withheld rows have no numeric uncertainty, the same count as the
   "Libre acceso" rows (inferred to be the same rows; not checked per record). So "most common
   values 26.8 to 28.9 km with a long tail" is the right description, and 22 withheld records
   would pass the R6 step on uncertainty alone; step 1 drops them first, so no table changes.
5. **"41 files already formatted"**: the reviewer sees 42 from the same tree; the previous review
   saw 35 against the builder's 34. Not pursued, not a headline number; recorded because it has
   now been off by one twice. The large-file guard's 56 against 57 is explained: the report was
   written before its own file was tracked.

The measured effect of the taxon-less key is stated with its scope (report:429-440): the
population (records reaching the step, all regions), the comparison's caveat (T1's threshold and
key differ), and the mechanism (file order decides which record survives). Holds.

Read, observed and inferred are labelled throughout; the reviewer found no inferred claim
presented as observed. The 242-record difference between the two predicates is labelled inferred
and listed as not checked, as it should be.

## 8. Revert check: holds

Two redone by the reviewer on src/forager_forecast/records/licenses.py, each with a copy saved to
/tmp and its sha256 recorded first, one line changed with sed, only tests/test_records_licenses.py
run, the copy restored with `cp` from /tmp (not from git), and `sha256sum -c` OK afterwards.

1. The builder's: :43 `if group is not None:` to `if False:`. "2 failed, 2 passed":
   `test_license_table_counts_every_stage_by_group_license_and_publisher` at :53,
   `AssertionError: assert 0 == 3` on `count("source", "cantharellus", "CC_BY_NC_4_0", INAT)`, and
   `test_license_rows_are_sorted_and_written_as_csv` at :72 on the missing group rows. That is the
   message the report quotes (report:130-135), and it is the one this edit and no other produces:
   the all_fungi row two lines up still passes. No ImportError, SyntaxError, collection error or
   "no tests ran" in the log (grep count 0).
2. A second: :39 `... .strip() or EMPTY` to `... .strip()`. "1 failed, 3 passed":
   the same test at :55, `assert 0 == 1` on `count("source", "all_fungi", EMPTY, EMPTY)`. The
   failure names the empty-licence mapping and nothing else. No import or collection error.

After each restore: `sha256sum -c` OK, `grep -c REVERT-MARK` 0, `git status --short` empty. Full
suite after: 75 passed. The report's positive control (a seven-row synthetic zip, report:143-148)
was not reproduced: the zip is not in the repo.

## 9. Headline numbers re-run: holds

- Tree: the worktree at b4ff6e3 with `git status --short` empty; `uv run` against the locked
  environment (the previous review's `uv sync --locked` state; not re-synced here).
- `uv run python scripts/t2_count_table.py data/t2/downloads/0005714-260916113435855.zip
  /tmp/t2-review-counts`: wall clock 8:22.74, maximum resident set 110,340 kB, exit 0 (report:
  7:48.55, 110,172 kB). summary.json equals the builder's data/t2/counts/summary.json in every
  field but the zip path (which is the same path anyway). counts_by_stage_group_region_year.csv
  sha256 d3b60346...e132 and counts_by_license.csv sha256 0bad7fab...2cb5, both equal to the
  builder's files byte for byte (`cmp`).
- `uv run python scripts/t2_render_tables.py /tmp/t2-review-counts`: the 59 table rows under the
  report's "The count tables" (step table, three stage-by-region tables, three year-by-region
  tables) equal the rendered rows line for line (`diff`, empty).
- The DOI record against `curl -s https://api.gbif.org/v1/occurrence/download/0005714-260916113435855`:
  every field equal (table in check 7).
- The zip's sha256 and size equal the DOI record; the header positions equal the report.
- One scope note: this reproduces the run on the same file. The report says the final row depends
  on GBIF's output order (report:437-439); a differently ordered file would give a different final
  row under the taxon-less key, and this check cannot say by how much. D27 removes most of that
  dependence.

## 10. Gaps: gap, and the stop is justified

What the dispatch asked for that the report does not evidence, and why:

- **The seeded 200-record hand-check CSV.** Not produced; population not on GBIF; the iNaturalist
  pull awaits a ruling; the dispatch forbids the substitute. Justified (check 4). The seed is now
  fixed twice, in the report and in D31, and they agree.
- **The person-only hand check.** Waits on the CSV.
- **The verdict on the 1,000-record premise** is T1's item; the report does not claim it.
- **Everything else the dispatch asked for is evidenced:** the DOI with its query beside it and
  marked provisional (doi.json), the count tables including by licence, the large-file guard
  result, a Conventions line, and a Not checked list of eight items stated plainly.

Gaps opened by rows that landed after the report (check 2): the taxon-in-key run under D27, which
changes every final row; the day-of-month table by dataset under D28; the constituent dataset list
beside the DOI under D29. Plus the reviewer's: the withheld-wordings script (check 7, item 3), the
b4ff6e3 record gap (check 5), and the 242 in-box records that the CONTINENT predicate lacks, which
the report lists as not checked and D26 now makes moot for the next download.

Is the stop justified? Yes, for the reasons in check 4. The report stopped at the same line the
previous review drew, pulled nothing beyond the one download, and left every open reading to the
owner with its cost measured. D32 says these commits are reviewed before anything of theirs
merges; this is that review.

## What the reviewer changed

This file, and one row appended to docs/audits/README.md, in one commit on t2-record-audit. Nothing
in the builder's code, tests, report, DOI record or record rows. Candidates for a reviewer's fix
that were not taken: the licence-table residual figures (a figure in a result), a script for the
withheld pass (builder's code), and adding b4ff6e3 to the builder's index row (rows are not
edited; this review's row names it instead).

## Conventions

Checked: the review protocol's ten checks and output form; the previous T2 review for the header
fields, verdict words, evidence tables and the three closing sections; docs/audits/README.md's
append-only rule; START_HERE.md working rules (no em dashes, every fact flagged); the Forager
CLAUDE.md rules on revert checks (saved copy, one-line edit, affected module only, build must
import, restore from the copy, check the tree afterwards), on citing a figure with its scope, and
on counting a check's sample against something outside it (the licence residual was found by
summing the printed rows against totalRecords). The hard rules of this review's dispatch were kept:
no credentials read, no download requested, no iNaturalist call. The phrase check 1 searches for
appears in this file only inside that check.

## Not checked

- rights.txt and citations.txt inside the zip, which carry the per-dataset licences D29 asks for.
- verbatim.txt and multimedia.txt.
- The 242 in-box records the CONTINENT predicate lacks (not extracted).
- Which records the 33 withheld rows with no numeric uncertainty are (inferred to be the "Libre
  acceso" rows from equal counts only).
- The withheld wording by publisher as a cross-tally; only the wording totals and the publisher
  totals were compared, each of which equals the builder's.
- The builder's seven-row positive-control zip (not in the repo).
- The T1 run report beyond the lines grepped for the figures the T2 report quotes.
- CI for the branch: `gh run list --branch t2-record-audit` printed nothing; no pull request is
  open, as the report says.
- Why ruff format counts 42 (or 41).
- The GBIF notification email.
- What `identifications=most_agree` means on the iNaturalist API (carried from both earlier
  reports).
- Any photo, and the misidentification rate. Person-only.

Renamed 2026-09-20 under D35. This document is a builder self-check, not a review under D18. The review of record is at docs/audits/2026-09-18-t2-credentialed-run-review.md.
