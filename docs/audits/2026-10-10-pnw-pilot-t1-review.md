# Review: the PNW pilot's T1 fit (D122), under the standing protocol (D18), run beside the build

- **Reviewed:** branch `pnw-pilot-t1`. Pass 1 read it at `5a527b7` (cut from main `36cc647`), then
  the three commits that landed while it was being written, to `bd49c03` (`1742544`, `8cfb43b`,
  `bd49c03`). Line cites are to `5a527b7` unless they say `bd49c03`.
- **Protocol:** `docs/dispatch/2026-09-18-review-protocol.md`, checks 1 to 10.
- **Dispatch:** `docs/dispatch/2026-09-18-t1-calendar-smoke-test.md` with its two amendments.
- **Rulings read:** D5, D11, D12, D13, D24, D25, D26, D27, D28, D31, D33, D46, D52, D54, D72, D97,
  D98, D100, D122 (`docs/planning/DECISIONS.md`), and Forager RECORD -806 to -816
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
- It appears in neither D122 nor RECORD -806 to -816 (grep, no match).
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
| 4 | Scope | **Holds.** Features are calendar, place and the 32 windows only. No habitat. The East box is not pulled, by D122. |
| 5 | Record | **Gap: S4.** D122 adds one row and edits none (`git diff 36cc647 -- DECISIONS.md`: 1 insertion). |
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
| No East box | D122, -811 | `pnw_t1_records.py:6-7`, `pnw_cds_pull.py:7-8` | `:6` |
| Weather pulled for the union box | D122, -812 | `pnw_cds_pull.py:39-45` | `:25` |
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

## Pass 2

Pending: the equivalence result, both fits, the headline and its interval, the per-fold table,
and the random-date comparison, each traced to its output file and sample.
