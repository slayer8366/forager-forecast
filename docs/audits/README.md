# Audits

Dated, point-in-time records: completion reports, pulse answers, rulings and the dispatches they
answer, each as it stood on its date. None is a maintained document. Findings are not updated as
they are fixed. A later entry supersedes an earlier one rather than editing it, and a row is
appended here, never rewritten. Every file states the base commit it was written against, and
every claim in it names a file and line or is marked inferred. This form is copied from the
Forager repo's docs/audits/README.md at 175b050.

Records are committed here so they survive the session that produced them.

Two files are edited by every session and will conflict when two run at once: this index, and
the session log in docs/planning/START_HERE.md. Append a row. Never rewrite the table.

| Date | Scope | File |
|---|---|---|
| 2026-09-18 | T0 completion report: the planning pack landed on the zynergy-site branch and was checked on a Pages preview; what T0 left undone and why | `2026-09-18-t0-planning-pack-landing-report.md` |
| 2026-09-18 | Pulse answer: what the Forager repo is and whether it could host the forecast model work, eight questions answered with file-and-line evidence against Forager main 175b050 | `2026-09-18-forager-repo-pulse.md` |
| 2026-09-18 | Dispatch T0b: bootstrap the dedicated forecast repo, as received | `../dispatch/2026-09-18-t0b-forecast-repo-bootstrap.md` |
