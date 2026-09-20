# D38 and D39 filed: ownership by machine, and the ruling on D36

**Date:** 2026-09-19.
**Type:** filing report. The rulings were given in chat by the owner; no dispatch file exists for them, and none is filed here (see "Decisions taken here").
**Base:** main 3625a55, on branch decisions-d38-d39. One commit: the two rows, this report, and one index row.
**Supersedes:** none.

Every claim names a commit, a file and line, or a command whose output is quoted, or is marked inferred.
Observed means this session ran the command; read means a file was opened. Read time for every state
claim below: 2026-09-19 22:37 PDT (2026-09-20 05:37 UTC), with the numbering and date re-checked at
22:48 PDT and the branch cut at 23:02 PDT.

## Verify first, as answered

1. **Main.** Observed. `git fetch --all --prune` at 05:37 UTC and again at 05:48 UTC; origin/main is
   3625a5549a5d345de87e42886d29e17e703531c9 both times, unmoved.
2. **Highest D.** Observed. D37 at line 8 of docs/planning/DECISIONS.md. `git grep -nE 'D38|D39'
   origin/main` printed nothing, so both numbers were free.
3. **The full D36 row.** Read, docs/planning/DECISIONS.md line 9, all six columns, untruncated. This
   check changed the ruling: see "The correction this filing carries".
4. **Header and shape.** Read, line 6: `| ID | Date | Decision | Reason | Alternatives considered |
   Supersedes |`. Six columns, eight pipe-separated fields per row.
   `awk -F'|' '/^\| D/ && NF!=8'` printed no rows before the edit and none after it.
5. **Date convention.** Observed. Rows are dated local Pacific, not UTC: f047309 and 233acb3 were
   committed 2026-09-19 05:25 PDT and carry row-date 2026-09-19 while UTC had not yet rolled over. The
   branch was cut at 2026-09-19 23:02 PDT, so both rows are dated 2026-09-19.
6. **D38's ownership test, against this machine.** Observed. The credentials file is at
   ~/.config/forager-forecast/gbif.env (mode 600). The archive is 158M under
   ~/Zynergy/forager-forecast-t1-calendar-smoke-test/data and 1.4G under
   ~/Zynergy/forager-forecast-t2-record-audit/data. Both are on one machine, so D38's concurrency
   clause covers a real situation.

## The correction this filing carries

A draft of D39 read "A committed secret is rotated at once and recorded in a new report or an appended
correction." It was written from a summary of D36 rather than from D36 itself, and the summary was
wrong. D36's own closing clause, read at line 9, is:

> A secret already committed is not edited out. A dated note is appended saying where it is, and the
> release checklist carries the account swap and a history check.

So D36 carries a dated note, a release-checklist account swap and a history check. It does not require
rotation at once, and the draft would have filed a swap timing D36 never proposed while dropping the
history check. The owner's ruling is that D36 is accepted exactly as written, and D39 therefore cites
D36 instead of restating it.

**Where this correction belongs, and why it is here.** The owner asked for it to be appended under the
handoff's D36 summary. That handoff is not in this repository and not on this machine: `git ls-tree -r
origin/main` matches no handoff file, `git grep -niE 'rotat' origin/main -- docs/` returns nothing, and
a filesystem search matched only a Forager-repo PR103 handoff, which is a different project. This
report is the nearest reachable home for the correction. Recorded here so it is not lost; the summary
itself is still uncorrected wherever it lives, and that is an owner item below.

## What landed

| File | Change |
|---|---|
| `docs/planning/DECISIONS.md` | D39 and D38 inserted directly under the table header, in the file's newest-first order |
| `docs/audits/2026-09-19-decisions-d38-d39-report.md` | this report |
| `docs/audits/README.md` | one appended index row |

## Decisions taken here, and what was rejected

- **The three empty columns were filled from the owner's own sentences.** Both rows arrived carrying
  ID, Date and Decision only, which is four pipe-separated fields where the table requires eight. The
  Decision column of each row is the owner's wording verbatim. Reason, Alternatives considered and
  Supersedes were written from the owner's stated reasoning in the same message: for D38, the
  restarted-session gap, the two-sessions-on-one-machine gap the concurrency clause closes, and the
  closing sentence's purpose; for D39, the line 182 argument, the D35 conflict the adjacency reading
  would create, and the three stated reasons for not amending the swap timing (nothing to apply it to,
  it matches the plan, revisit when the business account exists). Rejected: filing four-field rows,
  which breaks an invariant every one of the 37 existing rows holds; and leaving the columns empty with
  a placeholder, which would lose reasoning the owner had already given. The owner should read these
  three columns as transcription and correct any of them with an appended row if it is wrong.
- **One commit, not three.** The D35 to D37 precedent (c55c419, f047309, 233acb3) used three. The owner
  asked for one commit with its index row, so the precedent was not followed.
- **No dispatch filed as received.** The rulings came as chat text, not as an uploaded dispatch, so
  there is nothing to `cmp` against. The three index rows at lines 19, 21 and 23 that record a filed
  dispatch were read; that form does not apply here.
- **Rows inserted under the header**, following the file's newest-first order stated at line 3.
- **No session log row** in START_HERE.md, following the filing precedent that a filing is not a task.

## Owner items

- The handoff's D36 summary is still wrong wherever it lives. This report cannot reach it.
- Whether the Copernicus account is a test account. Asked three times, still unanswered.
- Stage 1 of the D32 merge pass is now unblocked and needs rewriting: with D38 and D39 filed, Part A
  runs, Part B drops out, and Part C runs. Not started here.
- The line-58 cite error inside the T1 review of record
  (docs/audits/2026-09-18-t1-credentialed-run-review.md, which says "Report line 52 reads" then "never
  edit line 58", where the value has been at line 52 in all eight commits holding it). The review of
  record stays untouched, so this is a planning-document note only.

## Not checked

- CI on this branch (documents only).
- Anything on the T1 and T2 branches. Nothing outside this branch was touched or read for this filing
  beyond the state checks recorded above.
- Whether the two `gbif_download.py` copies have diverged, which stage 2 needs in order to choose which
  survives.

Conventions: docs/audits/2026-09-19-decisions-d35-d37-report.md was read in full and its report shape
followed; the commit shapes of c55c419, f047309 and 233acb3 were read and deliberately collapsed to one
commit on the owner's instruction; the index-row form was taken from the last two rows of
docs/audits/README.md. Em dashes were avoided, as in every earlier filing.
