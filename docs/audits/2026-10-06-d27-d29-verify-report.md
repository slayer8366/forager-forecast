# D27 to D29: verify-first report

Answers "Verify first, report by message" in `docs/dispatch/2026-10-06-d27-d29-data-quality-tables.md`
(Forager RECORD -589). Written 2026-10-06 (UTC) by the coder session on this laptop (D38), branch
`dq-tables-d27-d29`, worktree `~/Zynergy/forager-forecast-dq`. Nothing built yet. No GBIF request has
been made by this session yet, and **no D28 count has been read**: the day-of-month measure in item 3
is fixed here first.

Conventions: "read" means opened in this session; "observed" means command output in this session;
"inferred" is marked. Line cites are to `6eb068a` (this branch after merging main `aa05c1f`).

## 1. Base and the download

- **Main moved.** The dispatch was written against `74c7f3b`. `origin/main` is now `aa05c1f`, the T5
  merge (Forager RECORD -599); `74c7f3b` is its ancestor (observed). I merged `aa05c1f` into this branch
  as `6eb068a`. One conflict, `docs/audits/README.md`, resolved keeping every row (main's ten T5 and
  T6b rows, then this branch's dispatch row).
- **What moved does not touch this task's cites.** `git diff 74c7f3b origin/main` on
  `src/forager_forecast/records/`, `scripts/t2_*`, and the D26 DOI record is empty; the register gains two
  rows (TreeMap, BIGMAP) and its GBIF row is unchanged (observed). Every cite in the dispatch re-checked:
  - handoff `:27` reads as quoted;
  - `gbif_download.py:221-236` is `fetch_download`'s body; the `"xb"` open is `:226`, the unlink `:233-234`;
  - `t2_render_tables.py:66-71` is the year-by-region loop over `REGIONS` only;
  - D27, D28, D29, D48, D61, D65, D66 read as the dispatch quotes them.
  - D100 already exists on main, and its row says it was numbered "to stay clear of ... D27 to D29 (D95
    to D99)". So D95 to D99 are free for this task (observed: highest row below D100 is D92).
- **Hash: matches.** `sha256sum` of `~/Zynergy/forager-forecast-d26/data/d26/downloads/0012112-260928105237408.zip`
  is `c0d5f6a1…b26c`, equal to `docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json:11`; size 1,434,032,123
  equals `:10`. The two September zips in `~/Zynergy/forecast-data/gbif/` match their `SHA256SUMS` and
  their DOI records (`6468a431…1683`, `d0e8e7cd…caaf`). All observed. Read in place; nothing extracted.
- **Suite before:** 315 passed, 211 test functions; `ruff check` and `ruff format --check` clean (observed).

## 2. D27: what the code gives today for the two keys

- Both keys exist: `event_key` (`records/filters.py:92-95`) and `observer_key` (`:98-107`). Taxon is
  `acceptedTaxonKey` (`occurrence.py:162-164`). The lowest gbifID survives (`filters.py:224-228`, D65).
- **Each step list counts one key only.** `t1_steps()` ends in the event key (`:155`), `r6_audit_steps()`
  in the observer key (`:166`). `git grep` finds no other caller of either key in `src` or `scripts`.
- Over D26's download, from the D26 build's own outputs (read, not re-run):
  - T1 list, event key: 655,088 reach the duplicate step, 63,764 dropped, **591,324** survivors (PNW
    144,048, East 447,276) (`docs/audits/2026-10-06-d26-build/t1_steps_0012112.json`).
  - R6 list, observer key: 1,341,108 reach it, 92,099 dropped, **1,249,009** survivors
    (`r6_0012112_summary.json`). The R6 summary carries no per-region split of survivors.
- **Missing for "Reports give both counts":** neither report gives the other key's count. No code tallies
  a second key over the same records. D65 and D66 settled what each key is and which record survives;
  "in full" still needs: (a) both keys counted over the same records reaching the duplicate step, for
  each list; (b) per region (PNW, East, outside both boxes); (c) a note of what the observer key does
  with an empty `recordedBy` (all such records share one observer, D32 follow-up report `:222`; no row
  rules on it). I will count those, not change them.
- **Proposed build (new code, no change to the step lists):** a duplicate-key tally that hooks on
  `Pipeline.on_pass` at the last filter's stage and keeps, per key, the lowest gbifID and its region.
  A test pins that its count for a key equals a real `Pipeline` run with that key as the duplicate step.

## 3. D28: the loader, and the measure, fixed before any count

**The loader keeps both.** `Record.dataset_key` from `datasetKey` (`occurrence.py:46`, `:190`). The date's
precision: `event_time` is `None` exactly when the eventDate text has no clock part (`:96-97`); a range
on one day keeps the start's clock (`:127-128`). So **date-only = `event_time is None`**. Month-only and
year-only values never become Records (D66); they are counted at the loader and are not in this table.

**The table (one row per datasetKey), over every record the loader can type, before any filter.** A
dataset's date practice is a property of the dataset, not of the filters, so the population is the source
stage. Columns:

| Column | Meaning |
|---|---|
| datasetKey, title | title from D29's list |
| loaded | records the loader typed |
| date-only (n) | `event_time is None` |
| date-only on the 1st (k) | of those, day of month 1 |
| share | k / n |
| ratio to 1 in 30 | share × 30 |
| 95% interval of the share | exact (Clopper-Pearson), two-sided |
| test | one-sided exact binomial test of k against n and 1/30, alternative "more than 1 in 30"; the p-value |
| excess on the 1st | k − n/30, and that as a fraction of k |
| verdict | below |
| midnight on the 1st with a clock time | shown for completeness; every candidate rule drops these, as the T1 dispatch's own wording does |

Plus a CSV of every dataset's date-only records by day of month 1 to 31.

**The measure, fixed now:**
- **Reference share: 1/30**, as D28 words it. The calendar figure is 12/365.2425 = 0.03285; 1/30 =
  0.03333 is slightly higher, which makes an excess slightly harder to show. Stated, not adjusted.
- **Minimum size: n ≥ 300** date-only records. Below that, the expected count on the 1st is under 10 and
  the row is "too few to test". Its counts are still shown.
- **Significance:** one-sided exact binomial, family level 0.01, Bonferroni over the m datasets tested:
  each dataset at 0.01 / m.
- **Verdicts:**
  - **too few to test:** n < 300.
  - **close to 1 in 30:** the test is not significant.
  - **clear excess:** significant, **and** the interval's lower end is at least 2/30. At twice the
    reference share, at least half of the records on the 1st are in excess of the calendar, so dropping
    them removes more suspect records than real ones. That is the reason for 2/30 and not another figure.
  - **small excess:** significant, but the lower end is below 2/30. Shown as its own verdict for the
    owner, not merged into either of the others.
- **Candidate rules, each run over both step lists and both keys, overall and per region:**
  - **drop all** (the provisional rule, today's code): date-only on the 1st dropped in every dataset.
  - **keep all** (the T1 dispatch's literal wording): only midnight on the 1st with a clock time dropped.
  - **per dataset:** date-only on the 1st dropped only in "clear excess" datasets.
  No rule is applied beyond the provisional one. The variants are new step lists built for the table.
- No "probability" or "chance" in any table (dispatch; D58). The column says "p-value".

**Not fixed by me, for the owner:** whether "small excess" datasets keep or lose their records, and
whether the "too few to test" ones do. The per-dataset rule above keeps both; the report will give the
records each would move.

## 4. D29: where titles, licences and counts come from

- **Distinct datasets in D26's download: 26.** The zip has 26 `dataset/*.xml` files (observed), and the DOI
  record says `number_of_datasets: 26` (`:20`). The zip also has `rights.txt` (title and "Rights as
  supplied" per dataset, as of the download) and `citations.txt`. One `rights.txt` entry has an empty title
  (observed); the API read will say which dataset that is.
- **Sources, all public, no credentials:**
  - per-dataset record counts in the download: GBIF's `GET /v1/occurrence/download/{key}/datasets`
    (one request, `limit` 100 covers 26);
  - title and licence now: `GET /v1/dataset/{datasetKey}`, 26 requests;
  - counted myself from `occurrence.txt`: rows by `datasetKey`, and by each record's own `license`
    (D48), and the dataset × licence cross table;
  - the zip's `rights.txt`, as of the download, beside the API's current licence.
- **Request count for 0012112: 27.** One at a time, a pause between, a `User-Agent` naming the project.
- **Form and path:** one JSON beside the DOI record, `docs/pulls/gbif-fungi-us-canada-2015-2025.datasets.json`:
  the download key and DOI, the read time (UTC) of each API response, then per dataset: key, title, licence
  as GBIF's API reports it (quoted), licence in the zip's `rights.txt`, records counted in `occurrence.txt`,
  GBIF's `numberRecords` for the download, and records by their own licence field; then the by-licence
  totals. The script that wrote it is committed. The DOI record is not edited (D41, D73); the register's GBIF
  row gains a pointer (the one edit D29 asks for).
- **The two older DOIs: proposed yes, both.** D29 says "next to each DOI", and both downloads' counts are
  cited in filed reports (T1's 0005709, T2's 0005714), so their records were used; D73 marks them
  superseded, which does not undo the use. Cost: about 2 list requests and only the dataset lookups not
  already made for 0012112 (0005709 has 15 datasets, 0005714 41). 0005709 is SIMPLE_CSV with no
  `rights.txt`, but its rows carry `datasetKey` and `license` (header read), so its list comes from the
  rows and the API. If the planner says no, I drop them; nothing else depends on them.

## 5. The D26 review's four minor items

| Finding | Proposed |
|---|---|
| 2. Wait loop and fetch call not saved | **Not recoverable as scripts.** `/tmp/claude-1000/d26/` survives on this laptop with `wait.log` (13 status lines, 06:52:24Z RUNNING to 07:40:36Z SUCCEEDED 1,434,032,123), `fetch.log` and `fetch_result.json` (path, size, sha256 equal to the DOI record), but no script file for either: both were inline commands. No session transcript on this laptop contains them (searched `~/.claude/projects` for `d26/wait.log` and `d26/fetch.log`, no hit). Fix: file the three logs into this task's evidence with a note saying the commands themselves are lost. I won't write a reconstruction and call it the original. |
| 3. `fetch_download` deletes a `.part` it did not create | Test first: a `.part` already present must raise and still be on disk afterwards. Fix: open the partial file with `"xb"` before the `try`, so the cleanup only runs for a file this call created. |
| 4. Renderer prints 0 for `outside_t1_boxes` on old CSVs | Test first: a count CSV with a region not in `REGIONS` (e.g. `rest_of_north_america`) must make `t2_render_tables.main` refuse, naming the region. Fix: refuse, and drop the stage table's "extra regions" columns, which only hid the problem in one of two tables. |
| 5. Builder's revert runner skips `__pycache__` and the edit probe | **None for the filed runner.** It is evidence of what ran, and the review infers its nine results unaffected. This task's runner does both, and is committed with this task's evidence. |

## Stops

None. Main moved, but no cite fails. The hash matches. `datasetKey` and date precision are both on the
Record. The D28 measure is fixed above, before any count.
