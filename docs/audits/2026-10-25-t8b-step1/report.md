# T8b step 1 report

**Written by Ash Transect (forecast coder); saved by the forecast planner (Alder Bearing).** The step-1 dispatch
said the planner would save Ash's hand-back as this file, as the owner allowed for the T6b check (forecast RECORD
2026-09-28-2057). Everything below the line is Ash's hand-back, word for word. The planner changed only the first
heading level.

---

## T8b step 1 report (Ash Transect): rules, code and tests, with no real outcome read; pulls priced

Branch `t8b-build`, final pushed commit **f949a05f9d34c2c7f20198696b8a0fc07c2bb69d**. I confirmed it with `git ls-remote origin t8b-build`, which returns that hash. Commits:
- dafb2b6: tests over stubs
- 159996f: code
- fcaf664: evidence
- f949a05: revert logs

Evidence is in `docs/audits/2026-10-25-t8b-step1/`. No PR was opened; the dispatch didn't ask for one.

Marking: **[R]** read at file:line or at source, **[C]** computed by a named script or command, **[I]** inferred.

## Wrong premises, and stops for the owner

1. **C5 can't take its rain from Daymet V4 R1 in February 2027.** This is a stop; I did not choose.
   - [R] The V4 R1 release record has added each year's data months later: 2022 on 1 March 2023, 2023 on 23 April 2024, 2024 on 12 September 2025, 2025 on 22 May 2026 (user guide; `source-checks.txt`).
   - [R] The dataset page says "Each subsequent year is processed individually at the close of a calendar year."
   - [I] 2026's data will arrive somewhere between March and September 2027.
   - [R] The plan's "monthly latency" belongs to a different product, Daymet V4 Monthly Latency (ds 1904). Its guide says it "should be considered provisional and still likely to change". `DATA_REGISTER.md:10` links that product's guide.
   - Options for the owner:
     - (a) Score C5 once V4 R1 2026 is out.
     - (b) Take 2026's M1 and M2 from the provisional product. That is a different product from the one the model trained on.
   - The C5 scorer takes arrays, so it works under either option.
2. **Daymet's box subsets now need an Earthdata Login, and this laptop has none.** This is a stop: creating an account means accepting terms (coder profile, "needs an agreement signed").
   - [R] The documented subset address (thredds.daac.ornl.gov/thredds/ncss/...) now redirects with a 301 to `opendap.earthdata.nasa.gov`, which sends a 302 to `/login/urs`.
   - [R] A metadata request (`.dmr.xml`) returned 401.
   - [R] There is no `urs.earthdata.nasa.gov` entry in `~/.netrc`.
   - [R] The full-file address answered a HEAD request without login: 200, 3,955,194,385 B. I made no GET there, so whether a download needs login is unchecked.
3. **The Daymet licence isn't "Public domain" in those words** (`DATA_REGISTER.md:10` says it is).
   - [R] The dataset page says "openly shared, without restriction, in accordance with the EOSDIS Data Use and Citation Guidance".
   - [R] That guidance says: "Unless the content is marked with a use restriction or license, data provided from a NASA-led mission are licensed as ... CC0."
   - [R] For the 2024 and 2025 files, the guide names an input licence: Environment and Climate Change Canada's open-data licence, covering the Canadian station data. No page I read says whether it carries over to Daymet's output.
   - This is a licence reading for the owner before any pull.
4. **Daymet's Canadian inputs changed in exactly 2024 and 2025.** [R] The guide says that for those years, Canadian station files came from CCCS and that "GHCNd station data labeled with the prefix CA0 were not included". That is the jump's two years and the box's Canadian part. [I] It's the same kind of between-fold source change the plan used to rule out HRRR. Flagged for the planner; nothing in the code depends on it.
5. **Daymet drops 31 December in leap years** [R] (guide, "The Daymet Calendar"). Under T8's rule, any window touching 2016-12-31, 2020-12-31 or 2024-12-31 would be refused, and the units can't change (D159 (1)). I built this as PENDING B-daymet-leap, proposing that a window counts Daymet days.
6. **The pull start date.** [C] The week-late 56-day window for Monday 2014-12-29 (ISO 2015-W01) starts on 2014-10-27, before the plan's "2014-11". This is PENDING B-pull-start, proposing a start of 2014-10-01. [I] It matters only if T1 has units in that week; I didn't read the units.
7. **C5 has no code path for 2026 effort or for a 2026 calendar.**
   - [R] `effort_term.py` refuses any week outside T6's frame, which ends in 2025 (the frame check sits just above `fold_effort`).
   - [R] T1's stored calendar predictions are held-out predictions for 2015–2025 only.
   - Both are PENDING (C5-effort, C5-calendar), as the dispatch asks.
8. **A minor citation.** [R] The plan cites `hourly_daily.py:33` for "top 7 cm only", but line 33 is a length check. Layer 1 is named at `hourly_daily.py:12-13` and `scripts/pnw_cds_pull.py:11-12`.

Base: [R] `t8b-build` is 5569780 (t8b-plan) plus the two dispatch commits. main is 98d4b33. T8's code is present.

## Items 1 to 7

**1. The measures** [R][C]: `src/forager_forecast/t8b/{design,daymet,era5land,measures,clamp}.py`
- **D159's five measures** are in `design.py` MEASURES. They reuse T8's `Measure`, seed, timings and bar constants by import, not by copying.
- **Daymet** (`daymet.py`) reads the delivered layout: `prcp[time,y,x]`, 2-D lat/lon, days since 1950 at noon, fill value.
  - It streams a chunk of days at a time.
  - **Cell mapping** (PENDING B-daymet-cell): a cell is the mean of the 1 km pixels whose centre falls in it by D46 (`cells.cell_for`). Pixels with no value on any day are off the land mask and left out. A pixel with values on some days but not all is refused.
  - **Water cells** (B-daymet-no-land): the nearest of the 8 neighbouring cells that has pixels, by `coastal.land_point` (-822's rule, reused). With none, the unit is refused.
- **ERA5-Land** (`era5land.py`) reads daily-statistics files, or hourly files reduced by `hourly_daily.daily_means`.
  - A file without `swvl2`, `stl2`, `t2m` and `d2m` is refused by name, so a layer-1 pull can't pass for layer 2.
  - M5 is daily mean t2m minus daily mean d2m.
  - **Water points** use T8's -822 path unchanged (`measures.unit_points` → `coastal.land_point`).
- **Windows**: land measures use T8's `weather.window_values`. Every window ends the day before the week, the week-late timing ends 8 days before, and nothing is filled. `measures_for_units` refuses any unit with a missing window and names the count.
- **The clamp** (`clamp.py`) limits each measure to its fold's training range. [I] It changes no tree prediction, because trees split only between training values. It does bite in the additive model.

**2. The models** [R]: `t8b/models.py`
- `loyo_trees` is T8's challenger form: day-of-year sine and cosine, latitude, longitude, effort, then M1 to M5, clamped per fold. Each fold is tuned by `t1_model.inner_choice` over T1's 20 configurations. `fixed_choice` holds that tuning for the swaps.
- The no-weather twin is the same with `use_weather=False`.
- `loyo_readable` is T8's additive model (`design_matrix`, `fit_predict_logistic`, the specification D136 ruled) on the clamped measures.

**3. The bar and C5** [R]
- `bar_run.tree_bar` calls T8's own `bar.evaluate_bar` unchanged: C1 to C4, 1,000 resamples, seed 20260918, 199 swaps. Tuning runs once per fold, and the swaps refit at that choice. `measure_shuffle` covers the per-measure shuffles.
- `frozen.py` fits on all eleven years and saves a sorted-key JSON file holding LightGBM's model text, the configuration and the clamp range. `save` returns the file's sha256 and refuses to overwrite. `load` refuses a sha256 that differs from the recorded one.
- `c5.py` refuses:
  - an unruled reading;
  - a download created before 2027-02-16T00:00Z;
  - any unit outside ISO 2026 weeks 27 to 52.
  It leaves out and names any `excluded_weeks`, and reports the skill with its interval.

**4. The jump check** [R]: `t8b/jump_reporting.py`. The plan section 3 rule runs on totals passed in. A move of a third is tested exactly, with fractions. Tests use made-up totals only; I queried no total.

**5. The pull list** [R] unless marked. Storage would be `/mnt/work/Zynergy/forecast-data/t8b/` (8.9 GB free at the end of this session) or the flash drive at `/run/media/zynergy-labs/forecast-data` (54 GB free, holding only `lost+found`).

- **Daymet V4 R1 `prcp`**, ds 2129, 2014-10-01 to 2025-12-31, files 2014 to 2025.
  - *Box subset by NCSS*: `.../thredds/ncss/ornldaac/2129/daymet_v4_daily_na_prcp_<yyyy>.nc?var=lat&var=lon&var=prcp&north=49.5&west=-125.0&east=-121.0&south=42.0&disableProjSubset=on&horizStride=1&time_start=...&time_end=...&accept=netcdf`
    - Size [C] (`daymet_box_grid.py.txt`): an LCC bounding box of 504 × 848 = 427,392 pixels, 236,415 of them inside the box. Over 4,110 days that is 7,026,324,480 B as uncompressed float32. [I] netCDF-4 output would be smaller; I couldn't size it, because the service needs login.
    - Checksum: none from the publisher. The check would be dimensions, days and the land mask, with sha256 taken at receipt.
    - Blocked by premise 2.
  - *Full North America files*:
    - Size: 12 files, 49,577,188,346 B in total [C, from CMR].
    - Checksum: each file has a publisher SHA-256 in CMR (`daymet-cmr-prcp-2014-2025.txt`).
    - The total fits only on the flash drive.
- **ERA5-Land**, licensed CC BY 4.0. [R] Both store catalogue entries link "CC-BY licence" to SPDX CC-BY-4.0.
  - Variables: `volumetric_soil_water_layer_2`, `soil_temperature_level_2`, `2m_temperature`, `2m_dewpoint_temperature`. Area [49.5, -125.0, 42.0, -121.0], 2014-10 to 2025-12.
  - *Daily route*: `derived-era5-land-daily-statistics`, daily_mean, utc+00:00, 1_hourly, 135 monthly requests. The store's costing endpoint gives 124 of a 400 limit per month [R]; that is request units, not bytes. Size [I]: about 75 to 200 MB.
  - *Hourly route*: `reanalysis-era5-land`, costing 5,952 of 12,000 per month [R].
    - Size [I]: about 1.78 GB, from the W41 file of 10,045,033 B for 3 variables × 744 hours × 3,116 points (`pnw-pilot-scoring` request JSON).
    - Time [I]: about a week if run one request at a time, since W41's months each took 4,516 to 4,880 s.
  - Checksum: the store publishes `file:size` and `file:checksum` (MD5) [R, pnw-pilot-w42 commit e6c855d].
- **CEC Level III ecoregions**, licensed CC BY 4.0 [R]. The metadata says "This material is licensed under CC BY 4.0, allowing ... commercial purposes, so long as attribution is given to the creator", and the Terms of use document agrees.
  - HEAD: 200, 35,236,046 B, the same ETag as `docs/pulls/t6b-cec-terrestrial-ecoregions-l3.request.json`.
  - The check after download is sha256 a99b4967…3338.

Every request I made, with URL and UTC time, is in `source-checks.txt`. That covers the HEAD and costing requests, the catalogue and licence pages, and the 48,977 B CEC `metadata.zip`, which holds the licence document only.

**6. No 2026 outcome read.** [R] This confirms the plan's inference. A read-only subagent read all five pilot branches with git, and I re-read its key citations.
- The W41 and W42 scripts read only 2026 ERA5-Land and ERA5 weather.
- The only use of records is in `pnw_pilot_score.py:137-138` and `:305-310`: it checks the download key named in T1's 2015–2025 `records_summary.json`.
- Every GBIF predicate in `docs/pulls` has YEAR ≥ 2015 and ≤ 2025 (e.g. `gbif-fungi-us-canada-2015-2025.doi.json:37-44`).
- "Scored" in those branches means predictions were computed, never compared with outcomes.
- **Weeks with a 2026 outcome read: none**, so C5 leaves out no weeks.

**7. Compute**
- [R] `/mnt/work/scratch/t8-fit/runner.log:13-19`: T8's challenger has the same shape as T8b's main bar (tuned per fold, then 199 swaps at fixed tuning). It ran 56 min 29.7 s wall, 3 h 53 min CPU on 4 threads, with a peak of 862.3 MB.
- [I] T8b's main bar should take about 1 h at under 1 GB, and the week-late timing about 1 h more.
- [I] The per-measure shuffles are 5 × 199 swap passes, about 4 to 5 h.
- [I] The readable model takes minutes.
- **Needs a measured trial before the fit word:**
  - (a) `read_daymet` on one real year's subset, for time and peak memory. This is the only new heavy input step, with 427k pixels a day.
  - (b) One tree swap pass at real size with M1 to M5, to price the 199 swaps and the 5 × 199 shuffles.

## PENDING readings, each with its proposal

All are in `t8b/design.py` PENDING. RULED is empty, so the fit, C5, count and pull steps refuse to run.

1. **B-daymet-cell**: mean of the land pixels whose centres fall in the cell.
2. **B-daymet-no-land**: the nearest neighbouring cell by -822's rule; none means refused.
3. **B-daymet-leap**: count w Daymet days (one calendar day further back across a dropped 31 December).
4. **B-daymet-day**: Daymet's day d is calendar day d, unshifted.
5. **B-pull-start**: pull from 2014-10-01.
6. **B-clamp-range**: under a swap, the clamp range comes from the training rows of the swapped weather. For trees this changes nothing.
7. **B-forecast-bar**: as D136's M-forecast-bar.
8. **B-measure-shuffle**: the full tree model with only that measure's column swapped, tuning fixed.
9. **B-ecoregion**: as D136's M-ecoregion, with trees tuned leave-one-block-out. Not built.
10. **C5-beats**: pooled skill > 0, interval reported but not required.
11. **C5-frozen-fit**: refit on all 2015–2025 units, inner leave-one-year-out over 11 years.
12. **C5-calendar**: T1's calendar form refitted on all 11 years and frozen beside the model.
13. **C5-effort**: the all-years surface at 2025's level, with the frame extended to 2026 by season slot.
14. **C5-units**: T1's steps on the C5 download, ISO 2026 weeks 27 to 52.
15. **C5-after**: the download's GBIF `created` time is on or after 2027-02-16T00:00Z.
16. **R-share-move**: a relative change, |s1/s0 − 1| > 1/3.
17. **R-years**: 2023 to 2024 only, as written (D134 took both years for T8).
18. **R-accuracy**: at most 1,000 m, out of all records.
19. **R-licence**: CC0, CC BY and CC BY-NC.
20. **R-grade**: research grade only.

## Tests

- **Before:** 695 passed (`tests-before.txt`).
- **Over stubs:** 53 failed and 10 errored, all 63 for their own reason (62 NotImplementedError, 1 missing validation) (`tests-over-stubs.txt`). 9 design tests passed over stubs because they read real constants; the M3 revert below shows they bite.
- **After:** 767 passed, 72 of them new (`tests-after.txt`). `ruff check .` and `ruff format --check .` are clean.
- **Revert checks:** 16 single-edit reverts, one per guarded rule, all bite (`revert-summary.txt`, `revert_checks.py`, `revert-logs/`). They cover:
  - the clamp three ways (tree, additive, function);
  - the window ending the day before the week;
  - the leap-day rule;
  - M5's definition;
  - M3's window;
  - swaps holding the tuning fixed;
  - the frozen checksum;
  - C5's weeks, cutoff date and ruling refusal;
  - the jump rule's third and its all-fungi condition;
  - never filling;
  - the partial-pixel refusal.

  How the runner works: each revert edits a fresh copy, never the worktree. The import log shows the copy was imported, and the logs show no collection or import error. Each failure names its own test. The worktree's 137 files hash the same before and after.
  The logs were renamed from `.log` to `.log.txt` because `.gitignore` ignores `*.log`. After a ruff reformat I re-ran the runner, so the committed version is the one that ran.

## What I couldn't check, and calls beyond the dispatch

- **Not checked:**
  - Any real Daymet or ERA5-Land file: whether real deliveries match the layouts I built from the guide and from T1's readers.
  - netCDF-4 subset sizes, and the daily-route size.
  - Whether a full-file GET needs login.
  - Whether T1's units include 2015-W01.
  - Whether T8b's land points equal T1's `land_point` (inferred yes: same land mask).
  - Ecoregion code for trees.
  - The glue that turns real files into fit inputs (a T8b equivalent of `fit.prepare` / `scripts/t8_fit.py`): not built, beyond the dispatch's items.
  - The frozen-model clamp in `predict`: can't be shown to bite through trees. The test checks the stored range instead.
- **Calls beyond the dispatch:**
  - One read-only subagent did item 6.
  - The C5 scorer leaves excluded weeks out rather than refusing them, as the plan says.
  - Scratch, the venv and the uv cache were deleted at the end.
