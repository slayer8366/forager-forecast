# Grid positions, part 2: exact-tie direction and off-grid area extraction (D46, D51): report

Answers `../dispatch/2026-09-22-grid-positions-d51-part2.md`. Written 2026-09-22, about 21:55 PDT
(2026-09-23T04:55Z), appended to branch `grid-positions-d51`, whose remote tip at the start was
`0212760bc7525d79e391198a3cc92520ea8130b1` (`git fetch`, then `git rev-parse origin/grid-positions-d51`, in
`~/Zynergy/forager-forecast-grid-positions-d51`). No file under `src/`, `tests/`, `pyproject.toml` or `uv.lock`
is changed. Part 1 is `2026-09-22-grid-positions-d51-report.md`.

Every position below comes from a `latitude`/`longitude` field Open-Meteo returned, from the committed
`cell_for`, or from a delivered NetCDF coordinate array, and names which.

## Result

- **Open-Meteo `era5_land`, exact 0.1° ties:** every latitude tie went to the higher latitude and every
  longitude tie went to the higher (less negative) longitude. That is toward +∞ on both axes, at all seven tie
  points.
- **Open-Meteo `era5`, exact 0.25° ties:** the same, toward +∞ on both axes, at all five tie points, including
  the repeat of part 1's (47.125, -123.125), which returned 47.25, -123.0 again.
- **`cell_for`:** agrees with Open-Meteo `era5_land` on every latitude tie and the control, and disagrees on
  every longitude tie (it goes 0.1° further west).
- **CDS off-grid box:** both delivered grids are part 1's point sets clipped to the new box, on multiples of the
  step, not shifted sets. D51's deduction that area extraction preserves the grid's points is **confirmed** by
  this pull, for these two datasets and this box.

## Open-Meteo exact-tie probe

URL form, as in part 1 (D25's pins, `src/forager_forecast/open_meteo.py:59-61` as part 1 cites them):
`https://archive-api.open-meteo.com/v1/archive?latitude=<lat>&longitude=<lon>&start_date=2024-06-01&end_date=2024-06-01&daily=precipitation_sum,temperature_2m_mean&models=<model>&elevation=nan&cell_selection=nearest&timezone=UTC`.
`<lat>` and `<lon>` were written exactly as in the tables below. All 15 returned HTTP 200. Account: none
(Open-Meteo is keyless). The returned bodies were kept, uncommitted, at
`data/grid-positions/open-meteo-part2-2024-06-01.json` (gitignored).

Every tie coordinate (47.25, 47.75, 49.25, -123.25, -123.75, -120.75, 47.125, 47.375, 48.625, -123.125,
-123.375, -120.875) is exactly representable in binary; checked with `Decimal(v) == Decimal(repr(v))`. The
non-tie coordinates 47.22, -123.22, 47.1 and -123.1 are **not** exact in binary. The dispatch says every
coordinate is; that holds only for the tie coordinates. The non-tie axis at each point lies at least 0.03°
from a half on the 0.1° grid and 0.025° on the 0.25° grid, so its inexactness cannot decide a tie.

As in part 1, 47.300003, 47.800003, 49.300003 and 47.199997 look like single-precision renderings of 47.3, 47.8,
49.3 and 47.2. That is inferred from their form, and they are read that way in the direction columns.

### (a) `models=era5_land`, 0.1°

| Requested at (UTC) | Point (lat, lon) | Tie | Returned `latitude`, `longitude` | Lat tie went | Lon tie went | `cell_for` | Agrees with OM |
|---|---|---|---|---|---|---|---|
| 2026-09-23T04:50:14 | 47.25, -123.22 | lat | 47.300003, -123.2 | +∞, away from zero | (no tie) | 47.3, -123.2 | yes |
| 2026-09-23T04:50:16 | 47.75, -123.22 | lat | 47.800003, -123.2 | +∞, away from zero | (no tie) | 47.8, -123.2 | yes |
| 2026-09-23T04:50:18 | 47.22, -123.25 | lon | 47.199997, -123.2 | (no tie) | +∞, toward zero | 47.2, -123.3 | **no** (lon) |
| 2026-09-23T04:50:20 | 47.22, -123.75 | lon | 47.199997, -123.7 | (no tie) | +∞, toward zero | 47.2, -123.8 | **no** (lon) |
| 2026-09-23T04:50:23 | 47.25, -123.25 | both | 47.300003, -123.2 | +∞, away from zero | +∞, toward zero | 47.3, -123.3 | **no** (lon) |
| 2026-09-23T04:50:25 | 47.75, -123.75 | both | 47.800003, -123.7 | +∞, away from zero | +∞, toward zero | 47.8, -123.8 | **no** (lon) |
| 2026-09-23T04:50:27 | 49.25, -120.75 | both | 49.300003, -120.7 | +∞, away from zero | +∞, toward zero | 49.3, -120.8 | **no** (lon) |
| 2026-09-23T04:50:29 | 47.22, -123.22 | control | 47.199997, -123.2 | (no tie) | (no tie) | 47.2, -123.2 | yes |

`cell_for` was run from the committed module, read-only, with `uv run python -c` in the worktree
(`from forager_forecast.cells import cell_for`), printing `center_latitude`, `center_longitude` and `id`:

```
47.25 -123.22 -> 47.3 -123.2 473_-1232
47.75 -123.22 -> 47.8 -123.2 478_-1232
47.22 -123.25 -> 47.2 -123.3 472_-1233
47.22 -123.75 -> 47.2 -123.8 472_-1238
47.25 -123.25 -> 47.3 -123.3 473_-1233
47.75 -123.75 -> 47.8 -123.8 478_-1238
49.25 -120.75 -> 49.3 -120.8 493_-1208
47.22 -123.22 -> 47.2 -123.2 472_-1232
```

`uv run` created the gitignored `.venv/`; `git status --short` was empty before and after.

### (b) `models=era5`, 0.25°

| Requested at (UTC) | Point (lat, lon) | Tie | Returned `latitude`, `longitude` | Lat tie went | Lon tie went |
|---|---|---|---|---|---|
| 2026-09-23T04:50:31 | 47.125, -123.1 | lat | 47.25, -123.0 | +∞, away from zero | (no tie) |
| 2026-09-23T04:50:34 | 47.375, -123.1 | lat | 47.5, -123.0 | +∞, away from zero | (no tie) |
| 2026-09-23T04:50:36 | 47.1, -123.125 | lon | 47.0, -123.0 | (no tie) | +∞, toward zero |
| 2026-09-23T04:50:39 | 47.1, -123.375 | lon | 47.0, -123.25 | (no tie) | +∞, toward zero |
| 2026-09-23T04:50:41 | 47.125, -123.125 | both (part 1 repeat) | 47.25, -123.0 | +∞, away from zero | +∞, toward zero |
| 2026-09-23T04:50:43 | 48.625, -120.875 | both | 48.75, -120.75 | +∞, away from zero | +∞, toward zero |
| 2026-09-23T04:50:45 | 47.1, -123.1 | control | 47.0, -123.0 | (no tie) | (no tie) |

The non-tie axes all returned the nearest 0.25° point: 47.1 to 47.0, -123.1 to -123.0.

### Tie rule observed

| Model | Latitude ties | Longitude ties |
|---|---|---|
| `era5_land` (0.1°) | toward +∞, 5 of 5 | toward +∞, 5 of 5 |
| `era5` (0.25°) | toward +∞, 3 of 3 | toward +∞, 3 of 3 |

The results are not mixed. One limit: every probed latitude is positive and every probed longitude is negative.
So on the latitude axis "toward +∞" and "away from zero" describe the same observations, and on the longitude
axis "toward +∞" and "toward zero" do. The one rule that fits both axes of both models is toward +∞. No
negative-latitude or positive-longitude tie was probed, so these results cannot tell that rule from
"latitude away from zero, longitude toward zero".

## CDS off-grid area

Both part 1 requests were repeated with only `area` changed to `[47.47, -123.47, 46.53, -122.53]`, whose edges
lie on neither the 0.1° nor the 0.25° grid. Client `cdsapi==0.7.7`, run as
`uv run --no-project --with cdsapi==0.7.7` from `/tmp`. Account: the D43 test account, the ECMWF login recorded
at `../planning/evidence/cds-credentials-report.md:37`; the key was read by `cdsapi` from `~/.cdsapirc` and
appears nowhere (the two run logs were checked for it: 0 occurrences each). The store asked for no terms.

Stored requests, each with its request time and account:
- `../pulls/grid-positions/derived-era5-land-daily-statistics-2024-06-01-offgrid.request.json`
- `../pulls/grid-positions/derived-era5-single-levels-daily-statistics-2024-06-01-offgrid.request.json`

`diff` against part 1's stored requests shows only `area` and `requested_at_utc` changed.

Coordinates were read with an uncommitted scratch script (`netCDF4` and `numpy` via
`uv run --no-project --with`). "On multiples" was tested in `Decimal`: each coordinate's `repr` rounded to 9
places, divided by the step, compared with its integral value. Steps are the distinct values of `numpy.diff`,
rounded to 9 places.

| | ERA5-Land daily statistics | ERA5 single-levels daily statistics |
|---|---|---|
| Requested at (UTC) | 2026-09-23T04:51:10 | 2026-09-23T04:51:56 |
| Job id | `af33b123-ee5e-4fe7-95bb-f4889a3fbd05` | `6cf9929e-2e33-414e-b2cd-6b09ace0e032` |
| Status path (PDT) | accepted 21:51:12, running 21:51:35, successful 21:51:47 | accepted 21:51:59, running 21:52:35, successful 21:52:53 |
| Delivered as (in gitignored `data/grid-positions/`) | `derived-era5-land-daily-statistics-2024-06-01-offgrid.nc`, 25157 bytes (server name `36f60c1dedd463fe1338bcc4513c5c92.nc`) | `derived-era5-single-levels-daily-statistics-2024-06-01-offgrid.nc`, 25198 bytes (server name `16da96a4c50a7792c042a6cbcba5f9a5.nc`) |
| Dimensions | valid_time 1, latitude 9, longitude 9; `t2m` | valid_time 1, latitude 3, longitude 3; `tp` |
| latitude first / last | 47.4 / 46.6 | 47.25 / 46.75 |
| longitude first / last | -123.4 / -122.6 | -123.25 / -122.75 |
| Step | lat -0.1, lon 0.1 | lat -0.25, lon 0.25 |
| Every point on a multiple of the step | yes, both axes (largest raw float distance 4.5e-14) | yes, both axes (largest raw distance 0) |
| Latitudes | 47.4, 47.3, … 46.6 | 47.25, 47.0, 46.75 |
| Longitudes | -123.4, -123.3, … -122.6 | -123.25, -123.0, -122.75 |
| Part 1's set clipped to [46.53, 47.47] × [-123.47, -122.53] | equal, both axes | equal, both axes |
| Shifted set | no | no |

Both files are the same byte size as part 1's (25157 and 25198). Their coordinate arrays differ from part 1's
(9 and 3 points per axis against 11 and 5), as read above, so they are not copies of part 1's files. The same
`time_shift` attributes as part 1 appear (`0 days 00:00:00` on ERA5-Land, `-1 days +23:00:00` on ERA5); they are
recorded and, as the dispatch directs, not investigated.

**D51.** D51's reasons record the deduction that the store's area extraction "should preserve those points"
(the full grid's points at multiples of 0.1°). For a box whose edges lie on neither grid, both datasets delivered
points at multiples of the step, the part 1 set clipped to the box, with nothing anchored at the box's corner.
The deduction is **confirmed** for these two datasets and this box. The longitudes are delivered in -180 to 180,
as part 1 found, not the 0 to 360 of the full-grid files D51 cites.

## Against the prediction

- Dispatch: Open-Meteo resolves exact ties toward +∞ on both axes for both models. **Observed** at every tie
  (sign limit above).
- Dispatch: `cell_for` disagrees on negative-longitude ties and agrees on positive-latitude ties. **Observed.**
- Dispatch: the off-grid pull returns points on multiples of the step, clipped. **Observed**; D51 confirmed.
- Coder's mechanism prediction (Forager record, intent 2026-09-23-13): `cell_for` values and the CDS arrays
  matched exactly. The prediction that Open-Meteo's 0.1° ties might go toward -∞ or be mixed, from
  single-precision division by 0.1, was **wrong**: they went toward +∞ like the 0.25° ties.

## Secret check

`git grep -c -F` over every tracked file on this branch, with this report and its index row staged, for the CDS
key value and the `GBIF_PWD` value, each read into a shell variable and never printed: CDS key, 0 files;
`GBIF_PWD`, 0 files. The same key check over the two CDS run logs in `/tmp` found 0.

## Not checked

- Ties at negative latitude or positive longitude, which would separate "toward +∞" from "away from zero" and
  "toward zero".
- Any other box, date or dataset at the CDS.
- Open-Meteo's code; the reason for its tie direction is not known.
- `time_shift`, null ERA5-Land precipitation, `frequency`, `product_type`: out of scope here.

## Decisions I made

- The Open-Meteo response bodies were kept in the gitignored `data/` and not committed. Part 1 committed its
  bodies. This dispatch lists the files to commit and does not list an Open-Meteo file, so I read it as not
  wanted. The URLs, times and returned coordinates are in the tables above.
- "Toward +∞" is read, for longitude, as toward the less negative value, and the direction columns use that.
- The file sizes are given for the files as saved under `data/`. The server's file names are given as well.
- The off-grid files were saved under my own names in `data/grid-positions/`, with `-offgrid` in the name.
