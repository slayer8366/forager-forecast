# Dispatch: run stage 1 step 1 ahead of the merge

Written 2026-09-20 about 11:30 PDT by the planning session.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

Authorises your 11:12 PDT proposal, with one change. Everything else in 2026-09-20-d32-merge-pass-stage-1-amendment-rev2.md stands.

## Why precondition 1 is waived, and only here

Step 1 files documents. It cites no line number in DECISIONS.md, and D38 governs the four task and review branches, which step 1 does not touch. So nothing in step 1 depends on a ruling that has not landed. Steps 2 and 3 stay gated: Part A needs D38's line number as it stands on main.

## The change: cut the branch off a8794f5

Cut d32-stage-1-records off decisions-d38-d39 at a8794f5, not off main at 3625a55. Both branches append rows to docs/audits/README.md, which you named as the file that serialises parallel work here. Off main, the two merges collide there. Off a8794f5, the history stays linear and one merge brings in both. Say so in your report, so the owner knows the records branch carries the decision rows too.

## Verify first, read-only

1. origin/main is still 3625a55 and decisions-d38-d39 is still at a8794f5. If either has moved, stop and report, because the branching choice above depends on both.

## Run

2. Step 1 of rev 2, items 3, 4 and 5, unchanged except for the branch point above.
3. In the Part D report, record D38 and D39 as filed on decisions-d38-d39 at a8794f5 and not yet on main, and record that precondition 1 was waived by the owner for step 1 only.
4. Do not merge anything. Do not run Part A or Part C.

## Report

- Read time at the top.
- The commit hashes, the branch point, files changed with lines added and deleted, and zero deletions confirmed or each deletion accounted for.
- Anything you noticed that this dispatch did not ask about.

**Closed without action, 2026-09-20.** This dispatch was authorised at about 11:30 PDT and crossed
with the merge of decisions-d38-d39 into main at about 14:30, which made it unnecessary rather than
unsafe. Its verify-first block stopped the run at 17:00 PDT because origin/main had moved from 3625a55
to cb0bca8. Step 1's work was already done, at 84edf09. Its branching change, to cut
d32-stage-1-records off decisions-d38-d39 at a8794f5, was sound when written and is now moot: a8794f5
is an ancestor of main cb0bca8, the records branch was cut at cb0bca8 and already contains it, and the
branch merges into main with no conflict at all. Cutting off a8794f5 now would put the records branch
behind main and reintroduce the index collision the change existed to avoid. Nothing in this file is
edited.
