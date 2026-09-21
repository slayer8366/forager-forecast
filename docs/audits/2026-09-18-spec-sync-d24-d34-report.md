# SPEC.md sync report: D24 to D34 appended

**Date:** 2026-09-18 (machine local time, UTC-7; the fetch below is UTC on 2026-09-19).
**Type:** completion report for docs/dispatch/2026-09-18-spec-sync-d24-d34.md.
**Base:** main 0931757, on branch spec-sync-d24-d34. Commits: 62cca94 (dispatch filed as received, index row), 3d5145a (SPEC.md), then this report with its index row.
**Supersedes:** none.

Every claim names a commit, a file and line, or a command whose output is quoted, or is marked inferred. Observed means this session ran the command; read means a file was opened.

## Verify first, as answered

1. **Main.** Observed. `git fetch origin` at 2026-09-19T06:31:23Z; origin/main is 093175784014c44aeb4324e8b9f7e45cefb1b3e3. `git log 0931757..origin/main` printed nothing: no commits since 0931757. Every premise in the dispatch's "State this was written against" held.
2. **Headings.** Read, docs/planning/SPEC.md at 0931757. In order: Goal (line 5), Scope (11), Out of scope (22), Decisions (32), Requirements (51), Constraints (74), Acceptance (83), Unverified (94), Open questions (103). All five named sections exist under exactly those names.
3. **Alaska line.** Read, SPEC.md:30 at 0931757: "- Alaska in phase 1, added 2026-09-18 under D31. BIGMAP covers the coterminous US only (T3), so no verified host-tree layer covers it and it stays masked with Mexico and the Arctic." Item A therefore needed no edit and none was made.
4. **Weather bullet under Decisions.** Read, SPEC.md:40-41 at 0931757: "- Train and serve on the same weather product, ERA5-Land. Thresholds belong to their product, and Daymet arrives a month late." It does not name models=era5_seamless and cites neither D19 nor D21 (`grep -c -E 'era5_seamless|D19|D21'` over the file returned 0). **Finding, not fixed:** that bullet is behind D19 and D21. The new D24 and D25 bullet appended beneath it cites D19 and D25, so a reader reaches the current product name from the section, but the stale line itself stands as the dispatch requires.
5. **Unmerged branches touching SPEC.md.** Observed. For every remote branch not an ancestor of origin/main (t1-calendar-smoke-test 9f6c132, t2-record-audit 4b22c8d, t1-credentialed-run-review e9fbdf5, t2-credentialed-run-review 9491ace), `git log origin/main..<branch> -- docs/planning/SPEC.md` printed nothing. No unmerged branch touches SPEC.md, so no merge conflict is foreseen on that file. The audit index will conflict with every one of those branches, as it always does; the repo's practice is a union merge keeping every row.
6. **Radar in the T3 report.** Read, docs/audits/2026-09-18-t3-verify-data-layers-completion-report.md at 0931757: lines 92 to 96 ("Radar coverage gaps in the mountain West", NOAA 2019 study, Figure B.1) and lines 144 to 146 (a Cascades-specific blockage evaluation, not found; Kucera et al. 2005 by title only). Found, so the "found" variant of the Unverified bullet was used with that path.
7. **Filing form.** Read, docs/audits/README.md at 0931757 rows at lines 19, 21, 23 and 24: dispatches are filed as received under docs/dispatch/ with a `cmp` check against the upload, and indexed with a row whose file column is the backticked relative path `../dispatch/<file>`. Commit shape from `git log -- docs/dispatch`: bbd6dba filed the review protocol alone with its index row in the next commit 0f860c2; d9b69fe and 8437497 filed a ruling document together with the rows it ordered, index row in the same commit. Report form from the T3 report lines 1 to 8: header with Date, Type, Base, Supersedes, then sections. Followed here: dispatch plus index row in one commit (62cca94), the SPEC.md change alone (3d5145a), the report plus its index row last.

## What landed

| Commit | Change |
|---|---|
| 62cca94 | docs/dispatch/2026-09-18-spec-sync-d24-d34.md, byte-identical to the upload (`cmp` exit 0); one row appended to docs/audits/README.md |
| 3d5145a | docs/planning/SPEC.md: ten bullets appended, four sections, zero deleted lines |
| next | this report and its index row |

## Evidence

`git diff --numstat main...spec-sync-d24-d34` for SPEC.md, observed at 3d5145a:

```
10	0	docs/planning/SPEC.md
```

Deleted lines in the SPEC.md diff: 0 (`git diff | grep -cE '^-[^-]'`). Em dashes in added lines: 0. The two occurrences of the barred phrase in SPEC.md are the pre-existing R3 and R8 lines that forbid it; none was added.

Bullets added, in file order, each with the DECISIONS.md line of the row it cites at 0931757 (D34 is line 8, so D(n) is line 42 - n):

| Section | Bullet (first words) | Cites | DECISIONS.md line |
|---|---|---|---|
| Decisions | "Every Open-Meteo archive request also pins..." | D25, D24, D19 | 17, 18, 23 |
| Decisions | "Every duplicate key includes taxon..." | D27 | 15 |
| Decisions | "T1's evaluation is fixed before any fit..." | D33 | 9 |
| Decisions | "The production seed is 20260918..." | D31 | 11 |
| Constraints | "A layer whose licence is not stated at source..." | D31 | 11 |
| Constraints | "Licence gate (D29)..." | D29, D22 | 13, 20 |
| Unverified | "Update 2026-09-18: T3 checked MTBS..." | T3 report | docs/audits/2026-09-18-t3-verify-data-layers-completion-report.md |
| Unverified | "Update 2026-09-18: radar blockage..." | T3 report lines 92 to 96 | same file |
| Unverified | "Update 2026-09-18: this repository is the codebase..." | SPEC.md:101, still present | n/a |
| Open questions | "Update 2026-09-18 on the commercial question..." | D29, D24, D19 | 13, 18, 23 |

The full SPEC.md diff is `git diff 0931757 3d5145a -- docs/planning/SPEC.md`; it consists of the ten added lines above and nothing else.

**The two D25 parameters.** Read on branch t1-calendar-smoke-test (tip 9f6c132 at the fetch above). The T1 completion report, docs/audits/2026-09-18-t1-calendar-smoke-test-completion-report.md line 55 (added at f9890ad), states: "elevation=nan and cell_selection=nearest turn both off (Evidence, \"Point versus cell\")"; lines 332 and 333 quote Open-Meteo's documentation on elevation=nan. The code, src/forager_forecast/open_meteo.py lines 59 and 60 (added at ac12f55), pins `"elevation": "nan"` and `"cell_selection": "nearest"`, with the reasons at lines 10 to 14. The two places agree: the same two names with the same two values. Not added to SPEC.md, per the dispatch's rejected alternative; returned here as evidence.

## Deviations

None from the dispatch. Item A was skipped because step 3 found the Alaska line, which the dispatch anticipated.

## Decisions taken here, and what was rejected

- Each bullet was added as one line, word for word, rather than wrapped to the file's usual width. Rejected: re-wrapping, since the dispatch said word for word and a wrapped bullet would not match the source text on a line-by-line comparison.
- No session log row in START_HERE.md. The dispatch names the report and its index row as the outputs and says stop; the review-protocol filing set the precedent that a filing is not a task.

## Owner items

- The weather bullet at SPEC.md:40 is stale against D19 and D21 (finding 4). A later dispatch can append an Update bullet beneath it.
- The branch is ready for the review the dispatch's person-only section names, then the merge.

## Not checked

- CI on this branch (documents only; ci.yml triggers on main pushes and pull requests).
- The planning doc's own copy of the Spec; only the repo's SPEC.md was read.
- The two D25 parameters against Open-Meteo's live documentation; the report's quotation was taken as read.
- The T1 branch beyond the lines cited.
- The zynergy-site repository.

Conventions: index rows at README.md lines 19, 21, 23 and 24 and the commit shapes bbd6dba, 0f860c2, d9b69fe and 8437497 were read; the form found was dispatch-as-received with a `cmp` check and a `../dispatch/` index row, report with a Date, Type, Base, Supersedes header; both were followed.

## Amendment 1 (version 2), applied 2026-09-19

**Base for this section:** branch spec-sync-d24-d34 at bc7e8bf, main 0931757, review at 7836465 on spec-sync-d24-d34-review; fetched 2026-09-19T07:59:05Z, none of the three had moved. Commit 08a20c0 carries the dispatch-file append and the SPEC.md bullets; this section and its index row follow in the next commit.

**Filing.** The amendment (version 2; version 1 was never filed) is appended to docs/dispatch/2026-09-18-spec-sync-d24-d34.md as a blockquote after the original text, the form the T1 amendments used (docs/dispatch/2026-09-18-t1-calendar-smoke-test.md lines 95 and 103). Stripping the quote prefix from the appended block reproduces the upload byte for byte (`diff` exit 0, observed).

**Verify first, as answered.**
1. T3 report lines 92 to 96 at 0931757, read: "Radar coverage gaps in the mountain West. NOAA 2019, 'Study: Gaps in NEXRAD Radar Coverage', https://repository.library.noaa.gov/view/noaa/25911/noaa_25911_DS1.pdf. Verified. Figure B.1 maps coverage at 4, 6 and 10 kft AGL: 'most of the radar coverage gaps are in the intermountain western US'; Appendix K: 'both central and coastal Oregon have limited to no radar coverage below 10,000 ft AGL'." In one line: T3 opened the NOAA 2019 study and quoted it; the Cascades-specific evaluation (lines 144 to 148) names McRoberts and Nielsen-Gammon 2017 as applied to the central and eastern US only and Kucera et al. 2005 as "found by title and not opened". The reviewer's reading holds, so the Unverified bullet was added.
2. SPEC.md at bc7e8bf, read: lines 40 to 41 are the ERA5-Land weather bullet with no product name and no D19 or D21; line 119 is the Open questions bullet containing "the Copernicus route is CC BY 4.0 (D24)". Both read as the review describes.

**What landed in SPEC.md** (commit 08a20c0): three bullets, 17 lines added, 0 deleted (`git diff --numstat bc7e8bf 08a20c0 -- docs/planning/SPEC.md`, observed). Placement, by first line: Decisions bullet at line 54 (after the D31 seed bullet), Unverified bullet at line 115 (after the codebase update), Open questions bullet at line 127 (after the CC BY 4.0 bullet it corrects). Every added line equals the amendment's lines 41 to 44, 59 to 61 and 47 to 56 (`diff` on the added lines, content identical, observed). Removing the 17 added lines gives a file byte-identical to bc7e8bf (observed). No em dashes added. Line 119 and the radar bullet were not edited or deleted; each correction sits beneath its target.

**Not done, per the amendment's scope:** no register row for the Copernicus store; the precipitation accumulation convention and UTC day boundaries under D24 stay open; the equivalence test stays open and remains a gate before any fit.

**Not checked:** cds-credentials-report.md, which the amendment quotes and which is outside this repository; the store's licence at source; CI on the branch.

The reviewer re-checks the drift item only, as the amendment asks.
