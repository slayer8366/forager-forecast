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
| 2026-09-18 | T0b completion report: the dedicated repo bootstrapped, with sha256, guard, CI and live-check evidence; findings for the owner: GDAL bindings under pip, no precipitation under models=era5_land, D14 to D18 missing from DECISIONS.md | `2026-09-18-t0b-completion-report.md` |
| 2026-09-18 | Standing review protocol, filed as received: a second agent checks every task from T0b onward for drift and gaps, with ten named checks, what the reviewer may change, and the output form (one `docs/audits/<date>-<task>-review.md` per review plus an index row). Filed by a separate session after T0b landed on main at 9a9a276, per the protocol's own header; content byte-identical to the owner's upload, checked with `cmp`. Two gaps in the record, reported not fixed: the protocol cites decision D18 and DECISIONS.md on main ends at D13, so D14 to D18 exist in the planning doc but not in the repo; and TASKS.md names `2026-09-18-t0b-completion-report.md` as the T0b report, which was not on main at 9a9a276. No session log row added to START_HERE.md, since this filing is not a task. | `../dispatch/2026-09-18-review-protocol.md` |
| 2026-09-18 | Export of decision rows D14 to D20 from the planning doc, filed as received (byte-identical to the owner's upload, checked with `cmp`) and applied in the same commit: D14 to D20 inserted under the DECISIONS.md table header unchanged, newest first, and the correction appended to the ERA5-Land row's flag cell in DATA_REGISTER.md, both per the export's own instructions. The export names main 4ed601d as its base; main was c66a865 when applied, and the two commits between touch only the review-protocol dispatch and this index, so DECISIONS.md (last changed 2fcb3c0) still ended at D13 and the register row was as the export assumed. D19 and D20 are proposals awaiting the owner; the export says T1 does not start until the ruling on them is recorded as a new row. Closes the "export D14 to D18" owner item in the T0b completion report. No session log row added to START_HERE.md, since this filing is not a task. | `2026-09-18-decisions-d14-d20-export.md` |
