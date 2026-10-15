# PNW pilot, T1 on the Pacific Northwest box: build and run report (in progress)

**Status:** IN PROGRESS. The sections marked PENDING are not done yet. Nothing in this file is the
T1 result until the "Result" section says so.
**Branch:** `pnw-pilot-t1`, cut from origin/main `36cc647`.
**Orders:** Forager RECORD -806, -807, -811 and -812 (filed here as D123), and -809 ("a standing
model ready before Monday"). The owner's "Train as it downloads if you need to" was relayed by the
planner on 2026-10-10.
**Verify report:** `2026-10-10-pnw-first-fit-verify-report.md`, on branch `pnw-first-fit-verify`.

## Fixed before any fit or weather value (committed first)

- Tuning grid (D31): `2026-10-10-pnw-pilot-t1/tuning_grid.json`. It holds 20 configurations drawn
  with seed 20260918 from `t1_model.GRID`. The fit script refuses to run if the file and the draw
  differ.
- D24 equivalence sample and tolerance: `2026-10-10-pnw-pilot-t1/equivalence_spec.md`, commit
  `4d6e864`.
- D123 (the pilot ruling), commit `4d6e864`, where it was filed as D122. It was renumbered on
  2026-10-10 because D122 is the SCANFI edge ruling (`f0c6065`, RECORD -805), filed first.

## Weather pull

- Script: `scripts/pnw_cds_pull.py`. Data goes to `~/Zynergy/forecast-data-pnw-pilot/cds/`
  (/mnt/work), with each request's JSON beside its file (D52). The log is
  `~/Zynergy/forecast-data-pnw-pilot/pull.log`.
- Area: T1's PNW box first, then the rest of the union 40 to 49.5 N, 111 to 125 W (RECORD -812).
- Order and why: 2019 to 2025 first. These are the years D33 (1) calls the PNW's useful data, and
  they hold 1,163 of the 1,235 Cantharellus survivors. Then 2014 (the warm-up months), then 2015 to
  2018. The point is that a fit on arrived years covers most of the positives, as the planner
  suggested.
- First request: ERA5 precipitation for 2019 (a whole year, 335 KB) took 758 s from submit to
  file.
- The store caps queued requests per dataset. With 6 in flight on the ERA5-Land daily-statistics
  dataset, every extra request was rejected: "Number queued requests for this dataset is
  temporarily limited". The single-stream run had left its queued request (job 4ad790df) behind
  when it was stopped, and it counted against the cap; it was dismissed. The pull now runs 2 per
  dataset. A cap refusal waits 120 s and does not count as an attempt.
- Second route (the planner's builder choice, 2026-10-10): the hourly `reanalysis-era5-land`
  dataset, which has its own queue. It is aggregated to the daily-statistics definition (mean of
  the 24 UTC hours, `hourly_daily.daily_means`, tested; revert check bites). The daily route walks
  back from 2025-12. The hourly route takes the overlap month 2019-01, then walks forward from
  2014-09. Each route skips months the other has. The weather builder records the route per month
  (`land_route_by_month`). The overlap month is checked between routes with the equivalence
  tolerances (`scripts/pnw_route_overlap.py`).
- Measured by 18:51 UTC: the hourly ERA5-Land month 2019-01 (10.1 MB) took 516 s from submit to
  file, with 86 s of queue. The daily-statistics land jobs submitted at 18:30 had still not started
  at 18:51 (store job list). The cap behaves per user, about 5 queued (inferred from the hourly
  route's request being rejected while 5 derived jobs were queued).
- Restructured at 18:52 (`f2f5a9f`): the hourly route carries every T1 land month, newest first,
  with 2 in flight. The daily-statistics route keeps the yearly rain requests (`--precip-only`).
  The overlap month 2019-01 is pulled by both routes. Jobs the store already holds are adopted, not
  resubmitted (`cds_jobs.fetch`). Queued land jobs ea0cc73c and 7942cc54 were dismissed. The
  scoring coder's rain job d6ae24ed (2026-07 to 2026-10) is adopted into
  `cds/scoring-era5-precip-2026-07-10.nc` (`cds_adopt_job.py`).
- Several months cannot go in one request: both ERA5-Land forms take `month` as one string (store
  schema).
- Per-month timings after the restructure: hourly ERA5-Land months took 389 to 896 s each, with
  2 in flight, about 10 months an hour.
- Rain (owner, RECORD -826, "Hourly, checked against 2019 (Recommended)"): years the derived route
  had not delivered now come from hourly ERA5 single-levels `total_precipitation`. Day d is the
  sum of stamps d 01:00 to d+1 00:00 (`hourly_daily.daily_sums_previous_hour`, tested; the revert
  with no shift fails). The summing code and the tolerance (1e-5 m) were committed in `a5a981b`,
  before the comparison. Requests cover two years each: the store's limit is 121,000 fields and
  one year is 52,560 (`estimate_costs`), and three years were refused.
- **2019 check (`267e3ad`): passes.** 192,355 values (365 days × 527 points), largest difference
  0.0 m, NaN positions equal. Under the other convention (stamps 00 to 23), 97,562 values would
  fall outside the tolerance, up to 8.7 mm. So the check discriminates. Result:
  `2026-10-10-pnw-pilot-t1/precip_hourly_vs_daily_2019.json`.
- Incident: a commit line that failed lint still launched the rain pull, three times in all. Job
  adoption kept them to one queued job at the store. All three were killed and one restarted.
  Nothing was duplicated.

## Coastal cells with no ERA5-Land value (measured, not yet ruled)

On the 2019-01 land mask (2,387 of 3,116 box points carry values):
- 182 of 2,043 unit cells have no ERA5-Land value.
- 8,704 of 53,186 cell-weeks and 189 of 1,139 positives (16.6%) would be dropped as "sea" under B3.
- 163 of those cells have an ERA5-Land land point among their 8 neighbours. They hold 188 of the
  189 positives.

The options went to the planner for the owner. Nothing has changed yet.

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

## Corrections to commit messages (append only; the commits are not amended)

- `9060ea6` names "3b0c0b1" as the commit where the weather builder started reading the hourly
  route's files. That hash was written without being checked. The next commit's message corrects
  it to "4f...", which is also unchecked and wrong. The commit is **`e2865eb`** ("weather builder
  reads both ERA5-Land routes", read from `git log`).

## Queue decisions (planner's go, option (c), 2026-10-10)

- At 20:20:10 UTC the two derived daily-statistics jobs were dismissed. Both had been accepted and
  never started:
  - `d6ae24ed-c8b4-428a-ae21-cf65e9f47b3e`: the map's 2026 rain, submitted by the scoring coder.
  - `8f202c97-fc95-4a8b-980d-2bc996fe7199`: rain 2025.
  Their data comes by the verified hourly routes: rain 2025 in the hourly rain chunks, and the
  map's months through `--scoring` (`61f9bf6`). The processes that waited on them were stopped.
- Hourly ERA5-Land restarted with 4 workers at 20:20. It adopted its 2 in-flight jobs. Once the
  remaining rain chunks are in, the rain worker's slot goes to land as well.
- Why: per-job time rose from 389 to 896 s to about 1,860 s per month (20:02 to 20:06 UTC). At 2
  in flight the land pull projected about 31 h.
- Route check for land: if no derived land month can be had before the fit, D24's equivalence
  comparison (hourly ERA5-Land aggregated by this code, against Open-Meteo's ERA5-Land daily
  values, within RECORD -818's restated tolerance) stands in for the route agreement check, as the
  planner set. One derived land month is still tried if a slot frees and the derived queue moves.

## Early partial equivalence (one span, 21:50 UTC; labelled partial)

Run on the spans whose land and rain had both arrived. That was one span (cell 492_-1246, from
2019-01-08), because rain 2021-24 was not yet aggregated. Three spans of one cell (427_-1245)
were skipped as a sea point. File: `2026-10-10-pnw-pilot-t1/equivalence_early_partial_2110Z.json`.
The file name says 2110Z; the run was at about 21:50 UTC.

- Hourly land route: offset 0 matches 192 of 192 hours for 2 m temperature, soil temperature and
  soil moisture alike. Offsets −1 and +1 match 32 to 103 of 192. So the best offset is 0 on all
  three. Partial pass, one span.
- Daily (reported, not the gate): 27 of 28 values within bounds. Rain on 2019-01-08 was 11.36 mm
  in the store against 9.3 mm from Open-Meteo (2.06 mm, over the 1.25 mm bound). That matches the
  scoring coder's finding that Open-Meteo's rain runs 4 to 8% below the store's, which led to
  RECORD -819.
- Rain convention test (7 days): the store is closer to Open-Meteo's hours 01 to 24 on 4 days and
  to 00 to 23 on 3. Mean absolute differences are 0.33 and 0.69 mm.
- The re-fetched hourly months (2025-03, -04, -07, -12) came from the store's existing successful
  jobs, adopted in seconds. Their daily aggregates equal the originals exactly.

## Review notes folded in (pnw-pilot-t1-review `d2655e9`)

- **N13.** The one rain day 18% low in the early check is consistent with the scoring coder's
  4 to 8% finding. It is not a measure of it. The summed rain ratio over every compared day is now
  reported (`rain_level`, S6). It was 0.974 over the 7 days compared so far.
- **N14.** In fits on 2019 to 2025, the early-2019 units whose windows reach into 2018 are dropped
  as `missing_days` if 2018 has not arrived. They are counted in `weather_units_dropped`. The hedge
  run waits for 2018-10 onward and rain 2018, so none should drop there.
- **N8.** The coastal cells that read a land neighbour (RECORD -822) are listed in every fit
  summary (`weather_units_dropped.neighbour_cells`). The equivalence result lists those it compared
  (`hourly_land_route.neighbour_cells_compared`).
- **N9.** For an adopted job, `requested_at_utc` is the time it was adopted, not the time it was
  first submitted. `adopted_job` names the job, and the store's job record holds the submit time.
  Stated in `pnw_cds_pull.py`'s docstring. D52 asks for the request's time; this records the time
  this pull took it up.
- **N1.** The docstring said the request is stored before the file is fetched. It is stored after.
  Corrected.
- **N3/N4. Traced.** Reading D26's zip by raw coordinates, 252,822 rows fall in T1's PNW box. That
  is D72's predicate count. 4 of them are rows the loader refuses ("eventDate spans more than one
  day", D66). 252,822 − 4 = 252,818, the `records_in_pnw_box` figure. Script `/tmp/pnwp_n4.py`,
  run once, not committed.

## Third land route: the store's point time series (2026-10-11, builder's choice)

- **Why.** From the store's job list: this account's gridded ERA5-Land jobs ran one at a time,
  about 4 to 5 min each, after 20 to 100 min in the queue. That gave 2 to 3 months an hour, with
  about 30 h left at 00:30 UTC.
- **What.** `reanalysis-era5-land-timeseries` serves one point for the whole period. The form takes
  `location` and `date`; the process description lists only `area`, and requests by `area` failed
  with MultiAdaptorNoDataError. One request per land point covers 2014-09-01 to 2025-12-31 and all
  three variables. The reply is a zip of three NetCDF files, 3.6 MB, in about 29 to 40 s.
- **Same product, checked.** At 47.0, −123.0 its hourly values equal the gridded hourly files on
  all 50,472 compared hours (every gridded month held then): largest difference 0.00025 K for the
  two temperatures and 0 for soil moisture (float32 packing).
- **Points.** 1,870: every ERA5-Land point a T1 unit reads (its own, or its RECORD -822 neighbour,
  on the land mask of the delivered 2019-01 file), plus the equivalence sample's 12 points, whose
  hourly zips are kept for the hourly land-route check. Daily means use the same 24-UTC-hour
  definition (`hourly_daily.daily_means`).
- **Assembly.** `scripts/pnw_ts_assemble.py` writes one gridded daily file. The builder reads it at
  the lowest precedence, so gridded months win where both exist (tested; the revert check bites).
  `land_route_by_month` names the route per month.
- **Pace.** With 4 in flight, 31 points in 7 min, about 265 an hour. At that rate the pull ends
  about 07:45 UTC Sunday.
- **Gridded jobs dismissed.** fb28d705, bc01764e and 311e6e4c at 00:40:39 UTC; ed826b8b (2023-06)
  at about 00:36 to free a slot for the probe. The 30 gridded months already delivered stay in use.

## Gate override and the fits (2026-10-11, Forager RECORD -854, -855)

Dispatch: `docs/dispatch/2026-10-11-pnw-pilot-gate-override-restart.md` (0eba532). Base verified
against the remote: `ae4f1e9` plus that dispatch commit only. Code for the run: `7d19c66`. Every
fit and model below records commit `7d19c66` and `working_tree_dirty: false`.

**The gate: failed, and the fail stands.** The hourly land-route check (`land_route_pass`,
`scripts/pnw_equivalence.py:70`) failed in all four runs: the two that stopped at 14:17 and 14:19
UTC, and the two rerun inside this chain at 15:28 (hedge) and 15:44 (main). Each time t2m at
offset 0 matched 6,911 of 6,912 hours. stl1 and swvl1 matched 6,912 of 6,912 hours. In t2m,
offset −1 matched 762 hours and offset +1 matched 675; in stl1, 2,356 and 2,218; in swvl1, 4,149
and 4,133. 36 spans were compared and none was skipped. The only sea-adjacent cell compared, at its
RECORD -822 neighbour, was 427_-1245. The hedge run compared all 25 of its 25 required spans.
`pnw_equivalence.py` is byte-identical to `ae4f1e9`. Its `"pass": false` is in
`equivalence/equivalence.json` and `hedge/equivalence/equivalence_partial.json` as written.

**The one failing hour, reproduced with code written for this check** (`scripts/pnw_land_route_failures.py`,
903a170). The code reads only cached responses and re-reads each failing value straight from its file.
- **Hour:** t2m, cell 493_-1250, its own land point [493, −1250], 2025-12-12T11:00 UTC.
- **Store:** 5.424951 °C (278.574951 K, `hourly-era5land-2025-12.hourly.nc`).
- **Open-Meteo:** 5.5 °C.
- **Difference:** 0.0750488, against the bound 0.075 + 1e-6.
- **Same hour in both runs.** It is the only failing hour in either run
  (`docs/audits/2026-10-11-gate-override/land_route_failures_{hedge,main}.json`). The main and
  hedge runs fetched separate copies of the 39 responses, and the copies differ only in
  `generationtime_ms`.
- **Observed, bearing on the rounding explanation:** the other Copernicus route (the point time
  series) gives 278.575012 K = 5.425012 °C for the same point and hour. That is just above the
  5.425 midpoint, and against it the difference would be 0.074988, which passes. The two routes
  straddle the midpoint at exactly this hour. How Open-Meteo rounds was not read. RECORD -854 asks
  the reviewer to check that independently.

**The override** (`scripts/pnw_gate_override.py`, 7d19c66). This is a separate step after the gate.
- **What it does:** the run scripts take `--override "Forager RECORD -854"`. The step writes a gate
  record: `gate_record.json` (main) and `hedge/gate_record.json`.
- **When it goes on:** only when the override is exactly that string, every required span was
  compared, and the failing hours agree with the run's own offset-0 counts and are exactly the
  ruled hour.
- **When it stops (exit 3):** in every other case, and always when no override is given.
- **Override with a passing gate:** recorded as unused.
- **Fits:** every fit summary and every `model.json` carries the record as `land_route_gate`. That
  covers `gate_pass: false`, the override text and the failing hour with both values, including
  `models/primary_t1_1000m_full/model.json`.
- **Decided beyond the dispatch's letter:** binding the override to the ruled hour.
- **Tests:** 11 tests, run through the command the scripts call. The suite is 458 passed.
- **Revert check:** I changed the no-override branch to go on, after saving a copy. The run
  collected cleanly (10 passed, 1 failed). The only failure was
  `test_a_fail_with_no_override_stops_with_exit_3` at `assert code == 3`. I restored from the
  saved copy, confirmed it with cmp, and the tests went back to 11 passed.

**The D24 daily comparison (reported, not the gate, RECORD -819).**
- **Result:** 30 mismatches of 1,008 compared values, all precipitation. Earlier dispatch text gave
  20; that was the length of the first-20 list (RECORD -855).
- **Largest differences:** temperature 0.056 °C, soil temperature 0.068 °C, soil moisture 0.0003,
  rain 5.005 mm.
- **Summed rain:** Open-Meteo / store = 0.982 (1,251.7 mm against 1,274.4 mm).
- **Rain convention:** over 252 days, the store is closer to Open-Meteo's hours 01–24 on 92 days
  and to hours 00–23 on 24 days; 136 days tie. The mean absolute differences are 0.107 and
  0.455 mm.

**Primary design, all years, 2015 to 2025: the T1 result** (`fits/primary_t1_1000m_comparison.log`).
- **Units:** 52,718 cell-weeks, 1,138 positive, 2,024 cells.
- **Weather drops:** 468 units were dropped as sea points (1 of them positive). Of the units kept,
  44,482 read their own land point and 8,236 read a RECORD -822 neighbour (188 of those positive).
- **Brier:** calendar 0.02061, weather model 0.02068.
- **Pooled Brier skill against the calendar:** **−0.004** (−0.0035). Its 95% interval, from 1,000
  resamples of cells, is **−0.0066 to −0.0001**.
- **Verdict (script):** "worse". The whole interval is below zero, so under D33 (5) this is not
  "not shown": the weather model scored worse than the calendar on held-out years. The upper end is
  0.0001 from zero.
- **AUC:** calendar 0.792, weather model 0.783.

| Year held out | Positive cell-weeks | Brier skill against the calendar | Informative? |
|---|---|---|---|
| 2015 | 3 | 0.0173 | no |
| 2016 | 7 | −0.0125 | no |
| 2017 | 12 | −0.0202 | no |
| 2018 | 27 | −0.0189 | no |
| 2019 | 72 | −0.0093 | yes |
| 2020 | 107 | 0.0015 | yes |
| 2021 | 115 | 0.0027 | yes |
| 2022 | 89 | 0.0048 | yes |
| 2023 | 97 | 0.0080 | yes |
| 2024 | 300 | −0.0063 | yes |
| 2025 | 309 | −0.0080 | yes |

Top features by gain in the weather model: doy_sin, longitude, latitude,
soil_temperature_mean_90d, precipitation_sum_42d, precipitation_sum_3d, soil_moisture_mean_90d.

**Random-date design (D13; a comparison only)** (`fits/secondary_t1_1000m_comparison.log`).
- **Units:** 16,042, 1,234 positive, 504 cells; 13 units dropped as sea points.
- **Skill:** −0.0022, interval −0.0075 to 0.0031.
- **Verdict:** "not shown".
- **AUC:** calendar 0.793, weather model 0.804.

**The 2019–2025 hedge (PARTIAL, not the T1 result)** (`hedge/fits/comparison.log`).
- **Units:** 49,235, 1,089 positive.
- **Skill:** −0.0029, interval −0.0073 to 0.0011.
- **Verdict:** "not shown".
- **Its model:** `models/primary_t1_1000m_full_years_2019_2025`.

**Scoring models.**
- **`models/primary_t1_1000m_full/model.json`:** written 15:58:06 UTC, config c10, years 2015 to
  2025. It holds `copernicus_sources` (era5_daily_sum, era5_hourly_precipitation, era5_land_hourly,
  era5_land_timeseries) and `land_route_gate`.
- **Other models carrying the gate record:** `secondary_t1_1000m_full` and the hedge model.

**D33 (3) and (4): not run.**
- **What happened:** `pnw_t1_run_all.sh extras` started at 16:54:20 UTC. Its first fit (5,000 m
  list, calendar) refused at 16:54:23: "weather missing for 22 units (months not pulled)".
- **Why:** the 22 units sit in 21 cells that are in the 5,000 m list but not the 1,000 m list. The
  time-series pull fetched only the points the 1,000 m list reads
  (`pnw_cds_timeseries.points_needed` reads `t1_1000m.csv`). So these 21 points have land
  values only in the 29 gridded months, and each of these units' windows reaches some of the
  other 107 months.
- **D33 (4) (the CC0/CC BY list):** has no missing units. It was not reached, because the extras
  loop stops at the first failure.
- **Chain log:** recorded no failure line. A copy with an ERR trap that writes one is now
  `scripts/pnw_override_chain.sh`.
- **My error:** my own wait loop matched its own command line (`pgrep -f override_chain.sh`), so I
  did not see the stop. The independent reviewer found it.

**Not checked.**
- Open-Meteo's rounding (for the reviewer, RECORD -854).
- The time-series route's values at any other hour of the sample.
- Whether the "worse" verdict is robust to the bootstrap seed. One seed was used, as fixed.
- The two D33 runs.
- Scoring with any of these models, publishing, the map: these belong to other dispatches.

### D33 (4): CC0 and CC BY records only (run 2026-10-11 17:19 to 17:35 UTC)

- **How it ran:** on the planner's call after RECORD -861, alone, through the same commands as
  `pnw_t1_run_all.sh extras` (driver `d33_4.sh` in the data folder, with an ERR trap). It ran
  under the 5G cap at commit fa6e89e with main's gate record. The fit summaries and
  `models/primary_t1_1000m_cc_full/model.json` carry `land_route_gate` (override used, the
  2025-12-12T11:00 hour).
- **Data:** primary design, all years. 9,689 units, of which 49 were dropped as sea points.
  9,640 units kept, 102 positive, 1,152 cells.
- **Brier:** calendar 0.01040, weather model 0.01040.
- **Skill against the calendar:** −0.0006, interval −0.0058 to 0.0049.
- **Verdict:** "not shown". `pnw_t1_compare.py` labels any all-years run "T1 result"; this is the
  D33 (4) sensitivity run, not the headline.
- **AUC:** calendar 0.793, weather model 0.772.
- **Per year:** only 2024 (30 positives) is informative. The other years have 0 to 24 positives:
  2015 0, 2016 1, 2017 4, 2018 2, 2019 6, 2020 11, 2021 11, 2022 9, 2023 4, 2025 24.

### D33 (3): waiting on the 5,000 m list's points

`scripts/pnw_cds_timeseries.py --lists t1_1000m,t1_5000m` (ffd5b88) would request 34 points:
1,904 against the 1,870 on disk. 21 of them carry the 22 units that lack weather. The other 13
are 5,000 m cells whose windows lie inside the gridded months, which take precedence, so those 13
change no value. All 34 are to be pulled (planner's call). The land mask comes from the gridded
months, which already cover every land point, so no neighbour choice changes. No request has been
made. It waits until the scoring pull finishes.

### D33 (3): the 5,000 m list (run 2026-10-11 22:41 to 23:44 UTC)

This supersedes the "waiting" note above, which stays as written. Driver: `d33_3.sh` in the data
folder (ERR trap; this run did not fail, so its FAILED line has still not fired in a real run). Run
under the 5G cap at commit f73b800, with main's gate record.

- **Pull:** started 22:41:08 UTC, with `--lists t1_1000m,t1_5000m` and 4 in flight. It finished at
  22:55:42: "1904/1904 points done, 0 gave up". 34 new points, one request each.
- **Check against the gridded months:** 1,904 points, 0 failed, 5,049,408 values compared. It now
  reads 33 gridded files, because the scoring pull's four 2026 months (2026-07 to 2026-10) are in
  the same folder. Assembly: 1,904 points, none left out.
- **Weather, its own file** `weather/t1_pnw_d33_3.npz`; `t1_pnw.npz` is untouched. I compared the
  two files on every point and day they share: they are identical (largest difference 0.0, no
  value lost). The new file fills 110,704 more land point-days for each of the three land
  variables, and none for rain.
  - Its summary also lists the four 2026 land months and a 2026 rain route. Both are outside the
    file's day axis, which ends 2025-12-31 (4,140 days), and no unit reads them.
- **Units:** 57,418 before weather, 491 dropped as sea points (1 positive), 56,927 kept, 1,365
  positive, 2,060 cells, 8,826 of them reading a RECORD -822 neighbour. The 22 units that refused
  at 16:54 are all kept (56,905 + 22). No unit was dropped for missing weather.
- **Brier:** calendar 0.02267, weather model 0.02285.
- **Skill against the calendar:** **−0.0080**, interval **−0.0120 to −0.0044**.
- **Verdict (script):** "worse". The whole interval is below zero, the same direction as the
  1,000 m primary result.
- **AUC:** calendar 0.802, weather model 0.785.
- **Per year** (* = under 30 positives, uninformative): 2015 6* −0.0155, 2016 10* 0.0103,
  2017 17* −0.0040, 2018 32 −0.0194, 2019 91 −0.0161, 2020 133 −0.0098, 2021 145 −0.0021,
  2022 108 −0.0132, 2023 121 0.0034, 2024 354 −0.0074, 2025 348 −0.0105.
- **Model:** `models/primary_t1_5000m_full/model.json` carries `land_route_gate` and
  `copernicus_sources`.
- **Not checked:** whether the 13 extra points' time series (windows wholly in gridded months)
  agree beyond the time-series check above.
