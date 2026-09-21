# Dispatch: D32 merge pass, stage 2b

Written by the planning session after the report read at 2026-09-20 22:00 PDT.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

Runs after docs-homes-handoffs-dispatches at f06115e is merged into main. Stage 2b lands T2 on main and prepares the T1 code move. The move's independent review and T1's landing are stage 2c.

## If the state has moved

Expects t1-calendar-smoke-test 163950e, t2-record-audit 932b9c9, t1-credentialed-run-review e9fbdf5, t2-credentialed-run-review 9491ace, and main containing f06115e. If a task or review branch has moved at all, stop and report. If main has moved forward past f06115e, carry on and say so.

## Verify first, read-only

1. Quote the Decision cells of D44, D45 and D46 from DECISIONS.md on main, with line numbers. If any is missing, stop.
2. Name the file and line of each of the two one-line changes D44 folds: the D31 docstring, on whichever branch your 21:45 report found it, and T2's duplicate key at records/filters.py lines 115 to 123. Quote each line as it stands.
3. Say whether T2's records carry a taxon field the duplicate key can use. If they do not, adding taxon to the key is not a one-line change; stop and report, because D44 assumed it was.

## Writer

Under D38, you. No other session writes to the four branches while this runs.

## Step 1: fold the two one-liners, per D44

4. Make each change as its own commit on its task branch, message naming the decision it folds. Run the test suite on that branch before and after, and report the counts: passed, failed, skipped, one unit being one test function. If any test that passed before fails after, stop and report; do not fix.
5. Push the task branches.

## Step 2: prepare T2's landing on main

6. Merge t2-record-audit into main locally, without fast-forward as D32 requires. Do not push. Resolve conflicts as follows and no other way:
   - docs/audits/README.md: keep every row from both sides. Report counts before, each side, after, and confirm after equals the distinct union.
   - docs/dispatch/2026-09-18-t1-t2-credentialed-run.md: take the task side, which is main's copy plus the note plus its correction. Confirm with cmp that main's copy is a byte-exact prefix of the result.
   - docs/planning/START_HERE.md: keep all rows from both sides.
   - docs/planning/TASKS.md: row by row. T2's status from the branch; T3's status from main. Then check lines 11 and 12, which your report said still call T1 and T2 not started; if the merge leaves a T1 or T2 status that contradicts the branch, quote it and do not edit it, because that is a planning-document fix for the owner.
   - Any other conflicting path: stop and report without resolving.
7. Run the test suite on the merge result and report counts as in item 4.
8. Report the local merge as ready, with its tree hash and the resolution of each conflict. **Stop here.** Under D40 the push to main waits for the owner's written authorisation naming t2-record-audit. When it comes, push and report the merge commit hash.

## Step 3: prepare the T1 move, per D42 and D45, on t1-calendar-smoke-test

Do not begin step 3 until step 2's merge is on main, so the package T1 moves into is the one on main.

9. Rebase or merge main into t1-calendar-smoke-test first, whichever the branch's history has used before; say which and why. Resolve the audits index by union, as above.
10. One commit, the move, and nothing else:
    - Move records.py, simple_csv.py and gbif_download.py into the records package under paths that collide with nothing. Propose the names in your report before committing if any is not obvious; records.py cannot keep its name.
    - Keep T1's frozen dataclass Record. Rewrite every import your 19:47 report listed to the new paths, and no other change to function bodies. Under D46 the cell code stays as it is; its check comes in the follow-up task.
    - gbif_download: T1's module is the base. Carry over T2's DWCA request template. Do not carry over the continent predicate. Remove T2's module, and move its test to exercise the unified module, or delete it if it only tested the continent predicate; say which.
    - Move the tests with their files.
11. Run the test suite before and after, counts as in item 4. A test that fails after the move because it imported an old path is a defect in the move; fix the import. A test that fails for any other reason: stop and report.
12. Push the branch. Report the commit as ready for independent review, and **stop**. The review is another session's, under D18, and stage 2c dispatches it.

## Do not touch

- main, except the authorised push in step 2.
- Any review of record. The self-checks stay untouched too.
- DECISIONS.md, RELEASE_CHECKLIST.md, the archive, every credential file.
- Any function body, beyond import paths and the gbif_download unification in step 3.

## Report

- Read time at the top, and a read time at the top of each step's report.
- Items 1 to 3.
- Each commit: hash, branch, files changed with lines added and deleted, each deletion accounted for.
- Test counts, before and after, at every point asked.
- Step 2's ready report, then the merge hash after authorisation.
- Step 3's ready report, including the diff summary of the unified gbif_download against both originals.
- Anything you noticed that this dispatch did not ask about.
