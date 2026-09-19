# D35 to D37 filing review

**Date:** 2026-09-19.
**Type:** review under docs/dispatch/2026-09-18-review-protocol.md.
**Reviewed:** branch decisions-d35-d37, commits 79b149c..233acb3 (c55c419 dispatch filed and index row, f047309 the three rows, 233acb3 report and index row), over main 79b149c.
**Reviewer base:** 233acb3, on branch decisions-d35-d37-review, cut from the branch under review at its tip.
**First under D35:** this is the first review conducted after D35 was filed. D35 is a row on the branch under review, so the review checks the row that names it. D35's ownership clause covers the T1 and T2 task branches and is not exercised here; its clause that the independent review is the review of record is what this document is.

Every claim below names a commit, a file and line, or quotes the command run. Observed means this reviewer ran the command in the review worktree. Read means the file was opened. Inferred is marked where used. The owner's upload of the dispatch is not in the repository, so "filed as received" can be checked only for internal consistency, and that is what check 7 does.

Before starting: `git fetch origin decisions-d35-d37 main`; origin/decisions-d35-d37 at 233acb3, origin/main at 79b149c, both as the launching note stated (observed). Fetched again before committing; see "What the reviewer changed".

## Check 1, terms: holds

- Added lines across the three commits: `git diff 79b149c 233acb3 | grep -E '^\+[^+]'` gives 115 lines (observed).
- "fruiting probability": 0 matches. "probabilit" in any form: 0 matches. "calibrat": 0 matches. "habitat" with a percent: 0 matches (observed, case-insensitive grep over the 115 lines).
- Em dashes (U+2014) and en dashes (U+2013): 0 and 0 in the added lines (observed).
- Secrets and account identifiers: an email pattern, and the words token, key, password, secret, and the GBIF and CDS variable names, grepped over the 115 added lines. The only hits are the word "secret" in the D36 row text itself (DECISIONS.md line 9 and the dispatch line 43) and the dispatch's "No secret in any file" line (dispatch line 71). No value, no username, no email address in the diff (observed). Commit metadata carries the repository's usual author name and email on all three commits; that is an account identifier in git metadata, not in the diff, and it is the same author every commit in this repository carries. Noted, not a finding.

## Check 2, decisions: holds

- The three rows equal the dispatch's rows: `diff <(sed -n '8,10p' docs/planning/DECISIONS.md) <(sed -n '41p;43p;45p' docs/dispatch/2026-09-19-file-d35-d37-and-rename.md)` exits 0. A word-by-word diff (each line split on spaces) also gives 0 differing lines (observed). Zero words differ.
- D36 (DECISIONS.md line 9) opens "Proposed." (read). D37 (line 8) says "D36 is not ruled on and stays proposed." (read).
- D37 quotes the owner's words: `Owner's words: "Yes, that's correct as asserted."` at line 8 (read). This follows the D34 precedent at line 11, which also quotes the owner whole.
- D35's Supersedes cell (line 10, seventh pipe field) reads "None. Answers the collision the T0b review surfaced." (observed by `awk -F'|'`).
- D35 against D18 (line 27, read): D18 says a second agent in a separate session reviews every task. D35 says the credentialed session's reviews of its own runs are builder self-checks and not D18 reviews, and the independent reviews on the side branches are the reviews of record. That keeps D18's independence. No contradiction.
- D35 against D32 (line 13, read): D32 says the credentialed-run commits on T1 and T2 are reviewed before anything else of theirs merges, then T1 and T2 merge without fast-forward keeping every appended row. D35 says the credentialed session owns those branches through the D32 merge pass and each self-check moves to its own filename before any merge. That adds a step before D32's merge and changes none of D32's order. No contradiction.
- The two process clauses the dispatch says are deliberately left out of D35 (dispatch lines 98 to 102: hand-offs filed on main before work starts; every commit on main carries an index row) do not appear in the D35 row: grep for "filed on main before", "every commit on main" and "index row" over line 10 gives 0 (observed).

## Check 3, fixed choices: holds, not applicable

No box, window list, year range, threshold or tuning budget is in the diff. Grep over the 115 added lines for seed, threshold, budget, year range, 20260918, 1,000 m, 5,000 m and window: 0 matches (observed). Nothing to compare against commit dates.

## Check 4, scope: holds

- `git diff --stat 79b149c 233acb3`: four files, 163 insertions, 0 deletions: docs/audits/2026-09-19-decisions-d35-d37-report.md (56), docs/audits/README.md (2), docs/dispatch/2026-09-19-file-d35-d37-and-rename.md (102), docs/planning/DECISIONS.md (3) (observed).
- Nothing under src, tests, scripts or .github; SPEC.md, DATA_REGISTER.md, TASKS.md and START_HERE.md untouched (`git diff --name-only` filtered, no match, observed).
- The four branches the dispatch names as do-not-touch or as part 2 targets are unmoved: `git log -1 --format=%h` on origin/t1-calendar-smoke-test 9f6c132, origin/t2-record-audit 4b22c8d, origin/t1-credentialed-run-review e9fbdf5, origin/t2-credentialed-run-review 9491ace (observed). Both self-check files still exist at their original paths on the task branches (`git cat-file -e`, observed), so no rename was done.
- One deviation, disclosed: the dispatch's header (lines 7 to 8) hands the whole dispatch to the credentialed session. The report (line 37) says a different session filed part 1 and gives its reason (part 1 needs no credentials; part 2 waits for the merge and D35 assigns it). The work done is exactly part 1, so this is not work outside the dispatch. Who runs part 2 is an owner item and the report lists it as one (line 47).

## Check 5, record: holds

- Rows inserted directly under the header, newest first, as DECISIONS.md line 3 requires. D1 to D34 byte-identical: `diff <(git show 79b149c:docs/planning/DECISIONS.md | sed -n '8,41p') <(sed -n '11,44p' docs/planning/DECISIONS.md)` exits 0 (observed). File length 41 at 79b149c, 44 at 233acb3 (observed).
- Index rows appended, none edited: `diff <(git show 79b149c:docs/audits/README.md) <(sed '35,36d' docs/audits/README.md)` exits 0, so the index minus its two new rows equals the base file (observed). The two new rows are lines 35 and 36.
- The dispatch is indexed with the `../dispatch/` path form at README.md line 35 (read).
- Report header has Date, Type, Base and Supersedes at lines 3 to 6 (read). Base names main 79b149c and the branch.
- The report's Conventions claims (report line 56) are true (observed): README.md lines 19, 21, 23, 24 and 30 each end in a `../dispatch/` path and lines 21, 23, 24 and 30 each mention `cmp`. 57f0f3a is "Record proposals D24 to D33 and the owner's ruling D34 accepting them" and touches DECISIONS.md (11 lines) plus two filed proposals and two index rows. 62cca94, 3d5145a and bc7e8bf are the SPEC.md sync's dispatch, change and report as three commits at 23:32:07, 23:33:08 and 23:33:09 on 2026-09-18. The branch under review follows that three-commit shape.

## Check 6, data hygiene: holds

- `./scripts/check-large-files.sh --all`: "48 file(s) checked, none over 1048576 bytes", exit 0 (observed).
- `git ls-files` filtered for data extensions (csv, zip, tif, parquet, nc, grib, geojson, gpkg, shp, pmtiles, sqlite, gz, tar, xlsx, pkl): none (observed). The only non-code, non-document tracked files are .githooks/pre-commit and docs/planning/evidence/fruiting-lag-atlas.html, both pre-existing. Largest blob at 233acb3 is uv.lock at 31,551 bytes (observed).
- No layer is used by this change, so DATA_REGISTER.md licence state does not apply.

## Check 7, evidence in the report: gap

Re-derived and holding (all observed unless marked):

- Main: origin/main is 79b149c7ff8305d7af7dc93449854ce677e839f7; `git log --oneline 79b149c..origin/main | wc -l` is 0. Report item 1 holds. The report's fetch time 12:24:18Z is one minute before the three commits at 12:25:18Z (`git log --format=%cI` converted to UTC), consistent.
- Header row at 79b149c line 6: `| ID | Date | Decision | Reason | Alternatives considered | Supersedes |`, exactly as quoted in report item 2.
- Field count, the owner's question: the report's "eight fields" and "37 rows, all eight fields" (lines 13 and 33) count pipe-delimited fields as `awk -F'|'` returns them, where a six-column row split on "|" gives eight fields with an empty field at each end; this reviewer split the header row and the D35 row (line 10) the same way and got NF=8 with empty first and last fields, and splitting the D35 row on " | " after stripping its outer pipes gives six columns. So the count is of fields, not columns, the report says so in item 2 ("Six columns (eight pipe-separated fields per row)"), and the row has six columns. Rows with NF not 8 at 233acb3: 0. D rows: 37 at 233acb3, 34 at 79b149c.
- Highest D at 79b149c: 34, at line 8. Report item 3 holds. D35, D36, D37 on every other remote branch (`git show <branch>:docs/planning/DECISIONS.md | grep -cE '^\| D3[567] '` over the 13 remote refs other than decisions-d35-d37): 0 on each.
- Paths and heads: t1-credentialed-run-review head e9fbdf5, file last changed e9fbdf5; t1-calendar-smoke-test head 9f6c132, file last changed 2c540e2; t2-credentialed-run-review head 9491ace, file at 9491ace; t2-record-audit head 4b22c8d, file last changed f8adaa4. All four match report item 4. The dispatch (lines 22 to 23) gives 2c540e2 and f8adaa4 without saying they are file commits and not branch heads; the report reads them as file commits and states both. That reading is the one the hashes support.
- Em dashes in the report: 0. Newest-first order: DECISIONS.md line 3 (read).

Claims that carry no evidence the repository can check, and are not marked inferred:

- Report line 37: "the credentialed session was restarted after this dispatch was written." Nothing in the repository records sessions or restarts. Not marked. Cannot tell from the repo.
- Report line 37: "filing decision rows on main is the work it has done for every row since D14." Every commit in 79b149c..233acb3 and in the earlier filings carries the same author, so the repository cannot tell one session from another. Not marked. Cannot tell from the repo.
- Report line 21: "byte-identical to the upload (`cmp` exit 0)." The upload is not in the repository, so this cannot be re-run. Cannot tell. Internal consistency holds: the dispatch's own header claims (line 15 to 16: main 79b149c, index at 18 rows, DECISIONS.md ends at D34, D35 and D36 on no branch) all re-derive true against 79b149c (18 index rows, D34 highest, 0 matches on every branch), and the filed file is 102 lines in both the working tree and `git show 233acb3:` (observed).
- Report items 3 and 4 say "Observed" without quoting the command. Both re-derive true above. A quoted command would have made the claim checkable without re-deriving it.

Proposed fix: none needed in the record. The two session claims at line 37 belong in an "inferred" or "from this session's own history" marking. This reviewer does not edit a report's findings (protocol, "What the reviewer may change"). The owner may want the "restarted" claim confirmed from their own knowledge before deciding who runs part 2.

## Check 8, revert check, adapted: holds

No test exists for a documents-only change. The check adapted to "purely additive":

- `git diff 233acb3 79b149c -- docs/planning/DECISIONS.md | grep -cE '^\+[^+]'` is 0: going backward adds nothing, so going forward deleted nothing (observed).
- `sed '8,10d' docs/planning/DECISIONS.md | cmp - <(git show 79b149c:docs/planning/DECISIONS.md)` exits 0: stripping lines 8 to 10 restores the base file byte for byte (observed).
- The same for the index: the base README.md equals the new one with lines 35 and 36 removed (check 5).

## Check 9, headline numbers: holds

- `git diff --numstat 79b149c f047309 -- docs/planning/DECISIONS.md`: `3	0	docs/planning/DECISIONS.md` (observed), as the report quotes at line 30.
- Filed dispatch: 102 lines (`wc -l`, observed), matching c55c419's stat.
- Index rows added in the range: 2 (`git diff ... -- docs/audits/README.md | grep -cE '^\+\| 2026'`, observed). Index rows in total: 20 at 233acb3, 18 at 79b149c (observed).
- Report: 56 lines, as 233acb3's stat says.

## Check 10, gaps: holds, with the list

What the dispatch asked for under "Evidence to return" (lines 84 to 91), against the report:

- Verify-first answers with hash, file and line, marked read, observed or inferred: present (report lines 12 to 15). Items 3 and 4 lack a quoted command (check 7).
- DECISIONS.md diff showing three added rows and zero deleted lines: the numstat is quoted (line 27 to 33); the diff itself is commit f047309. Present.
- `git log --follow` for part 2: not applicable, part 2 not started.
- Conventions: present and true (check 5).
- Not checked: present (report lines 50 to 54).

Everything the report marks not checked (lines 52 to 54): CI on the branch; the unfiled version 1 of D35 and D36; anything on the T1 and T2 branches beyond the four paths and heads. This reviewer also did not check CI, and could not check version 1 (in no repository).

Part 2 correctly not started: the dispatch says part 2 starts only once part 1 is merged (line 10 to 11, line 50), part 1 is not merged (origin/main still 79b149c), and the report says why at line 37. Holds.

The blank-line disclosure (report line 33): the dispatch's rows sit at lines 41, 43 and 45 with lines 42 and 44 blank (`sed -n '42p;44p' | cat -A` prints two bare line ends, observed). A blank line ends a Markdown table, so the rows had to be consecutive. The report says this and says the row text is unchanged, which check 2 confirms. The disclosure is accurate and complete. One more silent reading the report also discloses: the dispatch says "append" (line 38) and the rows went under the header, not at the bottom; the report gives the reason at line 41 (newest-first order). Accurate.

Rejected alternatives respected (dispatch lines 73 to 81): rows are numbered D35, D36 and D37 with D37 the ruling row, not D35 and D36 alone (DECISIONS.md lines 8 to 10); no rename done (check 4, files still at original paths, task branch heads unmoved); no Cowork report filed (the four files in the diff are the only files changed, check 4).

One observation beside the filing, for the owner, not a finding against the branch: D36's Reason cell says the T1 run report quotes a credential variable's value. On origin/t1-calendar-smoke-test at 9f6c132, a grep for a credential-variable assignment pattern matches docs/audits/2026-09-18-t1-credentialed-run-report.md line 92 and docs/audits/2026-09-18-t1-calendar-smoke-test-completion-report.md lines 61 and 62. This reviewer read none of those lines; a boolean test for placeholder markers on each returned no. That is consistent with D36's premise. File and line only, per the dispatch's rule and D36.

## What the reviewer changed

- Added this file and one row to docs/audits/README.md. Nothing else. No decision row, fixed term, requirement or scope touched. Before committing: `git fetch origin decisions-d35-d37 main`, both tips re-read; the result is in the index row and in the commit message.

Conventions: the two earlier reviews under the protocol were read for form, docs/audits/2026-09-18-spec-sync-d24-d34-review.md (index row at README.md line 32, additive check by stripping lines and `cmp`, a header with Reviewed and Reviewer base) and docs/audits/2026-09-18-t3-review.md (index row at line 28). That form was followed: ten numbered checks with a verdict word, a "What the reviewer changed" section, this line, and "Not checked".

## Not checked

- CI on the branch under review (documents only; not run here).
- The owner's upload of the dispatch (not in the repository). Only internal consistency was checked.
- The unfiled version 1 of D35 and D36 (in no repository).
- The content of the three lines on the T1 branch that matched the credential pattern (deliberately not read).
- Whether the credentialed session was restarted (not knowable from the repository).
- Anything on the T1 and T2 branches beyond the four paths, heads and the one pattern count above.
- scripts/verify-open-meteo-historical-fields.sh was not run (D30, frozen).
