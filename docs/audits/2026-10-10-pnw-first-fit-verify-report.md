# PNW first fit (pilot): verify-before-building report

**Date:** 2026-10-10, written 18:00 to 18:30 UTC (Saturday).
**Type:** verify-before-building report. No data pull, no model fit, no code change. One local
count was run (ecoregions in the boxes, section 4), from a file already on the drive.
**Base:** branch `pnw-first-fit-verify` cut from origin/main `36cc647`. Decision rows read from
origin/`d121-lean-start` at `aec605d`, which contains origin/`t6b-continental-layers` at `63dc6e4`
(checked with `git merge-base --is-ancestor`) and so holds every row D1 to D121. Neither branch is
merged to main. Forager RECORD read from Forager origin/`records-after-173` (entries -805 to -809,
fetched 17:58 and 18:02 UTC).
**Answers:** the planner's dispatch of 2026-10-10 on the owner's ruling, Forager RECORD -806,
verbatim: "Real forecast, PNW only, ASAP". Read with -807 ("The PNW can be our pilot run so we know
how it works before we commit to the entire country"), -808 ("Copernicus bulk, Open-Meteo live
(Recommended)") and -809 ("Let's get a standing model ready before Monday at least and we can see
how it works out"), each relayed by the planner while this report was being written.

Labels: **read** means a file was opened and the line is cited; **observed** means a command was run
here and its output seen; **inferred** and **estimated** are marked. Line numbers for DECISIONS.md
are in the file as it stands at `aec605d` (D121 at line 8, D1 at line 120).

---

## Short version

1. **T1 state.** Downloads, filters, counts and the date rule are all done and merged. Nothing
   on record still blocks T1's fit except things nobody has built yet: the weather pull, the
   equivalence test, the tuning grid and the fit itself. TASKS.md's "modelling waits on the owner's
   reading and the weather-pull ruling" (TASKS.md:11) is stale. The reading was answered by D33 (1),
   accepted in D34. The weather ruling is D24 (accepted in D34), D52 and D54, and RECORD -808 says
   they stand. T1's PNW box (42.0 to 49.5 N, 121.0 to 125.0 W) is **not** the T6b PNW box (40 to
   49 N, 111 to 125 W).
2. **Weather.** The CDS key file exists (`~/.cdsapirc`, 85 bytes, mode 600; contents not read). The
   four dataset names and the CC-BY licence are on record. The precipitation and UTC items are
   settled (D54, D52). The equivalence test is specified only in documents. No code for it exists
   on any branch. **Estimated** pull size: about 0.16 GB for T1's box, about 0.67 GB for the T6b
   box, or about 0.71 GB for the union both need (float32, 4,108 days). Pull time is
   **not measured** at this size. The only timings on record are 20 to 37 s for 25 KB requests.
3. **Beyond weather.** All of it is on the laptop and checked. D26's zip sha256 matches its DOI
   record. T6's stored surface matches all ten filed sha256 values. The cell keying is merged code.
   Missing: the T1 tuning grid that D31 requires to be committed first.
4. **T7 to T9.** T7 still depends on T6b by D100, and that dependency is what -806 changes for the
   pilot. No D-row has been filed for that change yet. Ecoregions: T1's box holds 12 CEC level III
   ecoregions (3 level I); the T6b box holds 25 (5 level I). Fourteen rules bend; they are listed
   in section 4 as pilot-scoped deviations.
5. **Machine.** The pull fits easily on either disk. **Estimated** fit memory is under 2 GB, beside
   T6b's 5 GB cap.

**The planner's order needs one correction (Premises).** -806's own order includes "the PNW box's
Canadian SCANFI tiles ahead of the continent" between T1 and T7. The planner's summary leaves that
step out. T1 does not need it: T1 uses no habitat layers. T7 does need it for the T6b box.

---

## 1. T1's exact state

### What landed (read)

| Item | Where | State |
|---|---|---|
| T1 build (design, filters, cell-weeks, windows, Open-Meteo URL builder, two named tests) | `src/forager_forecast/t1_design.py`, `cell_weeks.py`, `weather_windows.py`, `open_meteo.py`; report `docs/audits/2026-09-18-t1-calendar-smoke-test-completion-report.md` | merged (origin/t1-calendar-smoke-test is an ancestor of main, observed) |
| T1 credentialed run: download 0005709, DOI 10.15468/dl.hdkjmn, counts | `docs/audits/2026-09-18-t1-credentialed-run-report.md` | merged; download superseded by D26 (D73, line 48) |
| D32 merge pass and follow-up (one Record type, one filter pipeline) | TASKS.md:14-15 | merged (observed ancestor) |
| D26 shared download 0012112-260928105237408, DOI 10.15468/dl.8jxmeb, 2,493,578 records | `docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json` | merged |
| D27 keys, D28 date rule (D97 keep the 1st, D98 drop the midnight check) | DECISIONS.md:28-29 | merged |
| D29 dataset and licence lists (D96) | `docs/pulls/*.datasets.json` | merged |
| D63 and D64 tie rules in `cells.cell_for` | DECISIONS.md:57-58 | merged |
| T1 tuning grid (D31: "a grid written into the repo first") | none found | **missing**. `t1_design.py:1-58` fixes boxes, windows, years and filters but no grid; `git grep -i tuning` over src and scripts finds only T6's |
| T1 fit script, weather loader, CDS client, equivalence test | none on any branch | **missing**. `git grep -l -iE 'cdsapi\|equivalence'` over every origin branch's `*.py` and `*.toml` returned nothing (observed). `cdsapi` is not in `pyproject.toml:14-21` |

### What the TASKS.md cell waits on, and whether each is settled

TASKS.md:11 reads "modelling waits on the owner's reading and the weather-pull ruling". That cell
was written with the credentialed run on 2026-09-18 (START_HERE.md:76). Both waits were answered
after it:

- **The owner's reading.** The question, as asked in the T1 credentialed-run report's owner items
  (line 385-387): "**Read the premise table** and say whether "holds" stands for the PNW given 3, 8,
  12 and 29 usable records in 2015 to 2018. Modelling waits on that". It is answered by D33 (1),
  DECISIONS.md:88: "The feasibility premise is read as met in both boxes, with the Pacific Northwest
  recorded as thin: its useful data is 2019 to 2025". D34 accepted it (line 87): "Accept D24 to D33
  as proposed." The report's other owner items are also closed. Item 2, the date rule, by D97 and
  D98. Item 3, the weather, D25 and D26, by D34 and D26's download. Item 4, the licence gate, by
  D96 and D61.
- **The weather-pull ruling.** D24 (line 97) chooses the Copernicus store for bulk training weather,
  with an equivalence test against pinned Open-Meteo requests before any fit. D34 accepted it. D19
  and D21 (lines 100, 102) pin `era5_seamless`. D54 (line 67) takes precipitation from ERA5
  single-levels daily statistics as the UTC daily sum, and temperature and soil from ERA5-Land. D52
  (line 69) pins the UTC day and records time and account per pull. D43 (line 78) makes the CDS
  account a test account whose pulls need no redo. D46, D51, D63 and D64 key the cells. RECORD -808
  restates that D19, D21 and D24 stand, including the equivalence test. **Settled.**

**Is D33 accepted?** Yes, by D34 (DECISIONS.md:87). SPEC.md:52 carries it.

**Open "owner's reading": none found on record.** Inferred: the TASKS cell was never updated after
D33 and D34. It is not an open question.

### The boxes are different (read)

| Box | Definition | Source |
|---|---|---|
| T1 PNW | 42.0 to 49.5 N, 125.0 to 121.0 W, edges inclusive | dispatch `docs/dispatch/2026-09-18-t1-calendar-smoke-test.md:29`; code `t1_design.py:35`, `records/counts.py:43` |
| T1 East | 38.0 to 46.0 N, 84.0 to 70.0 W | dispatch :30; `t1_design.py:36` |
| T6b PNW render | 40.0 to 49.0 N, 125.0 to 111.0 W | origin/t6b-pnw-monday `src/forager_forecast/pnw.py:30` |

T1's box is narrower: it stops at 121 W, near the Cascade crest, and it reaches 0.5 degrees further
north, into British Columbia. The T6b box reaches east to 111 W (Idaho, western Montana, northern
Nevada and Utah) and 2 degrees further south. T1's dispatch forbids changing its box limits once a
test result is seen (dispatch :63-64). None has been seen, but the boxes are fixed choices
(`t1_design.py:4-6`), and D26's acceptance check was run against them.

### What blocks T1's fit, in order

1. A committed T1 tuning grid (D31, line 90). This is the builder's to write, before any fit.
2. The CDS weather pull for the box or boxes (D24, D54, D52).
3. The equivalence test passing (D24: "must match within rounding" "before any model is fit").
4. The fit and report themselves (dispatch "Then build", D33's evaluation).

---

## 2. The weather pull for the PNW

### What D24 requires, and where each item stands

| Requirement | Source | State |
|---|---|---|
| Bulk training weather from the Copernicus Climate Data Store: ERA5-Land for temperature and soil, ERA5 for precipitation, "for the two boxes and 2015 to 2025, using daily statistics if the store offers them" | D24, line 97 | route decided (-808). Not started |
| V1 dataset names at source | D24 verify first | done: `docs/planning/evidence/cds-credentials-report.md:18-22` names `reanalysis-era5-land`, `reanalysis-era5-single-levels`, `derived-era5-land-daily-statistics` and `derived-era5-single-levels-daily-statistics` |
| V2 licence at source | D24 | CC-BY on all four (`cds-credentials-report.md:23`); 4.0 observed on ERA5-Land only, inferred for the other three (SPEC.md:127-136). Attribution text settled by D53 (line 68) |
| V3 precipitation accumulation convention | D24 | answered by D54: the single-levels daily-statistics `daily_sum`, so no hourly accumulation step is involved |
| V4 UTC day boundaries | D24 | answered by D52: `time_zone` `utc+00:00` in every daily-statistics request |
| Equivalence test against Open-Meteo pinned per D19 and D25, "on a fixed sample of cells and days", "within rounding" | D24; SPEC.md:50 | **not built**. Specified only in documents (`docs/audits/2026-09-20-cleanup-and-d24-d31-status-report.md:210-220`), estimated there at "4 to 7 files, 250 to 500 lines" (:185). The sample and the meaning of "within rounding" are not fixed anywhere I found. Cowork's report says the test "should check" where Open-Meteo's `era5_seamless` takes soil and precipitation from, "not assume it" (`docs/planning/evidence/2026-09-20-cowork-attribution-licence-grid-report.md:191-195`) |
| Grid positions confirmed from a delivered file | D51 | done for two small boxes, one aligned and one off-grid (`2026-09-22-grid-positions-d51-report.md:96-110`; part 2 report :22-24). Each new pull should still check its own coordinate arrays (D51) |
| Request time and account stored beside each request | D52 | pattern exists: `docs/pulls/grid-positions/*.request.json` |

### Credentials on this laptop (observed, contents not read)

- `~/.cdsapirc`: present, `-rw------- 85 bytes`, dated Sep 19 00:32. The size matches the file
  Cowork reported (`cds-credentials-report.md:43`). Not opened.
- `~/.config/forager-forecast/gbif.env`: present, mode 600, 70 bytes. Not opened.
- `~/.ecmwfapirc`: absent. Not needed, since `cdsapi` reads `~/.cdsapirc`.

### Size and time

**Measured on record (read):**
- Two 25 KB daily-statistics requests took 37 s (ERA5-Land, accepted to successful) and 25 s (ERA5
  single levels) (`2026-09-22-grid-positions-d51-report.md:98-100`). Cowork's proof request took
  24 s for 25 KB (`cds-credentials-report.md:33`). No request anywhere near the size below has been
  timed.
- Request shape (read, :70-80): the ERA5-Land daily-statistics form takes `month` as **one string**.
  So it is one request per month. The single-levels form takes `month` as an array, so one request
  can cover a year. The ERA5-Land form lists 31 variables. Only `2m_temperature` was quoted. **Whether
  the soil variables (soil temperature level 1, volumetric soil water layer 1, both 0 to 7 cm) are
  among the 31 is not on record.**

**Estimated here (arithmetic, not measured).** The days needed: T1's windows reach 90 days before
the first scored Monday (`weather_windows.py:3-5`, `t1_design.py:43`). 2014-12-29 minus 90 days
is 2014-09-30, and the series runs to 2025-12-28, so 4,108 days (computed). Variables: three
ERA5-Land daily means (temperature, soil temperature, soil moisture) and one ERA5 daily sum. Grid
points are counted inclusive of the box edges.

| Box | ERA5-Land 0.1° points | ERA5 0.25° points | Values (float32) | Requests |
|---|---|---|---|---|
| T1 PNW (42 to 49.5 N, 121 to 125 W) | 76 × 41 = 3,116 | 31 × 17 = 527 | about 154 MB + 9 MB | 136 monthly ERA5-Land + 12 yearly ERA5 |
| T6b PNW (40 to 49 N, 111 to 125 W) | 91 × 141 = 12,831 | 37 × 57 = 2,109 | about 632 MB + 35 MB | same counts, bigger each |
| Union (40 to 49.5 N, 111 to 125 W), covers both | 96 × 141 = 13,536 | 39 × 57 = 2,223 | about 667 MB + 36 MB | same counts |
| T1 East (if T1 runs as dispatched) | 81 × 141 = 11,421 | 33 × 57 = 1,881 | about 563 MB + 31 MB | same counts |

Delivered NetCDF may be larger (float64, headers, sea points included) or smaller (compression).
Double the figures for a safe disk budget.

Time: **not estimable from repo measurements.** The store computes daily statistics at request time
from hourly data (D52's Reason, line 69), and queue time under load is not recorded anywhere here.
Bracket, **estimated**: 148 requests at 1 to 5 minutes each, run one after another, is about 2.5 to
12 hours. The store can queue several requests per user, which might shorten this; that is not
verified here. One timed one-month request for the chosen box would turn this into a measurement. It
is the first step of the route in section 6.

If the soil variables are not in the daily-statistics form, the fallback is the hourly
`reanalysis-era5-land` dataset. That is 24 times the values (about 3.7 GB for T1's box, 16 GB for the
union), and the daily mean would have to be computed here. That changes the size and time picture
completely, and it needs the same check.

---

## 3. What T1's fit needs beyond weather, and whether it is here

| Input | Rule | On the laptop? | Checked how |
|---|---|---|---|
| Records: D26's DWCA | D26, D71, D72 | yes: `~/Zynergy/forager-forecast-d26/data/d26/downloads/0012112-260928105237408.zip`, 1,434,032,123 bytes on /mnt/work | **observed** sha256 `c0d5f6a1…b26c` equals `docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json:11` |
| Filters: T1 step list, event key with taxon, date rule | D27, D28, D65, D97, D98; `records/filters.py` | code merged | read (TASKS.md:23; D98 line 28). The PNW event-key survivors over D26 for all fungi are 144,145 (`docs/audits/2026-10-06-d28-date-rule/survivors_0012112/pass_t1.json`, observed). **Usable Cantharellus in the PNW box on D26's download is not in any filed table.** The last filed figure is 1,226 on the superseded 0005709 (credentialed run report, line 322) |
| Effort layer | T6, D101 to D108 | yes: `~/Zynergy/forager-forecast-t6/data/t6/{all,cc,counts}` | **observed** all ten sha256 equal `docs/audits/2026-10-06-t6-fit/stored_surface_sha256.txt` |
| Cell keying | D46, D51, D63, D64; `cells.cell_for` | merged code | read (D63, line 58) |
| Weather | D24, D54 | **no** | section 2 |
| NetCDF reading | none | rasterio's bundled GDAL 3.12.4 has the `netCDF` and `HDF5` drivers (**observed** in the project environment). No new reader is strictly needed. Whether it reads the store's files cleanly is untested |
| Tuning grid | D31 | **no** | section 1 |

T1's dispatch says "Do not add habitat layers, elevation or tree data. This test is about timing
only" (dispatch :66). So T1 needs none of T4, T5 or T6b. **Inferred from the dispatch:** T1 does not
use T6's effort layer either. Its negatives are target-group cell-weeks (D13). Effort enters at T7
and T8.

---

## 4. T7 to T9 for a PNW pilot, and the rules it bends

### What each task would need (read from TASKS.md:80-97)

- **T7** (habitat): T4, T5, T6, and T6b by D100. For the pilot, the inputs are T6b's layers in the
  chosen box. US cells are done; Canada's cells in the T6b box (102,543, RECORD -806 Context) wait
  for SCANFI. The SCANFI stage is stopped (RECORD -805). D121's lean start fixes the inputs: host
  trees, soil pH, NALCMS mask, effort. Verify: "a spatial block validation report by ecoregion and a
  mask map".
- **T8** (trigger and joint): T1 and T6. Windows "with randomisation checks", comparison "on
  held-out years and ecoregions". D109 adds the lichen spike and the north-of-50 N caveat to T8's
  brief. Neither bites inside 49.5 N for the autumn groups.
- **T9** (calibration and gate): T7 and T8. "Compute skill per ecoregion"; each decile within 5
  points (R3); "the published set equals the passing set" (R2).

### Ecoregions in each box (observed)

Count of ERA5-Land 0.1° cell centres inside each CEC level III polygon. File: the T6b drive copy
`…/t6b/sources/terr_ecoregions_v2_level_iii_shapefile/…/NA_Terrestrial_Ecoregions_v2_level3`.
Point-in-polygon with shapely 2.1.2 and pyproj 3.8.0 under `uv run --no-project`. The script and
its output are kept outside the repo, at `/tmp/pnwv_eco.py` and `/tmp/pnwv_eco.out.txt`.

- **T1 PNW box:** 3,116 centres, 2,374 inside a polygon (the rest are sea). **12 level III, 3 level
  II, 3 level I.** By centres: Cascades 517, Coastal Range 471, Strait of Georgia/Puget Lowland 334,
  Eastern Cascades Slopes and Foothills 311, North Cascades 232, Klamath Mountains 177, Willamette
  Valley 167, Blue Mountains 50, Pacific and Nass Ranges 49, Coastal Western Hemlock-Sitka Spruce 30,
  Columbia Plateau 24, Northern Basin and Range 12.
- **T6b PNW box:** 12,831 centres, 11,970 inside. **25 level III, 5 level II, 5 level I.** The
  largest are Northern Basin and Range 1,531 and Central Basin and Range 1,277, both deserts. Seven
  hold under 100 centres; the smallest, Colorado Plateaus, holds 1.

Limit: a sliver narrower than 0.1° can hold no centre and be missed, so these are counts at the
weather cell's scale. Nothing on record says which ecoregion **level** R2 and T9 mean. That is an
open question below.

### Rules a PNW pilot bends (pilot-scoped deviations)

Each is quoted, then marked as a deviation the pilot takes, or a rule it keeps.

1. **D100 / TASKS.md:82**: "T6b, so the model is fitted on continental layers, not the test areas
   T4 and T5 built". *Deviation*, ordered by -806 for the first fit. It is **not yet filed** as a
   forecast decision (the newest row is D121, line 8).
2. **SPEC.md:15-16**: "One continental pipeline: static habitat layers on a 250 m equal-area grid".
   *Deviation in extent only*, if the pilot uses the same master grid and code. **D5** (line 116),
   "North America is one pipeline and one grid", is then kept.
3. **SPEC.md:20**: "Validation by ecoregion and held-out year against a day-of-year baseline". It
   is kept in form. In effect it is limited to 12 or 25 ecoregions, many with few records.
4. **TASKS.md:84 (T7 Verify)**: "a spatial block validation report by ecoregion". It can run, but
   ecoregion blocks inside one box give few blocks per level I region (3 in T1's box). *Deviation*:
   the pilot's block validation does not test transfer across the continent.
5. **TASKS.md:89 (T8)**: "compare both on held-out years and ecoregions". As 4.
6. **TASKS.md:95 (T9)**: "compute skill per ecoregion". This is kept, but it is a pilot-scoped
   reading. Most of the T6b box's desert ecoregions will be "not shown" under D33 (5). **Inferred**
   from where chanterelle hosts grow.
7. **SPEC.md:97-98 (Acceptance)**: "scored against the calendar baseline in every ecoregion with
   enough records". *Deviation*: the pilot covers the PNW only. Phase 1 acceptance stays continental.
8. **T1 dispatch :28-30, :55-58 and :87-89**: two boxes, "per box", and "How the owner will read the
   result: the interval excludes zero in both boxes". *Deviation if East is skipped*. RECORD -806
   calls T1 "the PNW calendar-vs-weather test". Whether East still runs is not ruled (open question 1).
9. **D24** (line 97): "for the two boxes and 2015 to 2025". *Deviation if only the PNW is pulled.*
10. **T1 dispatch :63-64**: "Do not touch ... the box limits". This is **kept** only if T1 runs on
    42 to 49.5 N, 121 to 125 W. Running T1 on the T6b box would break it.
11. **D18** (line 103): "A dependent task does not start until its prerequisite's review is filed".
    A review of the t6b-pnw-monday work exists (commit `5fea035`, "Review -786"). I found no
    independent review of the T6b continental layers, so T7 on the T6b layers bends D18 unless one
    is filed.
12. **D31** (line 90): "a grid written into the repo first". Kept. Nothing about the pilot requires
    bending it.
13. **D33 (3) and (4)** (line 88): the 5,000 m sensitivity run and the commercial-safe track,
    "reported anyway and ... not dropped after results are seen". *Deviation* if they are deferred
    to make the date. They must then be reported as pending, never as dropped.
14. **D24's equivalence test "before any model is fit"**. Kept in this report's route. Cutting it
    would be a rule bent (section 6).

D5's publication gate and D12's meaning are unchanged by -806. The pilot publishes nothing. D121's
lean start applies as written.

### What the pilot should measure to inform the continental commitment

| Measure | Already recorded in the repo for comparison |
|---|---|
| CDS pull time per request and total, bytes delivered, failures and retries | 25 KB requests in 20 to 37 s (`2026-09-22-grid-positions-d51-report.md:98-100`); nothing at scale |
| Equivalence test result: max difference per variable, where Open-Meteo's soil comes from | nothing yet (Cowork report :191-195 asks for it) |
| Weather disk use per box (scale to the continent by point count) | nothing yet; this report's estimates only |
| T1 fit wall time and peak memory per fold and per configuration | T6's figures for comparison: count peak 1.19 GB, fit 224 MB (START_HERE.md:91) |
| T7 to T9 wall time and memory on the pilot area | T6b layer timings: RECORD -805 (37.7 s per SCANFI unit), `docs/audits/2026-10-07-t6b-run/` on the t6b branch |
| D5's gate: skill and interval per ecoregion, how many are "not shown" and why (records, folds under 30 positives) | D33's rules (line 88); T1 counts (credentialed report :322) |
| Failure points: guards that stopped the run, rows refused by loaders, cells with missing weather | the loader's counted refusals (D66, D70); T6b's guards (D119, D120, RECORD -805) |

---

## 5. Machine limits

Observed at 18:05 UTC: the flash drive has 15 GB free (`df`). `/mnt/work`, where `~/Zynergy` is
bind-mounted, has 16 GB free. `/` has 28 GB free. RAM is 11 GB total, 7 GB available; swap is
3 GB; 8 cores. `forecast-data` holds `t6b` 18 GB, `t5` 9.9 GB and `pnw` 616 MB.

| Need | Disk (estimated) | Memory (estimated) |
|---|---|---|
| Weather pull, T1 PNW box | about 0.2 to 0.4 GB | streamed per file, small |
| Weather pull, union box | about 0.7 to 1.4 GB | as above |
| Hourly fallback, union box | about 16 to 32 GB: does **not** fit on either disk alongside current contents | per-month files |
| Cell-week table and features, T1 PNW | under 0.1 GB (inferred: about 144k event-key records collapse to fewer cell-weeks; 36 features) | under 1 GB |
| T1 fit (LightGBM: 11 outer folds × 20 configurations × inner folds × 2 models, plus bootstrap) | negligible | under 2 GB (inferred; T6's fit on a larger frame peaked at 224 MB) |
| D26 zip, read in place | already on /mnt/work, 1.43 GB | T6's streamed count peaked at 1.19 GB |

The T6b run is stopped (RECORD -805). If it restarts during the fit, its 5 GB cap (RECORD -802)
plus the fit's estimate stays inside 7 GB available. A Forager Gradle build at the same time would
not (inferred from Forager RECORD -610's memory crash, as cited in D114). The pull is network-bound
and can overlap anything.

---

## 6. Route to a fitted model by Monday

Asked by RECORD -809. "Standing model" is read as the planner relays it: a fitted PNW model with
held-out results against the calendar baseline under T1's design, not a publication. All hours are
**estimates**.

| Step | Hours | What could stop it |
|---|---|---|
| 0. Owner rules on the open questions below (East box, which box to pull, cuts) | minutes | nothing |
| 1. Commit the T1 tuning grid and the equivalence test's sample and tolerance, before any pull | 1 to 2 | none expected |
| 2. One timed one-month CDS probe for the chosen box, reading the ERA5-Land variable list for soil | 0.5 to 1 | soil variables absent from daily statistics, which forces the hourly route (section 2): likely loses Monday |
| 3. Full pull (148 requests), unattended | 2.5 to 12 wall | store queue, outage, request-size limits |
| 4. Build the equivalence test and run it on Open-Meteo (overlaps 3) | 3 to 5 | a mismatch. D24's fallback is a paid Open-Meteo plan, which loses Monday |
| 5. Weather loader to `DailyWeather` on D46/D63 cells, with tests (overlaps 3) | 2 to 4 | the store's files not reading cleanly through rasterio |
| 6. T1 fit script: PNW cell-week table from D26, features, leave-one-year-out with inner tuning, clustered bootstrap, reliability table, top ten features, the two named tests | 4 to 8 build, 1 to 6 run | leakage test failing; folds under 30 positives (D33 marks them, does not stop) |
| 7. Report | 1 to 2 | none |
| 8. Independent review (D18) | 2 to 4 | can run Monday; until then the result is labelled unreviewed |

Critical path: about 12 to 25 hours of build and run beside a pull of 2.5 to 12 hours. That fits
before Monday only at the low end of every estimate, and only if steps 2 and 4 pass.

**Cuts to make the date**, each marked:
- **T1 East box**: step skipped. It bends T1's dispatch and D24's "two boxes" (items 8 and 9). It
  saves about half the pull and fit.
- **Secondary random-date design** (D13): step deferred. The dispatch asks for it as a comparison
  only.
- **D33 (3) 5,000 m sensitivity and D33 (4) CC track**: rule bent if deferred (item 13). They must be
  run later and reported, not dropped.
- **D18 review before Monday**: step deferred. The result is labelled unreviewed.
- **Not recommended to cut:** the equivalence test before the fit. Cutting it bends D24 as accepted
  by D34 and restated by -808. Also not recommended: committing the tuning grid first (D31) and the
  two leakage tests (dispatch :79-81). These cost little and they are what make the result evidence.
- **Out of reach by Monday:** T7 to T9. They need T6b's Canadian cells or a box-limited habitat fit,
  plus the effort integration and a review.

---

## Decisions the owner must make before T1's fit starts

1. **Does T1 run the East box too?** The dispatch and D24 say two boxes. -806 names only the PNW.
2. **Which box is pulled:** T1's box only (smallest, fastest), or the union 40 to 49.5 N, 111 to
   125 W (so T7 to T9 on the T6b box need no second pull). T1 itself must stay on its fixed box.
3. **Which cuts to take for Monday**, from the marked list in section 6. In particular: is the
   equivalence test kept before the fit (recommended), and may D33 (3), D33 (4) and the D18 review
   follow after Monday?
4. **Filing the D100 change** for the pilot as a forecast D-row, citing -806 and -807. This is the
   planner's or owner's to word.
5. **For T7 to T9, not T1:** which CEC ecoregion level R2 and T9 publish by. Also whether the pilot's
   T7 waits for the PNW box's Canadian SCANFI tiles (as -806 orders) or fits on US cells first.

---

## Confirmed vs inferred

**Confirmed (observed or read, cited above):**
- CDS key file and GBIF credentials file present at mode 600 (observed, contents not read).
- D26's zip present, with sha256 equal to its record. T6's ten stored files equal their filed sha256.
- T1, T4, T5, T6, D26, D27 to D29, D28 and the D32 follow-up branches are ancestors of main.
  t6b-continental-layers, t6b-pnw-monday and d121-lean-start are not.
- D33 accepted by D34. The weather route is settled by D24, D52, D54 and D43, and restated by -808.
- The two box definitions and the ecoregion counts in both boxes.
- No CDS client, equivalence test, T1 tuning grid or T1 fit code on any origin branch (grep over
  `*.py` and `*.toml` on every origin branch, plus src and scripts on main).
- The netCDF and HDF5 drivers are present in the project's rasterio.
- Disk and memory figures.

**Inferred or estimated:**
- That the TASKS.md:11 cell is stale because it predates D33 and D34.
- Every size and time figure in sections 2, 5 and 6.
- The fit's memory.
- That the desert ecoregions will be "not shown".
- That T1 does not use T6's effort layer.

## Could not determine

- Whether `derived-era5-land-daily-statistics` offers soil temperature level 1 and volumetric soil
  water layer 1. Its 31-variable list is not quoted on record, and the dispatch forbids asking the
  store.
- The store's queue time and request-size limits at this scale.
- Usable PNW Cantharellus records on D26's download under the unified T1 list. No filed table splits
  by group, and computing it would have meant a 1.4 GB pass I judged outside a verify-only report.
- Whether an independent review of the T6b continental layers exists anywhere other than the
  branches read.
- The size on disk of the store's NetCDF files: dtype and compression.

## Premises that were wrong

- **The planner's reading of the order.** RECORD -806's "What it sets" reads: "T1 ... first; the PNW
  box's Canadian SCANFI tiles ahead of the continent; then T7 to T9 on the PNW". The planner's
  summary, "T1 first, then T7 to T9 on the PNW", leaves out the middle step. T1 does not need it.
  T7 on the T6b box does.
- **"Modelling waits on the owner's reading and the weather-pull ruling" (TASKS.md:11)**, which the
  dispatch quotes as the current state. Both were answered on 2026-09-18 (D33 and D34). What waits
  now is unbuilt work.
- **The "PNW box" is not one box.** T1's box and the T6b box differ (section 1). Anything that says
  "the PNW" needs to name which.

## Decided beyond scope

- I ran one local count (ecoregions per box) with `uv run --no-project --with pyshp==2.3.1 --with
  shapely==2.1.2`. It fetched those two packages from PyPI into uv's cache and touched no project
  file. No data was requested from GBIF, CDS or Open-Meteo.
- I read D26's zip once for its sha256 and T6's files for theirs. Nothing was extracted or written.
- The added "what the pilot should measure" list and the Monday route were requested mid-task by the
  planner (RECORD -807 and -809). They are included as asked; the hours in them are mine.
