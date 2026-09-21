# Planning handoffs

A handoff is written by one planning session for the next: where the work stands, what is waiting on
the owner, what is in flight, and what cost time and should not cost it again. It is a planner-to-
planner document, not a record of a task.

These live under `docs/planning/` rather than in `docs/audits/` for two reasons. A handoff summarises
the state of the plan, so it belongs beside the plan it summarises. And an audit entry is corrected by
a **later entry that supersedes it**, while a handoff is corrected **inside itself**, by an appended
section, because its value is that one document carries the current reading. `2026-09-19-planner-handoff.md`
already carries two such sections, both appended by later sessions, neither editing a word above it.

## Rules

- **Filed as received.** The file is byte-identical to what was received at the moment it is filed, verified with `cmp`, and afterwards changes only by appended corrections.
- **Naming: `YYYY-MM-DD-planner-handoff.md`**, dated when it was written.
- **Corrections are appended to the file, never edited in.** Each correction section is dated, says who
  appended it, and says how its facts were known. Nothing above it changes.
- **Every claim about the repository is a claim about the past.** A handoff is written by a session
  that usually cannot read the tree, from facts relayed to it, and those facts decay, sometimes inside
  the same pull request. Treat every hash, path and count in a handoff as a premise to re-check, not as
  knowledge. Where a handoff and the repository disagree, the repository wins and the handoff gets an
  appended correction.
- **One row in `../../audits/README.md`**, for the same reason dispatches take their row there: one
  index, not several.

## What does not belong here

Dispatches, which go in `../../dispatch/`. Reports and rulings, which go in `../../audits/`. Anything
that is a decision rather than a summary of one, which goes in `../DECISIONS.md`.
