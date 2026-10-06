# Review: D32 follow-up task (unify the filter pipelines), under the standing protocol (D18)

- **Reviewed:** branch `d32-followup-unify-filters` at `abac2b2` (base `origin/main` `1d5bd80`), seven commits
  `88b10ee`..`abac2b2`.
- **Protocol:** `docs/dispatch/2026-09-18-review-protocol.md` on `origin/main`, checks 1 to 10.
- **Dispatch:** `docs/dispatch/2026-10-06-d32-followup-unify-filters.md`. **Reports reviewed:**
  `2026-10-06-d32-followup-verify-report.md`, `2026-10-06-d32-followup-completion-report.md`.
  **Rulings read:** D63 to D67, D46, D51, D27, D42, D30, D41 in `docs/planning/DECISIONS.md`.
- **Reviewer:** a Claude session separate from the builder (D18), on the credentials machine, worktree
  `~/Zynergy/forager-forecast-d32-review`, branch `d32-followup-review` (sole writer, D38). Read the repo,
  not the builder's chat. An earlier reviewer session died before committing; nothing of its output
  (`/tmp/d32rev`) is cited or used here.
- **Base check:** `git fetch origin` on 2026-10-06 (UTC); `origin/d32-followup-unify-filters` = `abac2b2`,
  unmoved; `origin/main` = `1d5bd80`; `core.hooksPath` = `.githooks`.
- **Not done, as instructed:** no download, no weather pull, no model fit, no merge, no write to the builder's
  branch. No secret appears here (D36).
- **Conventions:** "read" means the file was opened in this session; "observed" means command output from
  this session; "inferred" is marked. Line cites are to `abac2b2`.

## Verdict

**Holds, with two small record gaps, one misreported headline count, and three items for the owner.** The
build matches D63 to D67 as written. Every real-data count the builder reports re-runs identically from a
clean checkout. Six revert checks of my own all bite. Nothing found contradicts a decision row. Nothing
found blocks a merge on technical grounds. Whether the three owner items (findings 3, 4 and 6) need a ruling
first is the owner's call.

## Findings

| # | Check | Result | Where | Proposed fix |
|---|---|---|---|---|
| 1 | 7, 9 | **Gap: headline test count wrong.** The branch has **117** test functions, not 109. Items are 213, as reported. | `2026-10-06-d32-followup-completion-report.md:87`; also `docs/planning/START_HERE.md:84` ("97 to 109") and `docs/audits/README.md:103` ("109 test functions") | Recorded here. Filed reports and rows are not edited (D41). A later row or the merge message can quote 117. |
| 2 | 5 | **Gap: two index rows have no File column.** The D63 row and the dispatch row have two cells where the table has three. | `docs/audits/README.md:99`, `:100` | **Closed in this review's commit** with one appended row naming both files. The two rows are not edited. |
| 3 | 2, 5 | **For the owner: `t1_record.py` was frozen with no decision row.** D67 names three files. `t1_record.py` joined the frozen set "on the Forager planner session's reading of D67", which the owner "can overrule". It is recorded in a header and a report, not in DECISIONS.md. Disclosed by the builder. | `src/forager_forecast/records/t1_record.py:5-7`; completion report "Frozen evidence" | The owner confirms or overrules. If confirmed, a decision row records it. |
| 4 | 2 | **For the owner: the frozen T1 evidence no longer reproduces its published figure.** `scripts/t1_count_table.py` over 0005709 now gives East **447,163**, not the published 447,164. The cause is that `t1_record.py` calls the shared `cells.cell_for`, which D63 changed. Disclosed by the builder in two headers. **I re-ran it: PNW 142,238, East 447,163.** D67 says the files "stay unchanged"; it does not say whether their output must still reproduce. | `t1_record.py:8-11`; `scripts/t1_count_table.py:5-6` | The owner rules whether a frozen record may drift through a shared dependency. Options: accept it as disclosed, or pin the pre-D63 cell rule inside the frozen path, which would edit frozen code. |
| 5 | 2, 4 | **Small, unreported change: the count table's year source.** `year_of` used to read GBIF's `year` column and now reads `event_date.year`. The completion report does not mention it. The verify report proposed a `year` field on the Record (§4), and the built Record has none. A test asserts the new behaviour (`tests/test_records_counts.py:60`). **Measured: 0 of 2,539,881 loadable rows of 0005714 differ,** so nothing changes on this data. | `src/forager_forecast/records/counts.py:73-75` | Accept, and note it in the merge message. No count is affected today. |
| 6 | 2 | **For the owner: two refusal reasons beyond D66's list.** D66 lists four reasons for a row that cannot be loaded (non-day date, range across days, missing or non-numeric coordinates, non-integer gbifID). The loader adds two more: `acceptedTaxonKey empty or not an integer`, and `coordinates out of range`. **Both fire 0 times on 0005714** (observed, `unloadable` in my run). D26's download could differ. Both are counted by reason, so nothing is dropped silently. | `src/forager_forecast/records/occurrence.py:172-173`, `:178-179` | The owner accepts them as part of D66's intent, or rules on them. |
| 7 | 7 | **Cannot tell: "tests first, seen failing".** The cell tests and the cell code land together in `5061338`, and the pipeline tests and code together in `39ba0cd`. Git shows no red commit, so the claim rests on the report alone. The revert checks (the builder's 12 and my 6) show the tests can fail. They do not show the order of writing. | commits `5061338`, `39ba0cd` | None needed for merge. Noted for the record. |
| 8 | (observation) | **Not drift, outside the dispatch: the antimeridian.** `cell_for(x, 180.0)` gives lon index 1800 and `cell_for(x, -180.0)` gives -1800. These are one physical meridian under two ids. `cell_for(x, 179.95)` goes to 1800. This behaviour is older than this branch. The delivered files in D51 covered only a small PNW box, so the grid's edge was never checked. It matters only if D26's continental pull includes records near ±180 (the Aleutians). | `src/forager_forecast/cells.py:68-96` | For D26's task to check, not this one. |

## The ten checks

1. **Terms: holds.** I searched every added line in `git diff 1d5bd80 abac2b2` for "fruiting probab",
   "probabilit", "calibrat", a percent beside "habitat", and "sighting chance". The one hit is the
   `cells.py:3` docstring, "The weather cell that defines sighting chance". It was carried over from the old
   docstring and uses the term as START_HERE.md's Fixed terms define it.
2. **Decisions: holds, apart from findings 3 to 6.** Read against each row:
   - **D63, D64:** read `cells.py:68-71`. Nearest index = floor(Decimal(repr(v))/step + 0.5), which sends an
     exact decimal tie toward +∞.
   - **0.25° mode:** `quarter_cell_for` at :90.
   - **D46:** `weather_cell` and the floor are gone (`git grep weather_cell` in src, scripts and tests is
     empty). Both keys call `cell_for` (`filters.py:95-110`).
   - **D27:** `taxon_key` is `acceptedTaxonKey` (`occurrence.py:171`).
   - **D65:** obscured step in both lists (`filters.py:148`, `:162`); T1's date rule (`:80-89`); lowest gbifID
     survives (`:230`).
   - **D66:** frozen-slots dataclass and counted loader (`occurrence.py:28-45`, `:202-220`). The parser body
     is identical to `t1_simple_csv.py`'s `_parse_instant` and `parse_event` (read side by side).
   - **D67:** `build_download_request` and `DOWNLOAD_FORMAT` are gone. `submit_download_request` sends
     `request_template` plus three personal fields (`gbif_download.py:115-136`). The three named files differ
     from `1d5bd80` by header comments only (`git diff`).
   - **D30:** `scripts/verify-open-meteo-historical-fields.sh` and `verify-inaturalist-access.sh` are not in
     the diff.
   - **D41:** both handoff diffs only add lines at the end (0 removed lines). DECISIONS.md diff: 5 rows added,
     0 removed.
3. **Fixed choices: holds.** Boxes, years 2015 to 2025, 1,000 m (T1) and 250 m (R6) are unchanged.
   `t1_design.py` is not in the diff. `R6_MAX_COORDINATE_UNCERTAINTY_M = 250.0` (`filters.py:41`) is the value
   T2's code used. No threshold moved after results were seen. The one expectation changed on purpose,
   (47.05, -123.05) to -123.0, follows D64, filed in `1924d0a` before the code in `5061338`.
4. **Scope: holds.** Every changed file is within items 1 to 6 or the record. Do-not-touch list:
   - No download or pull: the branch adds no network call path; `submit_download_request` only reshaped.
   - No secret: added lines scanned for credential names and e-mail addresses, none.
   - Frozen scripts unchanged.
   - No filed record edited.
   - Not merged: `origin/main` is still `1d5bd80`.
   - Nothing in the Forager repo.
   Finding 5 is a small unreported side change.
5. **Record: two gaps.** Findings 2 and 3. Both reports state their base commit. Decision rows are
   appended, not edited. The handoffs got dated corrections that say who appended them and how the facts
   were known.
6. **Data hygiene: holds.** `git ls-files` shows no zip, csv, nc or parquet. The largest added file is 240
   lines. The evidence JSONs carry counts, dates and column names, with no observer names or e-mail
   addresses (grep for `recordedBy` values and `@`). No new data layer is used.
7. **Claims carry evidence: mostly holds.** Finding 1 (wrong count) and finding 7 (order not evidenced).
   The builder marks R12's specificity as inferred, and that is fair. Every count I re-ran matched (check 9).
8. **Revert checks: holds. Six of my own, all bite.** The runner is my own script in my scratch directory.
   For each check it:
   - saves a byte copy of the file before editing, and restores from that copy, never from git;
   - deletes the previous JUnit XML before running;
   - refuses to cite a run with a non-0/1 exit or any XML error;
   - after restoring, confirms the sha256 matches the saved copy and the forward text is present.

   **Positive control (C0):** a syntax error in `filters.py`. Exit 2, "1 error during collection", refused as
   not citable. After all checks, `diff -r` of the revert tree against a fresh `git archive abac2b2` showed no
   difference.

   | # | One edit | Failed | Specific to that edit |
   |---|---|---|---|
   | V1 | obscured step removed from the **R6** list (the builder's R4 did T1's) | 7 of 70 | R6 name list, `...withheld...[r6]`, `...data_generalizations...[r6]`, the R6 count chains, the count table survivors `[1,3,4,5,6] != [1,3,4,5]` |
   | V2 | a date-only first of the month no longer default (`event_time is None or` removed) | 4 of 61 | `test_first_of_month_without_a_real_time_is_dropped[day0-None-True-t1]` and `[...-r6]`, plus two chain tests that carry such a record |
   | V3 | taxon removed from the observer key (D27/D44 fold) | 1 of 70 | `test_a_different_taxon_cell_or_day_is_kept[change0-r6]`: `1 == 2`. Only one case guards this. That is enough to bite, and it is thin. |
   | V4 | uncertainty limit made exclusive (`>` to `>=`) | 2 of 61 | `test_t1_uncertainty_limit_is_1000_m[1000.0-False]` and `test_r6_uncertainty_limit_is_250_m[250.0-False]` |
   | V5 | the range-across-days refusal disabled | 1 of 85 | `test_a_row_that_cannot_be_typed_is_refused_with_its_reason[...eventDate spans more than one day]`: DID NOT RAISE |

9. **Headline numbers re-run from a clean checkout: hold, except the test-function count (finding 1).**
   Clean checkout = `git archive abac2b2` into my scratch directory, `uv sync --frozen` offline.

   **Suite and lint:**
   - `pytest`: **213 passed**.
   - `^def test_` count: **117**. Collected test ids, unique per function: also 117. Base `1d5bd80`: 97,
     as the reports say.
   - `ruff check src tests scripts` and `ruff format --check src tests scripts`: clean.

   **Zips:** both sha256 match their stored `.sha256` files (0005709 `6468a431…`, 0005714 `d0e8e7cd…`).
   Read only.

   **T2 0005714, `scripts/t2_count_table.py`** (4 min 11 s, 749 MB peak). My `summary.json` equals the
   builder's `t2_unified_summary.json` on every key except the zip path:

   | Stage | Count |
   |---|---|
   | rows read | 2,549,508 |
   | unloadable: not a calendar day | 9,604 |
   | unloadable: range across days | 23 |
   | source | 2,539,881 |
   | user_obscured dropped | 156,543 |
   | coordinate_uncertainty dropped | 1,015,248 |
   | default_first_of_month_date dropped | 811 |
   | duplicate_taxon_observer_cell_day dropped | 94,081 |
   | survivors | 1,273,198 |

   The script's own tally shows all 9,604 non-day rows are year-only values.

   **Frozen T1 over 0005709, `scripts/t1_count_table.py`** (3 min 21 s), summed from its CSV:

   | Stage | PNW | East |
   |---|---|---|
   | inside a T1 box | 250,269 | 935,156 |
   | uncertainty ≤ 1,000 m | 162,122 | 490,909 |
   | not a default date | 161,958 | 490,506 |
   | one per taxon, cell and day | 142,238 | **447,163** |

   9,609 unloadable rows. The East total is the post-D63 figure (finding 4).

   **The unified T1 list over 0005714**, my own script, written independently of the builder's
   `t1_steps_over_dwca.py.txt` (3 min 15 s): every per-box figure equals the completion report's table.

   | Stage | PNW | East |
   |---|---|---|
   | inside a box | 250,165 | 935,018 |
   | not user-obscured | 233,471 | 883,150 |
   | uncertainty ≤ 1,000 m | 162,121 | 490,908 |
   | not a default date | 161,957 | 490,505 |
   | one per taxon, cell and day | 142,038 | 446,832 |

   1,354,698 rows were outside both boxes.

   **Year check** (same pass, finding 5): 0 loadable rows whose `year` column differs from
   `event_date.year`. This check is not empty by construction. A row whose `year` column was missing or
   unmatched would have been counted as "empty".
10. **Gaps against the dispatch:**
    - Item 1 to item 6 are all evidenced in the reports and the code.
    - The dispatch asked for "the full suite before and after, as test functions". "After" is misreported
      (finding 1).
    - The reports mark these as not verified, and they stay unverified here too:
      - the new DWCA body against real GBIF (forbidden here);
      - the unified T1 list on one download (needs D26's download);
      - the 1-per-box difference across downloads at the T1 uncertainty step;
      - the 9,604 coincidence;
      - how T1's 2026-09-19 request was invoked.
    - Functions with no production caller (`request_template`, `submit_download_request`,
      `credentials_from_env`, `read_occurrence_table`, `label_cell_weeks`) are reported, not unified, as the
      dispatch says.
    - Old T2 `summary.json` files can no longer be rendered by the updated `t2_render_tables.py`. The builder
      reports this, and I did not test it.

## What this review changed

- Appended one row to `docs/audits/README.md` naming the files for the two rows at `:99` and `:100`
  (finding 2), plus this review's own row. No other file is changed.

## What I did not check

- Real GBIF behaviour of the DWCA request body (no network allowed).
- The builder's 12 revert checks were not re-run one by one. I ran six of my own instead (check 8).
- `scripts/t2_render_tables.py` output, and rendering of old summary files.
- The 538,793 pre-D44 reproduction (`t2_oldkey_out.json`) was not re-run.
- Which record survives under the new rule against the old one (no count depends on it, D65).
- Behaviour near ±180 longitude on real data (finding 8).
- Whether the owner's answers in D64 to D67 match Forager RECORD -568 word for word. I did not open the
  Forager repository's record.

## Disclosure: an unintended network call by the reviewer

While checking that every script under `scripts/` still imports, I loaded each file as a module in my scratch
copy. `scripts/inat_taxon_ids.py` and `scripts/inat_counts.py` (planning-pack scripts, unchanged since
`2fcb3c0`) run their work at module level, with no `if __name__ == "__main__"` guard. So loading them made
unauthenticated read-only requests to `api.inaturalist.org`, and they wrote `ids.json` and `counts.json` into
my scratch copy only. There was no GBIF, Climate Data Store or Open-Meteo request, no credential was used, and
no repository file was written. The import check's result for those two scripts is therefore not meaningful.
The five `t1_*` and `t2_*` scripts imported cleanly.
