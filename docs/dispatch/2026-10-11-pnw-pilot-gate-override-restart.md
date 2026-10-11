# Dispatch: restart the PNW pilot chain past the land-route gate, on the owner's override

Written by the planner (Rowan Waymark), 2026-10-11 15:20 UTC. Owner's ruling: Forager RECORD -854 (branch records-after-173). Assumed base: forager-forecast `pnw-pilot-t1` at `ae4f1e9`. Verify that against the remote before acting. Every factual claim below is a premise to re-check from the committed state and the data on disk, not a fact.

Writing rule for everything you write (report, commits, messages): describe other products, services and device makers generically or by what they do. Don't discuss the rule; just write that way.

## What happened (premises)

- The time-series pull finished 2026-10-11 14:15:05 UTC: `pull_ts.log`, "1870/1870 points done, 0 gave up". `ts_check.log`: 1,870 points, 0 failed. `ts_assemble.log`: 1,870 points, none left out.
- `scripts/pnw_hedge_run.sh` stopped with exit 3: `hedge_run.log` "GATE FAIL: land route False, required spans 25/25 compared". `scripts/pnw_t1_run_all.sh main` then ran its own equivalence and also stopped at exit 3 (`equivalence.log`). Nothing was fitted.
- The cause, in both runs: in `hourly_land_route`, t2m at offset 0 matched 6,911 of 6,912 hours. `land_route_pass` (`scripts/pnw_equivalence.py:70`) requires all of them. stl1 and swvl1 matched 6,912 of 6,912.
- The planner found the one hour with an offline copy of the script, `/tmp/eqdiag/eqdiag.py`, which adds a print and reads only the cached Open-Meteo bodies. That copy is not committed and is not evidence; confirm with your own code. It reported: t2m, cell `493_-1250` (kind own, land point [493, -1250]), 2025-12-12T11:00, store 5.42495 °C, Open-Meteo 5.5 °C, difference 0.07505 against `HOURLY_TOL` 0.075 + `EPS` 1e-6.
- The planner's explanation, inferred and unconfirmed: 0.075 is exactly the worst case of Open-Meteo's two roundings (stored at 0.05 °C, shown at 0.1 °C). The store value sits about 0.00005 °C below a rounding midpoint, and the two Copernicus routes differ by up to 0.00016 K (`ts_check.log`, `worst_point_by_variable`). A decoding difference that small could flip the rounding.

## The owner's ruling (RECORD -854)

The owner chose "Fit anyway, failure on the record (Recommended)": the gate stays exactly as written and its failure is recorded. The fits run on the owner's word. The model, the reviewer's report and the briefing each state the failing hour.

## What to do

0. **Verify, then report by message before building anything.** Confirm the base. Read `land_route_pass` and the hourly loop. Independently reproduce the failing hour from the cached bodies and the hourly store, with your own code and not `/tmp/eqdiag`. Confirm it is exactly one hour in each run's comparison (main and hedge), and name the variable, point, time and both values. If anything differs from the premises above, stop and report.
1. **Add an override as a new path, without changing the gate.** `land_route_pass`, `HOURLY_TOL`, `EPS` and the comparison stay byte-identical, and the gate still runs and writes `"pass": false`. The scripts proceed past a land-route fail only when given an explicit override naming "Forager RECORD -854". Whenever the override is used, the gate result, the override and the failing hour(s) are written into each fit's output and each `model.json` (including `models/primary_t1_1000m_full/model.json`), so publishing can carry it. A fail with no override still exits 3. An override given when the gate passes is recorded as unused. Tests: no override plus a fail exits 3; override plus a fail proceeds and records; the gate function's result is unchanged. Do one revert check under CLAUDE.md's revert-runner rules: restore from a saved copy, never from git, and read the build log before the results.
2. **Run the chain in its existing order:** `scripts/pnw_hedge_run.sh` (2019–2025), then `scripts/pnw_t1_run_all.sh main` (all years), each with the override. Run one CPU job at a time, and every heavy command under `systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0`. The steps after the gate are unchanged: calendar and full fits on one unit set, coastal cells by nearest land neighbour (-822), the random-date comparison and D33 (3) and (4) (-828). The scoring model needs `copernicus_sources` in `models/primary_t1_1000m_full/model.json`.
3. **Report:** append a section to `docs/audits/2026-10-10-pnw-pilot-t1-report.md` on `pnw-pilot-t1`. Cover the gate result, the confirmed hour, the override, every figure the briefing's TO FILL lines need, and what was not checked.

Commit and push after every step. **Read back every edit you claim from the committed file before citing it.** This builder's chain has twice reported edits that had not applied (RECORD -834, -849).

## Stops: come back to the planner, don't choose

- More than one hour fails, or any other variable fails, or step 0 finds a different hour.
- Any other gate or check fails (the D24 daily comparison is reported, not gating; its 20 known mismatches, -833, are not a stop).
- Anything that would change a fixed threshold, tolerance, sample or seed.
- A fit or check that stops, runs out of memory, or produces figures the report can't explain.
- A wrong premise in this dispatch.

## Not in scope

Scoring, publishing, the site, the review: separate dispatches. The T6b continental run. Anything in the Forager app.
