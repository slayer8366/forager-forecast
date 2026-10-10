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
