# D32 merge pass, stage 2b: the two D44 folds, T2 onto main, and the T1 move; and the pass's close

**Date:** 2026-09-20.
**Type:** report for docs/dispatch/2026-09-20-d32-merge-pass-stage-2b.md, filed by
docs/dispatch/2026-09-20-d32-merge-pass-closeout.md.
**Read times:** stage 2b opened 22:33 PDT; step 1 read 22:34; step 2 read 22:34; step 3 read 22:56.
This filing read 23:27 PDT.
**Written:** now, at the close, by the session that ran stage 2b. It is written from that session's own
reports to the owner, which were given in chat, and from the commit messages, which carry the same
figures. Stage 2b ran without a report file, and the move review (check "Record") named that as a gap.
**Supersedes:** nothing.

## Merges into main, with the owner's authorisations

D40 needs each merge's authorisation recorded with its wording and time. D50, filed on
docs-cowork-grid-report and not yet on main, makes the merge commit message that record. Two of the
three merges below record it there. One could not.

| Merge | Commit | Owner's words, given in chat | Time (PDT, 2026-09-20) | Where recorded |
|---|---|---|---|---|
| docs-homes-handoffs-dispatches into main | 49a5ed5 | "Merge docs-homes-handoffs-dispatches into main" | about 22:32 | the merge message |
| t2-record-audit into main | bc7863a | "Merge t2-record-audit to main." | about 22:46 | **here only** |
| t1-calendar-smoke-test into main | 42f0743 | "t1-calendar-smoke-test into main, no fast-forward as D32 requires" | about 23:25 | the merge message, and here |
| t1-move-review into main | 47204f7 | "t1-move-review into main, right after. It sits on top of eb3b907, so it merges clean once T1 is in, and the review of record joins the T1 commits it reviews" | about 23:25 | the merge message, and here |

- **Why bc7863a's message lacks it.** The T2 merge was committed locally at step 2 and reported ready.
  Its message was written then, before the owner authorised the push. It says the push "waits for the
  owner's written authorisation naming t2-record-audit". The commit was pushed unchanged once the
  authorisation came; before pushing, both parents were confirmed unmoved. So this report is the record
  D40 asks for.
- **Where the times come from.** Each is when the message reached the session, not a clock the owner
  stated. The two T1 authorisations arrived in one message, read at 23:27 PDT.
- **An earlier message was not acted on.** "Merge when ready" named no branch, so it was not treated
  as authorisation.

## Step 1: the two one-line folds D44 names, on t2-record-audit

| Commit | Change | Lines |
|---|---|---|
| e3ec5e5 | D31 docstring. One line appended to `is_user_obscured`'s docstring: "The 26 to 29 km is the sample's most common range, not its span: values run past 67 km (D31)." | +1 / -0 |
| 6560b2d | D27. `duplicate_key` returns `acceptedTaxonKey\|observer\|cell\|day`. | +1 / -1, the old return line |

**The docstring fold appends rather than edits.** Editing line 48 in place would break ruff's 100
character limit without reflowing the paragraph. D31 says the correction is "appended, never
overwritten", so line 48 stands.

**Tests.** One unit is one test function. Before, and after each commit: 55 passed, 0 failed, 0
skipped (75 pytest items). Ruff check and ruff format are clean.

**The key fold needed a separate check.** The suite passes identically with or without it, so the
suite does not cover it. An uncommitted probe did:

- With the change, two records differing only in `acceptedTaxonKey` get different keys, and the second
  is kept.
- With the line reverted, they share a key and the second is dropped.
- The forward change was restored from a saved copy, not from git, and confirmed present.

**Left stale, as D44 scopes the fold:**

- The key's docstring ("Observer, 0.1 degree cell and day").
- The step name `duplicate_observer_cell_day`.
- `COLUMNS_READ` in scripts/t2_count_table.py, which does not require the column. That the archive
  carries `acceptedTaxonKey` is from GBIF's DWCA format; the archive was not read.

## Step 2: T2 onto main, bc7863a

bc7863a is a no-ff merge of 6560b2d into 49a5ed5. Against main it adds 3,740 lines and deletes 1, the old
T2 row in TASKS.md. Conflicts arose in exactly the four expected paths:

- **docs/audits/README.md:** every row kept. Base 8, main 48, t2 14, after 54. That equals the distinct
  union. Neither side edited a row.
- **docs/dispatch/2026-09-18-t1-t2-credentialed-run.md (add/add):** task side taken. Main's 3,551
  bytes are a byte-exact prefix of the 4,335-byte result (checked with cmp).
- **docs/planning/START_HERE.md:** every row kept.
- **docs/planning/TASKS.md:** T2's row from the branch, T3's from main. The two lines found
  contradicting the record at the time (T1 "Not started", T2 "duplicate-key ruling pending") were left
  for the owner. T1's line was corrected by the T1 merge; T2's by the D50 to D53 filing on
  docs-cowork-grid-report.

**Tests on the merge result:** 55 passed, 0 failed, 0 skipped.

## Step 3: the T1 move, on t1-calendar-smoke-test

**27abc03 merges main into the branch.** Merge, not rebase: the branch has taken other work in by merge
before (8ffb22f), and a rebase would rewrite commits the review of record cites.

- Audits index: 60 rows, equal to the union.
- START_HERE and TASKS were resolved as the owner ruled at about 22:55 PDT: "Keep every row from both
  sides in START_HERE, and in TASKS take T1's row from the branch with T2 and T3 from main." Item 9
  prescribed only the index.

**eb3b907 is the move**, +224 / -381. The owner's rulings of about 22:55 PDT settled the names, the
gbif_download carry-over and the handling of T2's test. The commit message and the move review of record
(docs/audits/2026-09-20-t1-move-review.md) give the detail. In brief:

- **Renamed:** `records.py` becomes `records/t1_record.py`, and `simple_csv.py` becomes
  `records/t1_simple_csv.py`.
- **Unified:** `gbif_download.py` becomes `records/gbif_download.py`, built on T1's module with T2's
  `request_template(predicate)` and checklist key added.
- **Predicate JSON:** moved into `records/gbif/`.
- **Imports:** 11 lines rewritten.
- **T2's test file:** 6 of its 7 tests deleted, each named in the commit.

**Tests** (one unit is one test function):

| Point | Result |
|---|---|
| T1 before the merge | 53 passed |
| After 27abc03 | 6 modules fail at collection, each with "cannot import name 'Record' / 'SOURCE_STAGE' from 'forager_forecast.records'" |
| After eb3b907 | 97 passed, 0 failed, 0 skipped (147 items) |

The review reproduced 97 and 147 from a clean checkout.

**The test comment at tests/test_records_gbif_download.py:102-104 now resolves.** It cites "the stage
2b ready report", which the review found unfiled. This file is that report.

## 4b22c8d

4b22c8d (scripts/t2_withheld_wordings.py, 65 lines) reached main inside the T2 merge at bc7863a,
**before** its independent review. D42 assigned it to the move's review ("The move's independent review
also covers 64146f7 and 4b22c8d", DECISIONS.md line 15 on main). That review found it clean: read in
full, no write of any kind, no import of project code. Its check 7 also observes that the script
hard-codes the Cantharellus genus key as a string, while t1_design.py:57 holds it as an int. The two
are equal today; this is not a defect.

## Inputs for D32's follow-up task

These are verify-first inputs, not instructions. Line cites are to main 47204f7.

- **Two Record types:**
  - T1's frozen dataclass `Record` at src/forager_forecast/records/t1_record.py:21-22.
  - T2's `Record = Mapping[str, str]` at src/forager_forecast/records/filters.py:32.
  - The follow-up task chooses one (D42).
- **Two cell conventions, for D46 and D51:**
  - `cell_for` at src/forager_forecast/cells.py:44 rounds to the nearest tenth, with ROUND_HALF_UP in
    `_tenths` at :39.
  - `weather_cell` at src/forager_forecast/records/filters.py:102 floors, and `duplicate_key` at :116
    uses it.
  - D46 retires the floor. D51 (on docs-cowork-grid-report) confirms grid positions from delivered data.
    ERA5 delivers longitudes 0 to 360 (research note), while the cell code works in -180 to 180.
- **Two request builders**, in src/forager_forecast/records/gbif_download.py:
  - `build_download_request` with `DOWNLOAD_FORMAT = "SIMPLE_CSV"` (:27, :96).
  - `request_template` with DWCA (:107).
  - D26's redo uses one; retire the other on purpose.
- **Three docstrings describing the old layout or a past state:**
  - records/__init__.py:1-13 lists four modules, and none of the moved ones.
  - records/t1_record.py:4-5 says the download "has not been requested".
  - records/gbif_download.py:1 says "prepared and not yet requested", and does not mention
    `request_template`.
- **Two handoff passages naming old paths:**
  - docs/planning/handoffs/2026-09-20-coder-handoff.md:84-96.
  - docs/planning/handoffs/2026-09-19-planner-handoff.md:111.
  - Both take dated appended corrections under D41.
- **A test comment citing an unfiled report:** tests/test_records_gbif_download.py:102-104. It resolves
  once this file is on main.
- **The credential loader's two-of-three-missing case is asserted nowhere.** T1's
  `credentials_from_env` (records/gbif_download.py:52) raises with "not set: GBIF_PWD, GBIF_EMAIL" when
  only GBIF_USER is set. The review observed this, but no test asserts it since T2's test was deleted.
  The review proposes one added assertion.

## Dispatches filed with this report

- **Stage 2a, stage 2b and this closeout:** as received by this session.
- **Stage 2c:** not received by this session. It was sent to the review session, and two
  byte-identical uploads of it are on this machine, received at 23:07 and 23:08 PDT. The same
  dispatch uploaded twice is the duplicate-upload case the relay-name rule names. It is filed once from
  those files.
- **The closeout** arrived as `...-closeout-1.md`; the `-1` is dropped and noted in its index row.
