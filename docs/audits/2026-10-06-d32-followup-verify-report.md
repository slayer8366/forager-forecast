# D32 follow-up task: verify-first report

Answers the "Verify first" section of `docs/dispatch/2026-10-06-d32-followup-unify-filters.md`.
Written 2026-10-06 (UTC) by the coder session on the credentials machine (D38), on branch
`d32-followup-unify-filters` at `88b10ee`, worktree `~/Zynergy/forager-forecast-d32-followup`.
**Nothing is built.** Four of the dispatch's stops are met (section 7), so this report goes to the
planner before any code changes. No download, no Open-Meteo or Climate Data Store pull, no model fit,
no merge. No secret appears here.

Line cites are to `88b10ee`. Where this report says "read", the file was opened in this session.
Where it says "measured", the count comes from the scripts in
`docs/audits/2026-10-06-d32-followup-verify/` (saved as `.py.txt`, byte-identical to what ran from
`/tmp/d32m/`, kept out of lint so the copy stays the code that ran; outputs `t1_out.json`,
`t2_out.json`), run read-only over the two downloads on this machine.

## 1. Base

- `git fetch`, then `origin/main` = `1d5bd805`. Unmoved.
- `origin/d32-followup-unify-filters` = `HEAD` = `88b10ee`, and `git log origin/main..HEAD` is that one
  commit.
- `git log 47204f7..1d5bd80 -- src tests scripts` is empty, so the stage 2b report's code cites still
  apply.
- Suite before any change: 147 collected items from 97 test functions (`git grep -c '^def test_'`),
  all passing. `ruff check` and `ruff format --check` are clean.

## 2. Cites

| Dispatch cite | Status |
|---|---|
| `records/t1_record.py:21-22` T1 `Record` | Confirmed: `@dataclass(frozen=True)` at 21, `class Record` at 22 |
| `records/filters.py:32` T2 `Record` | Confirmed: `Record = Mapping[str, str]` |
| `cells.py:39` ROUND_HALF_UP, `cell_for` at :44 | Confirmed: `_tenths` at 39, ROUND_HALF_UP at 41, `cell_for` at 44 |
| `cells.py` has no 0.25° mode | Confirmed: `GRID_STEP_DEGREES = Decimal("0.1")` at 16 is the only step |
| `filters.py:102` `weather_cell`, `:116` `duplicate_key` | Confirmed |
| `gbif_download.py:27` SIMPLE_CSV, `:96` `build_download_request`, `:107` `request_template` (DWCA) | Confirmed |
| `gbif_download.py:52` `credentials_from_env` | Confirmed. `tests/test_records_gbif_download.py:32-39` covers all three missing, and email blank. It does not cover two of three missing. |
| Docstrings `records/__init__.py:1-13`, `t1_record.py:4-5`, `gbif_download.py:1` | Confirmed stale as the stage 2b report says. `__init__.py` is lines 1-12, the docstring is 1-11 |
| Stale under D44: the key's docstring | Confirmed: `filters.py:117` says "Observer, 0.1 degree cell and day". The key at :124 leads with `acceptedTaxonKey` |
| Stale under D44: step name `duplicate_observer_cell_day` | Confirmed: `filters.py:158`, also the module docstring at :15 and the class name at :127 |
| Stale under D44: `COLUMNS_READ` in `scripts/t2_count_table.py` | Confirmed: lines 29-42 do not list `acceptedTaxonKey`, which `duplicate_key` reads. A file without it would key every record on an empty taxon, which is the silent failure the header check at :71-73 exists to stop. |
| Handoff `2026-09-20-coder-handoff.md:84-96` | Confirmed: names `records.py`, `simple_csv.py`, `test_records.py` and other pre-move paths |
| Handoff `2026-09-19-planner-handoff.md:111` | Confirmed: "records.py is shadowed ... gbif_download.py exists twice" |
| ERA5 longitudes −180 to 180 | Confirmed from `2026-09-22-grid-positions-d51-report.md:13` and :105 (both delivered files, `degrees_east`, negative). **I rely on the delivered files, not the research note's 0 to 360.** |
| D63 tie rule "toward +∞" | Row read. **See stop A.** |

## 3. Every filter step, both pipelines today

T1: `t1_record.py`, `T1_FILTER_STEPS` at :107-113, applied to rows that `t1_simple_csv.record_from_row`
could load. T2: `filters.py`, `default_steps()` at :152-159, applied to every row.

| Step | T1 | T2 | Agree? | Proposed for the unified pipeline |
|---|---|---|---|---|
| Rows that cannot be typed | Loader raises `UnloadableRow` for a non-day date, a range across days, missing coordinates or a bad ID, and the script counts it by reason (`t1_simple_csv.py:89-155`) | No such stage. Every row flows on. A row with no coordinates gets the key `no-cell` (`filters.py:122-123`), so all of one observer's coordinate-less records on a day collapse into one, silently | **No** | Depends on the Record type (stop C) |
| Inside a T1 box | `keep_inside_boxes` :55 | none (continental audit) | Different purpose | Keep, T1 step list only |
| Year 2015 to 2025 | `keep_years` :61 | none (the predicate selects years) | Different purpose | Keep, T1 step list only |
| User-obscured | none. SIMPLE_CSV has no `informationWithheld` or `dataGeneralizations` | `is_user_obscured` :43 | **No** | **Stop B1** |
| Coordinate uncertainty | present and ≤ 1,000 m (`MAX_COORDINATE_UNCERTAINTY_M`, T1 dispatch, D33 headline) | present and ≤ 250 m (SPEC R6) | Different limits, each set by its own document | One implementation, limit passed in: 1,000 m for T1, 250 m for R6 |
| Default first-of-month date | `is_default_date` :76 on the parsed date. Reads `T00:00` without seconds, offsets and same-day ranges | `is_default_first_of_month_date` :80 on the text. Range is never default; time must start `00:00:00` | **No**, at the edges | **Stop B2** |
| Duplicates | event key (taxon, cell, day), D27. Uses `taxonKey`. Cell from `cell_for`. Keeps the lowest `gbif_id` | observer key (taxon, observer, cell, day), D27. Uses `acceptedTaxonKey`. Cell from the floor (retired by D46). Keeps the first seen | Two keys, by D27. Three sub-differences | Both keys kept (D27). Cell: the D46/D63 cell for both. Taxon: `acceptedTaxonKey` for both (D27 says "accepted GBIF taxon key"). **Survivor: stop B3** |

D27 decides the two keys and which taxon field. It decides nothing about the survivor or the date
parser. T1's use of `taxonKey` departs from D27's "accepted" wording. SIMPLE_CSV has no
`acceptedTaxonKey` column (header read), so T1's first download cannot meet D27.

## 4. Proposals

**Record type (item 1).** Proposed: T1's frozen dataclass, extended with the fields the T2 steps and
tables read (`accepted_taxon_key`, `recorded_by`, `information_withheld`, `data_generalizations`,
`dataset_key`, `publisher`, `genus_key`, `license`, `year`), built by one DWCA row loader. Reasons:

- Each field is parsed once, at one place, with a counted reason when it cannot be parsed. Today T2
  re-parses `eventDate` and coordinates as text in several steps.
- T2's `no-cell` key merges records with no coordinates without a count, a fallback that nothing
  reports when it fires.
- Typed fields make the cell rule and the date rule one implementation each.

**Why this is a trade-off for the owner (stop C).** A typed Record changes what T2's audit counts.
Rows T2 passes through today would become a counted "cannot be loaded" stage before the first filter.
Measured on T2's download: **9,627 of 2,549,508** rows (9,604 non-day dates, 23 ranges across days).
The other option is a dataclass whose date can be "not a day". That keeps T2's source counts, but every
date step then has to handle that case. Keeping `Mapping[str, str]` is the third option. It keeps
T2's code and makes T1's typed steps re-parse text. I recommend the first option. The 9,627 rows are
also the rows nothing downstream can place in a week.

**Request builder (item 4).** Proposed: retire `build_download_request` and `DOWNLOAD_FORMAT =
"SIMPLE_CSV"`. `submit_download_request` builds its body as `request_template(predicate)` plus the
three personal fields (`creator`, `notificationAddresses`, `sendNotification`). Reasons:

- D45 carries DWCA.
- D26's download is DWCA.
- SIMPLE_CSV lacks `informationWithheld` (cited at `gbif_download.py:112-115`) and `acceptedTaxonKey`
  (header read).

**How T1's SIMPLE_CSV data is read afterwards.** Proposed: the unified pipeline no longer reads it.

- D26 makes that download provisional and superseded.
- It cannot satisfy D27's accepted-taxon key or the obscured step.
- D26's acceptance check needs only its `gbifID` column, which is a plain column read.

Proposed treatment: `t1_simple_csv.py`, `scripts/t1_count_table.py` and `scripts/t1_render_tables.py`
are retired from the package, and the D26 acceptance check reads `gbifID` directly. **This is a
proposal, not decided.** Keeping them frozen as the record of T1's provisional counts is the
alternative. Git history keeps them either way.

## 5. Who calls what

Searched with `git grep` over `src`, `scripts` and `tests`.

| Function | Production callers (`src`, `scripts`) | Tests |
|---|---|---|
| `apply_t1_filters_observed` | `scripts/t1_count_table.py:116` | yes |
| `apply_t1_filters` | **none** | `test_records_t1_record.py`, `test_records_t1_observed.py` |
| `T1_FILTER_STEPS` | `t1_count_table.py:42`, `t1_render_tables.py:22` | yes |
| `Pipeline` | `scripts/t2_count_table.py:92` | yes |
| `default_steps` | `Pipeline` default, `scripts/t2_render_tables.py:22` | yes |
| `cell_for` | `t1_record.py:95` (event key), `cell_weeks.py:38` (`cell_week_of`) | yes |
| `cell_week_of`, `label_cell_weeks` | `label_cell_weeks` has **no production caller**. `cell_weeks.CellWeek` is imported by `weather_windows.py:18` | yes |
| `weather_cell` | `filters.py:120` only (`duplicate_key`) | yes |
| `build_download_request` | `submit_download_request` only | yes |
| `submit_download_request` | **none** in `src` or `scripts`. T1's real request was made on 2026-09-19 (its record is `t1_request_submitted.json`, outside git); how it was invoked is not in the repo | yes |
| `request_template` | **none** | yes |
| `read_occurrence_table` | **none** (`read_occurrence_rows` is used by `t2_count_table.py:96`) | yes |
| `credentials_from_env` | **none** | yes |

The functions with no production caller are reported here and not unified. The one case that matters
is `request_template`. It is the builder D26's download will use, so its first caller is D26's task.
I propose keeping it, since the dispatch's item 4 keeps one builder.

## 6. What changes for real data (measured)

Both zips' sha256 match the `.zip.sha256` files stored beside them:

- `0005709-...` (T1, SIMPLE_CSV): `6468a431...`
- `0005714-...` (T2, DWCA): `d0e8e7cd...`

The unified pipeline does not exist yet, so this section has the old pipelines plus the cell change
alone. The unified pipeline's counts come after building.

### T1, download 0005709 (1,195,034 rows; 50 s, 557 MB peak)

| Stage | PNW | East |
|---|---|---|
| source (loadable, in a box) | 250,269 | 935,156 |
| inside a T1 box | 250,269 | 935,156 |
| year 2015 to 2025 | 250,269 | 935,156 |
| uncertainty ≤ 1,000 m | 162,122 | 490,909 |
| not a default date | 161,958 | 490,506 |
| one per taxon, cell, day (`cell_for`) | **142,238** | **447,164** |
| same, D46/D63 cell | 142,238 | 447,163 |

Unloadable: 9,604 non-day dates and 5 ranges across days. 0 rows were outside both boxes.

Every count equals the T1 credentialed run report (`2026-09-18-t1-credentialed-run-report.md:269-296`).
So the old pipeline reproduces, and the input is the one that report used.

Cell change under D46 and D63 (0.1°), for the records entering the duplicate step:

- PNW: 10 of 161,958 change.
- East: 17 of 490,506 change.

All 27 are decimal longitude ties going one step east. The latitude ties (4 and 13) do not change,
because `cell_for` already sent them north. The duplicate step keeps one record fewer, in the East box.
At 0.25° there are 3+2 and 4+4 decimal ties (latitude+longitude), and that grid has no old rule.

### T2, download 0005714 (2,549,508 rows; 4 min 37 s, 344 MB peak)

| Step | Dropped (today's code) | Published (`t2-credentialed-run-report.md:193-196`) |
|---|---|---|
| user_obscured | 156,543 | 156,543 |
| coordinate_uncertainty | 1,024,875 | 1,024,875 |
| default_first_of_month_date | 799 | 799 |
| duplicate, floor cell | **94,247** | 538,793 |
| duplicate, D46/D63 cell | 94,082 | n/a |

The duplicate count differs from the published one. That is explained: the published run used the
taxon-less key, and D44 folded taxon in afterwards (`2026-09-20-d32-stage-1-part-d-report.md:114`).
I have not re-derived the 538,793 under the old key. I infer the explanation, and the other three
steps match exactly.

Records entering the duplicate step: 1,367,291.

- Cell change, floor to nearest: 1,015,747 (74%). That is expected. The floor and the nearest cell
  differ whenever a point is in the upper half of its cell on either axis, which happens about 3 times
  in 4.
- Duplicates dropped: 165 fewer under the nearest cell.
- Decimal ties at 0.1°: 124 latitude and 46 longitude.
- Decimal ties at 0.25°: 22 latitude and 21 longitude.

Diagnostics on T2's rows, for the open questions:

- `taxonKey` ≠ `acceptedTaxonKey`: **246,510** at source. These are the records whose T1 event key
  would change if T1 moves to D27's accepted key.
- User-obscured with uncertainty ≤ 1,000 m: **23**. With ≤ 250 m: 22. That is the most adding the
  obscured step to T1 could remove, continent-wide.
- At the date step, T1's rule says default and T2's says not: **12** records. Zero the other way.
- T1's loader would reject 9,627 rows (9,604 non-day dates and 23 ranges).

**Unexplained, flagged:** the 9,604 non-day dates equal T1's own count exactly, on a different download
(two boxes against the continent). It could mean every month-only record in the continent pull lies in
the two boxes, or it could be coincidence. Not checked.

No count difference is unexplained apart from that flag, and that flag is about the old data, not the
unified pipeline.

## 7. Stops met

- **A. D63's tie rule against the source's observed behaviour.** D63's text says toward +∞, and its
  reason says "do what the weather source does". The one probed half point that is not an exact
  binary number is (47.05, −123.05) (`grid-positions-d51-report.md:130`). There Open-Meteo `era5_land`
  returned −123.1, which is west, toward −∞. D63 read on the decimal text gives −123.0. Nearest-on-binary
  gives −123.0 too, because the double is −123.04999…. Float32 does not explain the latitude result
  either. Open-Meteo's mechanism is unknown, and the part 2 report says the same (:165). So "exactly
  halfway" needs one ruling: on the decimal value GBIF reports, or on something else.
  - On real data this decides 27 T1 records and 46 T2 longitude ties at 0.1°.
  - D63 read on the decimal text is my recommendation. It is D63's literal wording, and `cell_for`
    already treats coordinates as decimal.
  - Telling the readings apart further would need an Open-Meteo probe, which this dispatch forbids.
- **B. Filter steps the two pipelines do differently, with no row deciding.**
  1. **The user-obscured step for T1's list.** R6 governs habitat training, not T1's calendar model.
     It affects at most 23 records. I propose adding it to both lists, because a withheld coordinate
     is not a location.
  2. **The default-date parser.** D28 states the rule but not the parsing. 12 records differ. I
     propose T1's parsed rule for both, since it reads more date shapes.
  3. **The duplicate survivor: lowest `gbifID` or first seen.** Counts are identical either way. It
     changes which record's licence and dataset the tables count. I propose lowest `gbifID`, because
     then the result does not depend on input order.
- **C. The Record type is a trade-off**: 9,627 rows of T2's audit change stage (section 4).
- **D. T1's taxon field.** D27 decides "accepted", and T1 uses `taxonKey`. This is decided, not open,
  but on T2's data 246,510 records carry a `taxonKey` different from their `acceptedTaxonKey`, so T1's
  event key moves for records like those. I flag it so the move is
  expected, not discovered.

## 8. Not verified

- Which T2 records the 538,793 → 94,247 change consists of (inferred from D44, not re-run under the old
  key).
- The 9,604 coincidence above.
- Which record survives under "first seen" against "lowest `gbifID`" in T2's data. Not measured.
- Open-Meteo's behaviour at any further half point. A probe is forbidden here.
- How T1's 2026-09-19 request was invoked.
