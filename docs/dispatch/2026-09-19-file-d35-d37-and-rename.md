# Dispatch: file D35 to D37, then rename the self-checks on the T1 and T2 branches

Date: 2026-09-19. From: planning session.
Supersedes 2026-09-18-proposed-rulings-d35-d36.md, which was never filed. Its D35 is rewritten here to
match the owner's ruling. Its D36 is rewritten because it was unworkable as written, see below.

Hand this to the session that holds the GBIF credentials and the two task branches. It owns those
branches under D35, and part 2 rewrites files on them.

Read all of it before starting. Part 1 lands on main. Part 2 only starts once part 1 is merged, because
the rename in part 2 is an application of D35.

## State this was written against

Relayed, not read by planning: main 79b149c after the spec sync merged, audit index at 18 rows.
DECISIONS.md is docs/planning/DECISIONS.md and ends at D34. D35 and D36 exist on no branch. From the
pulse of 19 Sep, still true as far as planning knows:

- Independent reviews: docs/audits/2026-09-18-t1-credentialed-run-review.md on branch
  t1-credentialed-run-review at e9fbdf5, and docs/audits/2026-09-18-t2-credentialed-run-review.md on
  branch t2-credentialed-run-review at 9491ace.
- Self-reviews at those same two paths on the task branches: t1-calendar-smoke-test at 2c540e2 and
  t2-record-audit at f8adaa4.

Every hash and path above is from a relay. Confirm each before acting.

## Part 1, verify first

1. origin/main after a fetch, and every commit since 79b149c.
2. DECISIONS.md's header row, word for word, and its column count. The rows below are written for six
   columns: ID, Date, Decision, Reason, Alternatives considered, Supersedes. If the file has a
   different shape, stop and report. Do not reshape the rows to fit.
3. The highest existing D number. If it is not D34, stop and report.
4. The four paths and branch heads listed above.

## Part 1, do

On a branch named decisions-d35-d37, append these three rows to DECISIONS.md in the file's existing
order, word for word. Change no existing row.

| D37 | 2026-09-19 | Owner's ruling: D35 is accepted as asserted. D36 is not ruled on and stays proposed. | Owner's words: "Yes, that's correct as asserted." The assertion ruled on is the four clauses in D35: the credentialed session owns the branches, its self-reviews are builder self-checks and not D18 reviews, both documents survive under different names, and the independent reviewer gets read-only archive access. | None raised by the owner. D35 lists the alternatives that were considered. | Accepts D35. |

| D36 | 2026-09-19 | Proposed. Reports, commits, logs and chat never carry a secret: a password, an API token or key, or the contents of a credentials file. Account identifiers, meaning a username or an email address, may appear where they are needed to say which account did something, and the report says which account it names. A secret already committed is not edited out. A dated note is appended saying where it is, and the release checklist carries the account swap and a history check. | The version 1 wording, "reports never carry credential values", would be broken on day one by three existing reports: the T1 run report quotes a credential variable's value, Cowork's GBIF report names the username, and Cowork's Copernicus report names the account email. A rule that every existing report breaks gets ignored. Separating secrets from identifiers gives a rule that can hold. | Ban identifiers too (three reports would need rewriting, against the append-and-preserve rule). Leave the rule unwritten (the T1 finding stands unanswered). | Replaces the version 1 wording, which was never filed: "reports never carry credential values". |

| D35 | 2026-09-19 | Owner's ruling, asserted by Claude and accepted in D37. Roles split by capability. The session holding the GBIF credentials owns the T1 and T2 branches through the D32 merge pass, because it holds the archive and can re-run the count scripts. Its reviews of its own runs are builder self-checks, not reviews under D18, and they keep their findings. The independent reviews on the side branches are the reviews of record. Both documents survive and neither is overwritten: before any merge, each self-check moves to its own filename in its own commit. The independent reviewer is given read-only access to the download archive, so a later review can re-run what it could only read about. | Two sessions both executed D32's review step and filed at the same path, so a merge would have overwritten one with the other. The independent T1 review found two things the self-review did not. The self-review re-ran the count script, which the independent reviewer could not reach. Each session saw something the other could not, so both documents are evidence. | One session does everything (loses the independence D18 asks for). Keep only the independent reviews (discards a re-run nobody else can reproduce). Let the merge resolve the path conflict (overwrites a review). | None. Answers the collision the T0b review surfaced. |

Then file this dispatch in the usual form with its index row, write a short report with its index row,
and stop. Do not merge. A reviewer takes the branch under D18.

## Part 2, only after part 1 is merged

On t1-calendar-smoke-test, move docs/audits/2026-09-18-t1-credentialed-run-review.md to
docs/audits/2026-09-18-t1-credentialed-run-self-check.md. On t2-record-audit, move
docs/audits/2026-09-18-t2-credentialed-run-review.md to
docs/audits/2026-09-18-t2-credentialed-run-self-check.md.

- Use git mv so the history follows the file. One commit per branch, the move alone, nothing else in it.
- The text of each file does not change, apart from one appended dated line: "Renamed 2026-09-19 under
  D35. This document is a builder self-check, not a review under D18. The review of record is at
  docs/audits/2026-09-18-tN-credentialed-run-review.md." Put the real N in.
- Update that branch's audit index row to the new path and say it is a self-check.
- Report the two commits and stop. The independent reviews stay where they are and are not touched.

## Do not touch

- Any existing decision row, any merged review, any report's findings.
- SPEC.md, DATA_REGISTER.md, TASKS.md, and every file the spec sync just merged.
- The frozen T0b verify script (D30).
- Any code, test or data file. Part 2 is a rename and one appended line, nothing else.
- The independent review branches t1-credentialed-run-review and t2-credentialed-run-review.
- No downloads and no network beyond git. No secret in any file, commit message or report.

## Alternatives already rejected

- Rename first and file the rows after. The rename is an application of D35, so the rule lands first.
- Fold the two Cowork reports into the repo now. They name account identifiers, and D36 is the rule
  that decides how those are filed. Filing them first and redacting later would mean editing a
  committed record. This waits for D36.
- Number these rows D35 and D36 as the unfiled version 1 did, and add no ruling row. The precedent is
  D34: the owner's words get their own row.

If you think any of this reasoning is wrong, say why in the report and do not implement the alternative.

## Evidence to return

- The verify-first answers, each with commit hash, file and line, marked read, observed or inferred.
- The DECISIONS.md diff, showing three added rows and zero deleted lines.
- For part 2, `git log --follow` on each renamed file, showing the history survived the move.
- Conventions: which earlier filing dispatch and index rows you checked, what form you found, and
  whether you followed it. "None checked" is allowed. A blank is not.
- What you did not check, stated plainly.

## Person-only items

- The owner hands each part to a reviewer under D18, then merges.
- Read-only archive access for the independent reviewer, under D35. This dispatch does not set it up.

## Still open, carried over from the unfiled version 1 and not ruled on

Two process clauses from that file were not part of what the owner ruled on and are deliberately left
out of D35: that hand-offs are filed on main before the work starts, and that every commit on main
carries an index row. Both are worth a decision later. Neither blocks the merge pass.
