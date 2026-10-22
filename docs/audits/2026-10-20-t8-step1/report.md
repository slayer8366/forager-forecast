# T8 step 1: Ash Transect's report to the forecast planner

Filed by the forecast planner (Alder Bearing), 2026-10-20 03:39 UTC. This is Ash's final message from the
third resumed step-1 session, copied as received, so that it isn't kept only in a session transcript.
Branch t8-build at d9c12ba when it was received. The planner checked that the branch was clean and
matched origin; nothing else in it has been re-derived yet.

Background, from the planner: the first step-1 session ran test_t8_run.py up to 7.4 GB at 19:53 PDT
2026-10-19. The laptop ran out of memory, and that killed it, the planner sessions and the app
planner's helpers. A second session was stopped by an interrupt. The third session's first run of
the same file was killed by the planner at 3.7 GB (03:01 UTC), and every run after that went under
a memory cap.

---

**Report to Alder Bearing, from Ash Transect: T8 step 1 (resume), stopped before the count**

Step 1 is built and tested on synthetic data and stubs only. No real records, outcomes or weather
were read; only file names, sizes, array shapes from `.npy` headers, and the zip's header row of
column names. Two things need you:
- **The memory cause is found and fixed.** test_t8_run.py now peaks at 192 MB; you killed it at
  3.7 GB, and it reached 7.4 GB earlier. The same cause would have hit the real fits much harder.
- **The count and the fit both refuse to start.** 19 readings that the plan and D133 leave open
  are still unruled.

Branch t8-build is pushed. Head is d9c12ba, the worktree is clean, nothing was force pushed, and
no PR was opened.

## The memory cause, and how it was measured

Every test run since the planner's message ran under `systemd-run --scope -p MemoryMax=2G
-p MemorySwapMax=0 nice -n 10` (1G for the small ones). Ash committed and pushed before each run,
and nothing hit the cap.

- **The cause** (computed, by the probes in this folder): each statsmodels GLM fit leaves its model
  and results objects in reference cycles that hold the design arrays. Python's cycle collector
  triggers on object counts, not bytes, and gen-0 had only reached 1,862 objects, so the arrays
  were never freed. Current RSS rose about 35 MB per 11-fold `loyo_additive` pass with no
  collection (181 to 464 MB over 8 passes). It held flat at 181 MB with `gc.collect()` after each
  pass (`probe_gc.py`). Python-tracked memory did not grow (`probe_mem2.py`). Neither
  `OPENBLAS_NUM_THREADS=1` nor `MALLOC_ARENA_MAX=2` changed it.
- **What the cause was not** (read and computed): not a dense array, not the materialised swaps,
  not the fixture size, not LightGBM. LightGBM holds flat at 95 MB (`probe_lgb.py`).
- **Consequence for the real fits** (inferred): a real fit is about 30 times larger, 52,718 units
  against the test's 1,760. Over 199 swaps × 11 folds it would have run out of memory far sooner.
- **The fix** (`models.py` `fit_predict_logistic`, commit 2a47ccc): only the coefficients leave
  the function, and the cycles are collected (`gc.collect(0)`) in a `finally`. The new test
  `test_a_fit_leaves_no_cyclic_garbage_holding_its_arrays` (1974c35) failed on the committed
  pre-fix code with `assert 18 == 0`, then passed. After the fix (computed): test_t8_run.py
  4 passed in 153 s, peak 192 MB; one real-size synthetic pass peaked at 343 MB; the full suite
  peaked at 914 MB.

## The WIP draft, c98773b: kept, changed or dropped

- `ecoregions.py` and its test: kept unchanged; 3 tests pass.
- `models.py`: kept, with the memory fix and one line ruff reformatted. Its 10 tests pass.
  Finding, left alone: `loyo_additive`'s `years=` parameter has no caller (read: grep), and would
  raise on a subset of years because of its NaN check.
- `run.py`: kept unchanged. The dropped None guard on `skill_vs_no_weather` stays dropped:
  `brier_skill` always returns a float here, because predictions lie strictly between 0 and 1, so
  the reference Brier is never zero (inferred).
- test_t8_run.py: kept unchanged. Its interrupted run was the memory growth; it now passes.
- Nothing was dropped.

## What was built (on top of 7973615 and 14cd074)

- **J5 fix** (03c5f71 test, 34594b8 fix): the rate's numerator now counts T1 units only, by the
  unit's ISO year, matching its denominator. It had counted by calendar year and included records
  in no T1 unit. The test failed first with `0.12 != 0.1`.
- **`t8/count.py`** with **`scripts/t8_count.py`**: the whole count under one word. It checks the
  zip's sha256 first, then streams the PNW box, and keeps speciesKey and taxonRank for J6. It
  resolves J5's six genus keys from the zip's own `genus` and `genusKey` columns, refusing a name
  with no key or several; this replaces a GBIF API lookup, so the count makes no network call.
  It runs T1's three step lists and requires that each reproduce T1's stored units and outcomes
  exactly. The allowed extras are the units T1 dropped for weather, read from T1's own summary:
  468 for the headline (read: 53,186 before, 52,718 kept). Then it attaches lichens and runs the
  jump check.
- **`t8/fit.py`** with **`scripts/t8_fit.py`**: one part per run (bar, forecast, alone,
  challenger, ecoregion). Identity checks run before any fit: the lichen file holds exactly T1's
  units in T1's order; every unit's land point equals T1's `land_point`; the swap tables
  reproduce the true weather under the identity mapping. Only `bar` on the headline design is
  labelled "verdict"; everything else is "no verdict". The weather file comes from T1's own
  `weather_npz` record, and the CEC sha256 from its request record. Also added:
  `weather.read_grids` and `effort_term.all_years_effort` (the ecoregion run's effort).
- **Premises checked against the files** (read): unit files hold 52,718, 56,927 and 9,640 units;
  the weather has 4,140 days; T6's counts are the `all_*` and `cc_*` files listed in SHA256SUMS;
  the CEC zip is 35,236,046 bytes on the mounted T6b drive; every needed column is in
  occurrence.txt.

## Tests, failing-first evidence and revert checks (computed)

- T8 tests: jump 16, bar 9, weather 12, units and effort 11, ecoregions 3, models 11, run 4, all
  pass. New: count 9 and fit 7, all pass.
- Full suite: 686 passed in 438 s. ruff check and format clean.
- Revert checks, each in a throwaway worktree at HEAD. The runner confirmed each edit changed
  exactly one line, read the import log to confirm the reverted file was the one imported,
  restored from a saved copy, and confirmed the forward change was still present afterwards.
  What each revert failed: C1 only `test_c1_fails_alone`; C2 `test_c2_fails_alone` and
  `test_c2_…interval_reaches_zero`; C3 only `test_c3_fails_alone`; C4 only `test_c4_fails_alone`;
  the count's T1-identity check, the 2 refusal tests with `DID NOT RAISE UnitsDiffer`; the fit's
  land-route check, the land-point test with `DID NOT RAISE InputsDiffer`.
- Not shown failing first on a stub: the count and fit tests were written alongside their code.
  The two revert checks above are their evidence; their other assertions are "not shown to
  bite". One count refusal test first failed on the wrong refusal (`T1's file holds 3 units,
  expected 4`), and was fixed so it exercises the path it names. The earlier sessions' claim that
  the 7973615 and 14cd074 tests were seen failing on a stub was not re-verified.
- Scripts: both load (`--help`). The count's real entry point, pointed at nonexistent paths,
  refused with `NotRuled: 8 reading(s) for the count…` before touching any file.

## The exact commands (each refuses until its readings are ruled)

Run from `~/.cache/forager-wt/t8-build`:

```
systemd-run --user --unit=t8-count -p MemoryMax=3G -p MemorySwapMax=0 -p Nice=10 --working-directory=$PWD .venv/bin/python scripts/t8_count.py --out ~/Zynergy/forecast-data/t8/count
systemd-run --user --unit=t8-fit-<design>-<part> -p MemoryMax=3G -p MemorySwapMax=0 -p Nice=10 --working-directory=$PWD .venv/bin/python scripts/t8_fit.py --design t1_1000m --part bar --count ~/Zynergy/forecast-data/t8/count --out ~/Zynergy/forecast-data/t8/fit
```

Then the parts `forecast`, `alone`, `challenger` (after `bar`) and `ecoregion`; then
`--design t1_5000m --part bar` and `--design t1_1000m_cc --part bar`.

## Expected run times

Base figure, one real-size synthetic pass: 15.2 s weather model, 5.5 s no-weather, measured niced
beside t6b-night (computed). Everything else is extrapolated (inferred).

| Run | Expected time |
|---|---|
| Count | about 5 min, under 1.5 GB (T6's pass over this zip took 3:13 at 1.19 GB, read) |
| Bar | about 51 min |
| Forecast | about 51 min |
| Alone | about 1.2 to 3.3 h |
| Challenger | about 1 to 3 h (from T1's 602 s and 2,057 s fits) |
| Ecoregion | minutes |
| D33 (3) | about 55 min |
| D33 (4) | about 10 min |

Each fit run also spends a few minutes in preparation. None of the fit runs should go beside
t6b-night.

## Calls beyond the dispatch

Genus keys come from the zip, not the GBIF API. J5 counts by the unit's ISO year. Two readings
added to the open list: M-sensitivity and M-sensitivity-effort. Evidence committed to this folder.
The README, the RECORD and the decision rows were not touched.

## Not checked

Anything on real data. Whether a real ecoregion block leaves the training rows with tied spline
knots (the code refuses that case; it never fills it). The CEC polygon test's speed on the real
file.

## Stop: 19 open readings

All are in `src/forager_forecast/t8/design.py` PENDING, each with its proposal and alternatives.
The count's 8: J-rise, J-unit, J-new-observer, J-main-dataset, J-concentration, J-genera,
J-species, L-outcome. The fit's 11: M-calendar-place, M-effort-form, M-effort-training,
M-effort-config, M-swap, M-challenger-swaps, M-forecast-bar, M-measure-alone, M-ecoregion,
M-sensitivity, M-sensitivity-effort. If the owner rules an alternative rather than a proposal, the
code needs a change before the count or the fit runs.
