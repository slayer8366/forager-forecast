# D35 to D37 filed: report for part 1 of the dispatch

**Date:** 2026-09-19.
**Type:** completion report for part 1 of docs/dispatch/2026-09-19-file-d35-d37-and-rename.md. Part 2 is not started here (see "Not done").
**Base:** main 79b149c, on branch decisions-d35-d37. Commits: c55c419 (dispatch filed as received, index row), f047309 (the three rows), then this report with its index row.
**Supersedes:** none.

Every claim names a commit, a file and line, or a command whose output is quoted, or is marked inferred. Observed means this session ran the command; read means a file was opened.

## Verify first, as answered

1. **Main.** Observed. `git fetch origin` at 2026-09-19T12:24:18Z; origin/main is 79b149c7ff8305d7af7dc93449854ce677e839f7. `git log 79b149c..origin/main` printed nothing: no commits since 79b149c.
2. **Header and shape.** Read, docs/planning/DECISIONS.md line 6 at 79b149c: `| ID | Date | Decision | Reason | Alternatives considered | Supersedes |`. Six columns (eight pipe-separated fields per row). Every existing row has eight fields (`awk -F'|' '/^\| D/ && NF!=8'` printed no rows). The three dispatch rows have eight fields each. No reshaping was needed.
3. **Highest D.** Observed. D34 at line 8 of DECISIONS.md at 79b149c. No branch carries D35, D36 or D37 (grep over every remote branch's DECISIONS.md, total 0).
4. **Paths and heads.** Observed, all as relayed: docs/audits/2026-09-18-t1-credentialed-run-review.md on t1-credentialed-run-review at head e9fbdf5 (file last changed at e9fbdf5) and on t1-calendar-smoke-test at head 9f6c132 (file last changed at 2c540e2); docs/audits/2026-09-18-t2-credentialed-run-review.md on t2-credentialed-run-review at head 9491ace (file at 9491ace) and on t2-record-audit at head 4b22c8d (file at f8adaa4).

## What landed

| Commit | Change |
|---|---|
| c55c419 | docs/dispatch/2026-09-19-file-d35-d37-and-rename.md, byte-identical to the upload (`cmp` exit 0); one row appended to docs/audits/README.md |
| f047309 | docs/planning/DECISIONS.md: D37, D36, D35 inserted directly under the table header, in the file's newest-first order |
| next | this report and its index row |

## Evidence

`git diff --numstat 79b149c f047309 -- docs/planning/DECISIONS.md`, observed:

```
3	0	docs/planning/DECISIONS.md
```

Deleted lines: 0. The three inserted lines diff identical to the dispatch's lines 41, 43 and 45 (observed). Lines 11 to 44 of the new file equal lines 8 to 41 of the file at 79b149c, so D1 to D34 are unchanged (observed). 37 rows, all eight fields. No em dashes added. The dispatch separates its three rows with blank lines; they are inserted as consecutive table rows, since a blank line inside a Markdown table ends the table. The row text itself is unchanged.

## Not done, and why

Part 2 (the two renames on t1-calendar-smoke-test and t2-record-audit) is not started. The dispatch says it starts only once part 1 is merged, and D35 assigns those branches to the session that holds the GBIF credentials. This session filed part 1 because filing decision rows on main is the work it has done for every row since D14 and needs no credentials. Whether it also runs part 2 is the owner's call, since the credentialed session was restarted after this dispatch was written.

## Decisions taken here, and what was rejected

- The rows were inserted under the header (newest first), the file's existing order, rather than at the bottom. Rejected: appending at the bottom, which would break the newest-first order every earlier row follows.
- No session log row in START_HERE.md, following the filing precedent (a filing is not a task).

## Owner items

- Hand this branch to a reviewer under D18, then merge (person-only item in the dispatch).
- Decide who runs part 2 now that the credentialed session has been restarted.
- Read-only archive access for the independent reviewer under D35 (person-only, not set up here).

## Not checked

- CI on this branch (documents only).
- The unfiled version 1 of D35 and D36, which is in no repository.
- Anything on the T1 and T2 branches beyond the four paths and heads above.

Conventions: index rows at docs/audits/README.md lines 19, 21, 23, 24 and 30 (dispatches filed as received with a `cmp` check and a `../dispatch/` index row) and the commit shapes of 57f0f3a (D24 to D34 rows) and 62cca94 plus 3d5145a plus bc7e8bf (dispatch, change, report as three commits) were read; the three-commit form was followed.
