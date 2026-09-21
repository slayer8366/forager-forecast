# Dispatch: D32 merge pass, stage 1, amendment, revision 2

Written 2026-09-20 about 03:50 PDT by the planning session.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

Supersedes 2026-09-20-d32-merge-pass-stage-1-amendment.md, revision 1, which was never filed. Work from this file. Revision 1 said the owner was merging decisions-d38-d39; that was a planner assumption written as state, and it was wrong. This revision corrects it, reorders the work, and settles the three questions revision 1 left open.

This still amends 2026-09-19-d32-merge-pass-stage-1.md, the stage 1 dispatch you received on 2026-09-19. That file stays authoritative for everything this one does not change. The planner has not seen its full text, so this amendment cites its parts by letter and does not restate them. Where the two disagree, this file wins. Report any disagreement you find.

## State this was written against

Relayed by you at 03:32 PDT, not read by the planner.

- origin/main at 3625a55, highest row D37.
- decisions-d38-d39 at a8794f5, four ahead of main and none behind, unmerged. The owner merges it before this dispatch runs. Do not merge it yourself.
- Task and review branch tips, confirmed unmoved at 03:32 PDT: t1-calendar-smoke-test 9f6c132, t1-credentialed-run-review e9fbdf5, t2-record-audit 4b22c8d, t2-credentialed-run-review 9491ace.
- Part D ran read-only at the 22:37 PDT read on 2026-09-19. Its results are committed nowhere.

## Verify first, read-only

1. D38 and D39 are on origin/main. Quote the Decision cell of each exactly, with its line number as it stands on main. This satisfies the original dispatch's precondition. If either is missing, stop, as you did at 03:32.
2. The four branch tips above are unmoved. If any has moved, stop and report.

## Writer

Under D38 the writer for every write below is you, the session on the machine holding ~/.config/forager-forecast/ and the archive. No other session writes to the four task and review branches while this runs.

## Order

Part D's results exist only in a chat reply, so the filing runs first. Then Part A, then Part C.

## Step 1, filing, on a new branch off origin/main named d32-stage-1-records

3. File a Part D report in docs/audits/. Re-run Part D items 1 and 3 at your new read time, and re-run the merged-tree check that found records.py coexisting with the records package and the duplicate gbif_download.py. That is the reading of "the shadowing check" you proposed and it is the right one. File Part D item 4 as reported, keeping its probe markings, and add the per-file line counts item 2 asked for. Mark every line as re-read or as carried from the 22:37 read.
4. File in docs/dispatch/, each with its index row, following c55c419: the original stage 1 dispatch, this revision 2, and 2026-09-18-t1-t2-credentialed-run.md, the credentialed-run dispatch that has been on the task branches only.
5. One commit, or one per file if that suits the index better. Push. The owner merges this branch.

## Step 2, Part A

6. Runs as written. Record D38's line number as it stands on main after the merge, not as it stands on the branch.

## Step 3, Part C

7. Runs as written, including its stop-or-proceed test, with one change to its second item. Do not annotate the credentialed-run dispatch as absent from main. Item 4 files it. Append instead a dated note on both task branches saying it is filed at docs/dispatch/2026-09-18-t1-t2-credentialed-run.md on branch d32-stage-1-records, pending the owner's merge, and name the commit that filed it.

## Part B is withdrawn

8. D39 applies: the GBIF user value is an account identifier, the two documents holding it name the account, and no edit is required. Nothing is written for Part B on any branch.

## Do not touch

- Any review of record, on any branch.
- DECISIONS.md.
- main directly. Do not merge anything, including decisions-d38-d39, d32-stage-1-records, and the task and review branches. The merges are stage 2.
- The archive and every credential file, except reads the original dispatch already permits for Part C.

## Report

- Read time at the top.
- The two quoted Decision cells from item 1, with their line numbers on main.
- For each commit: hash, branch, files changed with lines added and deleted, and zero deletions confirmed or each deletion accounted for.
- Part C's stop-or-proceed result, stated plainly.
- Anything in the original dispatch that this amendment leaves unclear.
- Anything you noticed that this dispatch did not ask about.
