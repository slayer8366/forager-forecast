# Rain gap between Open-Meteo and the store, for T10's live route

**Context.** Owner's request, Forager RECORD -828: "Rain-gap write-up for the live version". This
is analysis only.

- Written 2026-10-10 from 20:10 UTC. The file is dated 2026-10-11 as the planner named it.
- Branch `pnw-pilot-scoring`, after merging `origin/pnw-pilot-t1` at a8f85b9.
- No request was made to Open-Meteo or to the Copernicus store for this write-up. The Open-Meteo
  cross-check fetch was not touched.
- This is a builder's analysis. Nothing in it has been reviewed.

## Result in one paragraph

The whole gap is explained on the sample in hand, with no remainder. Open-Meteo's
`era5_seamless` daily rain equals the store's hourly ERA5 rain after two transforms:

1. The hour each day is summed over. Open-Meteo sums the stamps 00:00 to 23:00 of the day. The
   store, and so training, sums 01:00 to the next day's 00:00.
2. A drizzle cut. Each hourly value below 0.1 mm becomes 0. Every other value is rounded to
   0.1 mm.

With both applied, the result matches Open-Meteo's daily total on all 540 cell-days, with a
largest difference of 0.0 mm. Plain rounding without the cut does not reproduce it: 4.24 percent
of the store's rain is still missing.

The cut is what causes the 4 to 8 percent level gap. The hour offset only moves rain between
neighbouring days.

## What was compared

**Store side.** The builder's hourly ERA5 `total_precipitation`, a raw store file:
`~/Zynergy/forecast-data-pnw-pilot/cds/hourly-era5-precip-2019-2020.nc`, sha256 14c92c70...

- Its day convention is the builder's: day d is stamps d 01:00 to d+1 00:00
  (`hourly_daily.daily_sums_previous_hour`).
- That convention was confirmed against the daily-sum product: 192,355 values, largest
  difference 0.0 m, at pnw-pilot-t1 267e3ad
  (`docs/audits/2026-10-10-pnw-pilot-t1/precip_hourly_vs_daily_2019.json`).

**Open-Meteo side.** The bodies already on disk from the scoring branch's feature check
(`~/Zynergy/forecast-data-pnw-pilot/scoring/feature-check/`):

- daily `precipitation_sum` for 6 cells, 2019-07-09 to 2019-10-06, which is 540 cell-days;
- hourly `precipitation` for one of those cells (47.8, -121.2), 2019-07-08 to 2019-10-07, which
  is 2,208 hours.

**Matching.** Each cell is paired with the store's 0.25° point nearest its centre
(`cells.quarter_cell_for`, D46).

**Script and output.** Script: `scripts/rain_gap_analysis.py`. Output:
`docs/audits/2026-10-11-rain-gap/rain_gap.json`, sha256 5bbb7d59...

## Results

**Store variants against Open-Meteo's daily total.** Pooled over the 6 cells and 540 days:

| Store variant | Largest daily difference | Days within 0.05 mm | Store rain Open-Meteo lacks |
|---|---|---|---|
| S1: store convention (01 to 24), exact. This is the training value | 6.29 mm | 218 | 5.47 % |
| S0: stamps 00 to 23, exact (hour offset only) | 1.23 mm | 221 | 5.47 % |
| S1q: store convention, each hour rounded to 0.1 mm | 6.20 mm | 263 | 4.25 % |
| S0q: 00 to 23, each hour rounded | 1.20 mm | 276 | 4.24 % |
| S1t: store convention, each hour 0 below 0.1 mm, else rounded | 5.90 mm | 368 | 0.00 % |
| **S0t: 00 to 23, each hour 0 below 0.1 mm, else rounded** | **0.00 mm** | **540** | **0.00 %** |

By cell, the store's exact rain exceeds Open-Meteo's by 3.8 to 8.6 percent. S0t is exact at every
cell: 90 of 90 days at each.

**Hour by hour, at the one cell with Open-Meteo hourly.**

- At the same stamp, Open-Meteo's value against the store's: largest difference 0.0997 mm.
  Shifted by one hour either way: 2.49 mm. So the stamps are aligned, and Open-Meteo's hourly
  value describes the same hour as the store's.
- The rule "0 below 0.1 mm, else rounded to 0.1 mm" matches all 2,208 hours. Other cut-offs
  match fewer hours, so 0.1 is the only cut-off that fits this sample:

| Cut-off | Hours matched (of 2,208) |
|---|---|
| 0.05 mm (plain rounding) | 2,067 |
| 0.08 mm | 2,159 |
| 0.09 mm | 2,185 |
| 0.10 mm | 2,208 |
| 0.11 mm | 2,178 |

- Open-Meteo's own daily total equals its hourly values summed over stamps 00 to 23 on 90 of 90
  days. Summed over 01 to 24, it does not: largest difference 1.4 mm.
- At this cell, 690 hours have store rain above 0 and below 0.1 mm. They carry 18.6 mm of the
  281.2 mm over these 92 days (6.6 percent), and Open-Meteo reports 0 for every one of them.

## Answers to the two questions

**(1) Hour-boundary offset.** It is real.

- Read: Open-Meteo sums 00 to 23, the store sums 01 to 24, and the hourly stamps agree.
- It explains the large single-day differences. Summing the store 00 to 23 cuts the largest
  daily difference from 6.29 mm to 1.23 mm.
- It does not change totals over a window: 5.47 percent either way. It shifts one hour of rain
  across each midnight.

**(2) Drizzle quantisation.** Rounding to 0.1 mm alone does not reproduce Open-Meteo: 4.24
percent is still missing. Rounding plus a zero cut below 0.1 mm reproduces it exactly, 540 of 540
days. That cut is the 4 to 8 percent level gap.

**Unexplained remainder: none on this sample.**

**How the rule was established, and its limits.**

- It was found on one cell's hourly series. It was then tested, not fitted, on all 6 cells'
  daily totals, where it holds exactly.
- I did not find where in Open-Meteo's code the cut happens. I searched `Sources/App/Era5` and
  the precipitation helpers at f625df2. Earlier reading found the storage scale factor of 10
  (0.1 mm). The cut below 0.1 mm is **observed, mechanism not read**.

**What this sample does not cover.**

- Only 2019-07 to 2019-10: summer and early autumn, a dry season in the PNW.
- 6 cells, all inland or coastal Washington, Oregon and BC.
- Winter rain, snow hours and the ERA5T preliminary data of recent weeks are not in it. Whether
  Open-Meteo treats ERA5T the same is untested.
- The 2026 Open-Meteo bodies from the cross-check fetch can be checked the same way once the
  builder's `--scoring` hourly rain for 2026-07 to 2026-10-04 lands in the store. They are not in
  this write-up.

## What the live route (T10) could do

The archive and the store are both about 5 days behind. Observed for Open-Meteo on 2026-10-10:
the last day was 2026-10-04. For the store the lag is not measured here.

So the live route has two parts: the archive days, and the newest days that only a forecast
product covers.

**A. Request Open-Meteo hourly rain and sum it with the store's convention (01 to 24).**

- Fixes the day boundary.
- Does not fix the cut: S1t still lacks 5.47 percent of the store's rain, with daily differences
  up to 5.9 mm. Sub-0.1 mm hours are gone from Open-Meteo and cannot be recovered.
- Cost: one more hourly variable in the request the pilot already makes. By the pricing page's
  rule that is no extra call cost while the request stays at 10 variables or fewer (read,
  `open_meteo.api_call_units`). Code is small.
- Alone, it leaves the gap.

**B. Accept a calibrated bias.**

- Scale or offset Open-Meteo rain to the store's level, fitted on overlap years.
- Cost: an overlap pull and a fit.
- The correction is statistical while the loss is per hour. The total can be matched, but the
  day-to-day pattern of drizzle cannot. Its share varies by place and season (3.8 to 8.6 percent
  here, inferred to be higher in the wet season).
- Thresholds stop belonging to one product (START_HERE: "Thresholds belong to the weather product
  they were fitted on").
- Inferred to be the weakest option.

**C. Train on what Open-Meteo serves (new, follows from the result).**

- Apply the observed rule to the store's hourly rain before training: 0 below 0.1 mm, else
  rounded. Then sum both sides with one convention.
- Training and serving are then identical by construction on archive days. That is the S0t
  result, which is exact on 540 of 540 days.
- Cost:
  - The hourly rain route for every training year. The builder is already moving rain to the
    hourly route (RECORD -826; two years per request, `hourly-era5-precip-2019-2020.nc` is
    delivered).
  - A refit of the weather model.
  - The model loses sub-0.1 mm/h drizzle, about 4 to 9 percent of rain here.
  - The rule is observed, not documented by Open-Meteo, so it needs a standing check that a
    new body still matches.
- This removes the seam on the archive days. It does nothing for the forecast days.

**D. Another source.**

- For archive days: score from the store itself, as the pilot does now (RECORD -819). No seam,
  but the store's own lag applies.
- For the newest days, every option above fails: no reanalysis covers them, so the live route
  must bridge with a forecast product.
- The owner's point applies there (RECORD -820, verbatim): "Weather forecast models differ in the
  PNW in rain accuracy. This is a feature of the region changing every so often, not the data
  itself."
- It does not explain this gap. Read: both sides here are ERA5 (`era5_seamless` takes
  precipitation from ERA5, `Era5Variables.swift`).
- It does govern the bridge days. Which forecast model is least wrong on PNW rain changes over
  time, so a single pinned bridge model is a moving target.
- Cost (inferred): a seam test under R7, plus a recurring check of bridge-model rain against
  ERA5 once ERA5 catches up. This is D19's open T10 item.

**Read vs inferred.**

- Read: the two transforms and their exact fit on this sample; the pricing rule; the
  `era5_seamless` rain source.
- Inferred: the wet-season and ERA5T behaviour; the ranking of B; every cost.

**Not decided here.** Which option T10 takes changes what training reads and what users are
told, so it goes to the owner as a proposed row.
