# PNW pilot scoring: live weather, scoring, map files (report, in progress)

Written 2026-10-10 from 18:45 UTC, on branch `pnw-pilot-scoring`. The branch was cut from
`origin/pnw-pilot-t1` at 5a527b7 and merged `origin/pnw-pilot-t1` at 5fd4ce7 (merge 5919dad).
The task is the scoring coder's dispatch for the owner's target in Forager RECORD -814, "Prototype
map is the target". The planner's rulings during the session are Forager RECORD -818 (score
2026-W41), -819 ("Copernicus for both (Recommended)") and -820 (the rain lead). This is a builder's
report. Nothing in it has been reviewed.

## What was built

| File | What it does |
|---|---|
| `src/forager_forecast/live_weather.py` | Holds the box's cells (3,116), the window span for a week, the batched Open-Meteo archive URL with the same pins as `open_meteo.archive_request_url`, the call cost by the pricing-page rule, a rolling minute, hour and UTC-day budget, and response-to-cell matching that refuses a mismatched grid point |
| `scripts/pnw_pilot_fetch.py` | Resumable Open-Meteo fetch. Writes a plan, a ledger of every request (time, cost, status, sha256) and each body with its request beside it. A rate-limit answer stops it (exit 3) |
| `src/forager_forecast/pilot_output.py` | Turns Open-Meteo bodies into `pnw_weather`'s npz layout (rain keyed by the nearest ERA5 point, with a check that cells sharing a point agree). Checks units and value ranges. Builds D55's cell features, 1 degree blocks, polygons and drivers |
| `scripts/pnw_pilot_score.py` | Loads the builder's model (model.txt, model.json feature list) and builds features with the training code itself (`pnw_t1_fit.calendar_matrix`, `pnw_weather.weather_matrix`). Refuses a model whose feature list differs. Writes the combined GeoJSON, the block files and the manifest, then searches every output for the D58 terms. Weather source is one of Open-Meteo, Copernicus npz, or none (calendar floor, land mask from the store) |
| `scripts/pnw_pilot_cds_build.py` | Builds the week's window from the store with `pnw_weather.build` unchanged. It only resets the module's START, END and N_DAYS to the window, then range-checks the result |
| `scripts/pnw_pilot_cds_pull.py` | The week's store requests in the builder's request shape. Superseded: the planner had the builder submit them instead (see "Copernicus") |
| `scripts/pnw_pilot_publish.py` | Re-scores with one command: `--kind calendar` or `--kind full`, with `--repo-copy` to update `samples/` |
| `scripts/pnw_pilot_feature_check.py` | Compares the scoring path's features with the training path's on a historical Monday |

## Output format (fixed with the planner, D55 and D56)

- `pnw-pilot/<week start>/cantharellus.geojson` is one FeatureCollection of 0.1 degree cell
  polygons in WGS84. It has the same features as `pnw-pilot/<week start>/cantharellus/<block>.geojson`.
  A block is named by its south-west corner. For example, n47w123 holds the cell centres from
  47 to 48 N and from 123 to 122 W.
- Properties are exactly D55's nine.
- Departures from D55, agreed with the planner on 2026-10-10:
  - The combined file exists beside the block files.
  - `layers[]` names both, and there are no PMTiles entries, which the manifest states.
  - `uncertainty_low` and `uncertainty_high` are null, which D55 does not provide for. The
    manifest states it.
  - `weather_through` is null for the calendar model, which reads no weather.
- The manifest carries D55's fields that apply (published_at, groups[] with iNaturalist taxon
  47348, read from `api.inaturalist.org/v1/taxa?q=Cantharellus&rank=genus` on 2026-10-10;
  regions_published []; attribution; layers[]).
- It also carries the pilot fields: `pilot`, `validated` false, `reviewed` false,
  `beats_calendar` null, `t1_result` null, `weather_bridge`, `weather_source` and `model_kind`.
- Attribution: the display string is D53's daily-statistics text ("Contains modified ...
  information 2024") plus Open-Meteo's CC BY 4.0 credit. All four dataset texts are in
  `attribution_details`, with ERA5-Land's "<2019>" kept verbatim as D53 says.

## Live weather (Open-Meteo, now a cross-check only)

- **Archive lag (observed 2026-10-10 18:23 UTC).** The archive with `models=era5_seamless` held
  every day through 2026-10-04 and returned nulls from 2026-10-05.
  - 2026-W41 (Monday 2026-10-05) reads 2026-07-07 to 2026-10-04, so it needs no bridge.
  - The forecast endpoint (`api.open-meteo.com/v1/forecast`, `models=era5_seamless`) returned
    nulls on every day.
  - The historical-forecast endpoint returned values only to 2026-10-04.
  - So no bridge with the same pin exists. The planner chose W41 (RECORD -818).
- **Call cost.** Open-Meteo refuses a multi-location request unless `elevation` has one value per
  location. Each 50-cell, 90-day request costs 321.4 calls by the pricing page's rule
  (`open_meteo.api_call_units`).
  - The plan is 63 batches, about 20,250 calls, which is over the free tier's 10,000 a day.
  - Budget set: 400 a minute, 4,000 an hour, 8,000 per UTC day.
  - Cells holding T1 records go first: 2,043 of 3,116.
  - Plan: `docs/audits/2026-10-10-pnw-pilot-scoring/open-meteo-fetch-plan-2026-W41.json`.
  - Ledger at 18:45 UTC: 15 entries, 3,912.3 calls, every HTTP status 200 (or a hand-entered
    seed), no throttling, 12 batches on disk. The first entry is a hand-entered seed of 10 calls
    for the probes made before the script existed.
  - Whether Open-Meteo counts each location of a multi-location request as one call is
    **unverified**. The pricing page does not say. The ledger assumes it does.

## Rain gap (for T10)

**Check.** `scripts/pnw_pilot_feature_check.py` was run on Monday 2019-10-07 with 6 cells drawn by
seed 20260918. Only 2019 rain had been delivered to the store at that time.

- Both paths go through `pnw_weather.weather_matrix`. The training side is the store's
  `era5-precip-2019.nc` read by `pnw_weather.build`. The scoring side is Open-Meteo pinned per
  D19, D21 and D25.
- All 8 rain features are over D24's bound (half a unit per day, so w × 0.05 mm for a w-day sum):

| Feature | Largest difference | Bound |
|---|---|---|
| 3-day sum | 0.70 mm | 0.15 mm |
| 14-day sum | 3.63 mm | 0.70 mm |
| 90-day sum | 18.87 mm | 4.50 mm |

- File: `docs/audits/2026-10-10-pnw-pilot-scoring/feature-check-2019-10-07.json`. The data is in
  `~/Zynergy/forecast-data-pnw-pilot/scoring/feature-check/`:
  - feature-check-2019-10-07.json: sha256 00229d03...
  - open-meteo-2019-10-07.json: sha256 50f7a4c1...
  - om-hourly-precip-478_-1212.json: sha256 4a1c1d7b...

**Observed.**

- The nearest ERA5 point (`cells.quarter_cell_for`) matches better than any neighbour, and a
  lag of 0 days matches better than ±1 day. So the gap is not a cell or day mix-up.
- Open-Meteo's 90-day totals are 4 to 8 percent below the store's at all 6 cells. At 47.8,
  -121.2 they are 249.3 mm against 268.2 mm.
- At that cell, Open-Meteo's hourly rain summed over a day shifted one hour later cuts the
  largest daily difference from 1.75 mm to 0.88 mm. The total gap stays.
- Days where the store has 0.04 to 0.26 mm show 0.0 on Open-Meteo.

**Read, from Open-Meteo's source** (github.com/open-meteo/open-meteo at f625df2, 2026-10-09):

- `era5_seamless` is `Era5Factory.makeEra5CombinedLand`, a mixer of the `era5` and `era5_land`
  readers (`Sources/App/Era5/Era5Controller.swift`, the function after line 93).
- `Era5Variable.availableForDomain` returns false for precipitation on `era5_land`, with the
  comment "ERA5-Land wind, pressure, snowfall, radiation and precipitation are only linearly
  interpolated from ERA5" (`Sources/App/Era5/Era5Variables.swift`, about line 279).
- So `era5_seamless` rain is ERA5 at 0.25°, not ERA5-Land. The owner's lead (RECORD -820), a
  difference between models, is not the cause here: both sides are ERA5.
- Open-Meteo stores ERA5 precipitation with `scalefactor` 10, which is 0.1 mm per hourly value
  (`Era5Variables.swift`, the `scalefactor` switch).

**Inferred, not verified.**

- Rounding each hourly value to 0.1 mm drops drizzle hours, which biases daily sums low. That fits
  the zero days and the PNW's drizzle.
- Separately, a one-hour difference in where the UTC day boundary falls between the two products.
- No hourly store data was pulled to confirm either.

**Consequence.** A model fitted on store rain and scored on Open-Meteo rain would see rain about
7 percent low. The owner ruled that scoring uses the store (RECORD -819). For T10 this is an
open seam: a bridge or serving product that is not the store must be checked at feature level,
not only daily value level.

## Land mask

- The store's ERA5-Land grid (first land file, `hourly-era5land-2019-01.daily.h5`) has values in
  2,387 of the box's 3,116 cells.
- On the first 600 cells Open-Meteo answered, 94 get full Open-Meteo values but have no store
  ERA5-Land value. Examples: 48.7,-122.5; 48.5,-123.3; 44.3,-124.1. They are coastal and island
  cells holding T1 records.
- Read: the mixer above. Inferred: where ERA5-Land has no value, Open-Meteo falls back to ERA5
  for temperature and soil.
- Training consequence (inferred, for the builder to count): units in those cells have NaN
  weather in the store, so the full model drops them while the calendar model keeps them.
- The scoring outputs use the store's mask for both models, so both cover the same 2,387 cells.

## Copernicus (RECORD -819)

- Scoring weather is the store's two daily-statistics products for 2026-07-01 to 2026-10-04,
  through `pnw_weather.build`.
- I submitted one request myself before the planner said the queue cap is per user. That run was
  stopped, and one job stays queued: d6ae24ed-c8b4-428a-ae21-cf65e9f47b3e, 2026 rain, months 07
  to 10. The planner had the builder adopt it. The other months are submitted by the builder.
- Reviewer B1: `pnw_weather.build` subtracts 273.15 from soil moisture (`scripts/pnw_weather.py`,
  `pairs = [(k, LAND[k], 273.15) for k in LAND]`).
  - My range check stops scoring on it: "soil_moisture spans -273 to -272.8".
  - The obvious fix, no kelvin for swvl1, falls into `data * 1000.0`. The check reports that as
    "101.6 to 399.6".
  - The store-path test is `xfail(strict=True)` on B1. With a correct fix simulated in a scratch
    edit, restored from a saved copy, it passes.

## Outputs so far

The calendar floor was written 2026-10-10 18:43 UTC by `pnw_pilot_publish.py --kind calendar
--repo-copy`:

- 2,387 cells. Chance 0.0107 to 0.1677, median 0.0384.
- Model `pnw-pilot-t1-calendar-e2c272b7acfa`, the builder's all-years calendar model, commit
  1742544d in its model.json.
- `cantharellus.geojson`: 935,538 bytes, sha256
  c74ee7f06b2c1ed13a68438e92d488625932831705b5384b8811973a88ea99e7. `manifest.json`: sha256
  af683970a5d3994881a4ae1649865d1f2751e047190e39f4a0e5829dafaf0cf8.
- 40 files, each under the 1 MB guard, in the repository at `samples/pnw-pilot/2026-10-05/` and
  in `~/Zynergy/forecast-data-pnw-pilot/scoring/out/`.

## Tests

The suite stands at 456 passed and 1 xfailed (B1).

New test files:

- `tests/test_live_weather.py` (11)
- `tests/test_pilot_output.py` (10)
- `tests/test_pilot_score.py` (3)
- `tests/test_pilot_cds_build.py` (3, one xfail)

Order, stated plainly:

- Only `test_live_weather.py` and the unit and range tests were seen failing before their code
  existed (ImportError, AttributeError).
- `pilot_output` and the scoring script were written before their tests.
- So every test was then revert-checked. The runner restores from a saved copy, never from git,
  checks the output for compile errors, and confirms with `git status` that the forward code is
  intact.

Revert checks, each with the edit and the message it produced:

| Edit | Message |
|---|---|
| elevation as one value | `['nan'] == ['nan,nan,nan']` |
| UTC-day limit off | `0.0 == 1800` |
| grid-point check off | `DID NOT RAISE WrongCell` |
| shared-rain check off | `DID NOT RAISE RainDisagrees` |
| days shifted by one | all 32 features NaN against `window_features` |
| weather completeness ignored | the cell with a missing day appears: `['470_-1227', ...]` |
| feature-list check off | the later order check fires with its own message, not the expected one |
| Open-Meteo unit check off | `DID NOT RAISE UnitMismatch` |
| range check off | `DID NOT RAISE UnitMismatch` |
| unit check removed from the scoring script | `assert 0 != 0` |
| calendar uses the weather mask | `[] == ['470_-1229', ...]` |
| floor's weather-model guard off | the run fails later with "No such file", not the guard's message |

The first run of the "weather completeness ignored" check did not bite: a sea cell never reaches
the scored list, because the parser refuses it. The test then gained a land cell with a missing
day, and it bites.

## Not verified

- No weather-model output exists yet. It waits on the store's 2026 months, the builder's B1 fix
  and the builder's full model.
- No R7 training-range check. No area-of-applicability analysis.
- The two causes of the rain gap (rounding, hour boundary) are inferred.
- Whether the store accepts October days after the data's end in a whole-month request is
  untested.
- Whether Open-Meteo counts a multi-location request per location is unverified.
- The temperature and soil features have not been compared between the two paths. No land month
  had been delivered at check time.

## Addendum, 18:52 UTC: attribution follows what each output read

**What was wrong.** The planner flagged a go-live blocker in the manifest's attribution, and the
earlier "Output format" section was wrong on two points. That section stands as written; this
addendum supersedes it.

- At 18:43 the calendar floor's attribution credited Copernicus and Open-Meteo, although the
  calendar model reads neither.
- It did not cite the GBIF download its records come from.

**What it does now.** Attribution is built from the sources an output actually read
(`pilot_output.attribution`). The manifest carries them as `attribution_sources`.

- **GBIF.** The citation is the one GBIF itself returns for the download (read, not from memory):
  `https://api.gbif.org/v1/occurrence/download/0012112-260928105237408/citation`, read 2026-10-10,
  "GBIF.org (6 October 2026) GBIF Occurrence Download https://doi.org/10.15468/dl.8jxmeb".
  - The details line adds the 26 datasets and their licences (CC0 1.0, CC BY 4.0, CC BY-NC 4.0;
    D29, D61), pointing at `docs/pulls/gbif-fungi-us-canada-2015-2025.datasets.json`.
  - It also states that the download is provisional (test account).
  - The scoring script refuses a real model unless the builder's
    `docs/audits/2026-10-10-pnw-pilot-t1/records_summary.json` names download
    0012112-260928105237408.
- **Copernicus**, only for the products read: the weather model's training (from its model.json)
  plus the scoring window's months (from `pnw_weather.build`'s `land_route_by_month`).
  - Texts are taken from the evidence report under D53: daily statistics filled "... information
    2024", the single-levels citation reading "single levels", and ERA5-Land hourly verbatim
    "<2019>" if the hourly route was read.
  - "(Accessed on DD-MMM-YYYY)" is filled from the store's `requested_at_utc` records. A product
    with no access date is refused, not invented.
- **Open-Meteo** is credited only when an output reads it. None does now.

**Calendar floor re-published** at 18:51 UTC. Its attribution is the GBIF citation alone.

- `cantharellus.geojson` is unchanged: sha256
  c74ee7f06b2c1ed13a68438e92d488625932831705b5384b8811973a88ea99e7, the same features.
- `manifest.json`: sha256 4debbc8ba4d218509c3e4cbb481cede92f40cc571ba7a5a65e30d63ffe61da05.

**Tests.** The suite stands at 463 passed and 1 xfailed.

- New: `tests/test_pilot_attribution.py` (6), seen failing first with AttributeError.
- End-to-end assertions on `attribution_sources` were added for the calendar, Open-Meteo and
  store paths, plus a refusal test for Copernicus sources on the calendar model.
- Five revert checks all bite, each with a message specific to its edit:
  - `['gbif_downlo... 'open_meteo'] == ['gbif_download']`
  - `[] == ['gbif_download']`
  - the calendar refusal check off: the run fails later on the missing access date, not with
    its own message
  - access-date check off: `KeyError: 'era5_daily_sum'`
  - source filter off: `era5_land_hourly has no access date`

**Open: the weather model's attribution cannot be written yet.** `pnw_pilot_publish.py --kind
full` needs the full model's model.json to name the Copernicus products its training read. It
accepts either `copernicus_sources` or the build summary's `land_route_by_month`. Without one of
them it stops rather than guess.

## Addendum, 20:20 UTC: merged the builder's land rule and B1 fix

**What changed on the builder's branch.** Merged `origin/pnw-pilot-t1` at a8f85b9 (merge commit
3c04465). It brought three changes:

- B1 is fixed. `swvl1` is now taken as delivered, `scripts/pnw_weather.py:38`. The xfail marker
  is off, and the store-path test passes as a plain test.
- `weather_matrix` now returns a third value: where each cell's land point comes from.
- The coastal rule, owner's ruling in Forager RECORD -822: a cell with no ERA5-Land value reads
  its nearest land neighbour (`coastal.land_point`).

**What the merge broke, and the fixes.** The merge turned 7 tests red.

- Three of them were the builder's own `test_pnw_weather_units.py`, which pass when run alone.
  The cause was mine: `build_window` set `pnw_weather`'s module constants and never restored
  them. Every later test in the same process then built on a 90-day 2026 range. It now restores
  them in a `finally`, and a test checks this. That test's revert check fails with the message
  `(... 2026, 10, 4), 90) == (... 12, 31), 4140)`.
- Scoring now uses the builder's land rule for both models, so the calendar and the weather
  outputs cover the same cells as training. Revert check: an own-point-only mask fails the
  calendar test.
- The manifest counts cells filled from a neighbour.
- Attribution now covers hourly ERA5 rain (`era5_hourly_precipitation`, ERA5 single levels with
  the year filled as 2023 per D53).
- `pnw_pilot_publish.py --kind full` reads the scoring window's sources through the builder's
  `pnw_t1_fit.copernicus_sources`, and the training sources from the model.json's
  `copernicus_sources`.

**Calendar floor re-published at 20:18 UTC.**

- 2,618 cells: 231 of them from a land neighbour, 498 without a land point.
- Chance from 0.0107 to 0.1677, median 0.0389.
- `cantharellus.geojson` is 1,026,074 bytes, sha256
  6a4a3536b0676d2906450879f2c10c2469a53257eef53a82a86bbb4049687c84. That is under the 1 MB
  guard, but close: a weather-model file with drivers will exceed it and stay outside the
  repository.
- `manifest.json`: sha256 92b3049626d560370afbf50ed2d21e64e542ec4abce6fb8cf5ec0b5dc4987417.

**Suite:** 473 passed.

## Scoring step 4, 2026-10-11: the weather model published for 2026-W41

Dispatch: pnw-pilot-plans 8e3009b, `docs/dispatch/2026-10-11-pnw-pilot-scoring-step4.md`. Rulings:
Forager RECORD -854 (gate override), -861 (the weather model on the demo, labelled), -863 (banner
wording; the planner's technical calls). Base: this branch at 60c4285; pnw-pilot-t1 7d19c66 merged
at deca36a. The merge commit lacks the co-author line. It is recorded here and was not amended.

**Published.** `~/Zynergy/forecast-data-pnw-pilot/scoring/out/pnw-pilot/2026-10-05/`, written
2026-10-11T22:43:38Z by `pnw_pilot_publish.py --kind full --repo-copy --beats-calendar false
--reviewed true --t1-result "<the owner's wording, RECORD -863>"`.

- `cantharellus.geojson`: 1,594,691 bytes, sha256
  ac6038d39114e28c618bd5afc6c512f75dbdaf9b60d5aab8837c33a8d121a395. It is over the 1 MB guard,
  so `--repo-copy` refused it as designed and exited 1 after scoring. `samples/pnw-pilot/2026-10-05/`
  still holds the calendar floor.
- `manifest.json`: 14,242 bytes, sha256
  f0c43c6a081ffc3f0f7912167eb958a61ebe446a938a97bc8a06036443c9f44c. A copy is at
  `docs/audits/2026-10-10-pnw-pilot-scoring/window-2026-W41/published-manifest-full.json`.
- 40 block files, 1,596,290 bytes in total.
- The same week directory held the calendar floor's output, and this run overwrote it. The floor
  is still in the repository copy.

**Checks, read from the published files.**

- Cells: 2,618 scored of 3,116, the same as the calendar floor's 2,618.
  - 231 are from a land neighbour, as in the floor.
  - 498 are omitted as sea. 0 are omitted for an incomplete weather window.
  - 2,618 unique ids in the combined file and 2,618 across the blocks.
  - Every feature has week 2026-10-05 and weather through 2026-10-04.
  - Chance runs from 0.0067 to 0.1571, median 0.0411.
- Fields: pilot true, validated false, reviewed true. model_kind full. beats_calendar false.
  regions_published empty.
  - status_label and t1_result are the owner's wording, verbatim.
  - Model `pnw-pilot-t1-full-cd0c66a65752`.
- Attribution sources: era5_daily_sum, era5_hourly_precipitation, era5_land_hourly,
  era5_land_timeseries and gbif_download.
  - These are what training read (model.json `copernicus_sources`) together with what the window
    read, which is a subset of them.
  - Copernicus texts: 2023 (hourly single levels), <2019> (hourly ERA5-Land), 2024 (daily
    statistics) and 2025 (time series), plus the GBIF citation.
- Values from the free weather API: two keys, `open_meteo` and `open_meteo_body_raw` (both 5.5),
  under `model.model_json.land_route_gate.failing_hours[0]`.
  - There is also one null key, `weather.open_meteo_batches`.
  - The service's name appears in text twice: in `gate_record_attribution` (its credit) and in
    `weather_bridge` (the cross-check sentence). Neither carries a value.
  - The geojson files have no mention of it.
  - Under RECORD -863 the gate record's values stay. The -819 rule covers scoring and training
    inputs.
- The forbidden-terms check in the script passed.
- The embedded model.json `label` still reads "unvalidated pilot, unreviewed; sighting chance
  (D12)". It is the builder's file, left as written.

**weather.source, as published:** "Copernicus Climate Data Store (owner, Forager RECORD -819).
Scoring window read: reanalysis-era5-single-levels (hourly total_precipitation, summed per UTC day
from the 01:00 stamp to the next day's 00:00 stamp); reanalysis-era5-land (hourly 2m_temperature,
soil_temperature_level_1, volumetric_soil_water_layer_1, averaged over the 24 UTC hours of each
day). Training read: derived-era5-single-levels-daily-statistics (daily_sum of
total_precipitation; time_zone utc+00:00, frequency 1_hourly); reanalysis-era5-single-levels
(...); reanalysis-era5-land (...); reanalysis-era5-land-timeseries (point series of the same three
ERA5-Land variables, averaged over the 24 UTC hours of each day). Window days 2026-07-07 to
2026-07-31 are the store's final data (expver 0001); 2026-08-01 to 2026-10-04 are its preliminary
data (expver 0005), which can be revised."

**Window weather (RECORD -863; route by RECORD -829, confirmed by the planner 2026-10-11).**

- Job d6ae24ed no longer exists: the store answers 404. It had been dismissed at 2026-10-10
  20:20:10Z (builder's report, "Queue decisions").
- I pulled through the builder's `--scoring` routes: hourly ERA5-Land 2026-07 to 2026-10-04 and
  hourly ERA5 rain 2026-07-01 to the 2026-10-05 00:00 stamp.
- Queue waits:
  - Land jobs were submitted at 17:17Z. The first started at 18:27Z, and all had finished by 19:08Z.
  - Rain July to September took 97 min from submit to file.
  - Rain October 1 to 4 took 135 min, ending 21:32Z.
  - The closing stamp landed at 22:39Z.
- The store delivered August as a zip of two NetCDF files, although the request said unarchived.
  - The members were split by data version: swvl1 and stl1 all preliminary; t2m final for
    08-01T00 and preliminary after.
  - `scripts/pnw_split_delivery.py` merged them. All 31 days complete; no new request (job
    08142ab0 adopted).
- Every land month aggregated with 0 incomplete days.
- Rain aggregation wrote 96 days for 2026. The 2014 to 2025 daily rain files were unchanged: 12 of
  12 `sha256sum -c` OK against checksums taken before the pull.
- The pull's wrapper hit my shell's 2 h limit at 19:17Z. The rain step was restarted as a user
  service and adopted its queued job.
- The closing stamp was also fetched by a one-off beside it. Both runs adopted the same job, and the
  record kept is the rain step's.
- Request records and logs: `docs/audits/2026-10-10-pnw-pilot-scoring/window-2026-W41/`.

**Code (tests first for each).**

| Commit | Change |
|---|---|
| 57234aa | The time-series product is cited with the publisher's text (CC-BY-4.0), and access dates are read from ts/ too |
| 897e567 | `gate_record_attribution` added |
| 15a6d58 | `--reviewed` added |
| 2b1573f | weather.source names what training read |
| 963d208 | Zip-delivery merge |
| f7fc21e | The final/preliminary sentence |
| 22a01c8 | Scalar coordinates of a one-stamp file |
| 4a5faea | Window products from the window's months only; bridge text corrected |

- Revert check, for 57234aa: I dropped the dataset-table entry. 9 tests ran with 2 failures naming
  era5_land_timeseries, 0 errors and no collection errors. The file was restored from a saved copy,
  byte-identical, and the forward change confirmed present.
- Suite: 513 passed.

**Wrong figures caught before the final publish.** A first full publish at 22:41:42Z, superseded
at 22:43:38Z, wrote two wrong things:

1. weather.source said the window read the daily-sum and time-series products. The build summary
   lists the route of every month in the store, and the builder's `copernicus_sources` counts them
   all. Fixed in 4a5faea.
2. weather_bridge said the week was scored from "the store's daily statistics". That text dates
   from before RECORD -829. Corrected in the same commit.

The cell file's sha256 is the same in both runs, so the scores did not change.

**Not verified.**

- The chances were not recomputed independently on the real window. The store-path test recomputes
  them on synthetic files.
- The site does not read `gate_record_attribution`, so the credit is not on the page.
- No site change and no Gradle build were made.

**Republished 2026-10-11T22:48:19Z for the owner's banner weather line (Forager RECORD -893, commit
6f28021, test first).**

- `weather_bridge` now reads, verbatim: "This week's weather comes from the Copernicus climate
  archive, the same sources the model was trained on. A second weather service was checked for the
  same days but isn't used for scoring." The calendar model passes no bridge (null), so it is
  unchanged.
- `cantharellus.geojson`: byte-identical to the 22:43:38Z file, sha256
  ac6038d39114e28c618bd5afc6c512f75dbdaf9b60d5aab8837c33a8d121a395.
- New `manifest.json`: 14,081 bytes, sha256
  b94a15023d26450ff1b676ad59c31ce66cf71bcea906c4c363c8b02242f38759. Same path; the repository
  copy is replaced.
- I did not keep the earlier block files' hashes, so the 40 block files were not compared byte for
  byte. They are cut from the same features as the identical combined file.
- Correction to the free-weather-API check above: after this change, the service's name in text
  appears only in `gate_record_attribution`.

**Republished 2026-10-11T23:41:25Z for "This forecast's weather" (Forager RECORD -895, commit
92cd265, test first).**

- `cantharellus.geojson`: still byte-identical, sha256 ac6038d3...a395. The 40 block files were
  also byte-identical (`sha256sum -c` against hashes taken just before this run).
- New `manifest.json`: 14,085 bytes, sha256
  aae1e57bdbcd169d89ba9f9899891f383f3ae398b0827ef72b50418383d7ae22.
- **Slip:** a weather fit (`pnw_t1_fit.py --list t1_5000m`, pids 845648/845651) was running when
  this publish ran. My check printed the fact but did not stop the command. The publish ran under
  the 5G cap and took seconds.
- **Not changed, reported:** "this week" still appears once in the manifest, in
  `sighting_chance_meaning` (D12's definition, `SIGHTING_CHANCE` in scripts/pnw_pilot_score.py:116).
  - That field is published already, the same text as in the calendar manifest the site serves.
  - The site's pilot.js does not read it.
  - Changing it would reword a published definition, so the decision is the owner's.

**Republished 2026-10-12T00:48:38Z with `base_rate` (owner, Forager RECORD -901; commit 949a5cf,
tests first).** No fit was running; the command checks and stops if one is.

- Figures read from the model's own files: `models/primary_t1_1000m_full/model.json` gives units
  52,718 and positives 1,138. The comparison file `fits/primary_t1_1000m_comparison.json` gives the
  same, and so does the calendar model.json.
- As published: `{"positives": 1138, "units": 52718, "rate": 0.021586554876892143, "source":
  "model.json positives and units (primary_t1_1000m_full, 2015 to 2025): every cell-week of the
  design, each held out once in the leave-one-year-out test"}`.
- The calendar model's own model.json carries the same figures, so a calendar republish would carry
  the field too. The calendar was not republished.
- `cantharellus.geojson` and the 40 block files: byte-identical (ac6038d3...a395).
- New `manifest.json`: 14,341 bytes, sha256
  074879ffa7c53a04a22f5613e31abd8798e1ef53d53aa68c238d56587a994043.

## 2026-W42, step 0 (2026-10-15 UTC): stopped, the store does not yet have the window

Dispatch: the planner's message under Forager RECORD -1034 (the owner, verbatim: "Publish this week's
pilot meanwhile"). Branch pnw-pilot-w42 from main a79d667. Nothing was pulled, scored or published
for W42.

**W41 reproduces from its inputs on main.** At 2026-10-15T04:47:11Z, `pnw_pilot_publish.py --kind
full --week 2026-W41 --beats-calendar false --reviewed true --t1-result <W41's t1_result>` with
`--out /tmp/w41-repro/out` (nice 10, 5G cap, no fit running):

- 2,618 of 3,116 cells scored, 231 from a land neighbour, 498 sea, 0 incomplete.
- `cantharellus.geojson` and all 40 block files byte-identical to the published W41 directory
  (`sha256sum` of every file; cells ac6038d3...a395).
- `manifest.json` differs only in `published_at`: with that one value set back to
  2026-10-12T00:48:38+00:00 it hashes to 074879ff...4043, the published and live file.
- The run rewrites `scoring/cds-npz/weather_2026-W41.npz` in place; it came out byte-identical
  (0c49371a...7396, the hash in W41's manifest), checked against a copy taken before the run.

**Why it stopped.** W42's window (`live_weather.window_span`) is 2026-07-14 to 2026-10-11, and rain
also needs the 2026-10-12 00:00 stamp. At 04:46Z the store's catalogue gave both
`reanalysis-era5-land` and `reanalysis-era5-single-levels` a temporal extent ending
2026-10-09T00:00:00Z (catalogue updated 2026-10-15T00:00Z), and the constraints service listed
October days 01 to 09 only. 2026-10-10, 2026-10-11 and the closing rain stamp are not published
yet. The window cannot be built, and `pnw_pilot_publish.py` would stop on missing days.
When they appear is inferred, not checked: about one day per daily update, so the land days around
2026-10-17 and the closing stamp around 2026-10-18.

**Also found, for the run when it happens.**

- The two pull scripts' scoring routes are fixed to W41: `scripts/pnw_cds_hourly_pull.py:57-58`
  (`SCORING_MONTHS`, `LAST_DAY = {(2026, 10): 4}`) and `scripts/pnw_cds_precip_hourly.py:127-141`
  (`scoring_chunks`, ending at the 2026-10-05T00 stamp). Pulling W42 needs a change to them (pull
  only, not the model, copy or labels).
- The store's `hourly-era5land-2026-10.*` files hold 2026-10-01 to 04. A W42 pull of October under
  the same name replaces them and their request record.
- The citation access dates in `attribution_details` come from the store's request records, so a
  new pull moves them (W41: "Accessed on 10-Oct-2026 to 11-Oct-2026" for the two hourly products).
  That field cannot stay identical to W41's.

## 2026-W42, step 0 again (2026-10-19 UTC): the window is published; W41's store cannot take W42's files

Dispatch: `docs/dispatch/2026-10-18-pnw-pilot-w42-publish.md` (0f4bda9), by the forecast planner
(Alder Bearing); approval forecast RECORD 2026-09-28-2005, intent 2026-09-28-2006. Coder: Ash
Transect (Opus). Report accepted with rulings in the dispatch's Amendment 1 (a51adfe). Nothing was
changed, downloaded or scored in step 0. Tags: [read file:line], [computed: command], [inferred].

**Base.** Branch head 0f4bda9 = origin. The merge-base with main b0bc10a4 is 1305244 (main merged
this branch at c610926), not a79d667 [computed: `git merge-base`]. From there main also adds the
T6b host-genera code (`scripts/t6b_run.py`, `src/forager_forecast/{crown_cover,t6b_hosts,
t6b_layers,t6b_run}.py`) and one ruff exclusion; none is imported by `pnw_pilot_publish.py:31-35`,
`pnw_pilot_score.py:35-44`, `pnw_t1_fit.py:36-44` or `pnw_weather.py:26-28` [read], so no merge is
needed [inferred, one-level import trace].

**Premises.**
- Catalogue at 2026-10-19T04:49:57Z: `reanalysis-era5-land` and `reanalysis-era5-single-levels`
  both end 2026-10-13T00:00:00Z (updated 2026-10-19T00:00Z); licence `CC-BY-4.0`, linked to
  spdx.org/licenses/CC-BY-4.0 [computed: GET `/api/catalogue/v1/collections/<name>`].
- `lw.window_span(2026-W42)` = 2026-07-14 to 2026-10-11 (W41: 07-07 to 10-04) [computed;
  `live_weather.py:46-49`].
- Pull scripts fixed to W41: `pnw_cds_hourly_pull.py:57-58`, `pnw_cds_precip_hourly.py:127-142`
  [read]. Neither has tests [computed: grep of tests/].
- A same-name re-pull of October **skips** it (`pnw_cds_hourly_pull.py:147-149`;
  `pnw_cds_precip_hourly.py:155-157`), and the build would stop on missing days
  (`pnw_pilot_publish.py:188-190`) [read]. The rain `aggregate` rewrites every year's
  `hourly-era5-precip-<year>.daily.h5` in its directory, W41's 2026 file included
  (`pnw_cds_precip_hourly.py:208,227-237`) [read]. The reader takes only the fixed names
  `hourly-era5land-YYYY-MM.daily.h5` and `hourly-era5-precip-YYYY.daily.h5`
  (`pnw_weather.py:71-72`) [read], so own names alone cannot work.
- Access dates come from every `*.request.json` in the store and `ts/`, first to last per product
  (`pnw_pilot_publish.py:58-74,193`) [read]. Any W42 request record in `cds/` would therefore move
  W41's citation and W41 would stop reproducing. Today's tally: ERA5-Land hourly 32 on 10-10, 4 on
  10-11, 1 undated; single-levels hourly 6 and 6; daily sum 1 on 10-10; time series 1,904 on 10-11
  [computed: python tally].
- W41 live: manifest 074879ff...4043, geojson ac6038d3...a395 (zynergy-site 319871c, and the
  scoring output); npz 0c49371a...7396 [computed: sha256sum]. The 10-15 reproduction's raw manifest
  was bca36aa8...c0c0 (`/tmp/w41-repro/publish.log`) [read].
- No CDS row exists in `docs/planning/DATA_REGISTER.md` [computed: grep]; `SPEC.md:136` says so.
  W41's store files are not read-only (`-rw-rw-r--`) [computed].

**W41 flags reused** (`pnw_pilot_publish.py:150-159`; this report's line 492): `--kind full`
(manifest `model_kind`), `--beats-calendar false` (`beats_calendar`), `--reviewed true`
(`reviewed`), `--t1-result` = the JSON text of the manifest's `t1_result` string, passed through
`json.dumps` (`pnw_pilot_score.py:250,432` parse it with `json.loads`); no `--repo-copy`. W42 adds
`--store cds-2026-W42` (Amendment 1, ruling 1); the store path does not reach a full-kind manifest
(`pnw_pilot_publish.py:182-207`) [read].

**Mechanism prediction, written before any change.** A copy `cds-2026-W42/` (`cp -a` of `cds/` less
W41's October land trio and the 10-05T00 rain pair); new week-keyed functions in both pull scripts,
W41's constants and `--scoring` path untouched, refusing W41's `cds/` and any symlinked target; land
October as one month file, days 01-11; rain `2026-10-05-11` (24 h) and `2026-10-12T00`; aggregate in
the copy, then the copy read-only. Predicted W42 output [inferred]: 2,618 scored / 231 neighbour /
498 sea / 0 incomplete, same 40 blocks; `weather_through` 2026-10-11; versions 07-14 to 07-31 final,
08-01 to 10-11 preliminary; both hourly access dates "10-Oct-2026 to <pull date>", daily sum and time
series unchanged; attribution unchanged. W41 after the pull: unchanged hashes, its npz backed up and
compared because the reproduction rewrites it in place (`pnw_pilot_publish.py:185-187`).

**Not checked in step 0:** whether the store states a size or checksum for a result; whether
August has turned final at source; t6b-night's state. No tests or lint were run.

## 2026-W42, step 1 (2026-10-19 UTC): the pull, W42's own store, W41 still reproduces

Under Amendment 1 (a51adfe). Evidence in `docs/audits/2026-10-10-pnw-pilot-scoring/window-2026-W42/`.

- **Tests first** (32d7a0c): 9 tests in `tests/test_pnw_w42_pull.py`. Over stubs, 7 failed for their
  own reasons and 2 passed: the check that W41's constants are unchanged, and the W41-plan test,
  whose stub returned W41's constants. Those 2 are not shown to bite by the stubs; revert case 3
  below makes the W41-plan test fail. Before the guard, `aggregate` was shown writing through a
  link into the file it pointed at (`failing-first.txt`). One test input was mine and wrong (a
  September 30 "held through" date does not cross a month); it was corrected to 2026-09-29 before
  the implementation was relied on.
- **Change** (a2b12e4): `scoring_plan(week)`, `refuse_w41_store`, `refuse_links` and
  `--scoring-week` in `pnw_cds_hourly_pull.py`; `scoring_chunks_for(week, held_through)`,
  `refuse_w41_store`, link refusals in `pull` and `aggregate`, and `--scoring-week` /
  `--held-through` in `pnw_cds_precip_hourly.py`. W41's constants and `--scoring` path are
  unchanged. 9 passed. Five one-edit revert checks bite (`revert_checks.out.txt`); case 3 also
  fails the W41-plan test, which that same edit breaks. Suite 601 passed; ruff check and format
  clean.
- **Store** (c68cde2): `~/Zynergy/forecast-data-pnw-pilot/cds-2026-W42/`, `cp -a` of `cds/` (143
  files hashed first) less W41's October land trio and the 10-05T00 rain pair (138 files).
- **Fetches**, one at a time, each in a detached unit at Nice 10 under a 5G cap. Each size and MD5
  equals the `file:size` and `file:checksum` that the store states for the job's result
  (`check_land.out.json`, `check_rain.out.json`, `checksum_check.out.json`). The two rain chunks
  ran back to back in one unit, then both were checked.
  - ERA5-Land hourly October 01-11: 3,568,747 B, 264 stamps (2026-10-01T00 to 10-11T23), expver
    0005, the same 76 x 41 grid. Its days 01-04 equal W41's exactly (diagnostic).
  - Rain 2026-10-05 to 11: 83,304 B, 168 stamps. The 2026-10-12T00 stamp: 25,581 B.
- **Aggregate** in the W42 directory: 2026 has 103 days (07-01 to 10-11). W41's 96 days (10-04
  included, now closed by the new 10-05T00 stamp) are identical, as are the 2014-2025 files. The
  directory was then made read-only (145 files). W41's `cds/` re-hashed: 143 files identical.
- **Register** (05bdb48, corrected in e6c855d): a row for the three new files, with the licence read
  at source; the store's earlier files are noted as having no row. The first version of the row
  wrongly said the store publishes no checksum.
- **W41 reproduction** at 2026-10-19T05:11:16Z, with the W41 flags and `--out /tmp/w42-w41repro/out`,
  in a detached unit:
  - 2,618 scored, 498 sea, 0 incomplete.
  - geojson and all 40 block files equal the live W41 directory (41 of 41 OK).
  - The manifest differs only in `published_at`; with it reset, the manifest hashes to
    074879ff...4043.
  - W41's npz and its summary were backed up first and are byte-identical after (0c49371a...7396,
    8dab0c42...f88f).
  - t6b-night (`t6b_run.py`) was running during this 8-second run and was not touched. My pre-run
    "no fit running" check matched its own shell line, so it was not evidence; a later `ps` showed
    no pilot fit or score running.
