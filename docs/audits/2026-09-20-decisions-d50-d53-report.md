# D50 to D53 filed, with Cowork's attribution, licence and grid report and the ERA5 research note

**Date:** 2026-09-20.
**Type:** filing report for two dispatches run in one commit, as revision 2 asks:
docs/dispatch/2026-09-20-file-d50-to-d53-rev2.md and docs/dispatch/2026-09-20-file-cowork-grid-report.md.
**Base:** main 47204f7. Both dispatches' state clauses pass, since main moved forward. Revision 2 expects
49a5ed5 or a descendant, with D49 the highest row, which holds. The Cowork dispatch expects main to
contain f06115e, which it does. Main moved through bc7863a (T2), 42f0743 (T1) and 47204f7 (the T1 move
review).
**Read time:** 2026-09-20 23:27 PDT.
**Supersedes:** nothing.

## Verify first

- **Revision 2, item 1:** Cowork's report arrived as the named file, with its filing dispatch.
  Satisfied.
- **Revision 2, item 2, D46 (line 11 on main):** "...the grid's point positions are confirmed from the
  weather source's documentation, and the cell code is checked against them." D51 corrects this clause.
- **Leak scan (Cowork dispatch, item 1):** all five credential values were loaded: GBIF_USER, GBIF_PWD,
  GBIF_EMAIL, and the store's url and key. They were checked against the report, the research note and
  both dispatches. The positive control found GBIF_USER in the filed GBIF credentials report. No hits
  in any of the four files.

## What was filed

- **D50 to D53**, verbatim from revision 2 (each row compared with cmp), six cells each, newest first
  above D49. Stripping them restores the base byte for byte. 49 rows before, 53 after.
- **Cowork's report**, byte-identical at
  `docs/planning/evidence/2026-09-20-cowork-attribution-licence-grid-report.md` (12,337 bytes).
- **The research note**, byte-identical at
  `docs/planning/evidence/2026-09-20-planner-research-era5-grid-precipitation.md` (4,357 bytes). It
  arrived as `...-precipitation-1.md`; the `-1` is dropped and noted in its index row.
- **Both dispatches**, byte-identical, with their index rows.
- **handoffs/README.md**: the naming bullet also gives `YYYY-MM-DD-coder-handoff.md`, under D49.
- **TASKS.md**:
  - Line 11 needed no edit. T1's status had already reached main with the T1 merge at 42f0743, as the
    T1 branch reports it.
  - Line 12 was edited in place, following the file's own convention of rewriting a status: "duplicate-key
    ruling pending" became "duplicate key ruled by D27, taxon folded in under D44".
- **RELEASE_CHECKLIST.md**, three dated notes, none ticking an item:
  - Under item 2, per the Cowork dispatch: no store output predates the area-extraction change.
  - Under item 4, per the Cowork dispatch: the licence is observed, and the wording is obtained and
    awaits a ruling on four defects.
  - Under item 4, per revision 2: the ruling is D53, so the wording awaits only copying.
  - The two dispatches, written before either was sent, ask for one note saying the wording awaits a
    ruling and one saying it is ruled. They are appended in that order, and the second says it is in
    the same commit, so neither note is false where it stands.

## Deletions

Two lines, each replaced in place:

- TASKS.md line 12, the status edit above.
- handoffs/README.md, the first line of the naming bullet, rewrapped with the coder-handoff name.

## Not filed

**Revision 1 of this dispatch** (`2026-09-20-file-d50-to-d54.md`, carrying the withdrawn precipitation
row) is not filed. Neither dispatch asks for it. Under D41 it would be filed with a closeout note, as the
earlier stopped revisions were, so it is an owner item. Its staged work sits uncommitted on the t0b
clone's local branch `docs-cowork-grid-report`. The closeout dispatch says not to touch it until the owner
rules, so it was not touched. This commit reached the remote branch of the same name from a separate
worktree.
