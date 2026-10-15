# Dispatch: review pass 2 of the PNW pilot's T1 fit (D18)

Written by the planner (Rowan Waymark), 2026-10-11. Runs once the builder's chain has pushed results (forecast branch pnw-pilot-t1, dispatch docs/dispatch/2026-10-11-pnw-pilot-gate-override-restart.md). Assumed base: pnw-pilot-t1-review at 3e5aa7d. Verify that, and the pnw-pilot-t1 head you read, against the remote first. Every claim below is a premise to re-check.

Writing rule for everything you write: describe other products, services and device makers generically or by what they do. Don't discuss the rule; just write that way.

## Task

Continue docs/audits/2026-10-10-pnw-pilot-t1-review.md from its "## Pass 2" section, in worktree ~/Zynergy/forager-forecast-pnw-review. Merge pnw-pilot-t1 into the review branch at the head you read (merge, never rebase), and name that head in each section.

Trace each pending item to its output file and sample, and recompute every headline figure with your own code:
1. **The equivalence result,** including the land-route gate's failing hour and the owner's override (Forager RECORD -854). Check the planner's rounding explanation independently, from the cached responses, the gridded store and the time-series route (the builder's scripts/pnw_land_route_failures.py and docs/audits/2026-10-11-gate-override/). State whether it holds, fails, or can't be decided from the data.
2. **Both fits on the weather unit set** (calendar and full), hedge (2019–2025) and main (all years). Check pass 1's prediction: 52,718 units and 1,138 positives for a full-years fit with no missing days (review line 383).
3. **The headline and its interval.** The T1 headline is only ever the all-years run (D33).
4. **The per-fold table.**
5. **The random-date comparison and D33 (3) and (4)** (the extras run, RECORD -828).
6. **The labels:** each model.json and report carries the gate failure and the override (RECORD -854). The D24 daily mismatches are 30 of 1,008 (RECORD -855).

Run your own revert check on at least one result you depend on, under CLAUDE.md's revert-runner rules (restore from a saved copy, read the build log first). Heavy commands run under `systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0`, and never while a fit runs (`pgrep -f 'scripts/[p]nw_t1_fit.py'`).

End with a pass-2 verdict: blocking, should-fix, notes. Also give a one-line answer to "may the full model be published as reviewed?". Commit and push after each item.

## Stops: come back to the planner

A blocking finding; a figure you can't reproduce; anything that would change a fixed threshold, sample or seed; a wrong premise here.

## Not in scope

Fixing the builder's code (report it); scoring; the site; the Forager app.
