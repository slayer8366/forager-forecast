# T2 credentialed run review: seven commits checked for drift and gaps

**Date:** 2026-09-18
**Type:** review under docs/dispatch/2026-09-18-review-protocol.md, ordered by D32 (DECISIONS.md on
main at ef6c82a: the credentialed-run commits are reviewed before anything from the branch merges).
**Reviewed:** branch t2-record-audit commits 02af2c0..b4ff6e3, seven commits: b8bbfa2 (stream
reader, licence table, count script), 66c96d7 (renderer), 2548adc (filed dispatch), c29af4a (DOI
record), 501e24b (run report), 6bd688f (index row, session log row, TASKS cell), b4ff6e3 (DOI note).
The earlier review, docs/audits/2026-09-18-t2-review.md at 02af2c0, covered 4e247d5..83f44e6; this
one covers only what came after it.
**Reviewer base commit:** b4ff6e3, on branch t2-credentialed-run-review cut from it. `git fetch
origin t2-record-audit` at the start and again before this commit: the tip was b4ff6e3 both times.
**Supersedes:** none.

**Correction, 2026-09-18, appended after the first push (7cb0b59) and not edited in place.** The
header above says "the tip was b4ff6e3 both times". That was wrong when pushed: the second fetch
ran in the same command chain as the commit, and its result (4b22c8d) was read only afterwards.
origin/t2-record-audit moved during this review by two commits, both by the session that holds the
archive: f8adaa4 (22:13:23 local), which files its own review of the same seven commits at this
same path, docs/audits/2026-09-18-t2-credentialed-run-review.md, with its own index row; and
4b22c8d (22:14:56), scripts/t2_withheld_wordings.py, a 65-line tally script that reads
occurrence.txt out of the zip, writes nothing, and touches no filter, constant or test (`git show
4b22c8d --stat`: that one file). Neither is in the range this review covers (02af2c0..b4ff6e3),
and the review stands as written for that range. Read against the other review on content: it
reproduced the count tables from the archive (byte-identical CSVs, 59 of 59 rendered rows), which
this review could not; it found the same roll-up failure (3,253 and 34 against 3,100 and 36) and
adds that "(six publishers under 15 records each)" (report :305) is five; it found the same
b4ff6e3 record gap and the same D26 to D29 list; it adds that the report's "D26 as written"
(report :475) cites a text no commit held at the time, and that the withheld-wordings pass had no
script, which 4b22c8d now files. The two reviews disagree on nothing. Because the two files share
a path, merging this branch into t2-record-audit will conflict on it and on the index; the owner
decides which file, or both under distinct names, is kept. This note is the only change to this
file after 7cb0b59; the index row that said "the T2 tip did not move during the review" is
corrected by a new row, not edited.

The reviewer read the repo, not the builder's chat: the protocol, START_HERE.md, DECISIONS.md on
main D19 to D34 (the branch's copy ends at D23), SPEC.md R6 and Constraints, the two dispatches, the
run report, the earlier review, the two files under docs/pulls/, and every line of `git log -p
02af2c0..b4ff6e3`. Live sources were reopened on 2026-09-18. Read, observed and inferred are kept
apart. Line numbers are the file's own.

What this reviewer could not reach: the archive and the count CSVs sit in another session's
worktree, which the reviewer was told not to enter, so no count was re-run from the file. Check 9
says what was re-derived instead. Nothing in this review edits the builder's work.

---

## 1. Terms: holds

- `git grep -n -i "fruiting probabilit"` over the tree outside docs/planning and the protocol: two
  hits, README.md:27 (the rule that forbids the phrase) and the earlier review's own grep line.
  None in any file this run added.
- `git grep -n -i -E "probabilit|calibrat"` over src/, tests/, scripts/, docs/pulls/ and the run
  report: no hits.
- Added lines of the whole diff grepped for `percent`, `%` and `habitat` in code, tests, scripts and
  JSON: no hits. The report uses "percent" only on record counts (42 percent of records dropped, 6.1
  percent obscured), never on habitat.
- "Sighting chance" is not used in the new files; the report says why (Conventions, :504).
- No em dash in any added line (`grep -c` for U+2014 over `git diff 02af2c0..b4ff6e3`: 0).

## 2. Decisions: holds, with one gap recorded against D26

- **No bulk pull through the search API or the iNaturalist API.** No module under src/ or scripts/
  added in this range imports urllib, http, requests, socket, subprocess or httpx (grep over import
  lines: none). `population_query()`, `request_body()` and `curl_argv()` have no caller outside tests
  and one docstring mention (sampler.py:10). The download request was made from a Python session
  and is not a committed script, which the report states (:92-93). No file in the repo could hold
  an iNaturalist pull; whether one exists on the run machine's disk is not visible from here.
  Observed: `git ls-files` under data/ is empty.
- **Source records never modified.** scripts/t2_count_table.py reads occurrence.txt out of the zip
  (:93-96) and writes only two CSVs and a JSON to its output directory (:99-100, :117). filters.py's
  four predicates and `Pipeline.run()` are unchanged since 4e247d5 (check 3).
- **No model fit.** Nothing in the diff fits, scores or trains; the two scripts count and render.
- **The 200-record sample.** Not drawn. The report says so (:37-41, :391-416) and the code agrees:
  `sample()` (sampler.py:134-140) has no caller outside tests. D31's seed rule is therefore not yet
  engaged; the seed the report fixes for the real draw, 20260918 (:412), is the one D31 later fixed
  for every real draw, so the two agree.
- **D9 and D12.** Groups stay at genus level by genusKey (counts.py:48-52); counts.py and
  sampler.py are byte-identical to 4e247d5 (`git diff 4e247d5 b4ff6e3 --quiet` on both: unchanged).
- **D22.** No licence file added. The DOI record carries GBIF's download licence as a URL
  (doi.json:18) and the report's licence table reports, not rules.
- **D26, a gap and not drift.** This download selects by CONTINENT=NORTH_AMERICA (predicate file,
  doi.json:53-54, and the request GBIF stores, re-read live). D26 now orders one download selected
  by geometry and never by the continent field. The predicate was fixed at 4e247d5 (20:14 local) and
  D26 was proposed after this run and accepted in D34, so the run followed the rule it had. Recorded
  under check 10 as what D26 requires of this download.

## 3. Fixed choices: holds

The check that matters most. Three comparisons, then the timeline.

- **Predicate file against GBIF's stored request.** `curl
  https://api.gbif.org/v1/occurrence/download/0005714-260916113435855`, compared in Python against
  docs/pulls/gbif-fungi-north-america-2015-2025.json: predicate equal, format DWCA equal, checklistKey
  d7dddbf4 equal. The DOI record's embedded `request` (doi.json:19-58) equals the stored request on
  the same three fields. Observed live.
- **Predicate file over time.** `git log -- docs/pulls/gbif-fungi-north-america-2015-2025.json`
  lists one commit, 4e247d5; `git diff 4e247d5 b4ff6e3` on it is empty.
- **The code the counts ran through.** `git diff --stat 4e247d5 b4ff6e3 -- src/ tests/` names three
  files: filters.py (19 lines), licenses.py (new), tests/test_records_licenses.py (new), all in
  b8bbfa2. The filters.py change (diff read in full) splits `read_occurrence_table` into
  `read_occurrence_rows(handle)` plus a thin file wrapper (:209-225) and adds one import. It touches
  no predicate, no constant and no step: `R6_MAX_COORDINATE_UNCERTAINTY_M = 250` (:36),
  `WEATHER_CELL_DEGREES = 0.1` (:40), `is_user_obscured` (:43-56), `exceeds_r6_uncertainty` (:72-75,
  strict `>`), `is_default_first_of_month_date` (:79-98), `duplicate_key` (:115-123) and
  `default_steps()` (:151-157, the four steps in the dispatch's order) are unchanged. Plumbing only;
  it alters no filter's meaning. The boxes (counts.py:41-42) and the group keys (:51-52) are
  unchanged.
- **Timeline, commit times in UTC against the download record (live).** b8bbfa2 04:05:27Z, the
  download requested 04:11:37Z, 66c96d7 (renderer) 04:13:53Z, 2548adc 04:20:17Z, the download
  succeeded 04:40:18Z, the run took 7 min 49 s (report :154), c29af4a 04:44:43Z, the report and
  index 04:56:47Z, b4ff6e3 05:00:03Z. Every code commit landed before the download existed. No
  commit after 04:13:53Z touches src/, tests/ or scripts/. Author and committer times agree.
- Not checkable from here: that the working tree on the run machine equalled b8bbfa2 when the
  script ran. The report says nothing was changed (:111) and the tree here is clean.

## 4. Scope: holds

- The dispatch said pull, count including by licence, sample, stop. Pulled once, counted, sample
  blocked and reported, stopped. No model fit (check 2).
- **Credentials.** `git diff 02af2c0..b4ff6e3` grepped for GBIF_USER, GBIF_PWD, GBIF_EMAIL,
  gbif.env, Labs, password, netrc and `Authorization: Basic`: the three names appear only in the
  filed dispatch (2548adc, which is the owner's text as received) and in one sentence of the DOI
  record naming which variables the request read (doi.json:60). A second grep of every added line
  for an email address, a base64 basic-auth token or a `NAME=value` assignment of those names: no
  hits. No value, no file contents, no environment echo. The DOI record says the notification
  address is not recorded (doi.json:60) and the live record's `sendNotification` is true, which is
  consistent.
- Every file in the diff is inside the task: two records modules, one test file, two scripts, the
  dispatch, the DOI record, the report and the three record files.
- Additions beyond the dispatch's words, all disclosed in the report: a second pass over the
  withheld texts (:348-349), an eventDate shape tally (:332-344), a synthetic positive-control zip
  (:142-148, not committed), and the publisher column on the licence table (:452-453). All are
  counts, which is what the dispatch asked for.
- The report's reading of "the password must not appear in the command", which led it to use
  urllib rather than `curl_argv()` (:92-98), is a stricter reading than the dispatch requires and
  changes nothing the dispatch fixed.

## 5. Record: holds, with two small gaps

- docs/audits/README.md: one row appended at the end (diff: `@@ -24,3 +24,4 @@`, one `+` line).
  START_HERE.md: one session log row appended at the end. TASKS.md: the T2 status cell changed and
  no other line, which the working rules require. DECISIONS.md: untouched on the branch.
- The report header carries Date, Type, Base (02af2c0 over main f96d557) and Supersedes (:3-14).
  The index row names the base, the branch and the commits.
- The DOI record marks the download provisional with the test-account reason, stores the query
  beside it, and no test pins a record count (`grep -rn -E "2549508|2,549,508" tests`: empty). The
  dispatch's test-account rules (item 4) are applied in full.
- **The filed dispatch is not on main.** The launching premise said it would be byte-identical to
  main's copy; `git show origin/main:docs/dispatch/2026-09-18-t1-t2-credentialed-run.md` fails
  ("exists on disk, but not in origin/main"), and `git ls-tree origin/main docs/dispatch/` lists
  seven files without it. It is on the two run branches only, and the T2 copy (2548adc) has the
  same sha256 as the T1 branch's copy (1d935ec8...), as the report claims (:106). So the dispatch
  is filed twice, identically, and reaches main only when a run branch merges. A stale premise in
  the review order, not a fault of the run; listed so the merge pass knows the file comes in with
  the branch.
- **b4ff6e3 is not named in the report or the index row.** The report's "What landed" table (:102-
  109) ends at "index row, session log row, TASKS.md T2 cell"; b4ff6e3 came after, adding two keys to
  the DOI record (diff: one comma, two added lines, nothing removed). The row is appended-only, so
  the fix is not an edit to it; this review's own index row names all seven commits.

## 6. Data hygiene: holds for git, gap for D29

- `git ls-files` for anything under data/ or ending .csv, .zip, .txt, .tsv, .parquet or .gz: none.
  Largest tracked file: uv.lock, 31,551 bytes; the run report is 30,236. `./scripts/check-large-
  files.sh --all`: "57 file(s) checked, none over 1048576 bytes", exit 0. .gitignore:6 is `data/`.
- **The by-licence table exists**: in the report (:284-323, text :325-330) and, gitignored, in
  data/t2/counts/counts_by_license.csv on the run machine, keyed by stage, group, licence and
  datasetKey (licenses.py:24-30).
- **The constituent dataset list D29 asks for is not filed next to the DOI.** D29 wants, beside each
  DOI, the download's dataset list with each dataset's licence and record count, and the Data
  register's GBIF row pointed at it. What exists: the public datasets endpoint
  (`/occurrence/download/0005714-260916113435855/datasets`, re-read live) lists 41 datasets with
  record counts summing to 2,549,508, but carries no licence field; the report's table gives licence
  by datasetKey for the seven largest publishers at source and rolls the rest up. DATA_REGISTER.md:20
  still reads "Per record" and points at nothing. D29 came after this run, so this is a gap to close
  before use, not drift. Proposed fix: for the merge pass, a file next to the DOI record listing the
  41 datasets with title, licence (from `/dataset/{key}`), and record count, and the register row
  superseded to point at it. Not done here: it is D29's gate and a claim about licences.
- One name the datasets endpoint resolves that the report left as a key: 2b169d34 is also titled
  "Fungi of parks, forests and reserves of New Jersey" (a second New Jersey dataset, 1,877 records).

## 7. Evidence in the report: holds, with four items

Every file-and-line reference in the report's "What landed", "Evidence", "The withheld texts", "The
hand-check sample" and "What the two open readings cost" sections was resolved against the code
(26 references, each opened with `sed -n`): all point at what they describe. Read, observed and
inferred are labelled throughout; the reviewer found no observed claim presented as read and no
inferred claim presented as observed.

**Accounting identities**, checked by a script over the report's own tables (every identity below
was computed, not read):

- The four whole-pull steps: before minus dropped equals after at every step, each step's before
  equals the previous after, the first before is 2,549,508 and the last after is 828,498. Holds.
- Stage-by-region tables, all three groups: the three regions sum to the Total column in all fifteen
  rows; every region and total is non-increasing down the stages; the all_fungi totals equal the
  whole-pull step afters at every stage; cantharellus and laetiporus never exceed all_fungi in any
  cell. Holds.
- Year-by-region tables, all three groups: eleven years each, every year's final is at most its
  source, and the six column sums equal the stage table's source and final for that region (for
  example cantharellus 3,421 / 600 / 5,545 / 1,481 / 9,161 / 2,508). Holds.
- Source-stage total equals the public download's totalRecords, 2,549,508 (live). Holds.
- Withheld wordings sum to 156,543, step 1's drop; eventDate shapes sum to 2,549,508; the in-box
  differences are 4, 104, 0, 138 and 104 + 138 = 242; the percentages 42.3, 16.6, 39.4, 6.14, 16.7
  and 89.2 recompute from the tables. Holds.
- Licence table: cantharellus source 18,127 and last step 4,589, laetiporus source 39,067 and last
  step 19,786, all_fungi last step 828,498 all sum to their stage totals. **all_fungi at source
  does not:** the rows sum to 2,549,661, which is 153 over 2,549,508. The row at fault is the
  roll-up "(34 publishers under 1,000 records each) 3,253" (:318). From the live datasets endpoint,
  the five named datasets hold 2,546,408, so the rest hold 3,100 across 36 datasets, not 3,253
  across 34; the live licence facet splits that 3,100 as 456 CC BY-NC, 2,370 CC BY and 274 CC0.
  The seven named rows above it are right (the three iNaturalist rows sum to the dataset's
  2,221,740; Mushroom Observer, New Jersey, 2b169d34 and e3ce628e each match the endpoint). Not a
  headline number and it changes no conclusion; the CSV behind it is on the run machine, so which
  step of the hand roll-up went wrong is not visible from here. Proposed fix: a dated note in the
  successor report quoting the row and giving 3,100 and 36, or the roll-up regenerated from the CSV.

The four items:

1. The roll-up row above.
2. **The withheld-uncertainty figure is stated with its scope** in this report (:379-389): the old
   wording is quoted, called "the range of the most common values, not of the sample", and the
   review's 68 km and 75 km are cited. That is the correction D31 orders for the report, done before
   D31 was written. The same section says the docstring at filters.py:46-48 still reads "about 26 to
   29 km" and leaves it; confirmed (`git grep`), and the earlier completion report, its index row
   and its session log row still carry the unscoped wording unappended. Those three are D31 items,
   under check 10. Note that the report's own "clustering between 26.8 and 28.9 km" (:386) rests on
   the truncated-prefix tally in summary.json, which the report itself says cut numbers mid-value
   (:454-457); the sentence is hedged ("the exact distribution was not tallied") and stays inferred.
3. **Claims that rest on the archive** and cannot be re-derived from here: the 230-column header and
   the twelve column positions, the sha256 and member sizes, the 3,775 Mushroom Observer wording,
   the 3,280 threatened-taxon wording, the 52 "Libre acceso" and "none" rows, dataGeneralizations
   empty throughout, and every count table cell. The report labels each observed with its command.
   The reviewer checked their internal arithmetic (above) and every figure that has a public
   counterpart (check 9); the rest is taken as the builder's observation.
4. **"41 files already formatted"** (:122); the reviewer observed 42 from the clean tree. The
   earlier review saw the same one-off (34 against 35) and did not explain it; neither does this
   one. Not a headline number.

Figures the report cites from the T1 run report were opened on the T1 branch
(`git show origin/t1-calendar-smoke-test:docs/audits/2026-09-18-t1-credentialed-run-report.md`)
and matched: 1,424 to 1,226 and 2,908 to 2,748 (:262-263, :284-285), the T1 download SUCCEEDED at
04:10:34Z (:133), 9,330 year-only rows from the New Jersey dataset (:240), "562 of the 567 drops"
(:349), the 50 columns (:375), and the four in-box file counts (:227-230).

## 8. Revert check: holds

One redone by the reviewer, the same edit the builder reports (:130-135), so the two runs can be
compared. A copy of licenses.py saved to /tmp with its sha256 first. `sed` changed line 43,
`if group is not None:` to `if False:  # REVERT-MARK`; `git diff --stat` showed one file, one
line. `uv run pytest -q tests/test_records_licenses.py` alone: "2 failed, 2 passed in 0.10s",
`FAILED ...::test_license_table_counts_every_stage_by_group_license_and_publisher` and
`FAILED ...::test_license_rows_are_sorted_and_written_as_csv`, the second with "Right contains 2
more items, first extra item: 'source,cantharellus,CC_BY_NC_4_0,50c9509d-...,1'", which is the
group row this edit stops writing and nothing else could. The log has no ImportError, SyntaxError,
"ERROR collecting" or "no tests ran" (grep count 0). Restored with `cp` from the /tmp copy, not from
git; `sha256sum -c` OK; `grep -c REVERT-MARK` 0; `git status --short` and `git diff --stat` both
empty; line 43 reads `if group is not None:` again, so the forward change is still present. The
builder reported the same two failures with `assert 0 == 3` on the first; this reviewer's log tail
captured the second failure's message and both names.

## 9. Headline numbers: holds for what is public, cannot tell for the file counts

- Clean tree (`git status --short` empty), `~/.local/bin/uv sync --locked --all-groups`, then `uv
  run ruff check .` "All checks passed!", `uv run ruff format --check .` "42 files already
  formatted", `uv run pytest -q` "75 passed in 0.89s" (report: 75 passed, 4 new; the new module
  collects 4).
- **The download record, live** (`api.gbif.org/v1/occurrence/download/0005714-260916113435855`):
  status SUCCEEDED, DOI 10.15468/dl.k3mwnn, totalRecords 2,549,508, numberDatasets 41, size
  1,475,785,280, format DWCA, checklistKey d7dddbf4, created 2026-09-19T04:11:37Z, modified
  04:40:18Z, eraseAfter 2027-03-19, licence by-nc/4.0, no hash field of any name. Each equals the
  DOI record's field. The stored predicate equals the branch's predicate file (check 3).
- **The datasets endpoint, live**: count 41, endOfRecords true, numberRecords summing to 2,549,508.
- **Search-API counts the report quotes**, re-run live with the box limits from counts.py:41-42 as
  latitude and longitude ranges: PNW all fungi 250,169 with the continent filter and 250,273
  without (104 fewer); PNW genusKey 9623860 3,421 and 3,425 (4 fewer); East all fungi 944,623 and
  944,761 (138 fewer); East Cantharellus 5,545 both ways (0). All four rows of the report's in-box
  table (:170-175) match to the record, and the 242 gap is confirmed as the continent field's
  doing. Total with the continent filter 2,549,508. Licence facet: CC_BY_NC_4_0 2,039,359,
  CC_BY_4_0 394,607, CC0_1_0 115,542, three buckets and no empty value, as the report says (:325).
  Dataset facet with facetLimit 50: 41 buckets, so the earlier review's "twelve or more" was the
  facet's default limit, as the report says (:85).
- **Not re-run:** the count tables, the withheld tally, the eventDate tally, the header check and
  the sha256. They need the 1.48 GB archive, which sits in the other session's worktree. The
  reviewer did not enter it. The arithmetic inside the tables and every public counterpart were
  checked instead (check 7). No seed is involved: no real draw has happened.

## 10. Gaps

What the dispatch asked for that the report does not evidence:

- **The seeded 200-record hand-check CSV.** Not produced. The report's reason (:393-409) is the one
  the T2 completion report and the earlier review established: the population is not in any GBIF
  download, the one-query iNaturalist pull is a proposal awaiting the owner, and this dispatch bars
  that API as a substitute. The reviewer confirms no pull was made from the repo's side (check 2)
  and that the seed for the real draw is now fixed (20260918, :413, agreeing with D31).
- **The person-only photo check.** Waits on the CSV.
- **The concurrent-download limit.** Not confirmed from GBIF's documentation (:70-73, carried from
  the T1 run report); the run submitted one download after the other had succeeded, which the
  dispatch allows.

Marked not checked in the report (:482-493), all stated plainly: why the continent predicate drops
242 in-box records (now answered by D26: the field is empty on them); the New Jersey dataset's
uncertainty values; the exact withheld-uncertainty distribution; 38 publisher names; verbatim.txt
and multimedia.txt; the notification email; CI (no pull request open); `identifications=most_agree`.
The reviewer adds: the first-failure message of the builder's revert check, seen only as a name in
this reviewer's log tail; and the working tree on the run machine at run time.

What the rulings that came after this run now require of its download and code, for the D32 merge
pass and the redo. Listed, not applied; none is this reviewer's to do.

- **D26.** This download (continent-selected) is superseded by one geometry-selected Darwin Core
  Archive download serving T1 and T2. Its DOI record stays as provisional and superseded; when the
  successor lands, `superseded_by` (doi.json:62, now null) gets the entry. Its `why_provisional`
  sentence, "The business account will redo this exact request" (doi.json:4), is now wrong in one
  word: the redo is by geometry, not this exact request. A dated note in the record, not an edit.
  The acceptance check D26 names is against T1's first CSV, but the same shape applies here: the 242
  in-box records this download lacks (104 PNW, 138 East, 4 of them PNW Cantharellus) must reappear
  in the successor or be explained, and the report's item that their gbifIDs were not extracted
  (:484-485) is the list the check needs.
- **D27.** `duplicate_key()` (filters.py:115-123) is still observer, cell and day. D27 adds the
  accepted taxon key, names two keys (observer-duplicate for T2's audit counts, event key for T1's
  tables), and asks reports to give both counts. The report measured what the missing taxon costs
  (42 percent of Cantharellus records reaching the step, :429-440) for exactly this ruling; every
  final-stage cell in its tables moves when the key changes, and the run must be repeated on the
  successor download with both keys.
- **D28.** The day-of-month table for date-only records, by dataset, does not exist: the run
  tallied eventDate shapes (364,209 day-only rows, :338) but not the day of month. The successor run
  adds it before the owner rules on the date step.
- **D29.** The constituent dataset list with licence and count, filed next to the DOI; the register
  row pointed at it; and the commercial-safe subset (CC0 and CC BY) reported beside the all-licence
  figures. The report's licence table already separates the three licences per group and stage, so
  the subset is a sum over its rows once the list is filed. Check 6 has the detail.
- **D31.** The corrected withheld-uncertainty figure is in this report (check 7, item 2). It is not
  yet appended to the completion report's index row (README.md:25), the session log row
  (START_HERE.md:68) or the filters.py docstring (:46-48); D31 says all three are appended, not
  overwritten, and D32 says the merge pass carries them. The run's own index and session rows do not
  mention the correction. Also under D31: no real draw has been made, so the seed rule is met by
  omission; the tuning grid is T1's.
- **D33, for the unified pipeline D32 promises.** T2's step 2 drops "above 250 m or missing" as one
  count (filters.py:72-75); D33 asks T1's counts report to split missing from above the limit. The
  report's inference that the New Jersey dataset's records are missing uncertainty (:327-329) is the
  kind of claim that split would settle. A note for the follow-up task, not a finding against this
  run.

## What the reviewer changed

This file, and one row appended to docs/audits/README.md, in one commit on
t2-credentialed-run-review. Nothing in the builder's code, tests, report, DOI record or record
rows. Candidates for a reviewer's fix that were not fixed, and why: the roll-up row (a result), the
D31 appends (a ruling the merge pass carries, and the review order said list, not apply), the
dataset list (D29's gate, a claim about licences), and the DOI record's "this exact request"
wording (a record row, which gets a dated note rather than an edit).

## Conventions

Checked: the review protocol's ten checks and output form (verdict word, evidence, proposed fix,
Conventions line, Not checked); the earlier T2 review for the header fields and the shape of each
check; docs/audits/README.md for the index form and the append-only rule; START_HERE.md working
rules (no em dashes, short sentences, every fact flagged, append and preserve); the Forager
CLAUDE.md rules on revert checks (saved copy, one module, no collection error, restore from the
copy, confirm the forward change afterwards), on checking a check's sample against something
outside it (the report's tables against the live record and endpoints), and on citing a figure with
its scope. Followed all of them. The phrase check 1 searches for appears in this file only inside
that check's description.

## Not checked

- The archive, the count CSVs, summary.json and withheld_wordings.txt: not opened, they are in
  another session's worktree.
- The sha256 and `unzip -t` result of the zip.
- The run machine's working tree at run time.
- The T1 branch beyond the lines the report cites.
- The builder's synthetic positive-control run (not committed, so not reproducible).
- Which step of the hand roll-up produced 3,253 and 34.
- Why ruff format counts 42 here and 41 in the report.
- CI on either branch.
- What `identifications=most_agree` means on the iNaturalist API.
- Any photo, and the misidentification rate. Person-only.
