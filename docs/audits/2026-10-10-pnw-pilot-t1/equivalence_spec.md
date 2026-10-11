# D24 equivalence test: sample and tolerance, fixed before any weather value is read

Written 2026-10-10, on branch pnw-pilot-t1, before any CDS file arrived and before any Open-Meteo
request was made. These are the builder's choices. The planner relayed that the tolerance reading
"is fine to commit as a builder choice" (Forager RECORD -812, item 2).

## What is compared

The store's daily values (`scripts/pnw_cds_pull.py`) are compared with Open-Meteo's archive,
pinned per D19, D21 and D25 (`src/forager_forecast/open_meteo.py`: `models=era5_seamless`,
`elevation=nan`, `cell_selection=nearest`, `timezone=UTC`). Each value is compared at the same
0.1° cell and UTC day.

| Variable | Store | Open-Meteo | Unit |
|---|---|---|---|
| Temperature | ERA5-Land daily statistics `2m_temperature` `daily_mean`, minus 273.15 | daily `temperature_2m_mean` | °C |
| Precipitation | ERA5 single-levels daily statistics `total_precipitation` `daily_sum` × 1000, at the 0.25° point nearest the cell centre (`cells.quarter_cell_for`, D46, D54) | daily `precipitation_sum` | mm |
| Soil temperature 0 to 7 cm | ERA5-Land `soil_temperature_level_1` `daily_mean`, minus 273.15 | mean of the 24 hourly `soil_temperature_0_to_7cm` values | °C |
| Soil moisture 0 to 7 cm | ERA5-Land `volumetric_soil_water_layer_1` `daily_mean` | mean of the 24 hourly `soil_moisture_0_to_7cm` values | m³/m³ |

## Sample

- **Cells:** 12 distinct 0.1° cells. They are drawn with seed 20260918 (`numpy.random.default_rng`,
  `choice` without replacement over the sorted cell ids) from the cells holding at least one
  eligible T1 PNW cell-week. These are land cells, and they are the cells the fit uses. The draw
  needs only the record pass, not weather.
- **Days:** for each cell, 3 start days drawn with the same generator, continuing after the cell
  draw. They are uniform over 2015-01-01 to 2025-12-22. Each start day opens a 7-day span. That
  gives 12 × 3 × 7 = 252 cell-days and 1,008 compared values. There are 36 Open-Meteo requests,
  each one location for 7 days, far under the free tier's limits.

## Tolerance ("within rounding", D24)

A value matches when the absolute difference is at most half a unit of Open-Meteo's displayed
precision, plus 1e-6:

- temperature: 0.05 °C
- precipitation: 0.05 mm
- soil temperature: 0.05 °C
- soil moisture: 0.0005 m³/m³

The precision is read from the returned JSON. If a variable comes back at a different number of
decimals, the half-unit is taken from what was returned, and the report says so. The 24-hour soil
means are taken from rounded hourly values, so they carry the same half-unit bound.

**Pass:** every one of the 1,008 values matches. **Any mismatch** is reported by variable, cell and
day, and the fit waits for the owner (D24: "must match within rounding" "before any model is fit";
the paid-plan fallback is the owner's call). Nothing is re-sampled or loosened after a value is
seen.

---

## Restated 2026-10-10, before any Open-Meteo body was read (review B2, Forager RECORD -818)

The tolerance above is replaced. It is not edited above, so the original wording stands as
written. Why: the parallel review (origin/pnw-pilot-t1-review `222e927`,
`docs/audits/2026-10-10-pnw-pilot-t1-review.md`, B2) read Open-Meteo's own source
(`Sources/App/Era5/Era5Variables.swift:148, :151, :156, :158`). Open-Meteo stores hourly ERA5
quantised: temperature_2m and soil_temperature_0_to_7cm at 1/20 °C, precipitation at 0.1 mm per
hour, soil moisture at 1/1000. Half a display unit cannot hold the same product under that
storage. The owner's ruling (RECORD -818), verbatim: "Allow Open-Meteo's own rounding
(Recommended)".

A value now matches when the absolute difference is at most half Open-Meteo's storage step plus
half its display unit, plus 1e-6:

| Variable | Storage step | Display unit | Bound |
|---|---|---|---|
| Temperature (daily mean) | 0.05 °C | 0.1 °C | 0.075 °C |
| Soil temperature (mean of 24 displayed hours) | 0.05 °C | 0.1 °C | 0.075 °C |
| Soil moisture (mean of 24 displayed hours) | 0.001 | 0.001 | 0.001 m³/m³ |
| Precipitation (daily sum) | 0.1 mm per hour, 24 hours | 0.1 mm | 24 × 0.05 + 0.05 = 1.25 mm |

The precipitation bound is the rounding of its hours: each stored hour can be off by half its
step, and the daily figure is displayed to 0.1 mm. Hourly `precipitation` is now also requested,
for the convention test below. The span is extended by one day so that hour 24 (00:00 of the next
day) exists.

**Convention test (review B2 (c)).** Over the whole sample, the store's daily rain is compared
with two sums of Open-Meteo's hourly rain: hours 00 to 23 of the UTC day, and hours 01 to 24.
The test reports which is closer, by mean absolute difference and by the count of days where each
is closer. This separates a shifted day boundary from rounding, which the bound cannot. It is
reported and is not a pass condition.

Pass, mismatch and stop are unchanged: any value beyond its bound is reported by variable, cell
and day, and goes to the owner. **Status changed by RECORD -819** ("Copernicus for both
(Recommended)"): the pilot trains and scores on the store's data, so this test is run to completion
and reported, but it no longer gates the pilot fit. D24 and D19 are bent for the pilot only.

---

## Hourly land route, added 2026-10-10 before any Open-Meteo body was read (review S7)

The planner set this as the land-route check, in place of the daily stand-in. No derived land
month is available, because the derived queue did not move. At 0.075 °C, daily values cannot tell
a one-hour day-boundary shift from rounding. Hourly values can, the way the rain check did.

- For the same 36 spans, Open-Meteo is also asked for hourly `temperature_2m`,
  `soil_temperature_0_to_7cm` and `soil_moisture_0_to_7cm`, pinned as above
  (`models=era5_seamless`, D19; D25's two pins). Each is compared hour by hour with this pull's
  hourly ERA5-Land files at the cell's own point, at offsets −1, 0 and +1 hour.
- Bounds: 0.075 °C for both temperatures (half of Open-Meteo's 1/20 °C storage step plus half
  its 0.1 °C display unit) and 0.001 m³/m³ for soil moisture (half of 1/1000 plus half of 0.001).
- **Pass:** at offset 0 every compared hour matches, and offset 0 matches more hours than either
  other offset. The result reports the matched and compared counts at each offset and the best
  offset per variable. A fail stops the weather fit for the owner (`scripts/pnw_t1_run_all.sh`).
- Hourly files deleted before 20:40 UTC (2025-03, -04, -07 and -12, all in the sample) are fetched
  again (`--refetch-hourly`), so no span drops out for that reason.

**Correction (append only).** `0caf56d`'s message says the daily bounds in
`scripts/pnw_equivalence.py` were restated. The code edit did not apply (the replaced text did not
match), and the script kept 0.05/0.0005 until the rewrite that follows this section. The review
found it (S5), along with the 7 × 24 reshape of an 8-day span and a name clash (`a`) that would
have crashed the summary. No Open-Meteo body had been read in that time.
