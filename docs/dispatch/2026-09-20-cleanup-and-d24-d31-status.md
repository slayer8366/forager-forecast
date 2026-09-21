# Dispatch: file the stopped revisions, widen the relay-name rule, and report D24 to D31 status

Written 2026-09-20 about 21:00 PDT by the planning session.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

## If the state has moved

Expects origin/main 1d27f08 and docs-homes-handoffs-dispatches b888c4a. If either has moved sideways, stop and report. If either has moved forward, carry on and say so.

## Part 1, one commit on docs-homes-handoffs-dispatches

1. **Stopped revisions.** File, each in docs/dispatch/ with its index row and a dated closeout note appended inside it as D41 provides: revision 1 and revision 2 of the D40 to D43 filing dispatch, and revision 1 of the stage 1 amendment. Each note says when it was stopped, at which item, why, and which revision superseded it. File only versions you actually received. If you did not receive one, say so and do not reconstruct it.
2. **Relay names.** In both docs/dispatch/README.md and docs/planning/handoffs/README.md, the naming rule reads, in substance: a file is filed under the name its writer gave it; the relay's eight-character hex prefix is dropped without a note; a suffix such as "-1" or "-2" is dropped and noted in the index row, since it can signal a duplicate upload. Replace the suffix sentence added in b888c4a with this, and add it to the handoffs README. Word it to match the READMEs' style.
3. In the filing report, record that the planner handoff arrived as "-planner-handoff-2.md" and was filed at 4114474 without the suffix, unnoted at the time. Do not edit its existing index row.
4. File this dispatch with its index row. Push. Under D40 the merge waits for the owner's written authorisation naming the branch.

## Part 2, read-only: where D24 to D31 stand

D32, accepted by D34, says T1 and T2 merge "with the one-line changes from D25 to D31 folded in first". Part D, read at 22:37 on 2026-09-19, showed several are not one line. The owner will rule on this before stage 2b, and needs today's state.

5. For each of D24's open verify-first items, D25, D26, D27, D28, D29, D30 and D31, give its status on each task branch and on main as one of: done, with the file and line that does it; partly done, saying what is missing; not started; or not applicable to that branch. Mark whether you read the implementing code or only probed for a token, as Part D did.
6. For each item not done, say whether it is genuinely a one-line change, and if not, give its size as files touched and a rough line count, marked as an estimate.
7. Say which items depend on another item first. For example, whether D26's redo needs the unified gbif_download that D42 creates.
8. The Open-Meteo equivalence test: does any code or test for it exist on any branch?

## Do not touch

- main. Do not merge anything.
- DECISIONS.md, RELEASE_CHECKLIST.md, any review of record, the four task and review branches, the archive, every credential file.
- Any source or test file. Part 2 is read-only.

## Report

- Read time at the top.
- The commit hash, files changed with lines added and deleted, each deletion accounted for.
- Items 5 to 8, one line per item per branch where you can.
- Anything you noticed that this dispatch did not ask about.
