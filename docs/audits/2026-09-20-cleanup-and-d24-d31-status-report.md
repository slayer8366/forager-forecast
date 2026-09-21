# Cleanup filing, and where D24 to D31 stand

**Date:** 2026-09-20.
**Type:** filing report and read-only status report for
docs/dispatch/2026-09-20-cleanup-and-d24-d31-status.md.
**Read time:** 2026-09-20 21:22 PDT for the branch tips; code read between 21:25 and 21:45 PDT.
**Supersedes:** nothing. The revision 3 index row saying revisions 1 and 2 "are not filed" was true
when written. The new index rows for those two files record that they are now filed.

## State against the dispatch's clause

The dispatch expected origin/main 1d27f08 and docs-homes-handoffs-dispatches b888c4a. **Both moved
forward, neither sideways.**

- The branch went b888c4a, then 9009760 (the coder handoff), then 4d90647 (the appended correction).
- Main went to 1a575a2, which merges the branch at 4d90647 on the owner's written authorisation under
  D40.
- So this commit sits on a branch whose earlier tip is already on main. It needs its own D40
  authorisation to reach main.

Task tips at the read were t1-calendar-smoke-test 163950e and t2-record-audit 932b9c9. Review branches
were t1-credentialed-run-review e9fbdf5 and t2-credentialed-run-review 9491ace.
Every change since the Part D report's tips (9f6c132, 4b22c8d) is under docs/, so the code probed then is
the code read now.

## Part 1: what was filed

**Provenance of the three stopped revisions.** The previous coder session on this machine received all
three. They were uploaded to that session and are still on disk under its upload folder. This session
did not receive them itself. They are filed from those files, and each filed text was compared with
`cmp`: it matches the upload byte for byte, up to the appended note. None was reconstructed.

| Filed as | Upload bytes | Stopped at | Superseded by |
|---|---|---|---|
| `docs/dispatch/2026-09-20-file-d40-to-d43.md` | 5,486 | item 2, about 20:00 PDT | revision 2, then revision 3 at b888c4a |
| `docs/dispatch/2026-09-20-file-d40-to-d43-rev2.md` | 7,906 | item 2, about 20:11 PDT | revision 3 at b888c4a |
| `docs/dispatch/2026-09-20-d32-merge-pass-stage-1-amendment.md` | 3,284 | precondition 1, about 03:32 PDT | revision 2, on main |
| `docs/dispatch/2026-09-20-cleanup-and-d24-d31-status.md` (this dispatch) | 3,219 | not stopped | not superseded |

Each of the three stopped files carries a dated closeout note appended under D41. The note says when the
revision was stopped, at which item, why, and what superseded it. This dispatch is being acted on, so
under D41 it carries no note.

**Where the stop times and reasons come from.** The times are the upload files' timestamps. The
previous session's stop reports are not in the repository. So each reason is taken from two sources:
the superseding revision's own text, and the coder handoff. Each note names its source.

The "written at" times inside the D40 to D43 revisions (20:30, 21:00, 21:20) are all later than their
uploads (20:00, 20:11, 20:38). They are the planner's estimates, and the notes say so.

**The relay-name rule.** The rule is now the same in `docs/dispatch/README.md` and
`docs/planning/handoffs/README.md`. It has three parts:

- A file is filed under the name its writer gave it.
- The relay's eight-character hex prefix is dropped without a note.
- A suffix such as `-1` or `-2` is dropped and noted in the index row, since it can signal a duplicate
  upload.

In the dispatch README this replaces the sentence b888c4a added. In the handoffs README it is new, added
to the naming bullet.

**The planner handoff's suffix.** `docs/planning/handoffs/2026-09-19-planner-handoff.md` arrived as
`2026-09-19-planner-handoff-2.md`. It was filed at 4114474 without the `-2`, and nothing noted the change
at the time. Its content matches the upload byte for byte: `cmp` against the file at 4114474 is clean.
Its index row was not edited. See also the first owner item below: it has no index row of its own.

## Part 2: D24 to D31, read-only

**Method.** A subagent read the code on origin/main 1a575a2, t1 163950e and t2 932b9c9 using
`git show` and `git grep`. Nothing was checked out and no test was run. Each line below says whether
the implementing code was read (READ) or only a token was found (TOKEN).

This session then re-read the lines most of the conclusions rest on:

- t2 `src/forager_forecast/records/filters.py:101-123` and `:48`;
- t2 `records/gbif_download.py:55-70`;
- t1 `gbif_download.py:26` and `:94`;
- t1 `open_meteo.py:59-61`;
- t1 `cells.py:39-50`;
- t1 `records.py:76-100`;
- the zero-hit greps for "equivalen" and for 20260918 in `src/` and `scripts/` on all three refs.

All held.

D24 to D31 are at `docs/planning/DECISIONS.md` lines 27 down to 20 on main. D34 at line 17 accepts them.
D24's verify-first items are named V1 to V4 below.

### Item 5: status by branch

Main has no record or weather code, so on main only D24 (evidence files), D29 (register), D30 and D31's
document parts can be done. On t1 and t2, every D24 item is not applicable: neither branch carries the
Copernicus evidence, and no code on either touches the store.

**D24**

| Item | Branch | Status | Evidence |
|---|---|---|---|
| V1, dataset names at source | main | done | `docs/planning/evidence/cds-credentials-report.md:18-22`. READ |
| V2, licence at source | main | partly done | CC BY is observed on all four. Missing: the 4.0 version is observed on ERA5-Land only; the attribution wording is not copied (`:23-24`); DATA_REGISTER.md has no Copernicus row (`SPEC.md:136`). READ |
| V3, precipitation accumulation convention | all | not started | Recorded nowhere. READ, plus a grep on every ref |
| V4, UTC day boundaries | all | not started for the store | Only the Open-Meteo side pins UTC, at t1 `open_meteo.py:61`. READ |

**D25, pin the two Open-Meteo parameters**

| Branch | Status | Evidence |
|---|---|---|
| main | not applicable | No Open-Meteo code |
| t1 | done | `src/forager_forecast/open_meteo.py:59-60` pins `elevation=nan` and `cell_selection=nearest`; the test asserts them at `tests/test_open_meteo.py:25-26`. READ. `archive_request_url` has no production caller |
| t2 | not applicable | No Open-Meteo code |

**D26, one geometry-selected DWCA download**

| Branch | Status | Evidence |
|---|---|---|
| main | not started | No code |
| t1 | not started | The request is SIMPLE_CSV, hard-coded at `gbif_download.py:26` and sent at `:94`. The DOI record reads provisional, with `superseded_by: null`. READ |
| t2 | not started | The predicate selects `CONTINENT = NORTH_AMERICA` at `records/gbif_download.py:59`, which D26 forbids. READ |

**D27, taxon in every duplicate key**

| Branch | Status | Evidence |
|---|---|---|
| main | not applicable | No code |
| t1 | partly done | The event key `(taxon_key, cell, day)` is at `records.py:90-100`. Missing: the key uses `taxonKey`, and whether that is the *accepted* key is unverified. T1 reads no `recordedBy`, so the observer-duplicate count is absent. READ |
| t2 | not started | `records/filters.py:115-123` keys on observer, cell and day, with no taxon. No event-key count exists. READ |

**D28, day-of-month table for date-only records**

| Branch | Status | Evidence |
|---|---|---|
| main | not applicable | No code |
| t1 | partly done | The provisional rule is at `records.py:76-86`. There is no day-of-month table, and datasetKey is not read. READ |
| t2 | partly done | The same rule is at `records/filters.py:79-98`. The count script tallies date shapes only, with no day-of-month table. READ |

The owner's final ruling is not made on any ref.

**D29, dataset list with licences beside each DOI**

| Branch | Status | Evidence |
|---|---|---|
| main | not started | The GBIF register row at `DATA_REGISTER.md:20` points at no list. READ |
| t1 | partly done | A by-licence count exists at `scripts/t1_count_table.py:108-114`. There is no constituent dataset list and no datasetKey. READ |
| t2 | partly done | `records/licenses.py:24-59` counts by licence and datasetKey. Missing: no list filed beside the DOI, no register pointer, and no code for the secondary analysis, since no model code exists. READ |

**D30, keep the old verify script and add a new one**

| Branch | Status | Evidence |
|---|---|---|
| main, header | done | `scripts/verify-open-meteo-historical-fields.sh:2-9`. READ |
| main, t1, t2, new pinned script | not started | The main header at `:7-8` names it, and it exists on no ref. READ, plus ls-tree on every ref |
| t1 and t2, header | not applicable | Both carry the base blob, so the merge takes main's header |

**D31, by part**

| Part | Branch | Status | Evidence |
|---|---|---|---|
| Production seed 20260918 | all | not started | The number appears in synthetic tests only (t1 `tests/test_gradient_boosting.py:18`, t2 `tests/test_records_sampler.py`); it is in no src/ or scripts/ file on any ref. READ |
| 20-configuration grid committed first | all | not started | No grid file and no tuning code. READ |
| Third register state, POLARIS and BIGMAP | main | done | `DATA_REGISTER.md:13`, `:24`. READ |
| Alaska masked | main | done | `SPEC.md:30`. No masking code exists anywhere yet. READ |
| NBAC correction | main | done | The T3 completion report, `:391`. READ |
| Open-Meteo "Terms to confirm" | main | done | `DATA_REGISTER.md:9`. The task branches carry the old cell, which the merge resolves. READ |
| Withheld-uncertainty figure in three places | t2 | not done | Still "about 26 to 29 km" at `records/filters.py:48`, `docs/audits/README.md:25` and `docs/planning/START_HERE.md:68`. Commit 9290144 defers it to the merge pass. READ |
| T0b review | main | done | `docs/audits/2026-09-18-t0b-review.md` exists. TOKEN only |

### Item 6: sizes

**Genuinely one line:**

- the D31 docstring at t2 `filters.py:48`, plus the two appended notes it needs elsewhere;
- the bare key line of D27 on t2, taken alone.

Nothing else is one line. Every size below is an **estimate** from reading the code, not a count of
written lines.

| Item | Estimate | What drives it |
|---|---|---|
| D27 in full | 4 to 6 files, 40 to 100 lines | a taxon column and a second counter on t2; recordedBy and the accepted key on t1; fixtures; re-running both counts |
| D28 table | 2 to 3 files, 40 to 80 lines | then the owner's ruling |
| D29 gate | 3 to 4 files, 80 to 150 lines, plus one filed list per DOI and a register edit | resolving titles and licences for each datasetKey |
| D26 redo | 5 to 8 files, 200 to 400 lines, plus a new credentialed download | a geometry predicate, the DWCA format in the submit path, a DOI record, a key reconciliation, a DWCA loader for T1, re-runs |
| D30 new script | 1 to 2 files, 60 to 150 lines | |
| D31 seed and grid | 2 to 3 files, 40 to 100 lines | the grid's contents are unruled |
| D24 V3, V4 and the register row | 2 to 3 files, 20 to 40 lines | reading sources |
| Equivalence test | 4 to 7 files, 250 to 500 lines | new pinned dependencies, a store client, a committed sample, live pulls |

### Item 7: dependencies

- **D26 and D42.** D26 does not strictly need the unified gbif_download, but it is better done after
  the move.
  - T1's `submit_download_request` posts any predicate, and T1 already builds `within` geometry
    predicates.
  - But T1's request is fixed at SIMPLE_CSV and sends no checklistKey.
  - T2 has the DWCA template with a checklistKey, and no submit function.
  - Neither module has a US and Canada geometry.
  - So the redo needs T1's submit plus T2's template plus a new predicate builder: what D42's
    unification produces, plus one function. Doing D26 first means editing one of two modules that are
    about to be merged.
- **D27's code** is independent. Its re-run counts, and possibly the accepted-key column, wait on D26.
- **D28's table** needs datasetKey. The counts that settle the rule should come from D26's download.
  The owner's ruling follows the table.
- **D29.** Lists for the new DOI wait on D26. Lists for the two provisional DOIs could be filed now.
- **The equivalence test** waits on:
  - D24 V3 and V4, or a mismatch cannot be attributed;
  - store client code;
  - D25's pins, which reach shared code only after the merge.
- **D30's new script** needs D25's pins too.
- **Before any fit:** D31's seed and grid, and the owner's D28 ruling.

### Item 8: the Open-Meteo equivalence test

**No code or test for it exists on any ref.**

- "equivalen" was searched on all 18 origin refs. Excluding docs/ and uv.lock there are zero hits; this
  session repeated the search on main, t1 and t2.
- The only Open-Meteo code on any ref is:
  - t1's URL builder, parser and cell tests;
  - the T0b verify script, whose section 5 compares Open-Meteo models with each other and not with the
    store.
- The test is specified only in documents: `DECISIONS.md:27` (D24), `SPEC.md:50`, `DATA_REGISTER.md:9`
  and `docs/planning/handoffs/2026-09-19-planner-handoff.md:61`.

## Noticed, not asked

1. **The two branches' cells differ by half a cell.** T1 assigns the *nearest* 0.1° centre
   (`cells.py:39-50`, ROUND_HALF_UP). T2 *floors* (`records/filters.py:101-106`). The same "cell, day"
   key means different cells on each branch. This drift is not among those D32 names.
2. **D42's reason says "T2's predicate builders are what D26's redo will need".** T2's only predicate is
   the continent selection D26 forbids. What D26 can use from T2 is the DWCA and checklistKey template.
3. **D29 asks for "each dataset's licence", but licences vary within a dataset.** The iNaturalist
   dataset carries CC0, CC BY and CC BY-NC records (t2 run report, around `:286-290`, read by the
   subagent only). So the commercial-safe subset has to be decided per record. This is ambiguous and
   needs the owner.
4. **D26 narrows the area to the United States and Canada.** T2's "rest of North America" region
   (`counts.py:44`, `:67`, subagent read) included Mexico. D26 does not say it changes T2's scope.
5. **D31's grid contents are unruled:** which hyperparameters, what ranges, which library. That is a
   stop-and-ask before building.
6. **Main has two stale lines.**
   - `TASKS.md:11-12` still says T1 and T2 are not started.
   - `SPEC.md:54-57` says Open-Meteo is used for training. The D24 bullet at `:50` just above it puts
     training on the store. Subagent read; not re-read here.
7. **D26's acceptance check needs T1's first CSV zip on disk.** GBIF deletes that download on
   2027-03-19. The local copy under data/ was not checked.
8. **The Part D report's line 118 is slightly wrong.** It says the seed is in no code on t1, but it is
   in a t1 test. The meaning holds, since a test is not a production seed.

## Owner items

- **The planner handoff has no index row of its own.** The dispatch said not to edit "its existing
  index row". The only row mentioning `2026-09-19-planner-handoff.md` is the row for the dispatch that
  filed it (`docs/audits/README.md:40`). D41 gives every handoff a row. Adding one was not asked, so none
  was added.
- **The coder handoff's home is still undesignated.** Its appended correction makes that "your first
  task", on the owner's delegation. This dispatch did not ask for it, and it is not done. It also
  collides with the handoffs README's naming rule, `YYYY-MM-DD-planner-handoff.md`.
- **Authorise the merge of docs-homes-handoffs-dispatches under D40**, if this commit should reach main.

## Not verified

- No tests were run. CI was not checked.
- Nothing under data/ was read.
- Whether SIMPLE_CSV carries acceptedTaxonKey or recordedBy is unverified.
- The T0b review's content was not read.
- The lines marked "subagent read" above were not re-read by this session.
