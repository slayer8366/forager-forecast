# Dispatch: D32 merge pass, stage 2c, independent review of the T1 move

Written by the planning session after the stage 2b report read at 22:56 PDT on 2026-09-20.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

For a session other than the one that wrote eb3b907. D18 requires that, and D35 makes the review of record a document the builder never touches. This session is read-only on every branch except the one it creates for its review.

## State this was written against

Relayed by the builder, not read by the planner.

- main at bc7863a. t1-calendar-smoke-test at eb3b907, the move commit, whose parent 27abc03 is a merge of main into the branch.
- The move is ruled by D42 and D45, on main. D44 ruled that the fold-first clause of D32 covers only two one-line changes, both already on main via T2.
- The builder reports: files moved with content unchanged; 11 import lines changed; one function body changed, request_template gaining a predicate parameter; T2's gbif_download and its test replaced; six T2 tests deleted, each named in the commit; 97 tests passing after, from 53 before the merge.

## If the state has moved

Expects eb3b907 as the tip of t1-calendar-smoke-test. If it has moved at all, stop and report. The review is of that commit.

## What to review

The diff 27abc03..eb3b907, plus the two post-cut commits D42 assigns to this review: 64146f7 (a docstring in gbif_download.py) and 4b22c8d (scripts/t2_withheld_wordings.py, 65 lines, reads only). Quote D42's sentence assigning them.

## Checks, each with the command or file and line it rests on

1. **Content preserved.** For each moved file, show that the content at the new path equals the content at the old path in 27abc03, apart from the import lines. Do not rely on git's rename pairing; the builder reports it pairs gbif_download wrongly. Diff the unified gbif_download against T1's original and confirm it is additions only, and say how many lines.
2. **Only the named lines changed.** List every changed line outside the moved files. The builder reports 11 import lines. Confirm the count and that each is an import, or name what else changed.
3. **One body change.** Confirm request_template is the only function whose body differs from either original, and that the change is the predicate parameter. Confirm the continent predicate is not reachable from any module on the branch.
4. **Deleted tests.** For each deleted test, state what it tested and whether that thing still exists on the branch. A deleted test for code that still exists is a finding.
5. **Tests can fail.** Repeat the builder's revert check on the two carried tests, in a scratch copy, and report what each fails on. Run the full suite and report passed, failed, skipped, one unit being a test function, and reconcile the count against the builder's 97.
6. **Paths.** Confirm PREDICATE_PATH resolves at the new location and that no other file-relative path in src, tests or scripts was left pointing at the old layout.
7. **The two post-cut commits.** Read both. For 4b22c8d confirm it writes nothing and touches no filter, constant or test. For 64146f7 confirm the docstring matches what the function does.
8. **Documents.** The builder names three places that still describe the old layout: the records package docstring, T1's module docstring, and the two DOI records in docs/pulls. Confirm the list is complete or add to it. The DOI records stay as provenance; say whether the docstrings should be fixed in the follow-up task or now.
9. **D46.** The cell code is not changed by this move. Confirm that, and note where the nearest-point assignment lives, for the follow-up task.

## Filing

10. Write the review as docs/audits/2026-09-20-t1-move-review.md, following the standing review protocol on main. Create a branch t1-move-review off eb3b907 for it, with its index row. Do not file at any path the builder uses. Push. Under D40 the merge waits for the owner's written authorisation.
11. Close with one of: the move may land on main as is; or it may land after the named fixes; or it may not land, with the reason.

## Do not touch

- main. t1-calendar-smoke-test, and every other branch except t1-move-review.
- DECISIONS.md, the archive, every credential file, any file under data/.

## Report

- Read time at the top.
- Checks 1 to 9, each with its evidence.
- The review's closing verdict, quoted.
- The commit hash and branch of the filed review.
- Anything you noticed that this dispatch did not ask about.
