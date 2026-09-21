# Dispatch: D32 merge pass, stage 2a

Written 2026-09-20 about 19:30 PDT by the planning session.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

## If the state has moved

Expects, as relayed at 19:08 PDT: origin/main 1d27f08; t1-calendar-smoke-test e9f7e41; t2-record-audit 4c40017; t1-credentialed-run-review e9fbdf5; t2-credentialed-run-review 9491ace. If any has moved sideways, stop and report. If any has moved forward, carry on and say so.

## What stage 2 is, and why this is only 2a

D32 requires T1's record-handling code to move into T2's package "as its own commit with its own review". A review has to come from a session other than the writer. So stage 2 cannot run end to end in one dispatch. 2a does the work that needs no review and no judgment on main, and gathers what 2b is planned from. Nothing lands on main in 2a.

## Writer

Under D38, you. No other session writes to the four branches while this runs.

## Verify first, read-only

1. The five refs above.
2. Quote D18 and D32 exactly, from DECISIONS.md on main, with line numbers.
3. Recount the fully merged branches. Your 19:08 report said thirteen and listed twelve names. Give the count, the names, and the test you used for "fully merged".

## Part 1, writes on the task branches only

4. Merge t1-credentialed-run-review into t1-calendar-smoke-test, and t2-credentialed-run-review into t2-record-audit. Your prediction is that each conflicts in docs/audits/README.md only. Resolve by keeping every row from both sides. Report each file's row count before and after, and confirm the after count equals the number of distinct rows across both sides. If any other file conflicts, stop and report without resolving.
5. On both task branches, append a dated correction under the Part C note in docs/dispatch/2026-09-18-t1-t2-credentialed-run.md. Say that the dispatch is now filed on main, by the merge at 1d27f08, and that the "pending the owner's merge" sentence above is superseded. Do not edit the note. After this, each task branch's copy is main's copy plus the note plus the correction, so stage 2b can resolve that add/add conflict by taking the task side.
6. Push both task branches.

## Part 2, read-only: inputs for stage 2b

7. **D18 and the post-cut code.** Using D18's text from item 2, say whether 64146f7 (the gbif_download.py docstring on T1) and 4b22c8d (the 65-line tally script on T2) need independent review before landing on main. Quote the words you rely on. If D18 is ambiguous on this, say so and do not resolve it.
8. **The two gbif_download modules.** For src/forager_forecast/gbif_download.py on T1 and src/forager_forecast/records/gbif_download.py on T2, give the diff summary: which functions exist in one and not the other, and which differ in body. Say which one T2's other modules import, and which one T1's tests exercise. Propose which should be canonical and why, marked as a proposal.
9. **The move plan.** For each T1 file in the Part D report's item 2 table, give the target path inside the records package, whether a file already sits at that path, and which tests move with it. List every import, in code and tests on both branches, that the move would break.
10. **START_HERE.md and TASKS.md.** For main ← t2-record-audit, show each conflicting hunk in these two files as plain text: what main has, what the branch has. Say for each hunk whether both sides only add lines, or both sides changed the same existing lines. Do not resolve anything.

## Do not touch

- main. Do not merge anything into main.
- Any review of record, on any branch. Merging a review branch into its task branch carries the review in unchanged. It does not edit it.
- DECISIONS.md, the archive, every credential file.
- Any source or test file. Part 2 is read-only.

## Report

- Read time at the top.
- Items 2 and 3.
- For each commit: hash, branch, files changed with lines added and deleted, and each deletion accounted for.
- Items 7 to 10.
- Who authorised the merge at 1d27f08, as far as you know it. The planner's dispatches did not.
- Anything you noticed that this dispatch did not ask about.
