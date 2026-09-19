# SPEC.md sync review: D24 to D34, checked by a second agent

**Date:** 2026-09-18
**Type:** review under docs/dispatch/2026-09-18-review-protocol.md.
**Reviewed:** branch spec-sync-d24-d34, commits 0931757..bc7e8bf over main 0931757 (three commits:
62cca94 dispatch filed and index row, 3d5145a SPEC.md, bc7e8bf report and index row).
**Reviewer base commit:** bc7e8bf, on branch spec-sync-d24-d34-review, tree clean. `git fetch origin
spec-sync-d24-d34 main` at the start: branch tip bc7e8bf, main 0931757. Fetched again before this
commit; neither had moved.
**Supersedes:** none.

The task is documents only, so checks 3, 8 and 9 are adapted: no fixed choice can change, there is no
test to revert, and the headline numbers are line counts. Every claim below names a commit and a file
and line, or quotes a command run in this worktree (observed). Read means the file was opened. Nothing
here was taken from the builder's session. The dispatch's upload is not in the repo, so "filed as
received" can only be checked for internal consistency; see check 5.

## Drift checks

**1. Terms. Holds.** Observed: `git diff 0931757 bc7e8bf | grep -E '^\+[^+]'` piped through
`grep -iE 'fruiting probability|probabilit|calibrat|%|percent'` and, separately, the em dash character returns nothing across all three
commits (183 added lines). A byte grep for U+2014 and U+2013 over the same lines returns 0 and 0.
The two occurrences of the barred phrase in SPEC.md at bc7e8bf are the pre-existing R3 and R8 lines
that forbid it (SPEC.md:64 and :76 at bc7e8bf, :60 and :72 at 0931757), as the report says at line 36.
No added line puts a percent on habitat. "Sighting chance", "calibrated" and "relative habitat" do not
appear in any added line.

**2. Decisions. Drift, in one added line; the other nine hold.**

Word for word: observed. The ten added SPEC.md lines (`git diff 0931757 bc7e8bf -- docs/planning/SPEC.md
| grep -E '^\+[^+]'`) were compared with `diff` against the dispatch's bullet text at lines 42 to 45, 48,
49, 52, 54, 56 and 59 of docs/dispatch/2026-09-18-spec-sync-d24-d34.md, with `(PATH)` in line 54
replaced by the T3 report path. Zero words differ. The only substitution is the one the dispatch
ordered, and the path it names exists at bc7e8bf.

Meaning against the cited rows: read, docs/planning/DECISIONS.md at 0931757, D(n) at line 42 - n.

- Decisions, D25 and D24 bullet (SPEC.md:50, cites D25 at DECISIONS.md:17, D24 at :18, D19 at :23).
  Matches: "two cell-keeping parameters" is D34's own phrase (line 8); "same product, second access
  route" is D24's Supersedes cell; "match within rounding before any model is fit" and "paid Open-Meteo
  plan" as fallback are D24's decision and alternatives cells. Omits D24's verify-first list and the
  Cowork account. An omission, not a contradiction. Holds.
- Decisions, D27 bullet (SPEC.md:51, DECISIONS.md:15). Both keys, the taxon definition and "reports
  give both counts" match D27. Holds.
- Decisions, D33 bullet (SPEC.md:52, DECISIONS.md:9). Pooled Brier skill per box, bootstrap clustered by
  cell, per-fold table, 30 positives, 5,000 m sensitivity with 1,000 m as headline, "not shown" for the
  Pacific Northwest: all match D33 items (2), (3) and (5). Omits (1) and (4). Holds.
- Decisions, D31 seed bullet (SPEC.md:53, DECISIONS.md:11). Seed, budget, grid-first, same for both
  models, inner leave-one-year-out Brier on training years: match. Holds.
- Constraints, D31 licence-state bullet (SPEC.md:86, DECISIONS.md:11). "verified, licence not stated at
  source: blocked from use" for POLARIS and BIGMAP: matches. Holds.
- Constraints, D29 bullet (SPEC.md:87, DECISIONS.md:13 and D22 at :20). Dataset list, licence and count
  per dataset, by-licence table, register pointer, all-licence primary, CC0 and CC BY secondary, both
  fixed and neither dropped, nothing from CC BY-NC ships before the owner rules: matches. Holds.
- Unverified, three Update bullets (SPEC.md:108 to 110). The T3 report at 0931757 marks MTBS, NBAC,
  NALCMS, USGS 3DEP (line 48 to 50, "Verified"), POLARIS, CEC ecoregions and ESRI:102008 as opened; the
  radar item is at lines 92 to 96; SPEC.md:101 still says no codebase has been read, so the third bullet's
  condition held. Hold.
- Open questions, Update bullet (SPEC.md:119, cites D29, D24, D19). **Drift.** The line states "the
  Copernicus route is CC BY 4.0 (D24)". D24 at DECISIONS.md:18 does not state that. Its reason cell says
  "from memory its licence allows commercial use, which T3-style verification must confirm", and its
  decision cell lists "licence at source" under verify first. No record in the repo opens the store's
  licence: `git grep -iE 'climate data store|CC BY 4\.0' bc7e8bf -- docs` finds CC BY 4.0 only for CEC,
  NALCMS, SoilGrids, GlobalFungi, Lembrechts 2022 and the Open-Meteo archive data (T3 report lines 111 and
  363, a different route), never for the store. DATA_REGISTER.md has no row for the store, and
  RESEARCH_LOG.md does not mention it. So the Spec now carries a from-memory licence as a stated fact
  with D24 as its citation, against the Working rule in START_HERE.md that every fact carries its flag.
  The wording is the dispatch's own (line 59), copied word for word as ordered, so this is drift in the
  dispatch text and not a builder deviation. The report does not flag it, though the dispatch invited
  that at line 79. Not changed by the reviewer: it touches a requirement's wording and a licence.
  Proposed fix, for the owner: either a T3-style check that opens the store's licence at source and
  records it in DATA_REGISTER.md, after which the line is true as written; or an Update bullet beneath
  SPEC.md:119 that marks the licence as from memory under D24 until that check is filed.

**3. Fixed choices. Not applicable, and the transcription holds.** No box, window, year range,
threshold or budget is changed here; the bullets copy values from rows the owner accepted in D34 (line
8) before any fit. Observed: each figure appears once in SPEC.md and in its row (20260918; 20 random
configurations; 5,000 m; 1,000 m; fewer than 30 positive; taxon, observer, cell, day; taxon, cell, day),
by `grep -c` over both files. Commit 3d5145a is dated 2026-09-18 23:33:08 -0700, after the D34 row's date.

**4. Scope. Holds.** Observed: `git diff --name-only 0931757 bc7e8bf` lists exactly four files: the
filed dispatch, SPEC.md, the report, the index. `git diff --stat 0931757 bc7e8bf -- docs/planning/DECISIONS.md
docs/planning/DATA_REGISTER.md docs/planning/TASKS.md src tests scripts .github pyproject.toml uv.lock`
is empty. Item A was skipped as the dispatch allowed, since SPEC.md:30 at 0931757 already carries the
Alaska line. Rejected alternatives respected: the added SPEC.md lines match `D26|D28|D30|D32` 0 times and
`elevation|cell_selection` 0 times. Nothing was rebased, merged or cherry-picked from the T1, T2 or
review branches: the three commits have single parents in a straight line from 0931757.

**5. Record. Holds.** Observed: `git diff --numstat 0931757 bc7e8bf -- docs/planning/SPEC.md` is
`10 0`; the reversed diff `git diff bc7e8bf 0931757 -- docs/planning/SPEC.md | grep -cE '^\+[^+]'` is 0.
Stripping the ten added lines from SPEC.md at bc7e8bf and comparing with the file at 0931757 with
`cmp` gives byte-identical, 109 lines each. The two index rows are appended at the end (hunk
`@@ -27,3 +27,5 @@`), no earlier row touched. The report header has Date, Type, Base and Supersedes
(report lines 3 to 6) and names its base commit. The dispatch row uses the `../dispatch/` path form. The
report's form-found claims are true: README.md lines 19, 21, 23 and 24 at 0931757 are the four rows
with `../dispatch/` paths (all four such rows in the file), lines 21, 23 and 24 say `cmp`; bbd6dba
touches only the protocol file and 0f860c2 only the index row; d9b69fe and 8437497 each carry a ruling
document, DECISIONS.md rows and the index row in one commit (`git show --stat`). The three commits under
review follow that: 62cca94 dispatch plus index row, 3d5145a SPEC.md alone, bc7e8bf report plus index
row. "Filed as received" cannot be checked against the upload from the repo. It is internally
consistent: the filed file is 92 lines, the report at line 24 and the index row both say byte-identical
by `cmp`, and the report answers the filed text item by item.

**6. Data hygiene. Holds.** Observed: `./scripts/check-large-files.sh --all` reports 45 files checked,
none over 1048576 bytes, exit 0. `git ls-files` matches one data-like name,
docs/planning/evidence/inat_counts_2026-09-18.json, 2,310 bytes, from the planning pack at 2fcb3c0, not
from this change. The largest tracked blob is uv.lock at 31,551 bytes. No layer is used; documents only.

## Evidence checks

**7. Claims carry evidence. Holds, with three claims lacking a line.** Read, the report. Every
verify-first answer names a commit and a file and line or a command, and marks observed or read. Three
claims do not: line 24, byte-identical to the upload by `cmp`, which nothing in the repo can confirm;
line 36, "Em dashes in added lines: 0", no command shown, re-derived above as 0; line 73, ci.yml
triggers, no line cited, true at .github/workflows/ci.yml:6 to 8 (push to main, pull_request). Nothing
is presented as observed that was inferred.

Re-derived, all observed in this worktree: origin/main is 0931757 and `git log 0931757..origin/main` is
empty. The nine headings at 0931757 sit at lines 5, 11, 22, 32, 51, 74, 83, 94 and 103, as the report's
item 2 says. SPEC.md:30 at 0931757 is the Alaska line as quoted. SPEC.md:40 to 41 is the weather bullet
as quoted, and `grep -c -E 'era5_seamless|D19|D21'` over the file is 0. Of thirteen remote branches, five
are not ancestors of origin/main: the branch under review and the four the report lists at the tips it
gives (9f6c132, 4b22c8d, e9fbdf5, 9491ace); `git log origin/main..<branch> -- docs/planning/SPEC.md` is
empty for all four. The T3 report at 0931757 has the radar item at lines 92 to 96 and the
Cascades-specific gap at 144 to 148. On origin/t1-calendar-smoke-test at 9f6c132, read with `git show`
and `git blame` on the ref, never by entering that worktree: the T1 report line 55 says
"elevation=nan and cell_selection=nearest turn both off", blamed to f9890ad; src/forager_forecast/open_meteo.py
lines 59 and 60 pin `"elevation": "nan"` and `"cell_selection": "nearest"`, blamed to ac12f55, with
the reasons at lines 10 to 14. The two places agree, as the report says. All eight DECISIONS.md line
numbers in the report's table hold (D33 9, D31 11, D29 13, D27 15, D25 17, D24 18, D22 20, D19 23).
The dispatch's own premise at line 12 holds: `git log f96d557..0931757 -- docs/planning/SPEC.md` is the
single commit 9290144, and its line 13 holds: `D24|D25|D27|D29|D33|20260918` has 0 hits in SPEC.md
at 0931757.

**8. Revert check, adapted. Holds.** There is no test. The change is shown purely additive by the
reversed diff (0 added lines when the diff is read backwards) and by the `cmp` in check 5: removing
the ten lines restores the base file byte for byte, so removing any one bullet leaves its section
identical to 0931757 apart from the others.

**9. Headline numbers. Holds.** Observed: numstat 10 added, 0 deleted; `wc -l` gives 92 for the filed
dispatch and 79 for the report; `git diff --stat 0931757 bc7e8bf` shows README.md +2 and 183 insertions
in all, no deletions in any file.

## Gaps

**10. Gap, two items; the rest listed.**

- Report before editing. The dispatch's verify-first section (line 20) says report before editing.
  Whether the answers were shown to anyone before 3d5145a cannot be told from the repo: the three
  commits are 62 seconds apart (23:32:07, 23:33:08, 23:33:09 -0700). Cannot tell, as the T0b review found
  for T0b.
- The CC BY 4.0 claim in the Open-questions bullet is not flagged in the report (check 2). Gap.
- Session log row. The builder chose not to add one (report line 64), citing the review-protocol filing
  precedent, which README.md:21 records in the same words. START_HERE.md's Working rules ask for a row
  per session; the T0b and T3 tasks added one (4ed601d, 41e9cc1) and the filings and reviews did not.
  Reported, not changed: the dispatch names the report and its index row as the outputs and says stop.
- Radar wording. SPEC.md:109 says radar blockage "is covered in the T3 report". T3 lines 147 to 148
  say the Cascades-specific evaluation was found by title and not opened, ticked on the NOAA coverage
  map with the gap stated. The dispatch fixed the "found" wording, so the builder had no choice; the
  owner may want that gap visible in the Spec too.
- The owner finding the report leaves (line 68): SPEC.md:40 stale against D19 and D21. Re-derived,
  true. The dispatch's do-not-touch list barred fixing it. It waits for an Update bullet.
- Carried from the report's Not checked (lines 73 to 77): CI on the branch, the planning doc's own copy
  of the Spec, the D25 parameters against Open-Meteo's live documentation, the T1 branch beyond the
  cited lines, the zynergy-site repository. None re-checked here.

## What the reviewer changed

This file and one index row in docs/audits/README.md. Nothing else.

Conventions: the T3 review header (docs/audits/2026-09-18-t3-review.md lines 1 to 8) and the index rows
at README.md lines 28 and 29 were read; the form found was Date, Type, Reviewed, Reviewer base commit,
Supersedes, then one entry per check with a verdict word, then what the reviewer changed, a Conventions
line and Not checked; followed here, with the index row appended.

## Not checked

- The dispatch's upload. It is not in the repo, so byte-identity was not tested.
- The planning doc's copy of the Spec, and anything outside this repo.
- The store's licence at source (no network beyond git), and the D25 parameters against live
  documentation.
- The two other forager-forecast worktrees that hold live sessions were not entered; the T1 branch was
  read from its remote ref only.
- scripts/verify-open-meteo-historical-fields.sh was not run (D30).
- CI on the branch: documents only, and ci.yml runs on pushes to main and pull requests.
