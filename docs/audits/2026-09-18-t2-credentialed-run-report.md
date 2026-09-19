# T2 credentialed run: download requested, count tables produced, hand-check sample still blocked

**Date:** 2026-09-18 (machine local time, UTC-7). GBIF's own timestamps below are UTC and fall on
2026-09-19.
**Type:** run report for docs/dispatch/2026-09-18-t1-t2-credentialed-run.md, the T2 half. The T1
half, including the credential checks and the reading of Cowork's report, is on branch
t1-calendar-smoke-test in docs/audits/2026-09-18-t1-credentialed-run-report.md; those checks are
not repeated here, only cited.
**Base:** branch t2-record-audit at 02af2c0 (the T2 review) over main f96d557, which was still
origin/main when this was written. Code commits b8bbfa2, 66c96d7, 2548adc, c29af4a; this report is
the next commit; the index row, session log row and TASKS.md cell follow in one more.
**Supersedes:** nothing. It runs the pipeline the T2 completion report (0587c39) prepared and
answers its "count tables" gap. One figure in that report is corrected below ("A correction to
the record").

Every claim below names a file and line, a commit, a URL opened today, or a command whose output
is quoted, or is marked inferred.

---

## The short version

- **T1's download cannot serve T2**, so T2 has its own: SIMPLE_CSV carries neither
  informationWithheld nor genusKey (T2 completion report, verify-first item 1), and T2's regions
  include the rest of North America, which T1's two-box predicate does not. Requested with the
  committed template unchanged, after the T1 download had succeeded. DOI **10.15468/dl.k3mwnn**,
  key 0005714-260916113435855, 2,549,508 records, DWCA, provisional (test account); the request
  GBIF stored equals the committed template in format, checklistKey and predicate.
- **The count tables are below**, by group, region, year and filter step, and by license and
  publisher. Source rows equal the download's totalRecords. Every DWCA column the pipeline reads
  is present under the name the code uses (12 of 12).
- **The duplicate step's taxon-less key, which the T2 review raised as its first item, is the
  largest single loss of chanterelle records after the uncertainty filter.** It drops 42 percent
  of the Cantharellus records reaching it (7,960 to 4,589) where T1's per-taxon key drops 14
  percent of a comparable set. The owner's ruling on that key changes the final row of every
  table below.
- **The 200-record hand-check CSV was not produced.** Its population is not in this or any GBIF
  download (T2 completion report, finding 1, confirmed by the T2 review), the iNaturalist pull that
  carries it is a proposed decision row awaiting the owner, and this dispatch forbids the
  iNaturalist API as a substitute. The seed for that draw is fixed here, before any candidate is
  seen: **20260918**.
- Second wording found for withheld coordinates: "Coordinates obscured by observer" on 3,775
  records (Mushroom Observer, inferred from the publisher tally below). The pipeline's
  any-non-empty-text rule caught it; a rule matching iNaturalist's wording would not have.
- Stopped here. Nothing was modelled, sampled or pulled beyond the one download.

## Verify first, as answered

### Credentials, and the reuse question

The credential checks (file mode and location, login 200, negative control 401, Cowork's report
and its four differences, the test-account rules) are in the T1 run report, "Verify first" items
1 to 4, and were done once for both tasks in the same session. Applied here: the DOI is marked
provisional with its query beside it (docs/pulls/gbif-fungi-north-america-2015-2025.doi.json,
c29af4a), and no test pins a record count (`grep -rn -E "2549508|2,549,508" tests` is empty).

Reuse of T1's download, as the dispatch asks to consider first:

| T2 needs | In T1's SIMPLE_CSV? | Source |
|---|---|---|
| informationWithheld (step 1) | no | download-formats page, T2 completion report; the T1 file's 50-column header, listed in the T1 run report, confirms it |
| dataGeneralizations (step 1) | no | same |
| genusKey (group_of, counts.py:70-72) | no | same |
| records outside the two boxes ("rest of North America") | no, the predicate is the two boxes | src/forager_forecast/gbif/t1_fungi_two_boxes_2015_2025.json on the T1 branch |

So T2 requested its own download. The two are not nested either way: T2's CONTINENT predicate
returns 104 fewer PNW-box records and 138 fewer East-box records than T1's polygon predicate
(comparison below), so neither download is a subset of the other.

### GBIF's concurrent-download limit

Not confirmed from GBIF's documentation (T1 run report, item 5). The T2 request was submitted at
04:11:37Z, after the T1 download reported SUCCEEDED at 04:10:34Z.

## The download

| Field | Value | Source |
|---|---|---|
| Key | 0005714-260916113435855 | POST response, HTTP 201, observed |
| DOI | 10.15468/dl.k3mwnn | GET /occurrence/download/0005714-260916113435855, saved as data/t2/downloads/0005714-260916113435855.metadata.json |
| Created | 2026-09-19T04:11:37Z | same |
| Succeeded | 2026-09-19T04:40:18Z (29 minutes) | same |
| totalRecords | 2,549,508 | same; equals the search-API count in the T2 completion report and the T2 review |
| Format, checklist | DWCA, d7dddbf4-2cf0-4f39-9b2a-bb099caae36c (GBIF Backbone) | same |
| Datasets | 41 | same, `numberDatasets`; the T2 review counted "twelve or more" from a facet, which lists the largest only |
| Download licence | CC BY-NC 4.0 (GBIF's licence for the whole download; the per-record split is in the license table) | same |
| Zip | 1,475,785,280 bytes, sha256 d0e8e7cd...0ecaaf (full hash in the DOI record) | `ls -l`, `sha256sum`, observed |
| Members | occurrence.txt 3,561,013,686 bytes, verbatim.txt 2,077,868,784, multimedia.txt 1,395,088,270, meta.xml, metadata.xml, 41 dataset EML files | `unzip -l`, observed |
| Request equals the committed template | predicate True, format True, checklistKey True | compared in Python against docs/pulls/gbif-fungi-north-america-2015-2025.json, observed |
| Local copy | data/t2/downloads/, gitignored (`git check-ignore -v` names .gitignore:6) | observed |

The request was `request_body(credentials_from_env(os.environ))` from
src/forager_forecast/records/gbif_download.py, POSTed with HTTP basic auth from Python's urllib.
`curl_argv()` was not used because it places the password in a process argument list, which the
dispatch's "the password must not appear in the command" rules out; the docstring of `curl_argv`
says as much. The two names the T2 completion report could not validate without submitting,
`checklistKey` in the body and `CONTINENT` as a predicate key, were accepted: GBIF echoes both
back in the stored request.

## What landed

| Commit | Change |
|---|---|
| b8bbfa2 | filters.py: `read_occurrence_rows` over an open handle (filters.py:209-219), `read_occurrence_table` delegates to it (:222-225). records/licenses.py: `LicenseTable` (:32-59) keyed by stage, group, license, datasetKey; `fan_out` (:62-69). tests/test_records_licenses.py (4 tests). scripts/t2_count_table.py |
| 66c96d7 | scripts/t2_render_tables.py |
| 2548adc | docs/dispatch/2026-09-18-t1-t2-credentialed-run.md, byte-identical to the owner's upload and to the T1 branch's copy |
| c29af4a | docs/pulls/gbif-fungi-north-america-2015-2025.doi.json |
| next | this report |
| last | index row, session log row, TASKS.md T2 cell |

Nothing in the pipeline, the count table, the sampler or the predicate was changed. The script
streams occurrence.txt out of the zip (no extraction; the table is 3.6 GB), checks the header
for the twelve columns it reads before counting anything (scripts/t2_count_table.py:29-42 and
:68-73), and tallies eventDate shapes and the withheld texts at the source stage only.

## Evidence

### Lint, tests, guard

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 41 files already formatted
uv run pytest -q               -> 75 passed in 0.69s     (71 before this run, 4 new)
./scripts/check-large-files.sh --all -> 56 file(s) checked, none over 1048576 bytes
git ls-files data | wc -l      -> 0
```

### Revert check, restored from a saved copy

licenses.py, the group tally disabled (`if group is not None:` to `if False:`); a copy saved to
/tmp with its sha256 first. `uv run pytest -q tests/test_records_licenses.py`: the named test
failed with `AssertionError: assert 0 == 3` at
`count('source', 'cantharellus', 'CC_BY_NC_4_0', '50c9509d-...')`, and the CSV test failed on the
missing group rows. No import or collection error. Restored with `cp` from /tmp, `sha256sum -c`
OK, `grep -c REVERT-MARK` 0, full suite 75 passed.

One thing the fixture taught: the first draft of the test gave three rows the same observer,
cell and day and expected all three to survive; the duplicate step dropped two of them, which is
the taxon-less key doing exactly what the T2 review's check 3 describes. The fixture now names a
distinct observer per row and says why (tests/test_records_licenses.py:34-47).

### Positive control for the run script

On a seven-row synthetic DWCA zip (one row per: kept, obscured, over 250 m, first-of-month date
only, duplicate observer-cell-day, Laetiporus in the rest of North America under CC BY, an
ungrouped record in the East with a month-long range), the script printed the step counts
7 > 6 > 5 > 4 > 3 with each drop the row built to cause it, the region and license rows expected,
and `event_date_shapes` of 5 day-with-time, 1 day-only, 1 range.

### The real run

```
uv run python scripts/t2_count_table.py data/t2/downloads/0005714-260916113435855.zip data/t2/counts
Elapsed (wall clock): 7:48.55    Maximum resident set size: 110,172 kB    exit 0
```

Header: 230 columns; the twelve the pipeline reads are present under the names the code uses
(gbifID 1, license 5, informationWithheld 19, dataGeneralizations 20, recordedBy 25, eventDate 63,
year 67, decimalLatitude 98, decimalLongitude 99, coordinateUncertaintyInMeters 100, datasetKey
180, genusKey 205; observed with `unzip -p ... | head -1`). That closes the T2 completion
report's first "not checked" item.

| Source rows | Download totalRecords | Survivors of all four steps | Last step's `after` |
|---|---|---|---|
| 2,549,508 | 2,549,508 | 828,498 | 828,498 |

Against the T1 run report's source counts inside the two boxes (T1 loadable rows plus the rows
its loader could not read, which is every row of T1's file in that box):

| Box, group | T1 file (all rows) | T2 source, region = that box | Difference |
|---|---|---|---|
| PNW, Cantharellus | 3,425 | 3,421 | 4 fewer in T2 |
| PNW, all fungi | 250,273 | 250,169 | 104 fewer in T2 |
| East, Cantharellus | 5,545 | 5,545 | 0 |
| East, all fungi | 944,761 | 944,623 | 138 fewer in T2 |

T1 counts Cantharellus by genus name, T2 by genusKey 9623860; in the East they agree to the
record. The 242 in-box records T2 lacks are records the polygon predicate selects and the
CONTINENT=NORTH_AMERICA predicate does not; inferred to be records whose interpreted continent is
empty or other, not checked against the records themselves. Neither download is a subset of the
other.

## The count tables

Rendered by `uv run python scripts/t2_render_tables.py data/t2/counts` from
data/t2/counts/counts_by_stage_group_region_year.csv, which holds every group, region, year and
stage; the year-by-region tables here show the source stage and the last stage only.

### The four steps over the whole pull

| Step | Before | Dropped | After |
|---|---|---|---|
| user_obscured | 2,549,508 | 156,543 | 2,392,965 |
| coordinate_uncertainty | 2,392,965 | 1,024,875 | 1,368,090 |
| default_first_of_month_date | 1,368,090 | 799 | 1,367,291 |
| duplicate_observer_cell_day | 1,367,291 | 538,793 | 828,498 |

### cantharellus: stage by region, all years

| Stage | pnw | east | rest_of_north_america | Total |
|---|---|---|---|---|
| source | 3,421 | 5,545 | 9,161 | 18,127 |
| user_obscured | 2,424 | 5,078 | 7,598 | 15,100 |
| coordinate_uncertainty | 1,193 | 2,560 | 4,211 | 7,964 |
| default_first_of_month_date | 1,193 | 2,559 | 4,208 | 7,960 |
| duplicate_observer_cell_day | 600 | 1,481 | 2,508 | 4,589 |

### cantharellus: year by region, at the source stage and after the last step

| Year | pnw source | pnw final | east source | east final | rest_of_north_america source | rest_of_north_america final |
|---|---|---|---|---|---|---|
| 2015 | 26 | 2 | 187 | 6 | 119 | 15 |
| 2016 | 31 | 3 | 188 | 11 | 219 | 38 |
| 2017 | 53 | 5 | 284 | 36 | 270 | 37 |
| 2018 | 71 | 14 | 502 | 97 | 418 | 91 |
| 2019 | 222 | 31 | 479 | 112 | 499 | 153 |
| 2020 | 328 | 52 | 566 | 184 | 1,025 | 334 |
| 2021 | 369 | 63 | 817 | 278 | 1,102 | 335 |
| 2022 | 278 | 39 | 391 | 118 | 1,126 | 279 |
| 2023 | 321 | 45 | 1,009 | 299 | 1,481 | 396 |
| 2024 | 940 | 177 | 574 | 175 | 1,278 | 345 |
| 2025 | 782 | 169 | 548 | 165 | 1,624 | 485 |

### laetiporus: stage by region, all years

| Stage | pnw | east | rest_of_north_america | Total |
|---|---|---|---|---|
| source | 1,717 | 17,823 | 19,527 | 39,067 |
| user_obscured | 1,515 | 16,422 | 18,037 | 35,974 |
| coordinate_uncertainty | 897 | 10,598 | 12,238 | 23,733 |
| default_first_of_month_date | 897 | 10,595 | 12,234 | 23,726 |
| duplicate_observer_cell_day | 715 | 8,687 | 10,384 | 19,786 |

### laetiporus: year by region, at the source stage and after the last step

| Year | pnw source | pnw final | east source | east final | rest_of_north_america source | rest_of_north_america final |
|---|---|---|---|---|---|---|
| 2015 | 24 | 3 | 193 | 49 | 181 | 50 |
| 2016 | 15 | 3 | 322 | 80 | 303 | 88 |
| 2017 | 30 | 9 | 371 | 90 | 472 | 147 |
| 2018 | 60 | 20 | 728 | 254 | 708 | 345 |
| 2019 | 85 | 34 | 931 | 408 | 1,056 | 529 |
| 2020 | 173 | 71 | 2,210 | 1,017 | 2,212 | 1,164 |
| 2021 | 235 | 88 | 2,455 | 1,235 | 2,432 | 1,325 |
| 2022 | 214 | 96 | 2,033 | 1,042 | 2,738 | 1,526 |
| 2023 | 151 | 73 | 2,567 | 1,357 | 2,856 | 1,533 |
| 2024 | 267 | 116 | 2,871 | 1,461 | 2,935 | 1,625 |
| 2025 | 463 | 202 | 3,142 | 1,694 | 3,634 | 2,052 |

### all_fungi: stage by region, all years

| Stage | pnw | east | rest_of_north_america | Total |
|---|---|---|---|---|
| source | 250,169 | 944,623 | 1,354,716 | 2,549,508 |
| user_obscured | 233,475 | 892,755 | 1,266,735 | 2,392,965 |
| coordinate_uncertainty | 144,313 | 439,017 | 784,760 | 1,368,090 |
| default_first_of_month_date | 144,254 | 438,800 | 784,237 | 1,367,291 |
| duplicate_observer_cell_day | 81,566 | 262,687 | 484,245 | 828,498 |

### all_fungi: year by region, at the source stage and after the last step

| Year | pnw source | pnw final | east source | east final | rest_of_north_america source | rest_of_north_america final |
|---|---|---|---|---|---|---|
| 2015 | 2,492 | 325 | 39,677 | 1,201 | 15,149 | 2,275 |
| 2016 | 3,072 | 518 | 42,926 | 2,068 | 25,743 | 4,616 |
| 2017 | 4,087 | 958 | 49,231 | 3,718 | 37,788 | 7,215 |
| 2018 | 7,632 | 1,861 | 71,463 | 9,184 | 58,740 | 16,586 |
| 2019 | 13,497 | 3,692 | 74,364 | 14,085 | 82,763 | 28,031 |
| 2020 | 23,460 | 7,063 | 87,401 | 29,727 | 121,678 | 44,581 |
| 2021 | 27,971 | 9,316 | 109,812 | 39,234 | 163,637 | 60,885 |
| 2022 | 25,317 | 9,078 | 91,608 | 33,130 | 176,611 | 64,503 |
| 2023 | 40,734 | 13,669 | 126,870 | 42,594 | 208,335 | 77,814 |
| 2024 | 47,056 | 15,505 | 118,611 | 40,740 | 218,194 | 81,810 |
| 2025 | 54,851 | 19,581 | 132,660 | 47,006 | 246,078 | 95,929 |

### By license and publisher

From data/t2/counts/counts_by_license.csv, which holds every stage and all 41 publishers. Shown:
the two target groups at the source stage and after the last step, and the publishers above
1,000 records for all fungi. Publisher names are from the T2 completion report and review
(iNaturalist 50c9509d, Mushroom Observer d714382d, New Jersey fungi fca5e616); the others are
keys only, not resolved here.

| Group | Stage | License | Publisher | Records |
|---|---|---|---|---|
| cantharellus | source | CC_BY_NC_4_0 | 50c9509d iNaturalist | 14,168 |
| cantharellus | source | CC_BY_4_0 | 50c9509d iNaturalist | 1,507 |
| cantharellus | source | CC_BY_NC_4_0 | d714382d Mushroom Observer | 1,170 |
| cantharellus | source | CC_BY_4_0 | fca5e616 New Jersey fungi | 672 |
| cantharellus | source | CC0_1_0 | 50c9509d iNaturalist | 556 |
| cantharellus | source | CC_BY_4_0 | 2b169d34 | 27 |
| cantharellus | source | CC_BY_4_0 | 9ec7b624 | 24 |
| cantharellus | source | CC_BY_4_0 | 1ba64366 | 2 |
| cantharellus | source | CC0_1_0 | 39bd4817 | 1 |
| cantharellus | last step | CC_BY_NC_4_0 | 50c9509d iNaturalist | 4,084 |
| cantharellus | last step | CC_BY_4_0 | 50c9509d iNaturalist | 331 |
| cantharellus | last step | CC0_1_0 | 50c9509d iNaturalist | 147 |
| cantharellus | last step | CC_BY_4_0 | 9ec7b624 | 17 |
| cantharellus | last step | CC_BY_NC_4_0 | d714382d Mushroom Observer | 10 |
| laetiporus | source | CC_BY_NC_4_0 | 50c9509d iNaturalist | 34,056 |
| laetiporus | source | CC_BY_4_0 | 50c9509d iNaturalist | 2,608 |
| laetiporus | source | CC0_1_0 | 50c9509d iNaturalist | 1,193 |
| laetiporus | source | CC_BY_NC_4_0 | d714382d Mushroom Observer | 922 |
| laetiporus | source | CC_BY_4_0 | fca5e616 New Jersey fungi | 252 |
| laetiporus | source | (six publishers under 15 records each) | | 36 |
| laetiporus | last step | CC_BY_NC_4_0 | 50c9509d iNaturalist | 18,147 |
| laetiporus | last step | CC_BY_4_0 | 50c9509d iNaturalist | 1,038 |
| laetiporus | last step | CC0_1_0 | 50c9509d iNaturalist | 576 |
| laetiporus | last step | CC_BY_NC_4_0 | d714382d Mushroom Observer | 19 |
| laetiporus | last step | CC_BY_NC_4_0 | 8a863029, 84d26682 | 6 |
| all_fungi | source | CC_BY_NC_4_0 | 50c9509d iNaturalist | 1,872,856 |
| all_fungi | source | CC_BY_4_0 | 50c9509d iNaturalist | 233,616 |
| all_fungi | source | CC_BY_NC_4_0 | d714382d Mushroom Observer | 164,890 |
| all_fungi | source | CC_BY_4_0 | fca5e616 New Jersey fungi | 156,744 |
| all_fungi | source | CC0_1_0 | 50c9509d iNaturalist | 115,268 |
| all_fungi | source | CC_BY_4_0 | 2b169d34 | 1,877 |
| all_fungi | source | CC_BY_NC_4_0 | e3ce628e | 1,157 |
| all_fungi | source | (34 publishers under 1,000 records each) | | 3,253 |
| all_fungi | last step | CC_BY_NC_4_0 | 50c9509d iNaturalist | 725,510 |
| all_fungi | last step | CC_BY_4_0 | 50c9509d iNaturalist | 65,756 |
| all_fungi | last step | CC0_1_0 | 50c9509d iNaturalist | 34,729 |
| all_fungi | last step | CC_BY_NC_4_0 | d714382d Mushroom Observer | 1,942 |
| all_fungi | last step | (11 publishers) | | 561 |

Three licences and no empty licence value appear in the file. After all four steps, iNaturalist
holds 4,562 of the 4,589 Cantharellus records and 19,761 of the 19,786 Laetiporus records; the
New Jersey dataset contributes 672 Cantharellus records at the source and none at the end (its
year-only dates are not the cause, see the eventDate table; inferred: its coordinates carry no
uncertainty, which step 2 drops, not checked per record). CC BY-NC is 89 percent of the final
Cantharellus records (4,094 of 4,589).

### eventDate shapes at the source stage

| Shape | Rows |
|---|---|
| day with time | 2,175,668 |
| day only | 364,209 |
| year only | 9,604 |
| range | 27 |

The T2 completion report's rule that ranges and month-only dates pass the date step and are
dedup-keyed on their raw text applies to 27 ranges; there are no month-only dates. The 9,604
year-only rows have no day and pass the date step; the T1 run report traces 9,330 of them to the
New Jersey dataset.

### The withheld texts

Second pass over occurrence.txt (data/t2/counts/withheld_wordings.txt), every digit run
replaced by N so that one wording counts once; 2,549,508 rows read.

| informationWithheld wording | Rows | Publisher(s) |
|---|---|---|
| Coordinate uncertainty increased to Nm at the request of the observer | 149,436 | 50c9509d iNaturalist |
| Coordinates obscured by observer | 3,775 | d714382d Mushroom Observer (the publisher tally gives exactly 3,775 for it) |
| Coordinate uncertainty increased to Nm to protect threatened taxon | 3,280 | 50c9509d iNaturalist |
| Libre acceso | 33 | 1ba64366 |
| none | 19 | 98897462 |

Total 156,543, equal to step 1's drop; 3,027 of them Cantharellus, equal to step 1's Cantharellus
drop (18,127 to 15,100). `dataGeneralizations` is empty on all 2,549,508 rows, as it was on the
900-record sample.

Three things this settles or raises:

- **Mushroom Observer marks obscured coordinates with its own wording**, which the T2 completion
  report listed as not checked. The any-non-empty-text rule (filters.py:43-56) caught it; a rule
  matching iNaturalist's sentence would have passed 3,775 records as open.
- **Taxon-level obscuring exists in the pull**: 3,280 iNaturalist records were obscured "to
  protect threatened taxon". None can be Cantharellus or Laetiporus (T2 completion report,
  verify-first item 2: neither has a conservation status; step 1's Cantharellus drop equals the
  observer-requested count only if that holds, and 3,027 is the whole Cantharellus drop, so it
  does). They are other fungi and leave the all_fungi denominator at step 1.
- **52 records are misclassified by the rule**: "Libre acceso" (Spanish, "open access") and
  "none" say the opposite of withheld, and the rule drops them at step 1. That is 0.03 percent
  of the step's drop and 0.002 percent of the pull; it changes no table materially. Recorded
  rather than fixed, because the rule is the dispatch's step as the builder decided it and the
  T2 review accepted; a two-line allowlist is the fix if the owner wants it.

### A correction to the record

The T2 completion report and its index row say obscured records carry "uncertainties of 26.5 to
28.9 km"; the T2 review (check 7, item 1) found the builder's own sample ran to 68 km and the
reviewer's to 75 km, and asked for a dated note in the successor report. This is that note,
2026-09-18: the figure was the range of the most common values, not of the sample. On the whole
pull, the truncated-prefix tally in data/t2/counts/summary.json shows the most common withheld
uncertainties clustering between 26.8 and 28.9 km, as the report said, with a long tail above;
the exact distribution was not tallied. The old wording stands in the report and index row; the
docstring at filters.py:46-48 still reads "about 26 to 29 km" and is left for the next edit of
that file, as the review proposed.

## The hand-check sample: blocked, and the seed fixed

The dispatch asks for "the seeded 200-record hand-check CSV". It was not produced, and could not
be from this download:

- The population is genus-level Cantharellus records with two agreeing identifiers that are
  **not research grade**. GBIF's iNaturalist dataset is research grade only (T2 completion
  report, verify-first item 1, quoting the dataset's own description; re-derived by the T2
  review, check 7). No record in this download is in the population.
- The pull that carries the population is one iNaturalist search of about 17,165 observations
  (`population_query()`, sampler.py:45-62), which the T2 completion report proposed as a
  DECISIONS.md row (its owner item 2). It has not been ruled on.
- This dispatch says "No substitute for GBIF downloads: not the search API, not the iNaturalist
  API". Running the proposed pull would be exactly that substitute, taken without a ruling.

This is the stop-and-ask case, not a judgment call: the dispatch's premise that the CSV follows
from the download was already reported false by the T2 completion report, which the dispatch
was written before reading (its "State this was written against" says so of the repo). Reported
here, nothing pulled.

What is done now so that the draw is a test rather than a search, as the T2 review's check 10
asked: **the seed for the real draw is 20260918**, fixed here before any candidate has been seen.
When the owner rules for the pull, `sample(candidates, seed=20260918)` (sampler.py:134-140) is the
call, and this line is the record of the seed's provenance. The synthetic test in
tests/test_records_sampler.py happens to use the same number; that is a coincidence of naming
both after the date, and the test's pool is 300 synthetic records, not the population.

## Deviations from the dispatch

- **The hand-check CSV**, above. Blocked on an owner ruling, not skipped.
- **The predicate was T2's own**, not T1's, for the three reasons in "Verify first". The dispatch
  allows this ("otherwise request its own").
- **No filter, threshold, box, group or step was changed.** The two readings the T2 review left
  for the owner (the taxon-less duplicate key; date-only first of month as a default date) were
  run as the code stood at 02af2c0, and their effect is measured below rather than adjusted.

## What the two open readings cost, measured

**The taxon-less duplicate key** (filters.py:115-123, T2 review check 3 item 1). Over all
regions, Cantharellus records reaching the duplicate step: 7,960; surviving: 4,589 (42 percent
dropped). Laetiporus: 23,726 to 19,786 (17 percent). All fungi: 1,367,291 to 828,498 (39
percent). For comparison, T1's per-taxon key at its 1,000 m threshold dropped 14 percent of PNW
Cantharellus records (1,424 to 1,226) and 6 percent of East ones (2,908 to 2,748) at the same
step (T1 run report). The thresholds differ, so the two are not the same population, but the gap
between 42 percent and 6 to 14 percent is the taxon missing from the key: an observer who logged
a chanterelle and any other fungus in one 0.1 degree cell on one day keeps whichever came first
in the file. Which came first depends on GBIF's output order, which the T2 completion report
already noted is not a property of the data. The count table's final row is therefore not
reproducible from a differently ordered file. The owner's ruling decides the key; the change is
one line plus a test row, as the review said.

**Date-only first of month** (filters.py:79-98). The step drops 799 records over the whole pull,
4 of them Cantharellus and 7 Laetiporus. Under the T1 dispatch's literal rule (00:00:00 only) the
drop would be smaller; how much smaller was not split here (the T1 run report splits it for the
two boxes: 5 of 567). The step is not material to any table above.

## Decisions taken here, and what was rejected

- **A separate download rather than T1's.** Rejected: reading T1's SIMPLE_CSV with step 1
  disabled, which would silently merge "obscured" into "uncertain" and could not count the rest
  of North America.
- **The license table carries the publisher.** Rejected: license alone, which cannot answer the
  T2 review's licence gate (check 6), which is per publisher.
- **Withheld texts tallied twice**: a 40-character prefix in the run script, which turned out to
  cut the number in "increased to 27840m" and so counted 1,197 "distinct" texts that are a
  handful of wordings; then a second pass with digits normalised, which is the table above.
  Recorded because the first tally is in summary.json and reads as if the wordings were many.
- **The seed fixed in the report, not in code.** Rejected: a `HAND_CHECK_SEED` constant in
  sampler.py, which touches a choice about a result on a branch under review; the report is the
  record and the constant can follow the ruling.
- **urllib, not `curl_argv`**, for the submission. Reason above; `curl_argv` stays as the
  documented alternative for an owner with `--netrc`.

## Owner items

1. **Rule on the duplicate key** (T2 review check 3 item 1) with the 42 percent figure in view.
   Every final-stage number above moves with it.
2. **Rule on the proposed iNaturalist pull for the hand-check sample** (T2 completion report
   owner item 2). Until then there is no CSV and no photo check. The seed is 20260918.
3. **The licence gate before any use.** DATA_REGISTER.md's GBIF row reads "Per record"; the table
   above gives the per-publisher, per-licence counts the T2 review asked for. The New Jersey
   dataset (CC BY, 156,744 records at source) contributes nothing after the filters; Mushroom
   Observer (CC BY-NC) contributes 1,942 of 828,498. Whether the 39 small publishers need rows
   is the owner's or T3's call.
4. **D26 as written is overtaken**: both downloads exist, and neither is a subset of the other
   (242 in-box records differ). If one pull is still wanted, the polygon-or-continent question
   needs a ruling before the business-account redo.
5. **The obscured share** is now known on the whole pull: 156,543 of 2,549,508 records (6.1
   percent of all fungi); for Cantharellus 3,027 of 18,127 (16.7 percent), close to EVIDENCE.md's
   17.3 percent for research-grade Cantharellus on iNaturalist directly.

## Not checked

- Why the CONTINENT predicate returns 242 fewer in-box records than the polygons. The records
  are identifiable (a set difference of gbifIDs between the two files) and were not extracted.
- The New Jersey dataset's coordinate uncertainty values, inferred above to be missing.
- The exact distribution of withheld uncertainty values; only the wordings were tallied.
- The 41 publishers' names beyond the three already resolved; keys are in the CSV.
- verbatim.txt and multimedia.txt were not opened.
- The notification email GBIF sent.
- CI on this branch: no pull request is open, so the workflow has not run; lint, format and
  tests passed locally at c29af4a and again before this report.
- What `identifications=most_agree` means on the iNaturalist API (carried from the T2 review).

## Conventions

Checked in this repo at 02af2c0: docs/audits/README.md for the index form and the append-only
rule; the T2 completion report and T2 review for the header fields, "The short version" first,
the read/observed/inferred labels, and the review's request for a dated correction note in the
successor; docs/pulls/ for where a request record lives; pyproject.toml for exact pins and ruff
settings; .gitignore for data/; the Forager CLAUDE.md rules on revert checks, on stop-and-ask when
a premise is wrong, on citing a figure with its scope, and on counting a check's sample against
something outside it (source rows against totalRecords, T2 in-box counts against T1's). Followed
all of them. "Sighting chance" is not used here because no chance is estimated; the phrase the
terms check searches for appears nowhere in the added files. No em dashes.
