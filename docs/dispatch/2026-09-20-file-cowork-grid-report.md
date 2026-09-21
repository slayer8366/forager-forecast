# Dispatch: file Cowork's attribution, licence and grid report

Written by the planning session after the Cowork report read 22:27 to 22:33 PDT on 2026-09-20.
Project: forager-forecast. Repo: slayer8366/forager-forecast.
Attached: the Cowork report, as a file named 2026-09-20-cowork-attribution-licence-grid-report.md.

Run this after stage 2b's step 2 stop, not between its steps.

## If the state has moved

Expects main to contain f06115e. If it has moved forward, carry on and say so. Do not touch the task branches.

## One commit, on a new branch docs-cowork-grid-report off main

1. Leak scan the attached report against all five credential values, with a positive control, as before. It should contain none: it names DOIs, URLs and author lists only. If it contains a secret, stop and report the line.
2. File it byte-identical in docs/planning/evidence/, with an index row.
3. Append a dated note under item 4 of docs/planning/RELEASE_CHECKLIST.md: the licence version is observed as CC BY 4.0 on all four datasets, source the filed report, Part 2; the attribution wording is obtained, source the filed report, Part 1, and awaits the owner's ruling on four page defects the report names. Do not tick the item.
4. Append a dated note to the same checklist under item 2: the only CDS pull to date was the deleted proof retrieval of 2026-09-19, so no CDS output predates the store's 25 February 2026 change to area extraction described in the filed report. Cite the report and docs/planning/evidence/cds-credentials-report.md.
5. File this dispatch with its index row. Push. Under D40 the merge waits for the owner's written authorisation naming docs-cowork-grid-report.

## Do not touch

- main, the task and review branches, DECISIONS.md, any existing checklist item text, the archive, every credential file.

## Report

- Read time at the top.
- The scan result, the commit hash, files changed with lines added and deleted, zero deletions confirmed.
- Anything you noticed that this dispatch did not ask about.
