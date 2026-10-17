# Dispatch 2026-10-16: independent review (D18) of the T7 PNW fit

Written by the planner (Rowan Waymark), 2026-10-16. Forager RECORD: intent -1128; context -1126 (the fit's outcome) and -1127 (the owner's ruling). This is laid out in Forager's dispatch format (Forager docs/process/dispatch-format.md on pre-main), adapted for a review.

## Authorisation

The owner, verbatim, choosing from three options after the planner set out the fit's caveats: "Review, then decide on publishing (Recommended)". The option read: "The independent review runs now, with these caveats as its main questions … Its report comes back to you before any publish words; publishing stays a separate yes."

## Writing rule

Describe products generically. Commits end with `Co-Authored-By: Claude <noreply@anthropic.com>` and no model name.

## Change

A review report, `docs/audits/2026-10-16-t7-fit-review.md`, with an index row. Nothing else changes: no model code, no outputs, no decision rows.

## Scope boundary

- **Write only:** branch `t7-fit-review`, worktree `~/Zynergy/forager-forecast-t7-fit-review`. Your own scripts and evidence go under `docs/audits/2026-10-16-t7-fit-review/`.
- **Read only:**
  - t7-build;
  - `/mnt/work/Zynergy/forecast-data/t7/` (the fit's cache, outputs and manifests);
  - the D26 data;
  - Forager's RECORD on records-after-173.
- **Don't touch:**
  - `/mnt/work/Zynergy/forecast-data/t6b/` (the continental run uses it);
  - forecast main;
  - the site;
  - any publish command;
  - the Forager app.

## Baseline

These are premises to re-check against the remote before relying on them:
- t7-build is at `b5c3d26` (report) and `17bb84e` (evidence); the fit ran at `41f9c79`.
- The fit report is `docs/audits/2026-10-16-t7-fit-report.md`, and its evidence folder is `docs/audits/2026-10-16-t7-fit/`.
- The outputs are in `/mnt/work/Zynergy/forecast-data/t7/pnw-2026-10-17/`, with manifest sha256 `f041714e…49d5`.
- Per-block held-out predictions are cached in `/mnt/work/Zynergy/forecast-data/t7/fit/cache/` (42 files).
- The smoke run's log says "P10: fail" at 2026-10-16T11:43:32Z. The full run's log says "P10: pass" at 2026-10-17T01:34:58Z.

## Verify first

Confirm each Baseline premise, plus the manifest hashes against the files. Report any mismatch as a stop.

## The questions (the owner's caveats come first)

1. **Habitat or search effort?** The full model adds 0.004 pooled held-out AUC over effort alone (0.881 against 0.877). Does the map show habitat beyond where people search?
   - Recompute the pooled AUCs and both interval types (clustered by weather cell, and by block) from the cached predictions, with your own code.
   - Compare the full map with the effort-only map across shaded cells. Give a rank correlation, and say where they differ most.
   - Say plainly what a reader of this map would be told that the effort surface alone wouldn't tell them.
2. **Is it mycorrhizal-specific?** The comparison group (*Laetiporus*) gains +0.023 over A from the same inputs, and its map correlates 0.23 with the group's.
   - Recompute these.
   - Say whether the evidence supports labelling the map "mycorrhizal habitat", or whether something like "forest-associated fungal reporting" is the most it supports.
   - That wording is the owner's to choose; give the evidence and your recommendation.
3. **The weighting fix after a failed trial.** `41f9c79` rescaled weights to a mean of 1 after the smoke run gave P10 "fail".
   - Show, independently of any verdict, whether the fix is mechanically required: did the unfixed fit split at all?
   - Show whether it changes any ruled share, threshold or sample.
   - Show whether the main group's result depends on it. If you can do so cheaply, re-run the main group's verdict-relevant comparison with the unfixed weights.
   - Run your own revert check on the fix's test, under CLAUDE.md's runner rules.
4. **The usual D18 checks:**
   - the V9 counts against the D26 data, on a sample of 3 genera recounted with your own code;
   - the block table;
   - the area-of-applicability threshold;
   - the coder's readings beyond the plan (report section "Things that changed", and Forager RECORD -1126);
   - the "25 vs 26 level III blocks" premise.
5. **Look at the map.** Render `relative_habitat_pnw.tif` and `applicability_pnw.tif` to PNG under your evidence folder, and describe them in words:
   - where it is high and where low;
   - any artefact: seams, the Canada mask edge, stripes;
   - shading in forest no one searched.

   The images stay in the review branch; don't publish anything.

## Evidence required

- Every headline figure recomputed with your own code, matched to the report or flagged.
- At least one revert check of your own (question 3).
- File and line for every claim about code.
- Each claim marked as read, computed or inferred.

## Laptop limits

- Heavy commands run under `systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0`, with `Nice=10`.
- The continental job `t6b-night` (2 workers) runs alongside, until 07:00 PDT tomorrow. Don't stop it.
- No Gradle.
- One heavy job of your own at a time.
- Stream large reads instead of loading whole tables.

## Prediction (outcome, planner)

The headline AUCs and weather-cell intervals reproduce to within rounding. The block-clustered intervals include zero, as reported. The fix is mechanically required: without it the comparison group's model B doesn't split. The map is dominated by the effort surface's pattern.

## Prediction (mechanism, reviewer)

Write yours at the top of the report, before computing anything.

## Stops: come back to the planner

- a figure you can't reproduce;
- a manifest or hash mismatch;
- evidence that the fix was tuned to the verdict;
- anything that would change a fixed threshold, sample or seed;
- a wrong premise here;
- anything needing a publish step.

## Finish line

The review report and index row are pushed on `t7-fit-review`. Its verdict has three parts: blocking, should-fix and notes. It ends with two one-line answers:
- "Does the evidence support publishing this as a pilot habitat layer, and under what wording?"
- "What would most strengthen the habitat signal?"

## Final message

- commits;
- each question's answer, with its numbers and whether they matched;
- the revert check;
- the map described in words;
- what you couldn't check.
