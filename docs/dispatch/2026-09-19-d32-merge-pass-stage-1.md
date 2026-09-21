# Dispatch: D32 merge pass, stage 1

Date: 2026-09-19. From: planning session. Repo: slayer8366/forager-forecast, and only that one.
Nothing in this file concerns the Forager app repo.

## Why stage 1 only

D32's merge pass has five moving parts: the self-check renames, the application of D36, corrections to
findings the independent reviews raised, a review of commits made after those reviews were cut, the code
move into T2's package, the one-line folds from D25 to D31, and the two merges. The later parts depend on
the outcome of the earlier ones. Writing them now would mean specifying work against results nobody has.

So stage 1 does the work that is decided, and ends with an inventory a reviewer can act on. Stage 2 gets
written when stage 1's review reports.

## Preconditions, checked before anything else

1. D36 is ruled. 2. D38 is ruled. If either is still proposed, stop and report. Do not proceed on a
guess about which way it went, and do not treat this dispatch's existence as a ruling.

Quote each ruling's row from docs/planning/DECISIONS.md with its line number before acting on it.

## State this was written against

Relayed, not read by planning. Confirm each before acting.

- main 3625a55. DECISIONS.md runs D1 to D37 with no gaps. D38 is in no repo file.
- Unmerged: t1-calendar-smoke-test 9f6c132, t1-credentialed-run-review e9fbdf5, t2-record-audit 4b22c8d,
  t2-credentialed-run-review 9491ace.
- Independent reviews of record under D35 sit on the two review branches. The self-checks sit at the same
  paths on the task branches.
- The GBIF_USER value sits at line 52 of docs/audits/2026-09-18-t1-credentialed-run-report.md and at line
  157 of docs/audits/2026-09-18-t1-credentialed-run-review.md. It is on no commit reachable from main.
- Three findings are held only by the independent reviews: that credential value; a credentialed-run
  dispatch filed on the task branches but never on main, though the run report says it was compared
  against main; and a by-licence roll-up row at line 318 of the T2 run report that over-counts by 153
  records.
- Commits made after the independent reviews were cut, and so unreviewed: on T1 a syntax fix to the count
  script and a docstring refresh, on T2 a tally script.

## Part A. The self-check renames

Only if D38 was ruled in favour and the owner assigned this dispatch to you. Record the assignment and the
ruling's line number in your report.

On t1-calendar-smoke-test, git mv docs/audits/2026-09-18-t1-credentialed-run-review.md to
docs/audits/2026-09-18-t1-credentialed-run-self-check.md. On t2-record-audit, the same for the T2 file.

- One commit per branch, the move alone.
- Append one dated line to each moved file, and change nothing else in it: "Renamed 2026-09-19 under D35.
  This document is a builder self-check, not a review under D18. The review of record is at
  docs/audits/2026-09-18-tN-credentialed-run-review.md." Put the real N in.
- Update that branch's audit index row to the new path and mark it a self-check.
- Report `git log --follow` on each moved file, showing the history survived.

The independent reviews are not touched.

## Part B. Apply D36 to the two occurrences

Do exactly what the ruled row says, and nothing more. The two occurrences are named above.

- If D36 permits an identifier in a report that says which account it names, then check that each of the
  two lines does say which account it names. If a line does not, append a dated line to that file saying
  which account it is, and change the existing line in no way. Report both lines as compliant or as made
  compliant.
- If D36 does not permit it, do what the row prescribes. Report what you did, and never quote the value,
  in whole or in part, in any file, commit message or report.

This part happens before any merge, because after the merge the same change would mean rewriting main.

## Part C. Corrections to the findings, appended never edited

On t2-record-audit, append a dated correction beneath the by-licence roll-up at line 318 of the T2 run
report, stating that the row over-counts by 153 records, giving the corrected figure, and naming the
independent review as the source. Do not edit the original row. If the corrected figure is not derivable
from what is already in the file, say so and stop rather than recomputing from the archive.

On both task branches, append a dated line to the credentialed-run dispatch recording that it was filed on
the task branches only and was never on main, and that the run report's claim of comparison against main
is therefore unverified from main alone.

One commit per branch for part C.

## Part D. Inventory for the reviewer, no changes

List, with commit hash, file and line count for each:

1. Every commit on T1 and T2 made after the independent reviews were cut, with a one-line description.
2. Every file T1 would move into T2's package under D32, with its current path and its tests.
3. Every file that both branches change, which is where the merges will conflict.
4. Whether the one-line changes from D25 to D31 are already present on each branch or still to fold in,
   one row per decision.

This is the input to stage 2. Do not act on any of it.

## Do not touch

- Any merged file, any decision row, any review of record, any finding's original wording.
- main. No merge, no fast-forward, no push to main.
- The code move, the one-line folds, and the two branch merges. All stage 2.
- The frozen T0b verify script (D30).
- The archive, any credential, any download. No network beyond git.

## Alternatives already rejected

- One dispatch for the whole merge pass. Its later steps depend on results that do not exist yet.
- Merge first and correct after. Part B's window closes at the merge.
- Fix the T2 roll-up by recomputing from the archive. That is a rerun, and it belongs with the session
  that owns the branches under D35, in stage 2, with its own review.
- Have the builder review its own post-review commits. D18 asks for a separate session.

If you think any of this reasoning is wrong, say why in the report and do not implement the alternative.

## Evidence to return

- The two ruling quotations with line numbers, before anything else.
- Per part: the branch, the commits, and a diff summary showing added lines and zero deleted lines,
  except part A's renames, which show as renames.
- For every count you report, one clause saying what one unit of it is a unit of.
- Conventions: which earlier dispatch and index rows you checked, what form you found, whether you
  followed it. "None checked" is allowed. A blank is not.
- What you did not check, stated plainly.

## Person-only items

- The rulings on D36 and D38.
- Assignment of this dispatch, under D38 if it was ruled in favour.
- A reviewer in a separate session takes each part under D18. Then the owner merges nothing yet: these
  branches stay unmerged until stage 2.
