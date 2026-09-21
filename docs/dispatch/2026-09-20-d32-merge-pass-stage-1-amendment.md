# Dispatch: D32 merge pass, stage 1, amendment

Written 2026-09-20 about 02:50 PDT by the planning session.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

This amends 2026-09-19-d32-merge-pass-stage-1.md, the stage 1 dispatch you received on 2026-09-19 and stopped at its preconditions. That file stays authoritative for everything this one does not change. The planner has not seen its full text, so this amendment cites its parts by letter and does not restate them. Where the two disagree, this file wins. Report any disagreement you find.

## State this was written against

Relayed by you, not read by the planner.

- origin/main at 3625a55 at 02:36 PDT. The owner is merging decisions-d38-d39 at a8794f5, which files D38 and D39.
- Task and review branch tips, last reported at the 22:37 PDT read on 2026-09-19: t1-calendar-smoke-test 9f6c132, t1-credentialed-run-review e9fbdf5, t2-record-audit 4b22c8d, t2-credentialed-run-review 9491ace.
- Part D ran read-only at that read. Its results exist only in your chat reply and are committed nowhere.

## Verify first, read-only

1. D38 and D39 are on origin/main. Quote the Decision cell of each exactly, with its line number. This satisfies the original dispatch's precondition. If either is missing, stop.
2. The four branch tips above are unmoved. If any has moved, stop and report.

## Writer

Under D38 the writer for every write below is you, the session on the machine holding ~/.config/forager-forecast/ and the archive. No other session writes to the four task and review branches while this runs.

## Changes to the original

3. **Part A runs as written.**
4. **Part B is withdrawn.** D39 applies: the GBIF user value is an account identifier, the two documents holding it name the account, and no edit is required. Nothing is written for Part B on any branch.
5. **Part C runs as written, including its stop-or-proceed test.**
6. **Part D is not re-run in full.** Its results are filed instead, as in item 7.

## Filing, on a new branch off origin/main after the merge

Name the branch d32-stage-1-records. The owner merges it.

7. File a Part D report in docs/audits/. Re-run items 1 and 3, and the shadowing check from item 2, at your new read time, rather than copying the chat reply. File item 4 as reported, keeping its probe markings. Add the line counts item 2 asked for and that were not done. Say which parts are re-read and which are carried from the 22:37 read.
8. File the original stage 1 dispatch and this amendment as received in docs/dispatch/, each with its index row, following c55c419.

## Do not touch

- Any review of record, on any branch.
- DECISIONS.md.
- main directly. Do not merge anything, including the task and review branches. The merges are stage 2.
- The archive and every credential file, except reads the original dispatch already permits for Part C.

## Report

- Read time at the top.
- The two quoted Decision cells from item 1.
- For each commit on each branch: hash, branch, files changed with lines added and deleted, and zero deletions confirmed or each deletion accounted for.
- Part C's stop-or-proceed result, stated plainly.
- Anything in the original dispatch that this amendment leaves unclear.
- Anything you noticed that this dispatch did not ask about.

**Closed without action, 2026-09-20.** Received at about 03:32 PDT and stopped at its item 1, the
precondition that D38 and D39 are on origin/main. They were not: origin/main was at 3625a55, and
decisions-d38-d39 was not merged until cb0bca8 at 14:33 PDT. The line "The owner is merging
decisions-d38-d39 at a8794f5" was, in revision 2's words, "a planner assumption written as state, and
it was wrong". Nothing was written on any branch. Superseded by revision 2,
`2026-09-20-d32-merge-pass-stage-1-amendment-rev2.md`, written at about 03:50 PDT, which stage 1 ran on
and which is filed on main. The time is the upload file's timestamp and the state revision 2 cites as
"Relayed by you at 03:32 PDT"; the minute of the stop itself is not recorded. The session's stop report
is not in the repository; the item stopped at is taken from the coder handoff of 2026-09-20. Filed by
the cleanup dispatch of 2026-09-20. Nothing in this file is edited.
