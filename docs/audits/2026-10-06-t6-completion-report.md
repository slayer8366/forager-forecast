# T6, the observation layer: completion report

Branch `t6-observation-layer` (unmerged), from main `41005c1` with main `5540a2c` merged in at
`770635d`. Dispatch `docs/dispatch/2026-10-06-t6-observation-layer.md` (Forager RECORD -604);
proposal `2026-10-06-t6-proposal.md`; the owner's rulings came by the planner as Forager RECORD -609.
Written 2026-10-06 by the T6 coder session (writer, D38). Waiting for the independent review (D18)
and the owner's merge word (D40).

## Verdict

**TASKS.md T6's Verify passes, on both licence tracks, under the tests fixed before any fit.**

| Track | Beats constant effort (D104) | Weekend (D105) (i) ratio and 95% interval | (ii) day-type lowers held-out deviance |
|---|---|---|---|
| All licences (D61), 43,035 cells, 879,576 outings | −2,608,992, interval −2,816,366 to −2,411,888: **pass** | 1.496, 1.478 to 1.516: **pass** | −32,147, interval −34,202 to −30,191: **pass** |
| CC0 and CC BY (D108), 16,335 cells, 106,765 outings | −173,268, interval −201,183 to −146,380: **pass** | 1.563, 1.529 to 1.600: **pass** | −4,832, interval −5,360 to −4,343: **pass** |

Read the findings section before relying on the verdicts. Condition (i) passes by construction once
the weekend is real in the raw totals. Most of the gain over constant effort comes from "people go to
some cells more than others".

## What landed

| Commit | What |
|---|---|
| `770635d` | Merge of main `5540a2c`; audit index conflict resolved keeping every row |
| `9cd95df` | Proposal, tuning grid and index row, before any count of the outcome |
| `a87117d`, `b11d9a5` | Frame-size script and its measured counts (after the proposal) |
| `0a2510a` | D101 to D108 filed, quoting the owner (RECORD -609); EVIDENCE.md correction appended (Capinha et al. used pines) |
| `b623fe8` | statsmodels 0.15.0 pinned as a dev dependency (D106) |
| `446ce0b`, `60a7541` | `src/forager_forecast/effort.py`, `effort_evaluation.py`, `t6_effort_steps()` in `records/filters.py`, `Record.class_key` in `records/occurrence.py`; `tests/test_effort.py` (29), `tests/test_effort_evaluation.py` (10) |
| `5f7b3ca` | `scripts/t6_fit.py` (count and fit stages, 5 GB watchdog) |
| `ef3269f` | Count stage output: `2026-10-06-t6-fit/steps.json`, `count_run.log.txt`; revert runner |
| `0b2c0de` | Fit results `2026-10-06-t6-fit/all_results.json`, `cc_results.json`, `fit_run.log.txt`, stored-surface hashes |
| `144ffd8` | Revert results `2026-10-06-t6-fit/revert_results.jsonl` |

The stored surface is in `data/t6/all/` and `data/t6/cc/` (git-ignored, D107). Its sha256 values are
in `2026-10-06-t6-fit/stored_surface_sha256.txt` and in each results file. The manifests name code
commit `ef3269f`, the HEAD the fit ran at.

**Tests before code, as it actually happened.** Tests and code were written in the same step and
committed together (`446ce0b`), not as a red commit followed by a green one. The evidence that each
test is connected to the code it names is the strict revert runner below, not the commit order.

## Rulings filed

D101 unit and area; D102 outings, the 1 km limit and the observer key; D103 lichens, with the corrected
premise; D104 count-based scoring (D31 unchanged for T1's models); D105 the weekend test; D106 the
model; D107 the output; D108 the CC0/CC BY surface. Each row quotes the owner's answer as relayed. D109
is unused.

## Inputs, counted

D26's zip was read in place with its sha256 checked (`c0d5f6a1…b26c`); it was never extracted. Two
independent passes agree on every shared figure: the frame-size script (`a87117d`) and the fit
script's count stage (`5f7b3ca`).

| Step | In | Dropped | Out |
|---|---|---|---|
| rows read / loaded (D66) | 2,493,578 | 9,627 (9,604 not one day, 23 span days) | 2,483,951 |
| not user-obscured | 2,483,951 | 155,988 | 2,327,963 |
| coordinate uncertainty present, at most 1,000 m | 2,327,963 | 845,666 | 1,482,297 |
| date kept as given (D97, D98) | 1,482,297 | 0 | 1,482,297 |
| one record per taxon, observer, cell, day (D27) | 1,482,297 | 102,438 | 1,379,859 |
| in the two partial weeks (D101) | 1,379,859 | 1,846 | 1,378,013 |

- Outings: 879,576 across 43,035 cells and 14 bands (15 N to 80 N). The non-zero cell-week-day
  entries number 658,232, against a frame of 49,318,110.
- Lichen outings: 131,301. All 321,965 rows with `classKey` 180 carry `class` "Lecanoromycetes".
- CC track: 106,765 outings in 16,335 cells, with 25,106 of them lichen. The licence field held no
  value outside the three known ones.

## Evaluation (fixed in the proposal and D104)

Leave one year out, 11 folds, pooled Poisson deviance over every frame cell × week × day-type of the
held-out year, zeros included. Every model is given the held-out year's own total. Intervals come
from a bootstrap of 1,000 resamples clustered by cell, seed 20260918.

**Pooled held-out deviance, all-licence track.** Each ladder step's difference and interval are in
the results file.

| Model | Deviance | Step | Difference (95% interval) |
|---|---|---|---|
| constant effort | 7,337,763 | | |
| + cell | 4,775,677 | vs constant | −2,562,086 (−2,767,586 to −2,365,513) |
| + year | 4,775,677 | vs + cell | 0 (0 to 0) |
| + season (all-fungi) | 4,612,458 | vs + year | −163,219 (−170,584 to −155,212) |
| + day-type (all-fungi fit) | 4,580,310 | vs + season | −32,147 (−34,202 to −30,191) |
| **effort surface (lichen season)** | **4,728,771** | vs + day-type | +148,461 (+140,725 to +156,069) |

Shown beside, with no verdict: with the year's level interpolated from neighbouring years instead of
given, constant scores 7,353,891, the all-fungi fit 4,596,240 and the effort surface 4,744,668. The
per-fold table is in the results files. In every fold of both tracks the effort surface scores below
constant effort, and + day-type scores lowest. In one fold (CC, 2019) the effort surface also scores
below + season.

**Configuration.** The tuning chose pull 10 in every outer fold of both tracks. Smoothing was 3
weeks in 9 of 11 all-licence folds (5 in 2020, 9 in 2021) and 9 weeks in every CC fold. The stored
surfaces use pull 10 with smoothing 3 (all licences) and pull 10 with smoothing 9 (CC).

## Findings

1. **Weekend condition (i) cannot fail once weekends are busier in the raw totals.** With the four
   main effects on a full frame, the fitted weekend-to-weekday ratio equals the raw ratio exactly:
   1.4964378 fitted against 1.4964378 raw (all fungi), and 1.5988525 against 1.5988525 (lichens).
   The test is still a real reading of the data, but "the model reproduces it" adds nothing to "the
   data show it". Condition (ii) and the interval are the parts that carry information. This belongs
   to CLAUDE.md's family of checks that pass by construction. Recorded here, not resolved.
2. **"+ year" adds exactly zero under the headline scoring.** Each held-out year is given its own
   total, so a year level is a constant that the rescaling removes. On a full frame it also leaves
   the cell levels unchanged. The year term matters only where the total is not given (the
   interpolated scoring, shown beside) and in the stored surface T7 reads.
3. **The lichen season costs fit, as stated in advance.** It is 148,461 worse than the all-fungi
   season, but better than no season (4,728,771 against + cell's 4,775,677). This is the trade D103
   ruled for.
4. **In the bulk bands (30 N to 50 N) the two seasons peak months apart.** All-fungi outings peak
   around ISO weeks 39 to 41; lichen outings peak around weeks 16 to 17. The correlation between the
   two shapes is −0.03 to 0.63 there, and 0.80 to 1.00 north of 50 N, where any outing happens in
   summer. Week 17 is late April. A spring recording event would put a peak there (iNaturalist's City
   Nature Challenge is held in late April), but that cause is **inferred, not checked**. If the
   cause is an event, the lichen season measures that event rather than general effort. That bears
   on T8 and is for the owner and planner, with no verdict here.
5. **The chosen pull sits at the top of the grid (10) in every fold.** The best value may lie beyond
   the grid. The grid was fixed before the fit and was not widened after seeing this.
6. **Small bands.** 80 N has 4 cells and 75 N has 13. Their seasons swing by factors of 500 to 800
   between slots. Raw weekend ratios by band run from 0.57 (75 N, 13 cells) to 1.88 (80 N). All are
   shown with no verdict.

## Decided beyond the rulings (fixed in code before the fit ran, all in `effort.py`'s docstring or in `effort_evaluation.py`)

- **Season pull.** The sparse-cell pull is also applied to each band's season slot, toward that
  band's flat level. Without it, an empty slot would give an infinite deviance. The proposal named
  the pull for cells only.
- **Continental fallback.** Where a band has no training outings, both pulls use the continental
  average instead.
- **Bands missing from a resample.** A band with no cells in a bootstrap resample keeps its previous
  season (`R17`).
- **Which surface tuning scores.** The inner tuning and the final configuration score the effort
  surface (lichen season), the one the pass is judged on. The proposal said only "pooled Poisson
  deviance".
- **Final configuration.** It is the lowest plain leave-one-year-out deviance over all 11 years, with
  ties going to the grid's first entry. The ladder in each fold uses that fold's chosen configuration.
- **CC outings.** An outing is in the CC track when it has at least one CC0 or CC BY record. This
  equals counting outings from those records alone.
- **Interpolated constant.** For the interpolated scoring, the constant model's total is the
  geometric mean of the neighbouring years' totals, or the nearest year's total at an end.
- **Week 53.** ISO week 53 (2015 and 2020) shares week 52's slot, as proposed.
- **A peek at the weekend ratio before the full run.** A timing probe printed the all-fungi weekend
  ratio fitted on 2015 to 2023 (1.511). It ran after the rulings and changed nothing.

## Verification

- **Full suite:** 416 passed (377 before T6, plus 39 new). The 145 warnings are the same count as
  before T6. ruff check and format are clean.
- **Independent fit check:** `test_fit_equals_statsmodels_poisson_glm_on_a_small_table`. The IPF fit
  equals statsmodels' Poisson GLM (identified design, offsets log days) to a relative 1e-6 on the
  weekend ratio and 1e-5 on fitted values. Its first version gave a rank-deficient design and
  disagreed in the fourth digit. Making the design identified (one reference slot per band) fixed
  the test, not the code.
- **Deviance check:** the per-cell deviance, built from non-zero entries only, equals a brute-force
  dense deviance over every cell-week-day, for the given-total, interpolated and constant models.
- **Stored surface read back:** `EffortSurface.read("data/t6/all").effort(...)` for cell 293_-826
  in 2022-W30 equals the product recomputed from the four CSVs (0.0026986556). The surface's 2022
  total over all frame cells is 113,160.998, against 113,161 observed outings in 2022.
- **Strict revert runner** (`2026-10-06-t6-fit/revert.py.txt`, results `revert_results.jsonl`):
  **17 of 17 bite.** Each run made one edit, checked that a fresh interpreter imported the edited
  source by sha256, refused on any error or exit other than 1, required the named test among the
  failures, restored from saved bytes, and confirmed `git diff` empty on all four files at the end.
  R2's first edit (`week.week - 1`) was refused for 6 errors: slot 52 was out of range in the
  fixtures, which is a build that did not run. It was replaced with `(week.week - 1) % N_SLOTS`, which
  fails `test_week_53_shares_week_52s_slot` with `0 == 51`. Every failure message names its own
  edit, for example R12 `[5, 6] == [1, 6]` (the 1,000 m record dropped) and R13 `[1] == [1, 6]` (the
  second observer dropped by the event key).
- **Memory:** count stage peak 1.19 GB in 3 min 13 s; fit stage peak 224 MB in 2 min 36 s for both
  tracks. The 5 GB watchdog never fired.

## Citations

Confirmed by search (bibliographic level, not read in full): Johnston et al. 2021, Diversity and
Distributions 27:1265–1277; Clayton and Kaldor 1987, Biometrics 43:671–681; Ver Hoef and Boveng
2007, Ecology 88:2766–2772; Courter et al. 2013, Int J Biometeorol; Warton, Renner and Ramp 2013,
PLoS ONE 8:e79168; Phillips et al. 2009, Ecol Appl 19:181–197.

Opened: Capinha et al. (bioRxiv 10.1101/2023.05.05.539567).

**Still marked from memory:** "chapter 3" of Bishop, Fienberg and Holland 1975. The book and its IPF
results are confirmed; the chapter number is not. The pull here is a fixed λ in the spirit of
Clayton and Kaldor's empirical Bayes, not their estimator.

## Not done or not verified

- The proposal's frame-size estimates used an unchecked land area (about 240,000 cells). The
  measured frame is 43,035 cells.
- What the lichen spring peak is (finding 4).
- Whether a pull above 10 would score better (finding 5); the grid was not widened.
- T7's held-constant level (D107 leaves it to T7).
- No review yet (D18). No merge (D40).
- No forbidden term (D58) and no "probability" or "chance" outside D12's term in the new files
  (checked by grep). Nothing touched the Forager app repository.
