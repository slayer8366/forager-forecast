# Dispatch: Copernicus secret check, then pre-merge corrections on decisions-d38-d39

Written 2026-09-19 about 23:45 PDT by the planning session.
Project: forager-forecast. Repo: slayer8366/forager-forecast.
Attached with this file: 2026-09-19-planner-handoff.md.

## State this was written against

Relayed by you at 23:34 PDT, not read by the planner.

- origin/main at 3625a55. Branch decisions-d38-d39 at f14a0c1, unmerged.
- D39's Alternatives considered cell says "no secret is committed anywhere". The check behind it covered GBIF_USER, GBIF_PWD and GBIF_EMAIL on remote refs only.
- The Copernicus credentials were never checked. You located them at ~/Labs/cds-credentials.sh and ~/Labs/cds-credentials-report.md.
- The filing report's count correction cites a planning handoff that is not in the repository.

## Owner's decision carried by this dispatch

The D39 cell is corrected in place on decisions-d38-d39, not by a new D40 row. The row has never been on main, so this is review before merge, not a rewrite of the record. The branch history keeps both versions, and the filing report records the change.

## Verify first, read-only

1. origin/main is still 3625a55 and decisions-d38-d39 is still at f14a0c1. If either has moved, stop and report.

## Part 1, read-only: the Copernicus check

2. You may read ~/Labs/cds-credentials.sh, and ~/.cdsapirc if it exists, for this check only. Name every file you read. Hold values in memory only. Never write a value into any output, file or commit.
3. Compare each Copernicus credential value against every tracked file in every commit reachable from any remote ref. Report per variable: its name, whether it is a secret or an account identifier under D36, and every (branch, file, line) where it appears, or "none". Say what you searched and how.
4. **Stop condition.** If any Copernicus secret appears in any commit reachable from a remote ref, stop here. Make no writes and report the locations. That finding reopens the timing of D36's account swap, which is the owner's ruling to make.

## Part 2, one commit on decisions-d38-d39, only if Part 1 finds no secret

5. In D39's Alternatives considered cell, replace "no secret is committed anywhere" with: "no GBIF or Copernicus secret is committed on any remote ref, per checks read at 2026-09-19 22:37 PDT and at <your Part 1 read time>". Change nothing else in DECISIONS.md.
6. Append a dated note to the filing report saying that the D39 cell was corrected before merge, quoting the old and new wording, and why.
7. Scan the attached handoff for every GBIF and Copernicus credential value. If none appears, file it byte-identical at docs/planning/handoffs/2026-09-19-planner-handoff.md, unless the repository already has a home for planning handoffs, in which case use that and say so. If a value does appear, do not file it; report it.
8. Append to the count correction in the filing report the path where the handoff is now filed, so the "asked twice" figure can be checked.
9. Shorten the index rows you wrote on this branch to about the length of the older rows. The reports carry the detail.
10. File this dispatch as received in docs/dispatch/ with its index row, following c55c419.
11. One commit, pushed.

## Do not touch

- main. Do not merge.
- DECISIONS.md, except the one D39 cell in item 5.
- The four task and review branches, any review of record, and the archive.
- Any credential file except those named in item 2, and only for reading.

## Report

- Read time at the top.
- Part 1 results per variable, as item 3 asks.
- If Part 2 ran: the commit hash, the files changed with lines added and deleted, and the exact before-and-after of every changed line. Expect one changed line in DECISIONS.md and the shortened index rows. Anything else changed is a defect.
- Anything you noticed that this dispatch did not ask about.
