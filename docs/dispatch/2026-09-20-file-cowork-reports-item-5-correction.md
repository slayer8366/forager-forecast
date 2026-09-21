# Dispatch: item 5 corrected, file both reports

Written 2026-09-20 about 18:25 PDT by the planning session.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

Corrects 2026-09-20-file-cowork-credential-reports.md, which stands otherwise. Work from both files.

## If the state has moved

Expects origin/main at cb0bca8 and d32-stage-1-records at bb15fbb, as relayed at 17:59 PDT. If either has moved sideways, stop and report. If either has moved forward, carry on and say so.

## The correction

1. Item 5's stop condition means any **secret** under D36: a password, an API token or key, or the contents of a credentials file. It does not mean any credential value. The planner wrote it loosely. Your reading is the intended one, and your reasoning for it is correct: a stop on any value would also bar the T1 run report already on main, which would leave D36's reasoning uncheckable.
2. The three hits are an account identifier, an account identifier and a public endpoint. D36 permits them, and both reports name their accounts. The stop condition is met. Proceed to Part 2 of that dispatch.

## Run

3. Part 2, items 6, 7 and 8 of that dispatch, unchanged.
4. In the filing report, record the scan as run: the method, the positive control at line 52 of the T1 run report at e9fbdf5, the three identifier hits by file and line, and that the UUID-shaped string at line 42 of the CDS report was compared against the key directly and is not it. Quote no value.
5. Also record in that report: D36's Reason cell is now corroborated against actual values rather than by eye, for all three reports it cites.
6. File this correction in docs/dispatch/ with its index row, beside the dispatch it corrects.

## Do not touch

- main. Do not merge anything.
- DECISIONS.md, any review of record, the four task and review branches, the archive.
- Every credential file. The scan is done.

## Report

- Read time at the top.
- The commit hash, files changed with lines added and deleted, zero deletions confirmed or each deletion accounted for.
- Anything you noticed that this dispatch did not ask about.
