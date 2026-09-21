# Dispatch: D32 merge pass closeout

Written by the planning session after the review report read at 23:08 PDT on 2026-09-20.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

Runs after the owner has authorised, and you have pushed, the merges of t1-calendar-smoke-test and then t1-move-review into main.

## If the state has moved

Expects main to contain eb3b907 and 4134144. If it does not, stop: the merges have not landed, and this dispatch is early. If main has moved forward past them, carry on and say so.

## One commit, on a branch d32-merge-pass-closeout off main

1. File in docs/dispatch/ with index rows, per D41: the stage 2a dispatch if not already filed, the stage 2b dispatch, and the stage 2c review dispatch. Each byte-identical to the file you received; say which you have and which you do not, and do not reconstruct any.
2. File the stage 2b report in docs/audits/ as the record of steps 1 to 3, including the T2 merge authorisation the merge commit could not record: the owner's words "Merge t2-record-audit to main." at about 22:46 PDT. Say in the report that the commit message predates the authorisation, which is why it is recorded here.
3. Record the two T1 merge authorisations in the same report, with the owner's wording and time for each.
4. Append a dated note to the T1 move review's index row, or a short section in the stage 2b report, recording that 4b22c8d reached main inside the T2 merge before its review, and that D42 assigned it to the move's review, which found it clean.
5. Append to docs/planning/TASKS.md, following its in-place convention, that the D32 merge pass is complete, with the merge commit hashes.
6. Write the follow-up task's verify-first list into the report, as inputs, not instructions: the two Record types and where each lives; cell_for at cells.py line 44 and weather_cell at records/filters.py line 102, for D46 and D51; the two request builders, SIMPLE_CSV and DWCA; the three docstrings and two handoff passages that describe the old layout; the test comment citing an unfiled report; and the credential loader's two-of-three-missing case, asserted nowhere.
7. File this dispatch with its index row. Push. Under D40 the merge waits for the owner's written authorisation naming the branch.

## Do not touch

- main, DECISIONS.md, RELEASE_CHECKLIST.md, any review of record, any source or test file, the archive, every credential file.
- The t0b clone's uncommitted branch, until the owner has ruled on it.

## Report

- Read time at the top.
- Item 1: which dispatches were filed and which were missing.
- The commit hash, files changed with lines added and deleted, each deletion accounted for.
- Anything you noticed that this dispatch did not ask about.
