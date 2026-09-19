# T1 completion report: calendar smoke test, verify-first answered, stopped before data

**Date:** 2026-09-18
**Type:** completion report for docs/dispatch/2026-09-18-t1-calendar-smoke-test.md, including
both amendments. Verify-first and preparation only; the dispatch's "Then build" was not run on
data, because there is no data.
**Base:** main f96d557 on branch t1-calendar-smoke-test. Code commit ac12f55; this report and
the index, session-log and TASKS rows follow in two further commits named in the final message.
**Supersedes:** none.

Every claim below names a file and line, a commit, or a command whose output is quoted, or is
marked inferred. Flags: verified means the source was opened today; from memory means it was
not.

---

## The short version

**No model was fit.** The dispatch's first verify-first item is the GBIF download, and it cannot
be requested from this machine: there is no GBIF account here (no GBIF_USER, GBIF_PWD or
GBIF_EMAIL in the environment, no ~/.netrc), and the download request endpoint answers 403
without credentials and 401 with wrong ones. SPEC.md, Constraints, allows no other bulk pull
("Bulk record pulls go through GBIF downloads ... The iNaturalist API is for counts and spot
checks only"). The dispatch says "If not, report and stop for the owner", and that is what this
report does. Nothing was fit on preview or partial data.

Everything that does not depend on the download was done:

1. **Weather (item 2, amendment 2).** The archive serves all four T1 variables fully populated
   under models=era5_seamless at a point inside each box, in a September window. Rate limits and
   terms were read from Open-Meteo's own pages: 10,000 calls a day, 5,000 an hour, 600 a minute,
   non-commercial use only, and a call is weighted by days and variables. By that weighting one
   0.1 degree cell for 2014-10-01 to 2025-12-31 costs about 294 call units, so **the free tier
   does not fit a T1 pull of more than about 34 cells a day**. That is a stop for the owner
   (proposed row below), as the dispatch anticipates ("If it does not fit, propose the
   Copernicus Climate Data Store instead and wait").
2. **The rain grid (amendment 2).** Shown from a 10 by 10 block of 0.1 degree points in each box:
   one 0.25 degree rain value is shared by 4, 6 or 9 cells (2 or 3 per axis, since 0.25 / 0.1 is
   2.5), which averages 6.25 cells per rain value over a whole box. Temperature differed in every
   one of the 100 cells.
3. **Units (item 3).** A coordinate maps to the 0.1 degree cell whose centre is the nearest grid
   point, halves away from zero, which is the rule the archive was observed to apply; a date
   maps to its ISO week. Both are code with tests (src/forager_forecast/cells.py).
4. **Gradient boosting (amendment 2, D20).** lightgbm 4.7.0 has a wheel that imports and fits on
   Python 3.14.4 here; numpy 2.5.3 and scipy 1.18.1 come with cp314 wheels. Added, pinned exactly.
5. **Prepared, not run:** the exact download predicate (1,195,034 records by GBIF's own
   predicate search today), a submitter that reads the three credential variables, the filters,
   the cell-week labelling and the window features, with the two tests the dispatch names, both
   revert-checked.

Two observations about the archive that change how a cell's weather must be requested, both
verified live and both pinned in code: by default the archive downscales temperature to a 90 m
elevation model at the requested point, so two points inside one cell get different
temperatures; and by default it substitutes a nearby land cell for a coordinate over water.
elevation=nan and cell_selection=nearest turn both off (Evidence, "Point versus cell").

## Verify first, as answered

### Item 1. Records via a GBIF download. Blocked.

- Credentials: `echo "GBIF_USER=${GBIF_USER:-unset} GBIF_PWD=${GBIF_PWD:+set}
  GBIF_EMAIL=${GBIF_EMAIL:-unset}"` printed `GBIF_USER=unset GBIF_PWD= GBIF_EMAIL=unset`;
  `ls ~/.netrc ~/.config/gbif* ~/.gbif*` found nothing. Observed.
- Endpoint: POST to https://api.gbif.org/v1/occurrence/download/request with a valid predicate
  body and no auth: `HTTP 403`, body `Access is denied`. With `-u nobody:nothing`: `HTTP 401`.
  With an empty `{}` body and no auth: `HTTP 404` (noted because the launching session reported
  403; the difference is the body, not the auth). Observed.
- The predicate that would be submitted is src/forager_forecast/gbif/
  t1_fungi_two_boxes_2015_2025.json: TAXON_KEY 5 (Fungi), BASIS_OF_RECORD HUMAN_OBSERVATION,
  YEAR 2015 to 2025 inclusive, HAS_COORDINATE true, within either box as a counter-clockwise WKT
  polygon. POSTed to https://api.gbif.org/v1/occurrence/search/predicate with `"limit": 0`
  it answered `HTTP 201` and `{'count': 1195034, 'limit': 0, 'endOfRecords': False}`. Observed.
- The premise "each box has at least 1,000 usable Cantharellus records across at least 8 years"
  is **neither confirmed nor disproved**. The table below is an unfiltered preview from the
  search API, not the dispatch's counts table: it has none of the filters and no DOI. It is an
  upper bound. Every request had `hasCoordinate=true&basisOfRecord=HUMAN_OBSERVATION`, the
  box as `decimalLatitude=S,N&decimalLongitude=W,E`, and `taxonKey` 9623860 (Cantharellus) or 5
  (Fungi); URLs and counts are in data/t1/gbif_preview_counts.json (gitignored, on this machine
  only).

  | Box | Taxon | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2015 to 2025 |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | pnw | Cantharellus | 26 | 31 | 53 | 71 | 222 | 328 | 369 | 280 | 321 | 941 | 783 | 3425 |
  | pnw | Fungi | 2492 | 3073 | 4088 | 7635 | 13498 | 23467 | 27978 | 25323 | 40746 | 47079 | 54894 | 250273 |
  | east | Cantharellus | 187 | 188 | 284 | 502 | 479 | 566 | 817 | 391 | 1009 | 574 | 548 | 5545 |
  | east | Fungi | 39678 | 42927 | 49238 | 71463 | 74365 | 87402 | 109818 | 91612 | 126875 | 118720 | 132663 | 944761 |

  Two checks on this table. The two Fungi totals sum to 1,195,034, which equals the predicate
  search count above, so the polygon predicate and the search API's box parameters select the
  same records. The launching session's figure of 275,303 for PNW Fungi differs from 250,273
  here because it had no basisOfRecord filter. Inferred from the preview: the East box clears
  1,000 in every year before filtering; the PNW box has 3,425 in total with 2015 to 2017 under
  60 each, so it passes only if the filters keep more than about 30 percent, which the download
  alone can show. EVIDENCE.md:14 and 26 put hidden coordinates at 17.3 percent of North American
  research-grade Cantharellus records, and the uncertainty filter removes those; the rest of the
  loss is unknown.

### Item 2. Weather. Variables confirmed; rate limit does not fit; terms are non-commercial.

- Variables, verified live, with models=era5_seamless, timezone=UTC, 2024-09-01 to 2024-09-10:

  ```
  https://archive-api.open-meteo.com/v1/archive?latitude=47.0&longitude=-123.0&start_date=2024-09-01&end_date=2024-09-10&daily=temperature_2m_mean,precipitation_sum&hourly=soil_temperature_0_to_7cm,soil_moisture_0_to_7cm&models=era5_seamless&timezone=UTC
  HTTP 200   lat/lon returned: 47.0 -123.0 elevation 80.0
    daily.temperature_2m_mean: 10/10 non-null, unit °C, min 17.4 max 24.6 sum 204.4
    daily.precipitation_sum: 10/10 non-null, unit mm, min 0.0 max 0.0 sum 0.0
    hourly.soil_temperature_0_to_7cm: 240/240 non-null, unit °C, min 15.4 max 29.1 sum 4989.0
    hourly.soil_moisture_0_to_7cm: 240/240 non-null, unit m³/m³, min 0.163 max 0.21 sum 43.94

  https://archive-api.open-meteo.com/v1/archive?latitude=42.0&longitude=-77.0&start_date=2024-09-01&end_date=2024-09-10&daily=temperature_2m_mean,precipitation_sum&hourly=soil_temperature_0_to_7cm,soil_moisture_0_to_7cm&models=era5_seamless&timezone=UTC
  HTTP 200   lat/lon returned: 42.0 -77.0 elevation 538.0
    daily.temperature_2m_mean: 10/10 non-null, unit °C, min 11.1 max 20.2 sum 153.1
    daily.precipitation_sum: 10/10 non-null, unit mm, min 0.0 max 9.7 sum 12.7
    hourly.soil_temperature_0_to_7cm: 240/240 non-null, unit °C, min 10.6 max 22.8 sum 3833.4
    hourly.soil_moisture_0_to_7cm: 240/240 non-null, unit m³/m³, min 0.288 max 0.387 sum 79.05
  ```

  The PNW precipitation is 0.0 on all ten days, which is a dry spell, not a null: the same
  point returned 27.2, 7.3 and 5.2 mm for 2024-11-01 to 03 (Evidence, "Point versus cell").
  Full responses are in data/t1/openmeteo_pnw_era5_seamless.json and
  openmeteo_east_era5_seamless.json. T0b's finding that era5_seamless carries ERA5-Land
  temperature and soil with ERA5 precipitation was not re-derived; the soil sums here (4989.0,
  43.94) are close to but not equal to T0b's (4951.6, 43.7) because T0b requested
  timezone=auto, which shifts the 240-hour window by the UTC offset. Inferred.

- Rate limits and terms, verified: https://open-meteo.com/en/terms, section "Non-Commercial
  Use": "By using the Free API for non-commercial use you agree to following terms: Less than
  10'000 API calls per day, 5'000 per hour and 600 per minute. You may only use the free API
  services for non-commercial purposes. You accept to the CC-BY 4.0 licence". Examples on the
  same page: "Using our service for public research conducted at public institutions" is
  non-commercial; "Conducting undisclosed research at commercial entities" is commercial.
  https://open-meteo.com/en/pricing, "How is one API call defined?": "Requests for data
  covering more than 10 weather variables or extending over a period of more than 2 weeks for a
  single location are considered multiple API calls. To calculate the number of API calls
  accurately, fractional counts are used. For example, a request for 2 weeks of data with 15
  weather variables will be calculated as 1.5 API calls, while 4 weeks of data equals 3.0 API
  calls." Data licence: CC BY 4.0, attribution required (pricing page, "Is it necessary to
  provide attribution"). Saved copies: data/t1/openmeteo_terms.html, openmeteo_pricing.html.

- Does it fit? By the page's rule, coded as `api_call_units` in src/forager_forecast/
  open_meteo.py:66-70 and tested against the page's two examples, one cell with four variables
  for 2014-10-01 (90 days of lead before the first 2015 week) to 2025-12-31 is 4,110 days / 14 =
  293.6 call units. Computed:

  ```
  0.1 degree cells: PNW 75x40 = 3000 | East 80x140 = 11200 | total 14200
     100 cells ->       29,357 call units ->     2.9 days at 10,000/day
     500 cells ->      146,786 call units ->    14.7 days at 10,000/day
    1000 cells ->      293,571 call units ->    29.4 days at 10,000/day
    3000 cells ->      880,714 call units ->    88.1 days at 10,000/day
   14200 cells ->    4,168,714 call units ->   416.9 days at 10,000/day
  ```

  Only eligible cells need weather, and their number is unknown until the download exists; with
  944,761 fungal records in the East box, most of its 11,200 cells are likely eligible in some
  week (inferred). Whether the hourly soil variables weigh more than daily ones in the count is
  not stated on the page and was not tested. Whether this project is non-commercial is SPEC.md's
  open question ("Is the tool commercial?"), and the terms make it decisive here too. So item 2
  does not fit as a free-tier pull at 0.1 degree, and the options are the owner's (Proposed
  rows).

- Throttling, observed: one 100-location request took 6.1 s, a second identical one timed out at
  120 s and succeeded on retry after 20 s in 38.5 s, a third took 1.3 s. No 429 was received in
  this session. The verify script's backoff (scripts/verify-open-meteo-historical-fields.sh:
  61-89) remains the right shape.

- Amendment 2, cells per rain value, verified from two 10 by 10 blocks of grid points at 0.1
  degree spacing, 2024-11-01 to 2024-11-30, daily precipitation_sum and temperature_2m_mean,
  models=era5_seamless. PNW block lat 46.5 to 47.4, lon -123.5 to -122.6, requested with
  cell_selection=nearest and elevation=nan; East block lat 41.5 to 42.4, lon -77.5 to -76.6.
  Each letter is one distinct 30-day precipitation series:

  ```
  PNW block: 100 locations, 25 distinct rain series, 100 distinct temperature series
  group sizes: {1: 1, 2: 6, 3: 2, 4: 9, 6: 6, 9: 1}
         -123.5 -123.4 -123.3 -123.2 -123.1 -123.0 -122.9 -122.8 -122.7 -122.6
    47.4      U      U      V      V      W      W      W      X      X      Y
    47.3      P      P      Q      Q      R      R      R      S      S      T
    47.2      P      P      Q      Q      R      R      R      S      S      T
    47.1      K      K      L      L      M      M      M      N      N      O
    47.0      K      K      L      L      M      M      M      N      N      O
    46.9      K      K      L      L      M      M      M      N      N      O
    46.8      F      F      G      G      H      H      H      I      I      J
    46.7      F      F      G      G      H      H      H      I      I      J
    46.6      A      A      B      B      C      C      C      D      D      E
    46.5      A      A      B      B      C      C      C      D      D      E
  M 9 cells; lat 46.9 to 47.1; lon -123.1 to -122.9; Nov 2024 total 245.7 mm
  P 4 cells; lat 47.2 to 47.3; lon -123.5 to -123.4; Nov 2024 total 401.0 mm
  ```

  The East block gave the identical letter pattern and the identical size histogram. Reading:
  a 0.25 degree rain cell centred on a multiple of 0.25 covers 3 cells along an axis when its
  centre is a 0.1 grid point (47.0, -123.0) and 2 when it is not (47.25 sits between 47.2 and
  47.3), so full groups are 2x2 = 4, 2x3 = 6 or 3x3 = 9 cells; the 1s, 2s and 3s at the block's
  edge are groups cut by the block. Over a whole box the average is 3000 / (30 x 16) = 6.25 for
  the PNW and 11200 / (32 x 56) = 6.25 for the East. **Answer for the report: each rain value is
  shared by 4, 6 or 9 of the 0.1 degree cells, 6.25 on average.** Precipitation features will
  therefore be constant across those cells and take at most 480 distinct spatial values in the
  PNW box and 1,792 in the East. Responses: data/t1/openmeteo_pnw_grid_block_nearest.json,
  openmeteo_east_grid_block.json, with the URLs beside them.

### Item 3. Units. Confirmed and coded.

- Coordinate to cell, verified by asking the archive which grid point it used for eight nearby
  coordinates (data/t1/openmeteo_snap_probe.json):

  ```
  requested (47.0, -123.0)     -> returned lat 47.0      lon -123.0
  requested (47.04, -123.04)   -> returned lat 47.0      lon -123.0
  requested (47.049, -123.049) -> returned lat 47.0      lon -123.0
  requested (47.05, -123.05)   -> returned lat 47.100006 lon -123.1
  requested (47.051, -123.051) -> returned lat 47.100006 lon -123.1
  requested (47.06, -123.06)   -> returned lat 47.100006 lon -123.1
  requested (47.14, -122.96)   -> returned lat 47.100006 lon -123.0
  requested (46.96, -123.04)   -> returned lat 47.0      lon -123.0
  ```

  So the cell is the nearest 0.1 degree grid point with halves rounded away from zero
  (47.05 up, -123.05 to -123.1). `cell_for` in src/forager_forecast/cells.py:39-50 does this in
  Decimal, and tests/test_cells.py:15-40 holds exactly these seven cases plus the two where
  Python's round() would disagree. A cell is named by its centre in tenths of a degree
  ("470_-1230"). Whether the archive's own rounding is exactly half-away-from-zero at every
  half, or only at the ones probed, is inferred from these eight points.
- Date to ISO week: `iso_week_of` in cells.py:68-70 uses the standard library's isocalendar;
  tests/test_cells.py:48-68 covers the year-boundary cases (2021-01-01 is 2020-W53, 2024-12-30
  is 2025-W01). The week's Monday is the scored date (weather_windows.py:86-88).

### Amendment 1. Top weather features against 7 to 21 days. Cannot answer.

No model was fit, so there are no top features. The fixed window list (t1_design.py:44) spans
the 7 to 21 day rule of thumb unchanged.

### Amendment 2. Gradient-boosting wheel. Confirmed: lightgbm 4.7.0.

In a scratch uv project pinned to Python 3.14 (`uv init --python 3.14`; `uv add lightgbm`):

```
 + lightgbm==4.7.0   + narwhals==2.26.0   + numpy==2.5.3   + scipy==1.18.1
lightgbm 4.7.0 tags: ['py3-none-manylinux_2_27_x86_64', 'py3-none-manylinux_2_28_x86_64']
numpy 2.5.3 tags:    ['cp314-cp314-manylinux_2_27_x86_64', 'cp314-cp314-manylinux_2_28_x86_64']
scipy 1.18.1 tags:   ['cp314-cp314-manylinux_2_27_x86_64', 'cp314-cp314-manylinux_2_28_x86_64']
x86_64 ('glibc', '2.43') 3.14.4
lightgbm tiny synthetic fit ok, trees: 5 pred[0]: 0.4322
```

Then `uv add lightgbm==4.7.0` in the worktree (pyproject.toml:17, uv.lock +60 lines), and
tests/test_gradient_boosting.py repeats the import and a five-round fit on seeded random
numbers in CI. Alternatives resolved but not installed (`uv pip install --dry-run`): xgboost
3.4.1, which pulls nvidia-nccl-cu13 2.31.2 and is far larger; scikit-learn 1.9.1 with joblib,
threadpoolctl and cloudpickle. The Python 3.12 fallback in D20 was not needed and was not
exercised.

## What landed

| Commit | Change |
|---|---|
| ac12f55 | src/forager_forecast/{t1_design,cells,records,cell_weeks,weather_windows,open_meteo,gbif_download}.py, gbif/t1_fungi_two_boxes_2015_2025.json, seven test files, lightgbm==4.7.0 in pyproject.toml and uv.lock |
| next | this report |
| last | index row, session-log row, TASKS.md T1 status cell |

Tree added under src/forager_forecast/ and tests/ at ac12f55:

```
src/forager_forecast/t1_design.py        the dispatch's fixed choices and the two GBIF keys
src/forager_forecast/cells.py            Cell, cell_for, IsoWeek, iso_week_of
src/forager_forecast/records.py          Record, the five filter steps, apply_t1_filters
src/forager_forecast/cell_weeks.py       CellWeek, label_cell_weeks, positive/negative_units
src/forager_forecast/weather_windows.py  DailyWeather, window_features, calendar_place_features
src/forager_forecast/open_meteo.py       archive_request_url, api_call_units, daily_weather_from_archive
src/forager_forecast/gbif_download.py    credentials_from_env, load/expected predicate, submit
src/forager_forecast/gbif/t1_fungi_two_boxes_2015_2025.json
tests/test_cells.py test_records.py test_cell_weeks.py test_weather_windows.py
tests/test_open_meteo.py test_gbif_download.py test_gradient_boosting.py
```

Not landed, by design: any row loader for a download file, the random-date pseudo-absence
sampler, the model, the leave-one-year-out loop, the bootstrap, any table. None of it can be
exercised without the download, and the dispatch's order is verify first.

## Evidence

### Lint and tests, at ac12f55

```
uv run ruff check .          -> All checks passed!
uv run ruff format --check . -> 39 files already formatted
uv run pytest -q             -> 54 passed in 1.12s
```

The two tests the dispatch names:

- tests/test_weather_windows.py::test_no_feature_uses_weather_from_on_or_after_the_scored_date.
  A 400-day synthetic series with every value distinct; features for cell-week 2024-W36 (Monday
  2024-09-02); every day on or after the Monday set to 1e9; the feature row must be identical.
  Its positive control, test_the_leak_check_can_see_a_leak, poisons the day before instead and
  requires every weather feature to change and no calendar feature to.
- tests/test_cell_weeks.py::test_a_positive_cell_week_never_also_appears_as_a_negative. Seven
  synthetic records over three cells and two weeks, built so that one cell-week holds both a
  Cantharellus and an unrelated record; the positive and negative unit sets must be disjoint
  and every unit emitted once.

### Revert checks, both run and both restored from saved copies

Procedure each time: copy the module to /tmp, record its sha256, apply a one-line edit, run
that test file, restore with `cp` from the copy (not from git: the change was uncommitted at
the time), `sha256sum -c`, and grep that the edit's marker is gone.

1. weather_windows.py:41, windows shifted to end on the scored date
   (`range(window - 1, -1, -1)`). Three tests failed, the named one with
   `{'precipitation_sum_14d': 1000000004.2} != {'precipitation_sum_14d': 4.2}`, which is the
   sentinel leaking in. The positive control still passed, as it should. Restored: `OK`.
2. cell_weeks.py:43-61, one row emitted per record instead of one per unit. Two tests failed,
   the named one with `AssertionError: ['465_-1225@2024-W37', '470_-1230@2024-W36']`, the two
   units the fixture builds to carry both labels. Restored: `OK`.

Neither reverted build had a collection or import error; the failures are the ones the edits
predict.

### Point versus cell, verified live

Default request, 2024-11-01 to 03, three coordinates inside the cell 47.0, -123.0:

```
(47.0, -123.0)   -> elev 80.0  temp [8.7, 8.4, 8.8] rain [27.2, 7.3, 5.2]
(47.04, -123.04) -> elev 267.0 temp [7.4, 7.2, 7.6] rain [27.2, 7.3, 5.2]
(46.96, -123.04) -> elev 78.0  temp [8.7, 8.4, 8.8] rain [27.2, 7.3, 5.2]
```

Same cell, three elevations, two temperatures. The docs page says why (data/t1/
openmeteo_historical-weather-api.txt, parameter `elevation`): "The elevation used for
statistical downscaling. Per default, a 90 meter digital elevation model is used ... If
&elevation=nan is specified, downscaling will be disabled and the API uses the average
grid-cell height." With elevation=nan:

```
(47.0, -123.0)   elevation=nan -> elev 151.0 temp [8.2, 7.9, 8.3]
(47.04, -123.04) elevation=nan -> elev 151.0 temp [8.2, 7.9, 8.3]
```

And in the first PNW block request, made without cell_selection, 3 of 100 grid points came
back as a neighbour: `requested 47.1,-122.7 -> returned 47.1,-122.8 (elev 0.0)`,
`47.3,-122.7 -> 47.2,-122.7 (elev 0.0)`, `47.3,-122.6 -> 47.4,-122.6`. Those three are on Puget
Sound. The docs page, parameter `cell_selection`: "The default land finds a suitable grid-cell
on land with similar elevation to the requested coordinates using a 90-meter digital elevation
model." With cell_selection=nearest the same 100 points returned 100 distinct grid points with
0 mismatches. Both parameters are pinned in `archive_request_url`
(src/forager_forecast/open_meteo.py:47-63) and asserted in tests/test_open_meteo.py:15-31.

### GBIF backbone keys, verified

```
species/match?name=Cantharellus&strict=true            -> matchType NONE (homonym)
species/match?name=Cantharellus&rank=GENUS&kingdom=Fungi -> usageKey 9623860, ACCEPTED, Hydnaceae
species/match?name=Fungi                                -> usageKey 5, KINGDOM
```

### GBIF's Simple download format, verified

https://techdocs.gbif.org/en/data-use/download-formats (saved as data/t1/
gbif_download_formats.txt): SIMPLE_CSV carries gbifID, genus (name), taxonKey, speciesKey,
decimalLatitude, decimalLongitude, coordinateUncertaintyInMeters, eventDate, day, month, year
and basisOfRecord, and does not carry genusKey; genusKey is in the Darwin Core Archive's
occurrence.txt. So a loader for a SIMPLE_CSV file would match Cantharellus on the genus name
column or on the taxon's classification, and `Record.genus_key` (records.py:27) would be filled
from that. Not written; see Owner items on the format.

### Sizes and time

data/t1 on this machine: 916 KB, 27 files, all gitignored (`git check-ignore -v` names
.gitignore:6). Wall time for the session's live checks: about 40 minutes, most of it the
44 GBIF count requests and two Open-Meteo retries. Package versions: lightgbm 4.7.0, numpy
2.5.3, scipy 1.18.1, narwhals 2.26.0, rasterio 1.5.1, pyproj 3.8.0, pytest 9.1.1, ruff 0.16.8,
uv 0.12.17, Python 3.14.4. Seeds: 20260918 in test_gradient_boosting.py; nothing else random
ran.

## Deviations from the dispatch

- **Stopped at item 1**, as the dispatch instructs. No counts table with filter steps, no DOI,
  no skill table, no reliability table, no top ten features, no run time for a fit.
- **Item 2 answered as "does not fit"** on the rate limit, with the Copernicus alternative
  proposed and not acted on.
- **Two filter steps added** that the dispatch's filter list does not name: "inside a T1 box"
  and "year 2015 to 2025" (records.py:52-61, listed at 105-106). They re-check on the rows what the predicate
  selected and give the counts table its first two lines. They drop nothing the predicate would
  have kept.
- **Default dates**: the dispatch says "first of month at 00:00:00"; the code also drops a
  first-of-month record whose date carries no time at all (records.py:73-80). Reason: a defaulted
  date with its clock part stripped looks exactly like that, and GBIF's eventDate is a string
  that may or may not carry a time. This drops more than the dispatch's wording. If the owner
  prefers the literal rule, it is a one-line change with a test to flip.
- **Duplicates**: "keep one record per taxon, cell and day" keeps the lowest gbifID
  (records.py:87-97) so the result does not depend on file order. The dispatch does not say
  which to keep.
- **Extra pinned request parameters**: elevation=nan and cell_selection=nearest are not in the
  dispatch or D21. Both change the values a cell gets. They are here because the unit is the
  cell, and without them the archive returns point values and sometimes a different cell
  (Evidence). Recorded as a decision taken, open to reversal.

## Decisions taken here, and what was rejected

- **lightgbm over xgboost and scikit-learn.** Smallest wheel that resolves on 3.14 (xgboost
  pulls a 100 MB-class NVIDIA library; scikit-learn's boosting is fine but slower on this data
  size, from memory). Pinned exactly (pyproject.toml:17).
- **Nearest-grid-point cells, halves away from zero**, because that is what the archive does;
  the alternative, floor to the cell's south-west corner, would put records in a different cell
  from the one whose weather they get.
- **A missing day inside a window is an error** (weather_windows.py:54-59), not a shorter
  window; a window over fewer days would be a different feature under the same name.
- **A null in an archive response is an error** (open_meteo.py:73-111), not a skipped day; both
  T0b and this session saw the four variables fully populated under era5_seamless.
- **UTC for every archive request.** T0b used timezone=auto, which shifted hourly windows by the
  local offset; a day is defined once, in UTC, for both boxes.
- **The predicate is a JSON file read by code and held to t1_design by a test**
  (tests/test_gbif_download.py:18-28), so the boxes cannot drift between the file and the
  constants.
- **SIMPLE_CSV as the download format**, the smaller file; DWCA is the alternative (Owner
  items).
- **Credentials from GBIF_USER, GBIF_PWD, GBIF_EMAIL**, refusing by name when unset
  (gbif_download.py:44-63). Rejected: reading ~/.netrc, which nothing else here uses.
- **No loader, no sampler, no model code yet.** Rejected: writing them against the SIMPLE_CSV
  column list from the docs page, untested against a real file.
- **Preview counts through the search API, labelled as such**, because the dispatch's own
  premise needs a first look and the spec allows counts there. Rejected: paging the search API
  to fetch records, which the spec forbids and which caps at 100,000 anyway.

## Proposed DECISIONS.md rows (owner's call, not applied)

- **D24 (proposed). Weather pull for T1.** The Open-Meteo free tier is non-commercial and
  capped at 10,000 weighted calls a day; at 0.1 degree cells and 4,110 days a cell, that is
  about 34 cells a day (Item 2). Options, none chosen: (a) an Open-Meteo API subscription, which
  removes the daily cap and adds a commercial licence, and would settle SPEC.md's "Is the tool
  commercial?" for this source; (b) the Copernicus Climate Data Store, the dispatch's named
  fallback, ERA5-Land hourly at 0.1 degree plus ERA5 precipitation at 0.25 degree, which needs
  a CDS account (credentials again), a NetCDF or GRIB toolchain (xarray, netCDF4 or cfgrib, not
  yet checked for 3.14 wheels), and its own product check under R7, since "thresholds belong to
  their product" and this would be a different serving path from Open-Meteo unless the same
  archive is used at serve time; (c) throttled pulls within the free tier, feasible only if the
  eligible cell count is small, which the download will tell; (d) Open-Meteo's bulk open data on
  AWS (from memory, unverified: an S3 bucket in their own format with the ERA5 archives). The
  T0b and T1 evidence that era5_seamless returns ERA5-Land's own values suggests (b) is the same
  data, but that is inferred from equal sums at one point, not shown.
- **D25 (proposed). Cell-level archive requests.** Every archive request goes to the cell
  centre with elevation=nan and cell_selection=nearest, so a cell's weather is the cell's value
  and not a 90 m point downscale or a substituted land cell. Applies to serving as well as
  training if adopted. Alternative rejected: request at each record's coordinate, which gives
  up to 100 different temperature series inside one cell and breaks the unit.
- **D26 (proposed). One GBIF download for T1 and T2**, in DWCA format so T2 has genusKey and the
  identification fields, at the cost of a larger file. Alternative: SIMPLE_CSV for T1 as
  prepared, and a second download for T2.

## Owner items

1. **GBIF credentials.** Set GBIF_USER, GBIF_PWD and GBIF_EMAIL in the environment of the
   session that runs the pull (or tell the builder where else to read them; nothing else is read
   today, gbif_download.py:28-30). The request that would be submitted is
   `build_download_request(credentials, load_t1_predicate())` from
   src/forager_forecast/gbif_download.py: creator GBIF_USER, notificationAddresses [GBIF_EMAIL],
   sendNotification true, format SIMPLE_CSV (or DWCA per D26), predicate
   src/forager_forecast/gbif/t1_fungi_two_boxes_2015_2025.json, POSTed with HTTP basic auth to
   https://api.gbif.org/v1/occurrence/download/request. Expected size: 1,195,034 rows.
2. **Rule on D24**, the weather pull. Until then the weather half of T1 has a URL builder and a
   parser and no pull.
3. **Rule on D25 and D26**, or say they are the implementer's.
4. **The default-date rule** for date-only first-of-month records (Deviations).
5. The commercial-use question in SPEC.md now bears on Open-Meteo's terms directly.

## Not checked

- Anything about the records themselves: uncertainty values, obscured-record uncertainty
  figures, eventDate formats, duplicate rates. The claim that the 1,000 m filter removes
  obscured points is the dispatch's and is from memory here; T2's verify-first item 1 covers it.
- Whether Open-Meteo weighs hourly variables more than daily ones in its call count.
- Whether the archive's rounding at halves is away from zero at every half, or only at the six
  probed coordinates.
- The T0b finding that era5_seamless soil and temperature equal era5_land's; not re-run.
- The CDS toolchain's wheels on Python 3.14, and the AWS open-data option's existence.
- That the search API's `decimalLatitude=S,N` treats both ends inclusively the same way the
  `within` polygon does; the two totals agree to the record, which suggests so, and that is
  all.
- The behaviour of `submit_download_request` against the real endpoint with real credentials.
- CI on this branch: no pull request is open, so the workflow has not run; the same three
  commands passed locally at ac12f55.

## Conventions

Checked in this repo at f96d557: docs/audits/README.md for the index form and the append-only
rule; docs/audits/2026-09-18-t0b-completion-report.md for the header fields, "The short
version" first, the verify-first, landed, evidence, deviations, decisions, owner items and not
checked sections; pyproject.toml for exact pins and ruff settings; scripts/
verify-open-meteo-historical-fields.sh for the backoff shape and the models= pin; .gitignore for
data/ ; the Forager CLAUDE.md rules on revert checks (restore from a saved copy, read the
failure for the edit's own message) and on new capability as new functions. Followed all of
them. Terms: "sighting chance" is used where the quantity is named; the label R8 bans appears
nowhere in the added files (a case-insensitive `git grep` for it over src and tests returns
nothing).
