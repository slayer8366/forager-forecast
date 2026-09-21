# Dispatches

A dispatch is a task handed to an executing session: what to verify first, what to build or check,
what not to touch, and what evidence to return. This directory holds each one **as it was received**,
so a later reader can see the instruction that produced a commit rather than a summary of it.

Dispatches are not maintained documents. A dispatch describes what was asked on its date, against the
state named in it, and that state decays. Where a dispatch turns out to be wrong, the correction is a
new file, never an edit.

## Rules

- **Filed as received, byte-identical.** A dispatch is committed exactly as it arrived, verified with
  `cmp` against the source, and the report that files it records the byte count. Nothing is reflowed,
  retitled or tidied.
- **Naming: `YYYY-MM-DD-<slug>.md`**, dated the day the dispatch was written, not the day it was filed.
  Where those differ, the filing report says so. A dispatch is filed under the name its writer gave
  it. The eight-character hex prefix the relay adds is dropped without a note. A suffix such as `-1`
  or `-2` is dropped and noted in the index row, since it can signal a duplicate upload.
- **Corrections and amendments are separate files**, filed beside the dispatch they change, named for
  it. `2026-09-20-file-cowork-reports-item-5-correction.md` corrects
  `2026-09-20-file-cowork-credential-reports.md`; `2026-09-20-d32-merge-pass-stage-1-amendment-rev2.md`
  amends `2026-09-19-d32-merge-pass-stage-1.md`. File the corrected dispatch too, even if it was never
  filed at the time: an index row pointing at a correction to a document that is not in the repository
  is a dangling reference.
- **A closeout note goes inside a dispatch only when it was closed without being acted on.** Then a
  dated note is appended to the file saying why, so a reader does not take an unexecuted instruction
  for an executed one. `2026-09-20-stage-1-step-1-unblock.md` is the example. **A dispatch that was
  acted on stays byte-identical**, and the commentary lives in its index row or in the report that
  answers it. This split is ruled in D41.
- **Every dispatch gets one row in `../audits/README.md`**, not an index here. That file is already the
  single index for dated records, and a second index would duplicate rows and drift out of step with
  the first. The cost is that the one index conflicts whenever two branches append to it, which is
  accepted and handled by keeping every row at every merge.

## What does not belong here

Planner-to-planner state summaries, which go in `../planning/handoffs/` and follow different rules.
Reports answering a dispatch, which go in `../audits/`. Decisions, which go in
`../planning/DECISIONS.md` and are the owner's to rule.
