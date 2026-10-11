# Review: the PNW pilot's T1 fit (D123), under the standing protocol (D18), run beside the build

- **Reviewed:** branch `pnw-pilot-t1`. Pass 1 read it at `5a527b7` (cut from main `36cc647`), then
  the three commits that landed while it was being written, to `bd49c03` (`1742544`, `8cfb43b`,
  `bd49c03`). Line cites are to `5a527b7` unless they say `bd49c03`.
- **Numbering:** the pilot ruling was filed as D122 (`4d6e864`) and renumbered D123 (`544888c`).
  The SCANFI edge ruling D122 (`f0c6065`) had been filed first. Every pilot-ruling citation in
  this review reads D123. Commit messages, and code at `5a527b7`, still say D122.
- **Protocol:** `docs/dispatch/2026-09-18-review-protocol.md`, checks 1 to 10.
- **Dispatch:** `docs/dispatch/2026-09-18-t1-calendar-smoke-test.md` with its two amendments.
- **Rulings read:** D5, D11, D12, D13, D24, D25, D26, D27, D28, D31, D33, D46, D52, D54, D72, D97,
  D98, D100, D123 (`docs/planning/DECISIONS.md`), and Forager RECORD -806 to -816
  (`origin/records-after-173:RECORD.md`).
- **Report reviewed:** `2026-10-10-pnw-pilot-t1-report.md` (draft, most sections PENDING).
- **Reviewer:** a Claude session separate from the builder (D18). Worktree
  `~/Zynergy/forager-forecast-pnw-review`, branch `pnw-pilot-t1-review`, cut from
  `origin/pnw-pilot-t1` at `5a527b7`.
  - I never wrote to `pnw-pilot-t1`, its worktree, `~/Zynergy/forecast-data-pnw-pilot/` or its
    jobs. I listed that data directory and read `fits/primary_t1_1000m_calendar.{json,log}`,
    `pull.log` and `chain.sh` in place.
  - The only CPU work: the test suite once (116 s, `nice 19`) and small synthetic scripts. No fit.
  - I read the D51 task's two 2024-06-01 store files read-only, in
    `~/Zynergy/forager-forecast-grid-positions-d51/data/grid-positions/`.
- **Conventions:** "Read" means opened in this session. "Observed" means command output from this
  session, saved in `2026-10-10-pnw-pilot-t1-review/` (scripts as `.py.txt`, byte-identical to
  what ran). "Inferred" is marked. No sighting chance is given as a percent here.

## Pass 1 verdict (pre-fit)

**Three blocking findings, all in the weather path, none in the evaluation.**

What holds:
- The evaluation machinery: pooled skill, clustering by cell and the inner/outer year split.
- The tuning grid and equivalence spec were committed before any fit or weather value.
- The records pass.

What blocks:
- **B1.** Soil moisture is stored 273.15 too low.
- **B2.** The committed equivalence tolerance will fail on the same product, as the store and
  Open-Meteo quantise it.
- **B3.** Missing weather enters the full fit silently. As of `bd49c03` it will: months from the
  new hourly route are not read by the weather builder.

B1 and B3 are code fixes. B2 needs a decision before any equivalence value is read, and none has
been read yet.

## Findings

### Blocking

**B1. Soil moisture is converted as if it were kelvin.**
- `scripts/pnw_weather.py:71` gives every ERA5-Land variable, `swvl1` included, the offset
  273.15. `:78` subtracts it.
- Observed: `probe_soil_moisture_units.out.txt` (synthetic file through `build()` and `load()`):
  - temperature 6.85 (280 K): right.
  - soil temperature 7.85 (281 K): right.
  - **soil moisture −272.85 for 0.3 m³/m³.**
- **Effects:**
  - The equivalence test compares this with Open-Meteo's m³/m³ (`pnw_equivalence.py:91-94,
    :111-113`), so all 252 soil-moisture values mismatch. Under the spec (`equivalence_spec.md:46-49`)
    the fit then waits for the owner.
  - Any model trained on these grids and scored with Open-Meteo's live soil moisture (the -816
    scoring track) is fed values about 273 units outside its training range.
- **Inferred:** the held-out skill itself would not change, because a constant shift keeps the
  order of a tree's split values. That is no comfort for B1's other effects.
- **Fix:** offset only `t2m` and `stl1`, plus a units test on a synthetic file like the probe.
- Not fixed here: it changes a result path.

**B2. "Within rounding" as committed will almost surely fail on the same product.**
- The rule:
  - `equivalence_spec.md:32-49`: a value matches within half a unit of the displayed precision
    plus 1e-6.
  - Every one of 1,008 values must match.
  - Any mismatch stops the fit for the owner.
- Open-Meteo stores hourly ERA5 quantised. Read today in open-meteo/open-meteo main,
  `Sources/App/Era5/Era5Variables.swift:148, :151, :156, :158`:
  - temperature_2m and soil_temperature_0_to_7cm: scalefactor 20 (0.05 °C).
  - precipitation: 10 (0.1 mm per hour).
  - soil moisture: 1000.
- Its daily mean and sum are then built from those stored hours. **Inferred:** that it builds
  them this way, and that the archive files were written with these factors, is not confirmed
  from Open-Meteo's code.
- **Observed on data already on disk** (`prior_sample_diff.out.txt`). The D51 task's 2024-06-01
  pair uses the same request form as the pilot (`docs/pulls/grid-positions/*single-levels*.request.json`):

  | Variable | Distinct points | Over 0.05 | Differences |
  |---|---|---|---|
  | Precipitation (`models=era5`) | 5 | 4 | 0.083, −0.136, −0.119, −0.178 |
  | Temperature (`era5_land`) | 4 | 0 | 0.005 to 0.041 |

- **Simulation** (`quantisation_sim.out.txt`, under that file's stated assumptions):
  - A daily mean temperature exceeds 0.05 about 2.4% of the time, so all 252 temperatures pass
    with probability about 0.976^252, about 0.2%.
  - A wet day's rain sum exceeds 0.05 mm 25% to 73% of the time, rising with the number of wet
    hours.
  - Soil temperature (mean of 24 displayed hours) and soil moisture do not exceed it.
- **What has not happened yet:** at the time of reading, no Open-Meteo body exists
  (`~/Zynergy/forecast-data-pnw-pilot/` has no `equivalence*/open-meteo/`). No ERA5-Land month had
  arrived (only `cds/era5-precip-2019.nc`). So the tolerance can still be restated without tuning
  to results.
- **What it needs:** the meaning of "within rounding" is D24's wording, and the stop goes to the
  owner, so this is the planner's and owner's to decide, not mine. Options:
  - (a) Bound each value by Open-Meteo's storage step plus its display half-unit: 0.075 °C for both
    temperatures. For rain, also request hourly `precipitation` and bound the sum by its rounding.
  - (b) Keep the rule and expect a stop.
  - (c) A convention test for rain: is the store's daily sum closer to Open-Meteo's hours 00 to 23
    or to 01 to 24, over the whole sample? That separates a real boundary shift from rounding.
    (a) cannot.
- The −0.18 mm at 47.5, −123.0 could be either cause. This one day cannot tell them apart.

**B3. Weather that is missing reaches LightGBM as NaN, uncounted and unlabelled.**
- What the code says it does: `daily_grid.py:9-10` and `pnw_weather.py:13` say the caller
  "counts and refuses such units".
- What the caller does: `pnw_t1_fit.py:149-154` stacks `weather_matrix` straight into `x`. No
  count, no refusal, nothing in the summary.
- LightGBM treats NaN as missing, so such units are scored by a model with no weather for them,
  inside a run labelled "all years". Three routes in:
  - (i) **The hourly route's months are never read.** At `bd49c03`, temperature and soil for
    months the daily route skips arrive only as `hourly-era5land-YYYY-MM.daily.h5`
    (`pnw_cds_hourly_pull.py`, `pnw_cds_pull.py` "skip (hourly route has it)"). `build()` reads
    only `*.nc` named `era5land-…` or `era5-precip-…` (`pnw_weather.py:60-63`, unchanged at
    `bd49c03`). With the hourly route covering 2014-09 to 2018-12 first, those months would be
    NaN.
  - (ii) **Partial years.** Under "Train as it downloads", early-year units' 42 to 90-day windows
    reach into months not yet pulled.
  - (iii) **Sea points.** A cell whose ERA5-Land point is sea has all-NaN weather. Inferred
    possible for coastal and Puget Sound cells; not counted.
- **The same gap in the equivalence script:** a sea cell in the fixed sample exits as "pull
  incomplete" (`pnw_equivalence.py:95-100`), and under `--available` it is skipped forever as
  incomplete.
- `save_final_model` (`bd49c03`) inherits the same NaN.
- **Fix:**
  - Count NaN units by variable and year in each summary, and refuse a non-partial run with any.
  - Read the hourly route's files in `build()`.
  - Tell a sea point (all NaN) from a day not yet pulled.

### Should-fix

**S1. Precision is not read from the returned JSON.**
- `equivalence_spec.md:42-44`: the half-unit is "taken from what was returned".
- `pnw_equivalence.py:34-39` fixes the tolerance as constants instead.

**S2. The fit outputs carry no code commit.**
- Times:
  - The calendar fit started at 18:13:49Z (first line of `fits/primary_t1_1000m_calendar.log`).
  - Its script was committed at 18:15:12Z (`00e827b`, commit date).
  - The records pass wrote at 18:12:37Z, also before that commit.
- So which code produced them cannot be confirmed from the outputs.
- `bd49c03` adds a commit and dirty flag to the scoring model's `model.json` only, not to the
  evaluation summaries.
- **Fix:** write `git rev-parse HEAD` and the dirty state into every summary.
- In pass 2 I re-run the calendar baseline from a clean checkout once the processor is free.

**S3. The hourly route's agreement check has no tolerance fixed in advance.**
- It is a second route for ERA5-Land, planner's builder choice (`8cfb43b`), against D24's "using
  daily statistics if the store offers them". The store does offer them (RECORD -812).
- Its check is the 2019-01 overlap month (`pnw_cds_hourly_pull.py`, `OVERLAP`).
- **Fix:** commit the overlap's tolerance before the overlap month is read. It should be tighter
  than B2's, because both sides are the store's own unquantised values.

**S4. The "Train as it downloads" quote is not recorded.**
- It is cited as the owner's in the report (`:7-8`) and in `pnw_cds_pull.py:17-19`.
- It appears in neither D123 nor RECORD -806 to -816 (grep, no match).
- It authorises partial-year fits, so it should be filed.

### Notes

- **N1. The D52 docstring is wrong about timing.** `pnw_cds_pull.py:20-21` says the request is
  stored "before the file is fetched". The code writes it after download (`:131-149`), so a failed
  attempt leaves no request record. Its log line does survive.
- **N2. The pull's pace.** One unit took 758 s (`pull.log`: `era5-precip-2019`). At that rate
  serial, T1's 148 units would take about 31 h (inferred). `1742544` adds concurrency and
  `8cfb43b` adds a second dataset queue. Neither is measured yet.
- **N3. Records not reported.**
  - The observer-key count (D27) is not in `records_summary.json`. The filed figure is 150,099
    (`2026-10-06-d28-date-rule/survivors_0012112/pass_t1.json`).
  - D33 (3)'s split of the uncertainty step is not produced. It is deferred by -812 and labelled
    at report `:84`.
- **N4. A gap of 4.** `records_in_pnw_box` is 252,818. D72's predicate count for the PNW box was
  252,822. Not traced. It is probably among the 9,627 unloadable rows (inferred).
- **N5. Importance fits are seeded differently.** `top_features` (`pnw_t1_fit.py:229-237`) omits
  the `bagging_seed` and `feature_fraction_seed` that `fit_predict` sets (`t1_model.py:76-77`).
  Its importance fits may differ from the fold models. Descriptive only.
- **N6. The builder's revert evidence is in text only.** For the window test (report `:69-73`)
  there is no saved runner or output. R1 below re-runs it and it bites.

## Checks (pass 1)

| # | Check | Result |
|---|---|---|
| 1 | Terms | **Holds.** No "fruiting probability". "Probability" appears only as the statistical argument name in `t1_model.py:55, :182-193`. The scoring model's label says "sighting chance (D12)" (`bd49c03`, `save_final_model`). |
| 2 | Decisions | **Drift: B1 to B3** (D24's equivalence and D54's units). The hourly route is S3. D13: target-group negatives are `cell_weeks.py:43-61`, as used by `pnw_t1_fit.py:80-94`. D31: seed 20260918, 20 configurations from a committed grid, the same for both models, inner leave-one-year-out Brier on training years (`t1_model.py:89-139`). D33 (2): see the leakage table. D46 and D54: nearest point per grid (`cells.py`), rain at the quarter point nearest the cell centre (`pnw_weather.py:116-129`). D25: `open_meteo.py:59-60`. |
| 3 | Fixed choices | **Holds.** See below. |
| 4 | Scope | **Holds.** Features are calendar, place and the 32 windows only. No habitat. The East box is not pulled, by D123. |
| 5 | Record | **Gap: S4.** D123 adds one row and edits none (`git diff 36cc647 -- DECISIONS.md`: 1 insertion). |
| 6 | Data hygiene | **Holds.** No data in git. The pre-commit large-file guard runs. |
| 7 | Claims cite | **Gap: S2, N6.** The report is a draft. |
| 8 | Revert checks | **Holds.** Five reviewer reverts bite (below). |
| 9 | Headlines re-run | Not yet: pass 2. |
| 10 | Gaps | Below. |

**Fixed before fit (check 3, observed).**
- `tuning_grid.json` and `equivalence_spec.md` have exactly one commit, `4d6e864`, commit date
  18:09:23Z.
- The first fit started 18:13:49Z. The first store file was written 18:19:18Z.
- No Open-Meteo request has been made.
- `test_committed_grid_equals_the_draw` and the fit's refusal (`pnw_t1_fit.py:134-137`) tie the
  run to the file.
- Push time is not visible from git; the order above is by commit and file times.

**The spec's sample and tolerance.**
- The sample is fixed before data (`equivalence_spec.md:21-30`): a seed, a draw over cells
  defined by records only, and fixed days.
- The tolerance is fixed but not defensible as written (B2).
- "These are land cells" (`:25`) is asserted, not checked (B3 iii).

**Records (D26 to D28, D97, D98) hold.**
- The zip's sha256 is checked.
- The box subset is taken by `t1_design.box_of`.
- `t1_steps()` covers obscured, the 1,000 m limit, the date step as given, and the event key
  (taxon, cell, day).
- Observed: `records_summary.json` matches the filed counts: survivors 144,145 and duplicate-step
  reads 164,261.
- The 5,000 m and CC lists vary only the named step and the licence subset
  (`pnw_t1_records.py:43-55, :97-101`).

**Leakage, pooling and clustering: reviewer revert checks** (`revert_runner.py.txt`, committed at
`2ba722a` before it ran; `revert_runner.out.jsonl`).
- The runner refuses on collection errors, restores from its own copy, and confirms the sha256
  and the forward text.
- Every one ran with exit 1, no errors, and was restored equal.

| Revert | Fails | Message (specific to the edit) |
|---|---|---|
| R1 window shifted a day later (`daily_grid.py`) | both window tests | 32/32 features differ; `array_equal` False after adding 1000 to days ≥ scored |
| R2 outer fit trains on the held-out year | `test_held_out_predictions…` | predictions all 1, not 0 |
| R3 inner tuning sees the held-out year | `test_inner_tuning…` | `2015 not in {2015.0, …}` |
| R4 bootstrap resamples units, not cells | `test_brier_skill_and_bootstrap…` | 0.78 ≠ 0.8667 for one cluster |
| R5 headline = mean of fold skills (`pnw_t1_compare.py`) | new `test_headline_is_pooled…` | −0.716 ≠ 0.160 |

- **Closed here:** `pnw_t1_compare.py` had no test. I added `tests/test_pnw_t1_compare.py`. It
  checks:
  - pooled, not the mean of fold skills;
  - the partial label;
  - refusal of mismatched units.
- **Suite:** 429 passed with the added test, and ruff is clean.
- **Not reverted:** the positive and negative test (`test_cell_weeks.py:47`). It predates the
  pilot (`ac12f55`) and no one-line edit makes a unit both positive and negative.

## Deviations the pilot takes, and whether each is labelled

| Deviation | Authority | Labelled in code | Labelled in report |
|---|---|---|---|
| No East box | D123, -811 | `pnw_t1_records.py:6-7`, `pnw_cds_pull.py:7-8` | `:6` |
| Weather pulled for the union box | D123, -812 | `pnw_cds_pull.py:39-45` | `:25` |
| Partial-year fits | owner's "Train as it downloads", not recorded (S4) | `--years` → `partial`, "PARTIAL" (`pnw_t1_fit.py:142-145, :183-185`), carried by `pnw_t1_compare.py:45-48` | — |
| Missing weather inside a run labelled "all years" | none | **no** (B3) | **no** |
| D18 review after Monday | -812 | n/a | review now running beside the build |
| D33 (3) and (4) after Monday | -812 | lists built (`pnw_t1_records.py:97-101`) | `:84` |
| Random-date comparison kept before Monday | -812 | `pnw_t1_fit.py:97-110` | `:82` |
| Whole ISO weeks 2015-W02 to 2025-W52 | builder choice | `pnw_t1_fit.py:7-10` | `:57-59` |
| Hourly ERA5-Land route | planner's builder choice | `pnw_cds_hourly_pull.py:5-8` | not yet (S3) |
| A model saved on all years for the map (-814) | -814 | "NOT an evaluation result" (`bd49c03`) | not yet |

## Gaps and what I did not check (pass 1)

- I did not check the calendar fit's numbers. Its summary was read only for the time order, and
  for 53,186 units and 1,139 positives, equal to report `:57`. Pass 2 does the numbers.
- The secondary design's code is read, not tested. No revert covers it.
- Open-Meteo's daily aggregation and its archive's storage factors are read from current source,
  not confirmed for the stored archive (B2 is marked inferred on that point).
- ERA5-Land's sea mask over the eligible cells: not counted. That needs the land files.

## Pass 2a: the builder's fixes to pass 1 (read at `ab8d28f`, merged into this branch at `eff52de`)

**Rulings that landed meanwhile** (Forager RECORD, read on `origin/records-after-173`):
- -818: the tolerance allows Open-Meteo's storage rounding, and "Train as it downloads" is now
  recorded. That closes S4.
- -819: the pilot trains and scores on Copernicus. The equivalence test runs and is reported, but
  no longer gates the pilot fit. D24 and D19 are bent for the pilot only.

**Each pass-1 finding, as fixed:**

| Item | Fix | Status |
|---|---|---|
| B1 | `TO_UNITS` per variable (`9060ea6`, `pnw_weather.py`), plus `tests/test_pnw_weather_units.py` | **Closed.** Reviewer revert R6 (`swvl1` given −273.15 again) fails the units test with "Obtained: −272.85 … Expected: 0.3" (`revert_runner_pass2a.out.jsonl`). |
| B3 | `build()` reads `hourly-era5land-*.daily.h5` (`e2865eb`). `weather_status` sorts each NaN unit as sea or missing days. The fit drops sea units, counts them by reason and year, and refuses missing days in a run not labelled partial. The calendar model takes the same `--weather` so both models hold the same units (`9060ea6`, `pnw_t1_fit.py`). | **Closed.** Reviewer revert R7 (every NaN read as missing days) fails `test_weather_status_tells_sea_from_a_month_not_pulled` at index 1. The fit's refusal path itself is read, not tested. The calendar fit of 18:24Z ran without `--weather`, so it must be refit on the weather unit set (RECORD -821 says so). `pnw_t1_compare.py` refuses the mismatch if it is not (R5's sibling test, `test_runs_on_different_units_are_refused`). |
| S2 | The fit refuses a dirty tree and writes `commit` into every summary (`9060ea6`) | **Closed.** |
| S3 | Overlap tolerance 0.001 K and 0.00001 m³/m³ fixed in `pnw_route_overlap.py` (`9060ea6`) | **Closed on timing.** The daily-statistics file for 2019-01 has not arrived (`cds/` listing, 18:43Z), so no overlap value was read. Note: the bound assumes both routes start from identically packed hourly fields. That is plausible but unverified, so a failure there should be read before it is acted on. |
| S4 | RECORD -818 | **Closed.** |
| N5 | Seeds added to `top_features` | **Closed.** |

**New findings in the fixes.**

**S5 (should-fix; it is not the pilot's gate since -819). `pnw_equivalence.py` at `ab8d28f`
cannot produce a result.**
- (i) **Observed:** it crashes on its first span. The request now runs to `end + 1 day` (`:110`),
  so Open-Meteo returns 8 daily and 192 hourly values. `:122-127` still reshape to (7, 24), and
  `:130` subtracts 8 values from 7. `probe_equivalence_8day.out.txt` (mocked inputs, no network):
  `ValueError cannot reshape array of size 192 into shape (7,24)`. The Open-Meteo request is
  made and cached before the crash.
- (ii) **Read:** `TOL` at `:34-39` is still the superseded 0.05 / 0.05 / 0.05 / 0.0005. The
  restated spec's bounds (0.075 °C, 0.075 °C, 0.001, 1.25 mm) are not in the code.
- (iii) **Read:** `convention` is declared (`:78`) but never appended to, so the rain convention
  test always reports 0 days.
- (iv) **Read:** `:149` rebinds `a`, the parsed arguments, to a numpy array. `:161` and `:174-176`
  then read `a.available` and `a.out`, which would raise after every request has been made.
- -819 says this test "runs to completion and its result is reported". As written it cannot.
- **Fix:** slice the first 7 days for the comparison, apply the restated bounds, fill
  `convention`, and rename the array.

**S6 (should-fix). A rain "pass" under the restated bound would not show equivalence.**
- The bound is a worst case of 1.25 mm per day.
- The scoring coder's check (RECORD -819) found Open-Meteo's rain 4 to 8% below the store's at
  every one of 6 cells over 90 days: 249.3 against 268.2 mm, about 0.21 mm a day.
- A level gap of that size passes the daily bound on most days. So a pass on rain could sit beside
  a systematic gap that rounding cannot cause, since rounding is symmetric.
- **Fix:** report the sample's summed rain ratio (Open-Meteo over store) and its sign test beside
  the pass, so the reader sees the level as well as the bound.

**N7 (note). "Before any Open-Meteo body was read" is narrower than it reads.**
- The claim is in `0caf56d`'s message and the spec's restated header.
- It holds for the equivalence sample: no `equivalence*/open-meteo/` exists.
- But the scoring coder's Open-Meteo bodies were written from 18:34:15Z to 18:34:54Z
  (`scoring/feature-check/`, file times), and -819's rain gap was recorded at 18:36:11Z. Both came
  before the restated spec's commit (18:39:30Z).
- -818's ruling (18:34:34Z) names the rain bound's form ("rain bounded by the rounding of its
  hourly values"), and the committed bound follows mechanically from Open-Meteo's storage step. So
  I read it as not tuned to those values (inferred). The header should still say Open-Meteo rain
  values from outside the sample had been seen.

**Suite at `eff52de`:** not re-run in full. R6 and R7 ran their own class each. The full suite runs
in pass 2 once the fits finish, to leave the processor free.

## Pass 2b: pull restructure and the coastal-cell measurement (read at `4fd6c09`, merged at this commit)

**Coastal cells: every figure reproduced.**
- Observed: `coastal_recount.out.txt`. It uses this branch's `primary_units` over the builder's
  `records/t1_1000m.csv` and the 2019-01 hourly-route land file, both read-only.
- Box points with values on every day: 2,387 of 3,116. The same count when values on any day are
  enough, so the mask does not vary within the month.
- Unit cells with no value: 182 of 2,043. Their cell-weeks: 8,704 of 53,186.
- Positives in those cells: 189 of 1,139.
- Cells with a land neighbour: 163, holding 188 positives.
- Cited at report `4fd6c09`, "Coastal cells".

**N8 (note, for whoever rules on the coast). The positives dropped are not a random sixth.**
- They are the coastal cells. Inferred: those include coastal chanterelle country.
- A headline fitted without them describes a smaller, inland-weighted population.
- Whichever option is ruled, the report should give the headline's units and positives beside
  53,186 and 1,139, and say which cells left.
- If a neighbour's weather is borrowed, that is a change to D46's nearest-point rule for those
  cells, and should be labelled as one.

**N9 (note). Pull bookkeeping.**
- (i) `cds_jobs._norm` sorts list values, so `area` [N, W, S, E] is compared as a set. Two
  requests whose areas are permutations of each other would match. Harmless for these areas
  (inferred).
- (ii) For an adopted job, the hourly route's `requested_at_utc` is the adoption time
  (`pnw_cds_hourly_pull.py`: `requested_at` is set before `cds_jobs.fetch`), not the time the job
  was submitted. D52 asks for the latter. `cds_adopt_job.py` records `submitted_utc` correctly; the
  hourly route does not.

## Pass 2c: the coastal ruling and the records rerun (read at `0aec3bd`, merged at this commit)

**RECORD -822 holds as built.**
- The owner ruled: "Nearest land neighbour (Recommended)".
- `coastal.land_point` takes the cell's own point first, then the nearest of the 8 neighbours by
  great-circle distance, then none. The key `(d, −lat, −lon)` breaks ties north, then east (D63).
- `weather_matrix` gives each unit its class: own, neighbour or none.
- The fit counts neighbour units, neighbour positives and neighbour cells, and saves `land_point`
  per unit in the npz (`pnw_t1_fit.py` at `d16a231`).
- **Reviewer reverts** (`revert_runner_pass2c.out.jsonl`):
  - R8 (no neighbour ever) fails 3 tests. One of them is the end-to-end builder test: "['none'] ==
    ['neighbour']".
  - R9 (ties toward south-west) fails `test_tie_goes_east_then_north`.
- **N10 (note).** Only the east/west tie is tested. A north/south tie flipped to south passes every
  test, as R9 shows by failing on the east/west case alone.

**Prediction for the weather unit set**, written before any weather fit summary exists
(`coastal_recount.out.txt`, 2019-01 mask):
- 19 cells have no land neighbour. They hold 468 units and 1 positive.
- So a full-years fit with no missing days should hold 52,718 units and 1,138 positives.
- 8,236 of those units should read a neighbour.
- The 2019-01 mask is taken as every month's (inferred: ERA5-Land's land mask is fixed). If a
  summary differs, the mask or the missing days are where to look.

**Records rerun from committed code (`0aec3bd`): holds.**
- The three CSV hashes in the committed summary are unchanged from `5a527b7`.
- They equal `sha256sum` of the files on disk (observed).
- So the first run's outputs are the committed code's, which closes S2 for records.
- The calendar fit of 18:24Z has no such check yet, and is to be refit on the weather unit set
  anyway.

## Pass 2d: rain by the hourly route (read at `ff6d4f7`, merged at this commit)

**What changed.**
- RECORD -826 (owner: "Hourly, checked against 2019 (Recommended)") bends D54 for the pilot. Rain
  years not yet delivered come from hourly ERA5 single levels, summed in code.
- The code (`hourly_daily.daily_sums_previous_hour`) gives day d the stamps d 01:00 to d+1 00:00.
  It cites the store's `time_shift` attribute on its daily file (D51 report).
- The check tolerance is 1e-5 m on every point and day of 2019 against the store's own daily sum.
  It is committed in `pnw_cds_precip_hourly.py` (`a5a981b`) before any comparison.
- The other convention is shown as a diagnostic only.

**Reviewer revert R10** (`revert_runner_pass2d.out.jsonl`): summing stamps 00:00 to 23:00 fails
`test_accumulated_hours_sum_stamps_01_to_24` at the first day.

**N11 (note).** That test checks the code's convention, not the store's. The evidence that 01:00
to 24:00 is right is the 2019 check, which has not run yet. My pass-1 D51 pair (Open-Meteo against
the store, 4 of 5 rain points off by 0.08 to 0.18 mm) does not separate convention from rounding,
so it neither supports nor contradicts this choice. Pass 2 reads the check's output before
anything summed is used.

## Pass 2e: the 2019 rain check and the run order (read at `a8f85b9`, merged at this commit)

**The 2019 rain check holds, reproduced by independent code.**
- `rain_2019_recheck.py.txt` and its `.out.txt` share no code with `pnw_cds_precip_hourly.py`.
- It read the builder's two files read-only.
- Summing stamps 01:00 to 24:00 gives all 192,355 values (365 days × 527 points) **exactly equal**
  to the store's daily sum: max difference 0.0. This includes the wet days; the largest is
  126.2 mm, and 144,789 of the reference values are not zero.
- Stamps 00:00 to 23:00 put 97,562 values over 1e-5 m, max 8.67 mm.
- Both match `precip_hourly_vs_daily_2019.json` (`267e3ad`).
- The daily file's `valid_time` carries `time_shift` "-1 days +23:00:00", as `hourly_daily` cites.
- So the hourly rain route is the store's daily sum, and RECORD -826's condition is met. N11 is
  closed.

**Run order (`pnw_t1_run_all.sh`).**
- `main` builds the weather file once, then fits calendar then full for the primary design, then
  the random-date design, each with `--weather`, so both models share a unit set. It compares each.
- `extras` is D33 (3) and (4).
- One CPU job at a time. Every fit inherits the dirty-tree and missing-weather refusals.
- **S5 is still open:** the equivalence script is not in the run order and is unchanged since
  `ab8d28f`. -819 asks for its result to be reported.

## Pass 2f: queue decisions and the land route's stand-in check (read at `1f62e99`, merged at this commit)

**The derived jobs are dismissed, and both weather variables now come only by hourly routes.**
- Report "Queue decisions" (`:146-161` at `1f62e99`) names both dismissed jobs with their ids, and
  the time, 20:20:10 UTC.
- Rain by the hourly route is exactly the store's daily sum (pass 2e).
- No derived land month has arrived (`cds/` listing), so the hourly-to-derived land check
  (`pnw_route_overlap.py`, S3) has nothing to run on.

**The stand-in is stated as such.**
- Report `:158-161`: "D24's equivalence comparison … stands in for the route agreement check, as
  the planner set". One derived land month is still tried if a slot frees.
- **S7 (should-fix). The stand-in is weaker than the check it replaces, and cannot run today.**
  - (i) Its tolerance is 0.075 °C (RECORD -818). The route check's is 0.001 K. A one-hour shift in
    the land day boundary moves a daily mean by (T at 00:00 − T at 24:00)/24. Inferred: that is
    usually under 0.075 °C, so the stand-in may not tell the conventions apart. The route check
    would.
  - (ii) The script that would run it, `pnw_equivalence.py`, crashes on its first span, and still
    carries the superseded tolerances (S5, unchanged at `1f62e99`). The stand-in exists only on
    paper until S5 is fixed. It is also not in `pnw_t1_run_all.sh`.
  - The rain route needed its own exact check (pass 2e) because rain is accumulated.
    Temperature and soil are instantaneous, and `hourly_daily.daily_means` uses stamps 00:00 to
    23:00 (tested, `test_hourly_daily.py`). That is the store's daily-statistics definition as the
    module cites it. That makes a boundary error less likely for land (inferred), not ruled out.
  - The report's result section should say which check the land route actually passed, and its
    tolerance.

## Pass 2g: equivalence rewritten, with an hourly land-route check (read at `d9d396d`, merged at this commit)

**S5 is closed.**
- `split_span` takes the first 7 of 8 days and keeps all 192 hours (`pnw_equivalence.py:87-106`).
- The restated bounds are in code (`:50-55`).
- `convention` is filled (`:207-214`), and the argument clash is gone (`args`).
- The spec's append-only correction (`equivalence_spec.md`, "Correction") names the failed edit in
  `0caf56d`.
- **Reviewer reverts** (`revert_runner_pass2g.out.jsonl`):
  - R11 (temperature bound back to 0.05) fails `test_bounds_are_the_restated_ones`.
  - R12 (8 days compared) fails the span test, "8 == 7".

**S7 is closed by a stronger check than the one I asked for.**
- The land route is now checked hour by hour against Open-Meteo at offsets −1, 0 and +1
  (`:234-260`). The bounds are committed in the spec's "Hourly land route" section before any body
  was read: no `equivalence/` directory existed at 20:39Z.
- It passes only if offset 0 matches every compared hour and beats both other offsets.
- It gates the fit (`pnw_t1_run_all.sh`, exit 3).
- **Can it discriminate?** I measured how often one hour moves each variable past its bound, on
  the kept 2019-01 hourly file (`hourly_step_sizes.out.txt`): t2m 87%, stl1 51%, swvl1 28% of
  1,773,541 hourly steps. So a one-hour misalignment would lose matches on every variable. The
  "beats both other offsets" condition is not a coin-toss on slow variables, at least in January.
  Summer soil moisture is likely flatter; not measured.

**N12 (note).**
- (i) The pass rule (`:252-260`) is untested; it sits inside `main`.
- (ii) It compares matched hours by absolute count, not by share. An offset with fewer compared
  hours (store hours missing at a month edge) can lose on count alone. That would make the
  discrimination condition easier to meet than it reads, never harder.

**S6 is still open.** The rain convention test reports mean absolute differences per convention.
The summed rain ratio (Open-Meteo over store), which would show RECORD -819's 4 to 8% level gap
beside a daily pass, is not reported.

## Pass 2h: a subset-years scoring model for the map (read at `a23135f`)

**A deviation, labelled.**
- `--final-only --years` now saves a scoring model fitted on a subset of years under its own tag,
  `…_years_<first>_<last>` (`pnw_t1_fit.py` at `a23135f`).
- Its `model.json` says "fitted on <first>-<last> only; T1's all-years result pending" and
  `partial_years: true`.
- It has no held-out evaluation of its own, and the headline does not describe it, since that
  comes from the all-years held-out predictions.
- Added to the deviations above, in substance: the map may show a model on fewer years than T1
  evaluates. That is labelled in its `model.json`; whether the map's banner carries it is the site
  track's to show, and was not checked here.

## Pass 2i: the hedge run's gates and the early land-route check (read at `97a6610`, merged at this commit)

**The gate order in `pnw_hedge_run.sh` (`a5b0be3`) holds.**
1. `:21` builds the weather file.
2. `:22-26` runs the equivalence with `--available` and exits 3 on any non-zero return. That
   includes a land-route fail (`pnw_equivalence.py:295`) and a crash.
3. Only then come the fits (`:27-32`), the comparison (`:33`) and the scoring model (`:35-37`).
4. With `set -e`, a failed build stops it too.
- With zero spans available the land-route gate fails, not passes: `n0` is 0, so `pass` is False
  (`pnw_equivalence.py:258-260`). It cannot pass vacuously.
- Both models get the same `--weather` and `--years`, so `pnw_t1_compare.py` compares one unit
  set, and labels it PARTIAL.

**The early land-route check (`equivalence_early_partial_2110Z.json`, `97a6610`) is as reported,
but it is one span.**
- Cell 492_-1246 from 2019-01-08.
- Offset 0 matches 192/192 hours on t2m, stl1 and swvl1. Offsets −1 and +1 match 37 and 32, 103
  and 96, 59 and 58.
- So the best offset is 0 on all three. That agrees with the step-size measurement in pass 2g.
- Of the other 35 spans, 32 were skipped as incomplete (24 of them start in 2019 to 2025) and 3 as
  a sea point.

**S8 (should-fix). The equivalence skips the sea-point cell the fit keeps.**
- `pnw_equivalence.py:194-199` sets aside all three spans of cell 427_-1245 as a sea point.
- Under RECORD -822 the fit reads that cell's land weather from its nearest land neighbour.
- So 3 of 36 spans are never compared, and the neighbour path that 8,236 units use (pass 2c
  prediction) is never checked against Open-Meteo.
- **Fix:** compare those spans at the neighbour point the fit uses (`coastal.land_point`), or state
  in the result that the sample is 33 spans and the neighbour path is unchecked.

**S9 (should-fix). The hedge's land-route gate passes on however many spans have arrived.**
- `pnw_hedge_run.sh:22-26` with `--available` passes on one span. It did so at 21:50Z.
- 25 of the sample's 36 spans start in 2019 to 2025, which are the years the hedge fits.
- **Fix:** require every non-sea 2019 to 2025 sample span to be compared before the hedge's fits
  run, or at least print the number of spans compared beside the pass, so a one-span pass is not
  read as the gate.

**N13 (note). One day's 18% gap is not the 4 to 8% finding.**
- Report `:173-176` says the one daily rain miss (11.36 against 9.3 mm, 18% low) "matches" the
  scoring coder's 4 to 8% finding.
- One day 18% low is consistent with an aggregate gap. It is not a measure of it.
- S6's summed ratio over the sample would be the comparable figure.

**N14 (note). The hedge's early-2019 units may drop.**
- 2019's early units have 90-day windows that reach into 2018.
- In a `--years` run, units whose windows reach unpulled months are dropped as `missing_days`.
  They are counted, not refused (`pnw_t1_fit.py`, B3 fix).
- The hedge's 2019 fold may hold fewer units than the all-years run's. The summary shows how many.

## Pass 2j: the S6, S8, S9 and N12 fixes (read at `b665caf`, merged at this commit)

**Closed.**
- **S9:** `--require-years 2019-2025`. The gate needs every non-sea 2019 to 2025 span compared, and
  at least one (`spans_complete`). The hedge prints the GATE line.
- **S6:** a summed rain ratio is in `rain_level`.
- **N12:** the pass rule is the tested `land_route_pass`, including the tie and the
  zero-compared cases.
- The three new tests were read, not reverted.

**S10 (should-fix, urgent: it will make the gate fail on a correct route). S8's fix compares
two different points.**
- `compare_point` moves the *store* side of a sea cell to its RECORD -822 land neighbour.
- The *Open-Meteo* request is still made at the sea cell's own centre:
  `fetch(request_url(cell, start), …)`, `pnw_equivalence.py:250` at `b665caf`.
- **Observed** (`openmeteo_sea_point_probe.out.txt`, one request per model, 2016-11-17, cell
  427_-1245 at 42.7, −124.5):
  - `models=era5_seamless` returns values there: t2m 10.7, 10.2, 9.7.
  - `models=era5_land` returns null.
  - So for that cell, Open-Meteo's seamless series is not ERA5-Land. Inferred: it is ERA5's
    0.25° field.
- The hourly check then compares the store's ERA5-Land neighbour with Open-Meteo's other-product
  value at the sea point. Offset 0 will not match every hour, so `land_route_pass` fails.
- With `--require-years 2019-2025`, cell 427_-1245's 2023-02-20 span is required. Its other
  spans (2016, 2018) are compared whenever their data are in. **The gate in both
  `pnw_t1_run_all.sh` and `pnw_hedge_run.sh` would then stop the fit on a route that is correct.**
- **Fix:**
  - Request Open-Meteo's land variables at the neighbour point's coordinates.
  - Keep rain at the cell centre's quarter point, since the neighbour's nearest 0.25° point can
    differ.
  - Key the cache by the requested point, not the cell id.
  - Or leave neighbour cells out of the gate and report them apart.
- **N15 (note, for T10).** The same observation bears on serving. For a cell with no ERA5-Land
  value, Open-Meteo's `era5_seamless` silently serves another product. RECORD -822's neighbour rule
  has no counterpart on Open-Meteo's side.

## Pass 2k: notes folded into the builder's report (read at `1facf26`)

**Closed:**
- **N1:** the docstring is corrected.
- **N8:** neighbour cells are listed in every fit summary and in the equivalence result.
- **N9:** stated in the docstring and the report.
- **N13:** the report now says "consistent with … not a measure of it". The summed ratio was 0.974
  over 7 days.
- **N14:** dropped units are counted, and the hedge waits for 2018-10 onward.

**N3 and N4: traced by the builder, not verified by me.** The 4-row gap is put down to 4
multi-day `eventDate` rows (252,822 by raw coordinates, less 4). The script was `/tmp/pnwp_n4.py`,
"run once, not committed". I did not re-run a 2.5-million-row read while the pull and fits need the
processor. Until that script is committed, the trace is a claim with no checkable source.

**Still open:**
- **S10:** the sea-point comparison; urgent, since the gate is affected.
- **N10:** a north/south tie is untested.
- **N15:** for T10.

## Pass 2l: S10 fixed (read at `f6bc9a3`)

**S10 is closed.**
- `request_cells` asks Open-Meteo for the land variables at the land point the store side reads
  (the neighbour for a sea cell), and for rain at the cell centre.
- The cache is keyed by the requested point, so no body fetched at a sea centre is reused.
- Each row records `om_land_request`.
- The new test covers both cases. It was read, not reverted.
- Not observed on data yet: no store hourly month for cell 427_-1245's spans was checked by me.
  The equivalence result will show the neighbour cell among `neighbour_cells_compared`, with its
  hours inside the offset-0 counts.

## State at hand-back (2026-10-11 00:13 UTC)

- No pilot commit since `f6bc9a3` (15:07 PDT).
- The hourly pull is still running, and was retrying a DNS failure at the time (`pull_hourly.log`,
  last lines).
- Local fit outputs exist but are not pushed, and were not reviewed: the primary and secondary
  calendar fits, and `final_calendar.log`.
- The pass-2 items below need a new review session once results are pushed.

## Pass 2

Pending:
- the equivalence result;
- both fits on the weather unit set;
- the headline and its interval;
- the per-fold table;
- the random-date comparison.

Each will be traced to its output file and sample.

Pass 2 is written below, item by item, against `pnw-pilot-t1` at `7d19c66` (merged into this
branch at `398347b`). Base verified against the remote before starting: `pnw-pilot-t1-review` at
`3e5aa7d`, `pnw-pilot-t1` at `7d19c66`. The data read are in
`~/Zynergy/forecast-data-pnw-pilot/`, read in place, never written. Scripts and outputs are in
`2026-10-10-pnw-pilot-t1-review/pass2_*`.

**State found at 16:58 UTC, a wrong premise in the dispatch.** The planner's note said the extras
run was in progress. It is not: it stopped about three seconds after it started.
- `override_chain.log` ends at "16:54:20Z extras", with no "extras exit" line and no "chain
  finished". No fit process, chain shell or run script is running (`ps`, observed).
- `fits/primary_t1_5000m_calendar.log` holds two lines: "57418 units, 1366 positive", then
  "weather missing for 22 units (months not pulled); a run over all years refuses them (review
  B3)".
- So the first extras fit (D33 (3), the 5,000 m list) refused to start under the B3 guard, and
  `set -euo pipefail` in `override_chain.sh` ended the chain before it wrote an exit line. Inferred:
  the 5,000 m list reaches cells, or days, whose weather the 1,000 m pull never fetched. D33 (3)
  and (4) have no output. Item 5 below covers what can be checked (the random-date comparison,
  which ran in main).

### Item 1: the equivalence result, the failing hour and the override (RECORD -854)

**Recomputed** with my own code (`pass2_rounding_check.py.txt`), which imports nothing from the
builder. It reads the 36 cached Open-Meteo bodies the main run used
(`equivalence/open-meteo/`), the gridded hourly months (`cds/hourly-era5land-YYYY-MM.hourly.nc`)
and the time-series zips (`ts/pt_*.zip`) directly. The three `427_-1245_*` bodies are that sea
cell's rain requests at its centre; its land variables come from `427_-1244_*` (RECORD -822, S10).
The hedge's cached bodies hold the same hourly and daily data as the main run's, all 39 compared
field by field, and both runs read the same store files. So one recomputation covers both runs.

**The gate's figures reproduce exactly** (`pass2_rounding_check.out.txt`):
- Offset-0 matched/compared: t2m 6,911/6,912, stl1 6,912/6,912, swvl1 6,912/6,912.
- Offsets −1 and +1: t2m 762 and 675, stl1 2,356 and 2,218, swvl1 4,149 and 4,133.
- These equal `equivalence/equivalence.json`, the hedge's `equivalence.log` and both
  `gate_record.json` files.
- **One failing hour, the same in both runs:** t2m, cell `493_-1250` (own land point),
  2025-12-12T11:00 UTC.
  - Store (gridded month) 5.424951 °C, Open-Meteo 5.5 °C.
  - Difference 0.0750488, bound 0.075001.
  - The time-series route gives 5.425012 °C for the same hour.
- The gate code is byte-identical to `ae4f1e9`: `scripts/pnw_equivalence.py` is not in
  `git diff ae4f1e9 7d19c66`. `land_route_pass`, `HOURLY_TOL` and `EPS` are unchanged, and the
  gate still writes `"pass": false`.

**The rounding explanation holds. It is tested on every compared hour, not only argued from the
one that failed.** I modelled Open-Meteo's temperature as the store value rounded to 0.05 °C,
then shown at 0.1 °C with halves going up, and checked that model against every hour:
- Applied to the **time-series route's** value, the model predicts Open-Meteo's number exactly
  for **6,912 of 6,912** t2m hours and **6,912 of 6,912** stl1 hours.
- Applied to the **gridded route's** value (2,112 hours where a gridded month exists), it
  predicts 2,110 of 2,112 for each variable. The four misses (two t2m, two stl1):
  - each lies within 0.00005 °C of a 0.05 °C rounding midpoint;
  - in each, the time-series value lies on the other side of that midpoint;
  - in each, Open-Meteo shows the time-series side's rounding.
- The failing hour is one of those four. The other three miss by 0.025 °C on display, well
  inside the bound. Only this one lands on the far side of the bound.
- Where both routes hold the same hour (about 1,750 hours per variable), they differ by 0.5 to 4
  units of 2⁻¹⁴ K, up to 0.00024 K.

**What holds and what is inferred:**
- **Observed:** a 0.05-then-0.1 double rounding of the time-series route's value reproduces every
  one of 13,824 temperature hours, including the failing one. So 0.075 is the bound for that
  scheme's worst case, and the one failure comes from which Copernicus route the store read
  that month, not from a misaligned or wrong value.
- **Inferred, not checkable from here:** that Open-Meteo stores at 0.05 °C. Also that its own
  source decodes like the time-series route.
- **A carried figure, corrected.** RECORD -854's "the two Copernicus routes differ by up to
  0.00016 K (`ts_check.log`)" is a daily-mean figure: `pnw_ts_check.py` compares daily means
  (docstring `:5-9`). Hour by hour, on this sample, the routes differ by up to 0.00024 K. That
  widens the room for a flip, so it does not weaken the explanation. It is still the wrong figure
  to quote for one hour.

**The daily comparison (D24, reported, not gating) also reproduces**
(`pass2_daily_recount.py.txt`, `.out.txt`): **30 mismatches of 1,008 values, all precipitation.**
- The Open-Meteo side was re-read from the bodies: 0 differ from `equivalence_values.json`.
- The land store side was recomputed as 24-hour UTC means of the time-series route: 0 differ.
- The match flags were recomputed with the committed tolerances: 0 differ.
- The rain store side was **not** recomputed; it is the builder's.
- This agrees with RECORD -855.

**The override path** (`scripts/pnw_gate_override.py`) goes on only when all of these hold:
- the override string is exactly "Forager RECORD -854";
- the failing hours equal `RULED_HOURS`, the one hour above;
- the failures file agrees with the run's offset-0 counts.

Both runs' records say `"gate_pass": false`, name the hour, and say `"override": "used: …"`.
The main run's record has `spans_complete: null`: main requires no years, so the gate's span
requirement is empty there. The hedge's record has `true`.

**Verdict, item 1:** the equivalence result and the failing hour reproduce exactly. The rounding
explanation holds on the data, beyond what RECORD -855 claimed ("supports without proving"). Two
parts remain inferences about the other service's internals, as listed above.

### Item 2: both fits on the weather unit set, hedge and main (read at `7d19c66`)

**Recomputed** with my own code (`pass2_headline_recompute.py.txt`; outputs
`pass2_headline_main.out.txt` and `pass2_headline_hedge.out.txt`). It reads the held-out
predictions in each `<prefix>_{calendar,full}.npz` and nothing of the builder's but those arrays.
- **Main run, primary design** (`fits/primary_t1_1000m_{calendar,full}.npz`, commit `7d19c66`
  in both summaries):
  - **52,718 units and 1,138 positives in both fits, with the same units, labels and order.**
  - That is exactly pass 1's prediction (line 383), written before any weather summary existed.
  - 8,236 units read a neighbour, also exactly as predicted. They hold 188 positives.
  - 2,024 cells. The prediction is met, so neither the land mask nor missing days removed
    anything unexpected.
- **Hedge run, primary design** (`hedge/fits/`):
  - 49,235 units and 1,089 positives on 2019 to 2025, the same in both fits. 7,628 units read a
    neighbour.
  - Every 2019 to 2025 fold holds the same units and positives as the main run's fold for that
    year (2,965/72 for 2019, and so on). So N14's possible 2019 drop did not happen.
  - Both summaries say `partial: true` and "PARTIAL: a fit on a subset of years, not the T1
    result".
- **Fold year:** units dated 29 to 31 December sit in the next year's fold (322 units). That is
  the ISO year, as `pnw_t1_fit.py:8-10` states for the primary design. Not a fault.
- Brier and AUC for every fit reproduce the builder's to the printed precision.

**Verdict, item 2:** both fits hold the predicted unit set, and the hedge is labelled partial.
Holds.

### Item 3: the headline and its interval (read at `7d19c66`)

The T1 headline is the all-years run only (D33 (2)): `fits/primary_t1_1000m_comparison.json`,
labelled "T1 result", `partial` false in both fits. It is pooled over all 52,718 held-out
cell-weeks from 11 leave-one-year-out folds, with the interval from resampling cells.

**Recomputed** (`pass2_headline_main.out.txt`). My interval uses my own resampling code and seed,
not `tm.clustered_bootstrap_skill`:

| | builder | reviewer |
|---|---|---|
| Brier, calendar | 0.020609110 | 0.020609110 |
| Brier, full | 0.020681984 | 0.020681984 |
| Brier skill (full against calendar) | −0.003536 | −0.003536 |
| 95% interval (1,000 cell resamples) | [−0.006569, −0.000100] | [−0.006777, −0.000196] |
| AUC calendar / full | 0.7918 / 0.7828 | 0.7918 / 0.7828 |
| verdict | "worse" | the interval lies wholly below zero |

**How close the upper end sits to zero** (`pass2_interval_seeds.out.txt`):
- Over 50 seeds of 1,000 draws each, the upper end runs from −0.00064 to −0.00006. No seed's
  interval reaches zero.
- With 20,000 draws the interval is [−0.00680, −0.00027], and 1.6% of draws are at or above zero.
- The builder's −0.00010 is inside the spread across seeds. The sign of the upper end does not
  depend on the seed.

**What the headline says.** On held-out years, the weather model predicts worse than the
calendar-and-place baseline. The difference is small, but the 95% interval lies wholly below zero.

**What the rulings say about it:**
- D5: "Each ecoregion is published only after it beats a calendar baseline on held-out years."
- D33 (5) names only the case of an interval that includes zero ("not shown", off the map under
  D5).
- A wholly negative interval is a stronger failure to beat the baseline. So by my reading, D5
  rules the full model off the map for the PNW. That is a reading of D5, not a ruling, and the
  owner decides.
- The hedge (2019 to 2025, PARTIAL, not the headline) gives −0.002909 with my interval
  [−0.0077, 0.0012] ("not shown"). It does not change this, and under D33 it could not.

**B4 (blocking, for publication only; the computation holds).** The T1 headline is "worse".
Yet nothing in `models/primary_t1_1000m_full/model.json` or
`models/primary_t1_1000m_full_years_2019_2025/model.json` says so:
- Both were written before the comparison ran (15:58Z and 15:44Z, against 16:29Z for the main
  comparison).
- They carry the label "unvalidated pilot, unreviewed", the gate record and the sources, and no
  verdict.
- So a scoring or publishing step reading only `model.json` would publish a full model that fails
  D5's test.
- **The owner decides** whether the full model is withheld, or the calendar model shown, or
  something else. This review does not pick.

**Verdict, item 3:** the headline and its interval reproduce. The result is that the full model
is worse than the calendar baseline on held-out years.

### Item 4: the per-fold table (read at `7d19c66`)

**Recomputed** from the npz arrays (`pass2_headline_main.out.txt`, "per fold"). Every row matches
the builder's `folds` in `fits/primary_t1_1000m_comparison.json`: units, positives, the
informative flag (30 positives or more), and skill to 1e-12.

| year | units | positives | informative | skill |
|---|---|---|---|---|
| 2015 | 391 | 3 | no | +0.0173 |
| 2016 | 580 | 7 | no | −0.0125 |
| 2017 | 842 | 12 | no | −0.0202 |
| 2018 | 1,670 | 27 | no | −0.0189 |
| 2019 | 2,965 | 72 | yes | −0.0093 |
| 2020 | 5,329 | 107 | yes | +0.0015 |
| 2021 | 6,315 | 115 | yes | +0.0027 |
| 2022 | 6,482 | 89 | yes | +0.0048 |
| 2023 | 8,297 | 97 | yes | +0.0080 |
| 2024 | 9,342 | 300 | yes | −0.0063 |
| 2025 | 10,505 | 309 | yes | −0.0080 |

- 2015 to 2018 are marked uninformative, as D33 (2) requires.
- 4 of the 7 informative folds favour the weather model.
- The two folds with the most positives (2024 and 2025, 609 of 1,138) favour the calendar model,
  and they dominate the pooled figure.
- Pooled over the informative folds alone, the skill is −0.0030 (49,235 units). The four thin
  folds do not drive the negative headline. They are only reported here; D33 pools all years.

**Verdict, item 4:** the table reproduces and is marked as D33 (2) requires.

### Item 5: the random-date comparison, and D33 (3) and (4) (RECORD -828)

**The random-date comparison (D13, secondary design) ran in main and reproduces**
(`pass2_headline_main.out.txt`):
- `fits/secondary_t1_1000m_comparison.json`: 16,042 units, 1,234 positives, 504 cells, the same
  units in both fits.
- Skill −0.002213. Builder's interval [−0.00747, 0.00306], mine [−0.00739, 0.00327]: "not
  shown".
- AUC calendar 0.7934, full 0.8045. All per-fold rows match.
- It is a comparison only (D13), not the headline. The two designs agree that weather adds no
  shown skill.

**D33 (3) (the 5,000 m list) and D33 (4) (the commercial-safe list) have no result.**
- The extras run refused at its first fit, as recorded at the head of pass 2: "weather missing
  for 22 units (months not pulled)", under the B3 guard.
- The chain then stopped silently, with no exit line in `override_chain.log`.
- RECORD -828's extra runs are therefore not done. D33 (4) never started, since it runs after
  (3) in `pnw_t1_run_all.sh extras`.
- **S11 (should-fix):**
  - `override_chain.sh` logs an exit line only on success. Under `set -e` a failure leaves the log
    looking like a run in progress, which is how the planner read it.
  - Inferred, not traced: the 5,000 m list reaches cells whose weather the pull, built for the
    1,000 m list, never fetched.
  - Which 22 units, and whether to pull their weather or drop them, is a decision for the planner.
    It touches a fixed sample.

**Verdict, item 5:** the random-date comparison holds ("not shown"). D33 (3) and (4) cannot be
reviewed: there is no output.

### Item 6: the labels (RECORD -854, -855)

**Read, in every `models/*/model.json`** (five: primary calendar, primary full, the 2019 to 2025
scoring model, secondary calendar, secondary full; all commit `7d19c66`):
- Each holds `land_route_gate` with `gate_pass: false`, `override: "used: Forager RECORD -854
  …"`, and the failing hour (t2m, `493_-1250`, 2025-12-12T11:00, store 5.424951, Open-Meteo 5.5).
- `models/primary_t1_1000m_full/model.json` also has `copernicus_sources` (four products).
- The 2019 to 2025 model says `partial_years: true` and "fitted on 2019-2025 only".
- The six fit summaries (main and hedge) carry the same `land_route_gate`.

**Not carried:**
- No `model.json` carries the D24 daily count (30 of 1,008, all rain). Nothing required it there:
  RECORD -854 asks for the failing hour. The count is in `equivalence.json` and in this review
  (item 1).
- No `model.json` carries the T1 verdict (B4).
- The builder's report section for the override (gate-override dispatch, step 3) is not on the
  remote. `docs/audits/2026-10-10-pnw-pilot-t1-report.md` at `7d19c66` does not mention RECORD
  -854. So the report does not yet carry either label.

**Reviewer's revert check** (`revert_runner_pass2.py.txt`, the pass-1 runner with two checks
added; output `revert_runner_pass2.out.jsonl`). It saves a byte copy, makes one edit, and runs the
tests with a fresh JUnit XML. It refuses any run with collection errors. It restores from the
saved copy, never from git.
- Forward run first: `tests/test_pnw_gate_override.py`, 11 passed.
- **R13** (`load_gate_record` no longer refuses a stop record): exit 1, 11 tests, no errors. It
  fails `test_the_fit_carries_a_go_record_and_refuses_a_stop_record` with "DID NOT RAISE
  SystemExit".
- **R14** (a gate fail with no override returns 0): exit 1, 11 tests, no errors. It fails
  `test_a_fail_with_no_override_stops_with_exit_3` with "assert 0 == 3".
- Each failure is specific to its own edit. Both files were restored byte-equal, the forward
  text was confirmed present, and `git status` was clean afterwards.

**Verdict, item 6:**
- Every model and fit summary carries the gate failure, the override and the hour.
- The daily count is not in `model.json`, which nothing required.
- The builder's report does not carry the labels yet.
