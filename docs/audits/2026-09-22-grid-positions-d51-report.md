# Grid positions from delivered data (D46, D51, D54): report

Answers `../dispatch/2026-09-22-grid-positions-d51.md` (revision 2). Written 2026-09-22, about 21:45 PDT
(2026-09-23T04:45Z), against `origin/main` `82f28b65e1c46148c0518e30b411428ee0a7e2bb`, read by `git fetch` and
`git rev-parse origin/main` in `~/Zynergy/forager-forecast-t0b` at the start. Branch `grid-positions-d51`, cut
from that commit. No file under `src/`, `tests/`, `pyproject.toml` or `uv.lock` is changed.

Every position number below comes from a delivered NetCDF coordinate array or from a `latitude`/`longitude`
field returned by Open-Meteo, and names which. None comes from documentation.

## Result in one paragraph

Both delivered grids use longitudes in -180 to 180 and descending latitudes. The ERA5-Land daily-statistics
file's points lie on multiples of 0.1 (within 5e-14 float noise). The ERA5 single-levels daily-statistics
file's points lie exactly on multiples of 0.25. `cell_for` agrees with the nearest delivered 0.1° point at every
probe point where one point is nearest. It also agrees with Open-Meteo's `era5_land` centre at all seven probe
points. At the 0.25° grid, the nearest delivered point and Open-Meteo's `era5` centre agree at every probe
point where one point is nearest. `cell_for` has no 0.25° mode.

There are three limits, all detailed below:
- The area I requested has edges on both grids, so the pull cannot tell a grid anchored at multiples of the
  step from one anchored at the request's corner.
- At the one exact 0.25° tie, Open-Meteo rounded longitude toward zero, not away from zero, which is not the
  rule `cells.py` states.
- The precipitation file's time coordinate carries a `time_shift` attribute of minus one hour.

## Open-Meteo probe

Stored: `../pulls/grid-positions/open-meteo-2024-06-01.json`, which holds each exact URL, its request time
(UTC), HTTP status, and the full returned body. Account: no account (Open-Meteo is keyless). All 14 returned 200.

Every URL has the form
`https://archive-api.open-meteo.com/v1/archive?latitude=<lat>&longitude=<lon>&start_date=2024-06-01&end_date=2024-06-01&daily=precipitation_sum,temperature_2m_mean&models=<model>&elevation=nan&cell_selection=nearest&timezone=UTC`.
These are D25's pins, as `src/forager_forecast/open_meteo.py:59-61` sets them.

| Requested at (UTC) | latitude, longitude | models | returned `latitude`, `longitude` |
|---|---|---|---|
| 2026-09-23T04:39:03 | 47.049, -123.049 | era5_land | 47.0, -123.0 |
| 2026-09-23T04:39:05 | 47.05, -123.05 | era5_land | 47.100006, -123.1 |
| 2026-09-23T04:39:06 | 47.051, -123.051 | era5_land | 47.100006, -123.1 |
| 2026-09-23T04:39:08 | 47.125, -123.125 | era5_land | 47.100006, -123.1 |
| 2026-09-23T04:39:09 | 47.12, -123.13 | era5_land | 47.100006, -123.1 |
| 2026-09-23T04:39:10 | 47.13, -123.12 | era5_land | 47.100006, -123.1 |
| 2026-09-23T04:39:11 | 47.2, -123.2 | era5_land | 47.199997, -123.2 |
| 2026-09-23T04:39:13 | 47.049, -123.049 | era5 | 47.0, -123.0 |
| 2026-09-23T04:39:14 | 47.05, -123.05 | era5 | 47.0, -123.0 |
| 2026-09-23T04:39:15 | 47.051, -123.051 | era5 | 47.0, -123.0 |
| 2026-09-23T04:39:16 | 47.125, -123.125 | era5 | 47.25, -123.0 |
| 2026-09-23T04:39:18 | 47.12, -123.13 | era5 | 47.0, -123.25 |
| 2026-09-23T04:39:20 | 47.13, -123.12 | era5 | 47.25, -123.0 |
| 2026-09-23T04:39:21 | 47.2, -123.2 | era5 | 47.25, -123.25 |

The returned values 47.100006 and 47.199997 look like single-precision renderings of 47.1 and 47.2. That is
inferred from their form; the API does not say so. They are read as 47.1 and 47.2 below. `era5_land` returned
`precipitation_sum` null at every point, which matches D19's reason as quoted in D54.

## CDS request schema

Read from the store's own API process descriptions, on the host `~/.cdsapirc` names
(`https://cds.climate.copernicus.eu/api`). Only the `url:` line was read; the key was not printed.

- `https://cds.climate.copernicus.eu/api/retrieve/v1/processes/derived-era5-land-daily-statistics`, read
  2026-09-23T04:39:43Z, HTTP 200, 6163 bytes, version 1.0.0.
- `https://cds.climate.copernicus.eu/api/retrieve/v1/processes/derived-era5-single-levels-daily-statistics`,
  read 2026-09-23T04:39:45Z, HTTP 200, 14737 bytes, version 1.0.0.

The fields used, quoted from the `inputs` of each. "Land" means the ERA5-Land dataset and "single" means
the single-levels dataset.

| Field | Schema (land) | Schema (single) | Value used |
|---|---|---|---|
| `variable` | array, enum of 31, includes `2m_temperature`, no `total_precipitation` | array, enum of 262, includes `total_precipitation` | land `["2m_temperature"]`; single `["total_precipitation"]` (D54) |
| `daily_statistic` | `"enum": ["daily_mean", "daily_maximum", "daily_minimum"]`, default `daily_mean` | `"enum": ["daily_sum", "daily_mean", "daily_maximum", "daily_minimum"]`, default `daily_mean` | land `daily_mean`; single `daily_sum` (D54) |
| `time_zone` | enum `utc+00:00` … `utc+14:00`, `utc-01:00` … `utc-12:00`, default `utc+00:00` | same | `utc+00:00` (D52, D54) |
| `frequency` | `"enum": ["1_hourly", "3_hourly", "6_hourly"]`, no default | same | `1_hourly`; see Decisions |
| `product_type` | absent | `"enum": ["reanalysis", "ensemble_mean", "ensemble_members"]`, default `reanalysis` | `reanalysis`; see Decisions |
| `year` | string, enum of 77 | string, enum of 87 | `"2024"` |
| `month` | **string**, enum `01`…`12` | **array** of string, enum `01`…`12` | land `"06"`; single `["06"]` |
| `day` | array of string, enum `01`…`31` | same | `["01"]` |
| `area` | `"Area selection"`, array of 4 numbers, default `[90, -180, -90, 180]` | same | `[47.5, -123.5, 46.5, -122.5]` |

Neither schema has a data-format field. Both files arrived as NetCDF (`application/netcdf`, HDF5 magic).

## CDS pulls

Client: `cdsapi==0.7.7`, the latest on PyPI (read 2026-09-23T04:40:35Z; uploaded 2025-09-30). It was run as
`uv run --no-project --with cdsapi==0.7.7` from `/tmp`, with no change to the project. Account: the D43 test
account, the ECMWF login recorded at `../planning/evidence/cds-credentials-report.md:37`. The key was read by
`cdsapi` from `~/.cdsapirc` and appears nowhere. The store asked for no terms.

Each stored request is under `../pulls/grid-positions/`, as
`<dataset>-2024-06-01.request.json` with its time and account. The delivered files are in the gitignored
`data/grid-positions/` only.

| | ERA5-Land daily statistics | ERA5 single-levels daily statistics |
|---|---|---|
| Requested at (UTC) | 2026-09-23T04:41:07 | 2026-09-23T04:41:50 |
| Job id | `ba0fb12f-bcca-4966-b8ea-947fce969182` | `95ee13ef-18b0-4f9f-9443-0263d6892e5f` |
| Status path | accepted 21:41:08, running 21:41:25, successful 21:41:45 PDT | accepted 21:41:53, successful 21:42:18 PDT |
| Delivered as | `643841da217465e19949fef2c5a09c6b.nc`, 25157 bytes | `804e96056b84720f0ed89cc2c1347b7a.nc`, 25198 bytes |
| Dimensions | valid_time 1, latitude 11, longitude 11; `t2m` | valid_time 1, latitude 5, longitude 5; `tp` |
| latitude first / last | 47.5 / 46.5, `stored_direction: decreasing` | 47.5 / 46.5, `stored_direction: decreasing` |
| longitude first / last | -123.5 / -122.5 | -123.5 / -122.5 |
| Step | 0.1 (lat -0.1), from `numpy.diff` rounded to 1e-9 | 0.25 (lat -0.25) |
| Longitude convention | -180 to 180 (negative, `degrees_east`) | -180 to 180 (negative, `degrees_east`) |
| On multiples of the step | yes: largest distance of any coordinate from a multiple of 0.1 is 5e-14 | yes, exactly: largest distance 0 |
| `valid_time` `time_shift` attr | `0 days 00:00:00` | `-1 days +23:00:00` |

The ERA5-Land arrays carry float accumulation noise, for example latitude `47.199999999999996` and longitude
`-123.00000000000003`. The values look like they were generated as start plus i times step. That is inferred
from their pattern. A consumer that matches coordinates by float equality would miss them.

**Limit on what the pull shows.** The requested box's edges (47.5, 46.5, -123.5, -122.5) are themselves multiples
of both 0.1 and 0.25. So a grid anchored at multiples of the step and a grid anchored at the request's
north-west corner would deliver identical arrays. The pull confirms the positions for this request. It does not
confirm D51's deduction that area extraction preserves the global grid's points whatever the box. A box with
edges off both grids (for example 47.53, -123.47, 46.47, -122.53) would separate the two. That pull was not
specified and was not made.

## Per-point table

`cell_for` comes from `src/forager_forecast/cells.py:44`, run unmodified with `PYTHONPATH=src`. "Nearest
delivered" was computed in `Decimal` on the probe's exact decimal value, against the delivered coordinates
rounded to 9 places. Where two points are equally near, both are listed as a tie. Open-Meteo's 47.100006 and
47.199997 are read as 47.1 and 47.2.

| Probe point | `cell_for` | Nearest delivered 0.1° | OM `era5_land` | 0.1° agreement | Nearest delivered 0.25° | OM `era5` | 0.25° agreement |
|---|---|---|---|---|---|---|---|
| 47.049, -123.049 | 47.0, -123.0 | 47.0, -123.0 | 47.0, -123.0 | all agree | 47.0, -123.0 | 47.0, -123.0 | agree |
| 47.05, -123.05 | 47.1, -123.1 | **tie**: lat 47.1 or 47.0, lon -123.1 or -123.0 | 47.1, -123.1 | `cell_for` = OM; delivered grid cannot decide | 47.0, -123.0 | 47.0, -123.0 | agree |
| 47.051, -123.051 | 47.1, -123.1 | 47.1, -123.1 | 47.1, -123.1 | all agree | 47.0, -123.0 | 47.0, -123.0 | agree |
| 47.125, -123.125 | 47.1, -123.1 | 47.1, -123.1 | 47.1, -123.1 | all agree | **tie**: lat 47.25 or 47.0, lon -123.25 or -123.0 | 47.25, -123.0 | delivered grid cannot decide; OM picks lat up, lon toward zero |
| 47.12, -123.13 | 47.1, -123.1 | 47.1, -123.1 | 47.1, -123.1 | all agree | 47.0, -123.25 | 47.0, -123.25 | agree |
| 47.13, -123.12 | 47.1, -123.1 | 47.1, -123.1 | 47.1, -123.1 | all agree | 47.25, -123.0 | 47.25, -123.0 | agree |
| 47.2, -123.2 | 47.2, -123.2 | 47.2, -123.2 | 47.2, -123.2 | all agree | 47.25, -123.25 | 47.25, -123.25 | agree |

No disagreement appears at any point where a single point is nearest. The disagreements and undecided cases:

1. **(47.05, -123.05), 0.1°.** This is an exact decimal tie, so the delivered grid does not decide it.
   `cell_for` and Open-Meteo both give 47.1, -123.1, as on 2026-09-18 (`cells.py:5-7`). Neither 47.05 nor
   -123.05 is exact in binary, so this probe does not show which way Open-Meteo resolves an exact tie. Its
   answer may come from float representation, not a rounding rule. That is inferred; Open-Meteo's code was not
   read.
2. **(47.125, -123.125), 0.25°.** Both values are exact in binary, so this is a true tie on both axes.
   Open-Meteo returned latitude 47.25, which is away from zero, and longitude **-123.0, which is toward zero**.
   That is consistent with rounding halves toward +infinity, not away from zero. It is one observation, and the
   rule is inferred. `cells.py:4-5` states that halves round away from zero, which `_tenths` at `:39` applies
   through `ROUND_HALF_UP` on both axes. At a western longitude tie that would give the opposite answer to this
   observation. The observation is on the 0.25° grid, where `cell_for` does not apply. No exact 0.1° tie was
   probed.
3. **`cell_for` has no 0.25° mode.** `GRID_STEP_DEGREES` is fixed at 0.1 (`cells.py:16`), and no 0.25° code
   exists on main. Each record's nearest 0.25° point, which D54 requires, cannot be computed by current code.
   This is a finding, not a fix.

## Against the prediction

Expectations from the dispatch:
- ERA5-Land on multiples of 0.1 and ERA5 on multiples of 0.25: **observed**, with the limit above.
- CDS longitude convention unknown: **-180 to 180** for this area request, on both files.
- Open-Meteo `era5_land` matching `cell_for`, including at the halves: **observed at all seven points**. The one
  "half" probed is not an exact binary tie (finding 1).
- Open-Meteo `era5` returning 0.25° centres: **observed** at all seven.

The coder's mechanism prediction in the Forager record (intent 2026-09-23-11) matched on every point, except
that it did not foresee the tie-direction finding or the `time_shift` attribute.

## Secret check

`git grep -c` over every tracked file on this branch, for the CDS key value and the `GBIF_PWD` value, each read
into a shell variable and never printed, run over the index with this report and the request files staged:
CDS key, 0 files; `GBIF_PWD`, 0 files. The same key check over the uncommitted pull output and log in `/tmp`
also found 0.

## Not checked

- Any area not aligned to both grids (see the limit above).
- An exact 0.1° tie at Open-Meteo.
- What `time_shift: -1 days +23:00:00` on the precipitation file's `valid_time` means for D52's "no shift" and
  for D54's UTC-day sum. It is recorded here as read and not interpreted.
- The data values themselves. `t2m` and `tp` were not compared with Open-Meteo, which is the D24 equivalence test
  and out of scope.

## Decisions I made

- `frequency` = `1_hourly`. The dispatch says "the frequency the schema offers for the base data". The schema
  offers `1_hourly`, `3_hourly` and `6_hourly` with no default and no description. I read "the base data" as the
  hourly datasets named at `../planning/evidence/cds-credentials-report.md:19-20`. Deciding it properly needs a
  ruling on which sub-daily frequency the daily statistics are computed from.
- `product_type` = `reanalysis`, on the single-levels dataset. No value is listed in the dispatch. I took it as
  fixed by D54 read with D24 (DECISIONS.md:38, "The store serves the same reanalysis"), and by D54 comparing
  this sum with Open-Meteo's ERA5. It is also the schema default. Deciding it properly needs a ruling that names
  the product type.
- Area `[47.5, -123.5, 46.5, -122.5]`, my reading of "about 1° around 47°N, -123°". Choosing edges on the grid is
  what causes the limit above.
- Storing Open-Meteo's full returned bodies beside the URLs, beyond the URL, time and account the dispatch asked
  for, so the returned `latitude`/`longitude` can be checked against their source.
