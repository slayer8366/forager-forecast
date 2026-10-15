# Dispatch: T6b host genera for the mycorrhizal habitat map (build, tests first; no run on the drive)

Written by the Forager planner (Rowan Waymark) on 2026-10-15. Records: Forager RECORD -1029 (M7, the owner: "M7 let's add them now, it's not a huge task now, but it will be later."), -1032 (the verify report), -1033 (the owner's rulings, "All recommended", provisional until review), and -1037 (this dispatch; the owner's go: "1 to 3 yes").

**Base:** forager-forecast `origin/main` at `a79d667`. Check it against the remote.
**Branch:** `t6b-host-genera`. Merging into main follows D40.
**Evidence:** read `docs/audits/2026-10-15-t6b-host-genera-verify-report.md` on branch `t6b-host-genera-verify` (`80e807a`) in full first. Every claim in it is a premise to re-check.

## What the owner ruled (-1033, provisional)

1. **One pass.** Add every genus below in a single pass:
   - **Tier A:** *Larix*, *Betula*, *Populus*, *Alnus*, *Notholithocarpus* (tanoak), *Chrysolepis* (chinquapin) and *Arbutus*. Tanoak and chinquapin are either one Fagaceae band or two; propose which.
   - **Tier B:** *Fagus*, *Carya*, *Tilia*, *Ostrya* and *Carpinus*.
   - **A total band** for ectomycorrhizal hosts.
   - **Tier B and D116.** Tier B needs D116 amended by a new decision row. Write the row as proposed, marked for the owner's review. Never edit D116's own row.
2. **Canada.** The genera SCANFI folds into broadleaf are flagged "not available" on the Canadian side, as the code already does. This dispatch adds no second Canadian source.
3. **D121.** The new bands enter the fit under D121; that is T7's business, not built here.
4. **Crown widths.** Aspen's crown-width coefficients stand in for genera without their own, as D89(2) already does.
5. **Order.** The PNW box comes first, then the rest of the US. Old tiles are kept until the new ones are verified.
6. **T5 stays as it is.** Use a T6b-only genus list; leave T5's `HOST_GENERA` and its products unchanged.

## What to build (tests first)

- **The T6b genus list,** kept separate from T5's, and carried through:
  - the plot table;
  - the per-genus share and flag bands;
  - the US halves;
  - the Canadian fill.
- **The total band.** Its membership is the ectomycorrhizal-host genera of the old and new lists together. List the members explicitly and propose them for the owner's review.
- **F1 fix.** A tile's manifest line records the band layout it was built with: the genus list, or a hash of it. `done_units` (`src/forager_forecast/t6b_run.py:61-72`) counts a tree unit as done only if that layout matches the current one, so old-layout tiles are rebuilt rather than skipped.
- **F2 fix.** The plot table is rebuilt whenever the genus list changes, not only when the rulings string changes (`scripts/t6b_run.py:143-150`).
- **A trees-only supersede.** It moves aside only the tree outputs being replaced, never soil, SCANFI layer tiles or the manifest. Old tiles are kept in a dated folder, not deleted.
- **US halves (D119).** They are rebuilt as new files; the old ones are kept.
- **A free-space check** before each tree tile, as the SCANFI stage already has.
- **A way to run the PNW box alone,** using the existing `--tiles` option or one beside it.

**Tests:** each is shown failing first, against the current code, for its stated reason. Then the fix. Then revert checks under Forager CLAUDE.md's runner rules: restore from a saved copy, check the log for errors, and confirm the forward change is still present.

Must be covered:
- the band layout;
- F1: an old-layout tile is not counted done;
- F2;
- the trees-only supersede leaving soil and SCANFI untouched;
- the free-space stop;
- T5 unchanged, with its existing tests passing untouched.

Run the full suite and ruff locally. The laptop is for forecast work.

## Do not run on the drive

A continental section, user unit `t6b-night`, is running on the flash drive's `forecast-data/t6b` and writes its manifest. **Do not run any T6b stage, and do not write anything under the drive's `t6b` folder.** The planner schedules the PNW run after reading your report, pausing the night section first, because two writers on one manifest is unsafe. Only listings and manifest reads are allowed.

## Stops

- A premise in the verify report is wrong in a way that changes the design.
- A genus has no data in the US tree table.
- The plot table can't carry the new columns without changing an existing column's meaning.
- Any change to T5's outputs.
- Two failed attempts on one symptom.

## Report

Write `docs/audits/2026-10-15-t6b-host-genera-build-report.md`, plus one row in `docs/audits/README.md`, keeping every row. It covers:
- commits;
- the failing-first evidence;
- revert checks;
- the suite and ruff results;
- the proposed total-band membership and the D116 row;
- the exact command for the PNW run, its expected tile count, time and space;
- what is untested.

Push with `git push -u origin t6b-host-genera`. Never force push. Commits end with `Co-Authored-By: Claude <noreply@anthropic.com>`, with no model name.
