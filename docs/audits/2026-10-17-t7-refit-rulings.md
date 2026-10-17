# T7 re-fit: the owner's rulings on the Phase 1 open items, built

Hazel Cairnwright (coder), 2026-10-17. On the planner's relay of the owner's rulings (Forager RECORD -1187) and "1 yes" (-1188). Branch `t7-refit`, PR #5 into t7-build, unmerged. **Phase 2 has not started.** The trial run's figures prove the plumbing only, and are not results.

Evidence is in `docs/audits/2026-10-17-t7-refit-rulings/`: `tests_over_stubs.txt`, `revert_checks.py` and `.txt`, and `smoke/`. The Phase 1 report is `2026-10-17-t7-refit-phase1.md`.

## The rulings as built

- **Access direction: −1** ("Yes, always fewer (Recommended)").
  - The fit is run with `--access-monotone -1`.
  - The trial ran with it: access monotone −1, P6 ranking unchanged at both the effort quartiles and the access quartiles.
- **Condition 4** (`t7/condition4.py`, wired into `scripts/t7_fit.py` after the map is written):
  - **Score.** Each specimen's score is the map's mean over its stated uncertainty circle: the cells whose centres lie within the radius of the record's point. Its own cell is always included, and masked cells are left out, never filled.
  - **Background.** It is matched to the specimens' road-distance mix: ten scorable cells per specimen, in the same road band (edges 50, 100, 250, 500, 1,000, 2,000 and 5,000 m), drawn without replacement within the band, seed 20260918. Each background point carries that specimen's radius and is scored the same way.
  - **Figure.** The unweighted AUC minus 0.5, with a 95% interval from resampling whole level III blocks.
  - **Verdict.** The whole box carries it. The interior sub-box is reported beside it, with no verdict.
  - **The specimens file** is sha256-checked against the registered kept set before use.
- **Decision rows:**
  - D156: access, applying -1182 and -1187;
  - D157: condition 3, applying -1182;
  - D158: condition 4, applying -1187 and -1182.

  Each quotes the owner's words.

## Tests first, revert checks, suite, CI

- **Over stubs.** All 7 new tests in `tests/test_t7_condition4.py` failed: 6 on `NotImplementedError`, and the P10b test on the missing condition 4 figure (`KeyError: 'low'`).
- **Two test-data fixes after the first implementation run** (disclosed):
  - the scene used raster-order integers as cell ids, and now uses real packed ids;
  - the scene had four blocks, so a block resample could hold no specimen, and now has 64.

  Revert checks c4, c7 and c9 show the fixed scene bites.
- **Nine revert checks**, under the Phase 1 runner's rules (`revert_checks.txt`). Each failed with a message specific to its own edit:

  | revert | what it undid |
  |---|---|
  | c1 | the circle ignored |
  | c2 | the point's own cell no longer always included |
  | c3 | masked cells no longer left out |
  | c4 | the background no longer matched to the road band |
  | c5 | the background no longer carrying its specimen's radius |
  | c6 | the interval resampling rows, not blocks |
  | c7 | the interior set no longer the interior specimens |
  | c8 | P10b no longer taking condition 4 |
  | c9 | specimens on cells with no map value no longer dropped |

  The runner was formatted before it ran, so the committed file is the one that ran.
- **Suite.** 734 tests, 0 failures, 0 errors, read from the JUnit XML. That is 727 plus the 7 new tests. The temp folder was on `/mnt/work`. ruff is clean.
- **CI.** It runs on PR #5 as a draft. The workflow triggers on `pull_request`, and every push has run. The planner's premise that it showed no result was out of date: e8f818d was green. See the report to the planner for the head's result.

## The trial run (`--smoke`, `--access-monotone -1`, condition 4 live; plumbing only)

- **Folders.** Work dir `t7/refit-smoke/`; outputs in `t7/refit-smoke/outputs-rulings/`.
- **Cost.** 1,235 s, peak 2,700 MB, under the memory cap beside t6b-night.
- **Log.** `smoke/fit_log.txt`. Phase 1's trial log was set aside as `fit_phase1_monotone0.log`.
- **Condition 4's numbers** (counts only; the figures are not results):
  - **Whole box:** 6,026 kept specimens in; 2,012 not scorable (their own cell has no map value: not code 1, or outside the trial's area of applicability); 4,014 specimens scored against 40,140 background points.
  - **Interior:** 387 specimens against 3,870 background points.
  - **Matching:** the background's road-band counts equal ten times the specimens', in both sets.
- **P10b.** It was evaluated with all four conditions, and condition 4's status reads "computed".

The full run's area of applicability will differ from the trial's, so the scorable count may move a little from 4,014.

## The Phase 2 command line (not run)

```
cd ~/Zynergy/forager-forecast-t7-refit && systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0 \
  nice -n 10 .venv/bin/python scripts/t7_fit.py fit /mnt/work/Zynergy/forecast-data/t7/refit \
  docs/audits/2026-10-17-t7-refit --access-monotone -1 --threads 4 \
  --out /mnt/work/Zynergy/forecast-data/t7/refit/outputs > /mnt/work/Zynergy/forecast-data/t7/refit/fit.out 2>&1
```

- The work dir already holds the re-fit table and Phase 1's timing log, and no cache.
- The evidence goes to `docs/audits/2026-10-17-t7-refit/`; it can be renamed to the finishing date when the report is written.
- The estimate is about 16.5 h (16 to 21 h). Condition 4 adds seconds.

## Calls beyond the rulings

- Ten background points per specimen.
- The band edges.
- Unweighted AUC.
- Block resampling for condition 4's interval, with each background point in its own cell's block.
- "Scorable" means the own cell has a map value.
- `--access-monotone` stays a required argument rather than being fixed in code. The ruled −1 is in the command line and in D156.
