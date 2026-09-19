# Standing review protocol: a second agent checks every task for drift and gaps

## State this was written against

- Written 2026-09-18 by Claude, on the owner's ruling that day (D18 in the planning doc): rigorous quality
  standards at all times, and a second agent checks the work for drift and helps close gaps.
- The forecast repo may not exist yet. File this at docs/dispatch/ when T0b lands, and add an index row.
- It applies to every task from T0b onward, including planning-only tasks such as T3.

## Who and when

- The reviewer is a different agent session from the one that did the work. It reads the repo, not the
  builder's chat: the dispatch, the completion report, the commits, START_HERE.md (Fixed terms),
  the newest rows of DECISIONS.md, and the SPEC.md requirements the task touches.
- A task that depends on another does not start until that task's review is filed and the owner has
  seen any drift finding.
- Finding nothing is an acceptable result. Saying what was checked is mandatory.

## Drift checks

1. Terms. Search code, docs, labels and outputs for "fruiting probability", for "probability" used where
   sighting chance is meant, for a percent on relative habitat, and for "calibrated" used loosely.
2. Decisions. Anything built that contradicts a row in DECISIONS.md or a decision in SPEC.md.
3. Fixed choices. Any change to boxes, window lists, year ranges, thresholds or tuning budgets made
   after results were seen. Compare the dispatch with the code and the commit dates.
4. Scope. Work outside the dispatch, and every item on its do-not-touch list.
5. Record. Rows edited instead of superseded, missing index rows, headers without a base commit.
6. Data hygiene. Large files or data in git, and any layer used before its license is in DATA_REGISTER.md.

## Evidence checks

7. Every claim in the report carries a file and line or command output, with read, observed and
   inferred kept apart.
8. At least one guard or test per task gets a revert check: undo the fix, confirm the test fails for the
   right reason, restore it.
9. Headline numbers are re-run from a clean checkout with the recorded seeds and compared.

## Gaps

10. List what the dispatch asked for that the report does not evidence, and everything marked not checked.

## What the reviewer may change

- It may close small gaps in its own commit and list them in the review: a missing index row, a typo,
  a missing test, a missing header field.
- It reports and does not fix anything that touches a decision, a fixed term, a requirement, a result,
  or the scope of the task. The owner decides those.

## Output

- One file per review in docs/audits/, named <date>-<task>-review.md, with an index row.
- For each check: holds, drift, gap, or cannot tell, with the evidence and a proposed fix.
- A Conventions line, and what the reviewer did not check.

## End of project

- Review whether the guard that bars Forager's fruiting-lag visualizer from feeding any ranking has
  gone stale. It stays untouched until then (owner, 2026-09-18).
- Review whether the planning doc and the repo records still agree. For anything built, the repo wins.
