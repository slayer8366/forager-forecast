# Dispatch: file Cowork's two credential reports

Written 2026-09-20 about 18:10 PDT by the planning session.
Project: forager-forecast. Repo: slayer8366/forager-forecast.
Attached: cds-credentials-report.md, gbif-credentials-report.md.

## If the state has moved

Expects origin/main at cb0bca8 and d32-stage-1-records at bb15fbb. If either has moved sideways, onto a commit that does not contain those, stop and report. If either has moved forward, meaning the expected commit is an ancestor of the new one, carry on and say so.

## Why

D36's row cites three reports. The T1 run report is in the repository. These are the other two. Filing them gives the row's reasoning a checkable source, and gives the corrected "asked twice" count a citation: line 102 of the CDS report lists the test-account question as asked twice and not answered.

## Verify first, read-only

1. The branch tips above.
2. docs/planning/evidence/ exists and is where evidence of this kind lives. If it is not, say what the existing home is and use that.

## Part 1, read-only: the leak scan

3. Scan both attached reports against the actual credential values: the two entries in ~/.cdsapirc, and GBIF_USER, GBIF_PWD and GBIF_EMAIL in ~/.config/forager-forecast/gbif.env. Hold values in memory. Never write one into any output, file or commit. Use the method from your Copernicus check, including a positive control, so a negative result is worth something.
4. Specifically: the CDS report's evidence table prints a request ID that is UUID-shaped, and the same report describes the key as a 36-character UUID-shaped token. Compare that string against the key directly. The planner cannot tell them apart from the outside.
5. **Stop condition.** If any credential value appears in either file, do not file that file. Report where the value sits, by line, without quoting it, and stop.

## Part 2, one commit on d32-stage-1-records

6. File both reports byte-identical in docs/planning/evidence/, keeping their filenames, with index rows.
7. Add a short filing report in docs/audits/ recording: which three reports D36 cites, where each now lives, that D36's row on main is unedited, and that line 102 of the CDS report is the source for the "asked twice" count corrected on this branch.
8. Push. The owner merges the branch.

## Do not touch

- main. Do not merge anything.
- DECISIONS.md, any review of record, the four task and review branches, the archive.
- Every credential file, except reads for item 3.

## Report

- Read time at the top.
- The leak scan: what you compared against what, the positive control, and the result per file. Say plainly whether the UUID-shaped string in the CDS report is the key.
- The commit hash, files changed with lines added and deleted, zero deletions confirmed or each deletion accounted for.
- Anything in either report that changes a decision already ruled, or that contradicts something filed on any branch.
- Anything you noticed that this dispatch did not ask about.
