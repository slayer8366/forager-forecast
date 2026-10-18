# Dispatch 2026-10-17: two independent reviews (D18) of the T7 PNW re-fit under P10b

Written by the planner (Rowan Waymark), 2026-10-17, for two Sorrel Tally sessions on two models, neither of them Opus, which the coder used. Forager RECORD: intent -1232; the result -1229 and -1230; the bar D145 (with its amendment) and D156 to D158. Laid out in Forager's dispatch format, adapted for a review, as the 2026-10-16 review dispatch was.

## Authorisation

The owner, verbatim: "Go ahead and start the reviews."

## Writing rule

Describe products generically. Commits end with `Co-Authored-By: Claude <noreply@anthropic.com>` and no model name.

## Who you are

Sorrel Tally, the independent reviewer. Read the profile first: `git -C ~/Zynergy/Forager show origin/pre-main:docs/process/reviewer-profile.md`, and `~/Zynergy/Forager/CLAUDE.md`.

There are two reviews, run side by side:
- **Review 1:** branch `t7-refit-review`, worktree `~/Zynergy/forager-forecast-t7-refit-review`, report `docs/audits/2026-10-17-t7-refit-review.md`.
- **Review 2:** branch `t7-refit-review-2`, worktree `~/Zynergy/forager-forecast-t7-refit-review-2`, report `docs/audits/2026-10-17-t7-refit-review-2.md`.

Each review is forbidden to read the other's branch, worktree or report.

## Change

A review report and its evidence folder (`docs/audits/2026-10-17-t7-refit-review[-2]/`), on your own branch from `t7-refit` at `da1f207`, pushed, with no PR. Nothing else changes: no model code, no outputs, no decision rows, no index rows (the planner adds those).

## Scope boundary

- **Read only:**
  - forecast branches t7-refit and t7-build;
  - `/mnt/work/Zynergy/forecast-data/t7/refit/` (work dir, cache, outputs) and `t7/specimens/`, `t7/v9/`, `t7/v9c/`, the access layer, and the judged 2026-10-16 run's `t7/fit/` and `t7/pnw-2026-10-17/`;
  - Forager's RECORD on records-after-173.
- **Don't touch:**
  - anything under `/mnt/work/Zynergy/forecast-data/t6b/`, or the running `t6b-night` unit;
  - forecast main;
  - the site;
  - any publish command;
  - the Forager app;
  - the other review.
- **Heavy steps** run under `systemd-run --user --scope -q -p MemoryMax=4G -p MemorySwapMax=0` at `nice -n 10`, one at a time.
- **No re-fit:** recompute from the cached held-out predictions and the saved tables. A refit of anything is a stop unless it is small and stated first.

## Baseline (premises to re-check before relying on them)

- **Code and report:**
  - `t7-refit` is at `da1f207`, holding the report `docs/audits/2026-10-17-t7-refit-report.md` and the evidence folder `docs/audits/2026-10-17-t7-refit/`;
  - the fit ran code `0560dae`;
  - the forecast's draft PR #5 is open.
- **Run outputs:** the run's manifest sha256 is `af0fc2dd5c5868773da1a41d5231abdcf1aab16c8d5a1ee95e86392434b648ec` (fit.log's last line); the outputs are in `/mnt/work/Zynergy/forecast-data/t7/refit/outputs/`.
- **The result as reported** (1,000 resamples, seed 20260918):
  - (1) full minus B, block-clustered: +0.00379 [+0.00105, +0.00924];
  - (2) full minus A within a weather cell, block-resampled: −0.00722 [−0.02570, +0.01614];
  - (3) mycorrhizal gain minus saprotroph gain: +0.00279 [−0.00196, +0.01054];
  - (4) specimens above a road-matched background: +0.196 [+0.066, +0.285], with the interior reported beside as +0.103 [−0.157, +0.240].
  - P10b fails; P10 passes.
- **The specimen download:** key 0032050-260928105237408, DOI 10.15468/dl.5mvzg2, zip sha256 `28efb80e…34ad`.

## The questions, in order

1. **Reproduce P10b.** Recompute all four conditions and their intervals with your own code from the cache, with condition 2's interval resampled as D145's amendment requires (level III blocks, condition 1's exact resampling). Say whether each figure matched or not. Confirm the verdict.
2. **Condition 1's pass.**
   - The three added bands (Lithocarpus, Chrysolepis, Arbutus) were picked on the same held-out blocks that score them, and base minus B is +0.0016 [−0.0013, +0.0067].
   - Estimate how much of condition 1's margin that selection explains. A nested or held-apart selection is welcome if it can be done cheaply from the cache; if not, give the strongest bound you can.
   - Say plainly whether condition 1 would pass without the selection.
3. **Road access.** dist_road_m enters as access: in effort's interaction group, monotone decreasing, held at 258.3 m on the map, and outside the area of applicability (D156).
   - Is that implemented as stated?
   - Does holding access on the map remove habitat signal that is correlated with remoteness?
   - Is condition 2's collapse (+0.054 before, −0.007 now) the road band explaining reporting within a cell, or something else?
4. **Condition 3 and the comparison groups.**
   - Recompute the saprotroph gain and the Laetiporus gain.
   - Does the evidence support anything "mycorrhizal" in a label?
5. **Condition 4, the specimens** (D158).
   - Check the specimen filters: licence, uncertainty, genera.
   - Check the scoring by the mean over each record's circle, and the road-band matching.
   - Assess what the pass can bear, given that the records are mostly decades old, about three quarters come from one herbarium, and collecting stations and decade are not matched.
   - Is the interior result usable at all?
6. **Look at the map.** Render the new habitat raster and its applicability mask to PNG in your evidence folder. Describe the map in words, and compare it with the 2026-10-16 map: where it moved, any artefacts, and the Canada mask edge.
7. **The verdict and one-line answers:**
   - Does the evidence support showing this map to anyone, and under what wording?
   - Is a further strengthening step likely to change the P10b verdict, and which one?
   - Or does the evidence point to stopping T7 for the PNW?

   These are recommendations. Publishing and the next step are the owner's decisions.

## Evidence required

- Your mechanism prediction at the top, written before computing anything and scored at the end.
- Every claim marked READ, COMPUTED or INFERRED.
- At least one revert check under CLAUDE.md's runner rules, on a result you depend on.
- Your scripts committed exactly as they ran.

## Stops

- a baseline mismatch;
- anything that needs a refit beyond a small stated one;
- anything that would touch t6b or publish;
- reading the other review.

## Finish line

The report and its evidence pushed to your branch. Your final message is the report's verdict (blocking, should-fix, notes) and the one-line answers.
