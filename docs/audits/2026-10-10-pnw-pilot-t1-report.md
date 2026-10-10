# PNW pilot, T1 on the Pacific Northwest box: build and run report (in progress)

**Status:** IN PROGRESS. The sections marked PENDING are not done yet. Nothing in this file is the
T1 result until the "Result" section says so.
**Branch:** `pnw-pilot-t1`, cut from origin/main `36cc647`.
**Orders:** Forager RECORD -806, -807, -811 and -812 (filed here as D122), and -809 ("a standing
model ready before Monday"). The owner's "Train as it downloads if you need to" was relayed by the
planner on 2026-10-10.
**Verify report:** `2026-10-10-pnw-first-fit-verify-report.md`, on branch `pnw-first-fit-verify`.

## Fixed before any fit or weather value (committed first)

- Tuning grid (D31): `2026-10-10-pnw-pilot-t1/tuning_grid.json`. It holds 20 configurations drawn
  with seed 20260918 from `t1_model.GRID`. The fit script refuses to run if the file and the draw
  differ.
- D24 equivalence sample and tolerance: `2026-10-10-pnw-pilot-t1/equivalence_spec.md`, commit
  `4d6e864`.
- D122 (the pilot ruling), commit `4d6e864`.

## Weather pull

- Script: `scripts/pnw_cds_pull.py`. Data goes to `~/Zynergy/forecast-data-pnw-pilot/cds/`
  (/mnt/work), with each request's JSON beside its file (D52). The log is
  `~/Zynergy/forecast-data-pnw-pilot/pull.log`.
- Area: T1's PNW box first, then the rest of the union 40 to 49.5 N, 111 to 125 W (RECORD -812).
- Order and why: 2019 to 2025 first. These are the years D33 (1) calls the PNW's useful data, and
  they hold 1,163 of the 1,235 Cantharellus survivors. Then 2014 (the warm-up months), then 2015 to
  2018. The point is that a fit on arrived years covers most of the positives, as the planner
  suggested.
- Timing: PENDING.

## Records (observed)

The D26 zip was read in place, with its sha256 equal to its DOI record. The run took 170.6 s and
peaked at 164 MB RSS (`scripts/pnw_t1_records.py`; summary in
`2026-10-10-pnw-pilot-t1/records_summary.json`). The loader read 2,493,578 rows. 9,627 of them
could not be loaded: 9,604 not a calendar day and 23 spanning days. 252,818 records fall in T1's
PNW box.

| List | Obscured dropped | Uncertainty dropped | Duplicates dropped | Survivors | Cantharellus |
|---|---|---|---|---|---|
| t1_1000m (headline) | 16,912 | 71,645 | 20,116 | 144,145 | 1,235 |
| t1_5000m (D33 (3)) | 16,912 | 56,073 | 22,601 | 157,232 | 1,487 |
| t1_1000m_cc (D29 track) | 1,961 | 10,699 | 4,783 | 24,198 | 109 |

Two cross-checks against filed counts. Both hold:
- Survivors in the PNW are 144,145, equal to D28's filed `survivors/event/by_region/pnw`.
- The duplicate step read 164,261 records, equal to the filed `duplicate_step_reads/by_region/pnw`
  (`2026-10-06-d28-date-rule/survivors_0012112/pass_t1.json`).

Cantharellus by year (t1_1000m): 2015 3, 2016 8, 2017 12, 2018 29, 2019 81, 2020 111, 2021 122,
2022 98, 2023 99, 2024 346, 2025 326. The superseded 0005709 gave 1,226 (credentialed-run report
:322).

## Units (primary design)

There are 53,186 eligible cell-weeks, 1,139 of them positive. Only ISO weeks wholly inside
2015-01-01 to 2025-12-31 count (2015-W02 to 2025-W52, as T6 framed weeks under D101). This is a
builder choice, made so that no unit is part-cut by the year filter. The fold year is the ISO year.

Positives per fold: 2015 3, 2016 7, 2017 12, 2018 27 (all four under 30, so uninformative under
D33), then 2019 72, 2020 107, 2021 115, 2022 89, 2023 97, 2024 301, 2025 309.

## Builder choices (logged, not rulings)

- Precipitation for a unit is read at the ERA5 0.25° point nearest the 0.1° cell's centre, not
  the record's own position. Every unit in one cell then reads one rain series, which keeps the
  cell as the unit (D12, D19, D25). No cell centre is ever an exact tie on the 0.25° grid.
- Weather windows are computed by cumulative sums (`daily_grid.window_matrix`). A test checks they
  equal `weather_windows.window_features` on a fixture, and a second test checks no value from the
  scored date on is used. Revert check: shifting the window one day later failed both tests, with
  `assert False` at `test_daily_grid.py:45` and `:56`. The restore was from a saved copy, and the
  forward code was confirmed back (0 matches for the edited line, 3 passed).
- LightGBM runs deterministic, with 4 threads and seed 20260918.

## Calendar baseline: PENDING

## Equivalence test (D24): PENDING

## Weather model and comparison: PENDING

## Random-date comparison (D13, kept before Monday per RECORD -812): PENDING

## D33 (3) and (4): allowed after Monday (RECORD -812); PENDING

## Not checked: PENDING
