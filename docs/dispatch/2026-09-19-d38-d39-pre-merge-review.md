# Dispatch: pre-merge review of D38 and D39, and one count correction

Written 2026-09-19 about 23:30 PDT by the planning session.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

## State this was written against

Relayed by you, not read by the planner.

- origin/main at 3625a55.
- Branch decisions-d38-d39 at dcc3a76, off 3625a55, pushed 23:04 PDT. It files D38 and D39, one index row, and a filing report. Not merged.
- The Reason, Alternatives considered and Supersedes cells of both rows were transcribed by you from planner chat. They have not been reviewed by the owner.

Established: D38 and D39 wording in the Decision column, as filed.
Open: the three transcribed columns, and the merge.

## Verify first, read-only

1. origin/main is still 3625a55 and decisions-d38-d39 is still at dcc3a76. If either has moved, stop and report.

## Part 1, read-only: the transcribed cells

2. Quote the Reason, Alternatives considered and Supersedes cells of D38 and of D39 exactly, one cell per sentence. Six cells.
3. If either Supersedes cell names anything, say so. The intended value for both is none. D39 accepts D36 and does not replace it. D38 files a rule that was never in the repo.
4. If any cell says or implies that no secret is committed anywhere, flag it. The check read at 22:37 PDT covered the GBIF variables on remote refs only. The Copernicus credentials were not checked.

Do not change any cell. Corrections to D38 or D39, if any, come as a separate instruction after the owner has read your quotes.

## Part 2, one write: the count correction

5. The filing report on dcc3a76 says the Copernicus test-account question was asked three times. That count came from planner chat and is wrong. Append a dated correction directly under that line saying: the only count on record is the prior planning handoff's "asked twice and never answered"; the planning session listed the question as an owner item but never put it to the owner, so it added no ask; the question is still open. Do not edit the original line.
6. File this dispatch as received in docs/dispatch/ with its index row, following c55c419, in the same commit as the correction.
7. One commit, on decisions-d38-d39, pushed.

## Do not touch

- main. Do not merge decisions-d38-d39. Merging is the owner's.
- DECISIONS.md, on any branch.
- The four task and review branches, and any review of record.
- The archive and any credential file.

## Report

- Read time at the top.
- The six quoted cells, with the flags from items 3 and 4.
- The new commit hash, files changed with lines added and deleted, and confirmation that zero lines were deleted.
- Anything you noticed that this dispatch did not ask about.
