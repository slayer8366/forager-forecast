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
