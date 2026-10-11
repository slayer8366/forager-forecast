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
