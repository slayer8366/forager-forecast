# Review of the T1 move (D32 stage 2c) under the standing protocol

Read time 23:08 PDT on 2026-09-20 (06:08 UTC 2026-09-21). Reviewer: a separate session from the one that wrote eb3b907, as D18 and D35 require. Review branch t1-move-review, cut from eb3b907; nothing else was written to.

## State this was written against

- main at bc7863a. t1-calendar-smoke-test at eb3b907, whose parent 27abc03 merges bc7863a into the branch. Both observed by `git rev-parse origin/main origin/t1-calendar-smoke-test` after a fetch at read time; both equal the dispatch's expectation, so the review proceeded.
- bc7863a is an ancestor of eb3b907 (`git merge-base --is-ancestor`), and `git merge-tree --write-tree bc7863a eb3b907` exits 0. The merge into main has no conflicts; it would fast-forward unless run with no-ff, which D32 requires.
- Under review: the diff 27abc03..eb3b907, plus 64146f7 and 4b22c8d. D42 assigns those two in its Decision column: "The move's independent review also covers 64146f7 and 4b22c8d." (docs/planning/DECISIONS.md:15). 64146f7 is on the branch and not on main; 4b22c8d is on both, having landed on main inside the T2 merge at bc7863a, so its review here is after the fact.
- The stage 2b dispatch and the builder's stage 2b report are not in the repository on any fetched ref. The builder's account used here is the commit message of eb3b907, which is in the repo; the dispatch to this review relays the report, and that relay is marked as such below wherever it is relied on.
- Environment: uv 0.12.17, `uv sync --locked --all-groups`, Python 3.14.4, pytest 9.1.1, ruff 0.16.8, in the review worktree and in scratch copies under /tmp made with `git archive`.

## Checks

### 1. Content preserved: holds

Each moved file compared at its new path in eb3b907 against its old path in 27abc03 by explicit path pairs (`git diff <rev>:<old> <rev>:<new>`), not git's rename pairing.

| Old path (27abc03) | New path (eb3b907) | Difference |
| --- | --- | --- |
| src/forager_forecast/records.py | src/forager_forecast/records/t1_record.py | none |
| src/forager_forecast/gbif/t1_fungi_two_boxes_2015_2025.json | src/forager_forecast/records/gbif/t1_fungi_two_boxes_2015_2025.json | none |
| src/forager_forecast/simple_csv.py | src/forager_forecast/records/t1_simple_csv.py | one import line (line 26) |
| tests/test_records.py | tests/test_records_t1_record.py | one import line (line 3) |
| tests/test_records_observed.py | tests/test_records_t1_observed.py | one import line (line 5) |
| tests/test_simple_csv.py | tests/test_records_t1_simple_csv.py | two import lines (8, 9) |
| tests/test_gbif_download.py (T1's) | tests/test_records_gbif_download.py | one import line (5) plus additions, check 4 |
| src/forager_forecast/gbif_download.py (T1's) | src/forager_forecast/records/gbif_download.py | additions only, below |

The unified gbif_download against T1's original: `git diff --stat` reports 25 insertions and 0 deletions; counted with `-U0`, 21 non-blank lines added and 4 blank, 0 removed. The additions are one import (`from typing import Any`, new line 20), the constant `GBIF_BACKBONE_CHECKLIST_KEY` with its four-line comment and a one-line provenance comment (new lines 29 to 34), and the function `request_template` (new lines 107 to 121). The builder's "0 lines removed and 25 added" matches git's count. The constant's value and its four comment lines are byte-equal to T2's at 27abc03 (records/gbif_download.py:26-30 there).

### 2. Only the named lines changed: holds

`git diff -U0 27abc03 eb3b907` on the four files that were neither added nor deleted shows five changed lines, every one an import: scripts/t1_count_table.py:25 and :31, scripts/t1_render_tables.py:19, src/forager_forecast/cell_weeks.py:15, tests/test_cell_weeks.py:13. Inside the moved files, six more import lines changed (table above: t1_simple_csv.py:26, test_records_t1_record.py:3, test_records_t1_observed.py:5, test_records_t1_simple_csv.py:8 and :9, test_records_gbif_download.py:5). Five plus six is the builder's 11, and each of the 11 rewrites `forager_forecast.records`, `.simple_csv` or `.gbif_download` to `forager_forecast.records.t1_record`, `.records.t1_simple_csv` or `.records.gbif_download`. `git diff --stat --no-renames` lists 20 paths and no document: no index row, no report, no docs change rides in the commit.

### 3. One body change: holds

Against T1's original, no existing function body differs (check 1: additions only). Against T2's original, the only carried function is `request_template`; T2's took no parameter and returned `"predicate": predicate()` (27abc03 records/gbif_download.py:64-70), the unified one is `request_template(predicate: dict[str, Any])` returning `"predicate": predicate` (eb3b907 records/gbif_download.py:107-121). The other body lines (`"format": "DWCA"`, `"checklistKey": GBIF_BACKBONE_CHECKLIST_KEY`) are unchanged; the docstring grew by six lines quoting T2's DWCA reasoning.

The continent predicate is not on the branch. `grep -rniE 'continent|NORTH_AMERICA|request_template_json|FUNGI_TAXON_KEY|curl_argv|request_body\b|MissingCredentials' src tests scripts` finds no GBIF predicate term: the hits are `REST_OF_NORTH_AMERICA` in records/counts.py:44 and :67 (a region label for the count table), `NORTH_AMERICA_INAT_PLACE_ID` in records/sampler.py:27 (an iNaturalist place id for the hand-check sampler, not a GBIF predicate), the T2 docstring sentence at records/gbif_download.py:110 that explains the removal, and test names. `def predicate` exists in no module. The JSON body with the CONTINENT clause survives only as docs/pulls/gbif-fungi-north-america-2015-2025.json, which nothing reads (grep above; the test that read it was deleted, check 4). The dispatch's request is met: the continent predicate is reachable from no module.

### 4. Deleted tests: holds, with one coverage note

T2's tests/test_records_gbif_download.py at 27abc03 held seven tests. One was kept and re-pointed; six were deleted. For each, what it tested and whether that thing exists at eb3b907:

| Deleted test (27abc03 line) | Tested | At eb3b907 |
| --- | --- | --- |
| test_committed_request_file_matches_the_code (:19) | docs/pulls/gbif-fungi-north-america-2015-2025.json equals `request_template_json()` | `request_template_json` deleted. The JSON file remains as provenance and is now unguarded by any test, which is correct for a superseded query (D26); nothing regenerates it. |
| test_predicate_is_exactly_the_dispatch_terms (:23) | T2's `predicate()` carries the six terms incl. CONTINENT | `predicate()` deleted, per D45. |
| test_missing_credentials_name_every_unset_variable (:42) | T2's `credentials_from_env` with one of three set raises `MissingCredentials` with `.missing == ["GBIF_PWD", "GBIF_EMAIL"]` | T2's loader and `MissingCredentials` deleted. A function of the same name remains: T1's `credentials_from_env` (records/gbif_download.py:52-69), raising `MissingGbifCredentials` with the names in the message. See note. |
| test_empty_variable_counts_as_unset (:48) | T2's loader treats `""` as unset | Same as above. |
| test_request_body_adds_only_the_notification_fields (:54) | T2's `request_body` adds exactly notificationAddresses and sendNotification | `request_body` deleted. T1's `build_download_request` (records/gbif_download.py:96-104) is the surviving builder, covered by test_download_request_body (test file :49-55). |
| test_curl_argv_posts_the_body_file_with_basic_auth (:71) | T2's `curl_argv` | `curl_argv` deleted. T1's `submit_download_request` posts with urllib and is covered by two tests (:73, :93). |

Note on the two credential tests. The code they exercised is gone, but the behaviour they asserted is the behaviour of the surviving loader too, checked directly: `credentials_from_env({"GBIF_USER": "someone"})` raises with the message ending `not set: GBIF_PWD, GBIF_EMAIL`, and with `GBIF_PWD` set to `""` the message ends `not set: GBIF_PWD` (observed, scratch copy). T1's own test (test file :32-40) covers the all-missing case and a blank-space value; the two-of-three-missing case that T2's test pinned is no longer asserted by any test, only observed here. That is a small coverage difference, not a deleted test for live code. Proposed fix, for the follow-up task if wanted: one assertion in test_missing_credentials_are_named_not_guessed for the two-missing case.

The kept test, test_format_is_dwca_because_simple_csv_lacks_information_withheld, was rewritten from `json.loads(g.request_template_json())` to `request_template(expected_t1_predicate())` (test file :107-110); its two assertions are unchanged.

### 5. Tests can fail: holds

Revert checks, run in a scratch copy of eb3b907 (`git archive` into /tmp/t1mr-revert, own `uv sync`), with the module saved to a file before editing and restored from that file, then `cmp`-checked. Baseline: the nine gbif tests pass.

- Revert A: `"DWCA"` to `"SIMPLE_CSV"` inside `request_template` only (one line, diff shown). Result: `1 failed, 8 passed`; test_format_is_dwca_because_simple_csv_lacks_information_withheld fails at tests/test_records_gbif_download.py:109 with `AssertionError: assert 'SIMPLE_CSV' == 'DWCA'`. Restored, cmp identical.
- Revert B: `"predicate": predicate,` to `"predicate": expected_t1_predicate(),` (one line, the pass-through removed). Result: `1 failed, 8 passed`; test_request_template_carries_the_callers_predicate_and_nothing_personal fails at :116 with `assert {'type': 'and', ...} == {'type': 'equals', 'key': 'HAS_COORDINATE', ...}`. Restored, cmp identical; nine pass again.

Both failures are at the lines the commit message names (109, 116) and each message is specific to its own edit; neither run had a collection error. The review worktree was confirmed unchanged afterwards (`git status --short` empty; the forward `request_template(predicate` signature present).

Full suite from the clean review worktree: `uv run pytest -q` gives **147 passed, 0 failed, 0 skipped** (147 items); `pytest --collect-only` lists **97 distinct test functions**; `ruff check` and `ruff format --check` clean (104 files). This equals the builder's 97 / 147.

Reconciliation, each count observed from a `git archive` scratch copy with its own `uv sync`: T1 before the merge (163950e) collects 53 functions / 83 items; main (bc7863a) collects 55 / 75; the shared modules test_large_file_guard.py and test_package.py hold 6 functions at main; T2's gbif test file held 7 (check 4). 53 + 55 - 6 - 7 + 2 = 97. At 27abc03, the merge before the move, collection stops with 6 errors ("cannot import name 'Record' from 'forager_forecast.records'" family, `records/` shadowing `records.py`), 69 functions collected in the remaining modules. That is the failure the move exists to cure, observed.

### 6. Paths: holds

`PREDICATE_PATH` is `Path(__file__).parent / "gbif" / "t1_fungi_two_boxes_2015_2025.json"` (records/gbif_download.py:25); from the review worktree it resolves to src/forager_forecast/records/gbif/t1_fungi_two_boxes_2015_2025.json, `.exists()` is True, and `load_t1_predicate() == expected_t1_predicate()` is True (observed). `grep -rnE '__file__|parents\[|\.parent\b|open\(["'"'"']' src tests scripts` finds two other file-relative paths: tests/test_large_file_guard.py:14 (`Path(__file__).resolve().parents[1]`, the repo root; tests/ did not move, so unaffected) and the two pack scripts scripts/inat_counts.py and scripts/inat_taxon_ids.py that open `ids.json` relative to the working directory (frozen by T0, excluded from lint, untouched). The commit message's "that is the only file-relative path in src, tests or scripts" is therefore one short; the omission has no consequence for the move.

### 7. The two post-cut commits: holds, one observation

**4b22c8d**, scripts/t2_withheld_wordings.py, 65 lines, identical at eb3b907 (`git diff 4b22c8d eb3b907 -- scripts/t2_withheld_wordings.py` empty). Read in full. It opens a zip and reads occurrence.txt (lines 24-26), tallies, and prints (46-59). No `open(..., "w")`, no write of any kind; imports are io, re, sys, zipfile, collections, pathlib only, so it touches no forager_forecast filter, constant or test. It hard-codes `CANTHARELLUS_GENUS_KEY = "9623860"` (line 20) as a string; src/forager_forecast/t1_design.py:57 holds the same key as the int 9623860. Duplicate by value, equal today; an observation, not a defect of this move.

**64146f7** changed two files. (a) The docstring of `submit_download_request` (now records/gbif_download.py:130-132) says the function was first run against the real endpoint on 2026-09-19 UTC and returned key 0005709-260916113435855 on the first call. The function POSTs the built request with basic auth and returns the response body as the key (133-150). The T1 credentialed run report gives that key at line 130, `Created 2026-09-19T03:57:12Z` at line 132, and "It returned the key on the first call" at line 145. The docstring matches the function and the report. (b) It also parenthesised the `except KeyError, ValueError:` clause in scripts/t1_count_table.py:55; the next commit 9f6c132 ("ruff format") put it back, and `git diff 2c540e2 9f6c132 -- scripts/t1_count_table.py` is empty, so the branch carries the unparenthesised form at line 55 today. That form is valid on the pinned 3.14 (pyproject.toml `requires-python = "==3.14.*"`, ruff `target-version = "py314"`) and would not parse on the 3.12 fallback D21 names. Nothing in this move touches it; it is recorded here because D42 puts 64146f7 in this review's scope and the commit's own message describes a change the tree no longer has.

### 8. Documents describing the old layout: holds, with additions

The builder's three, confirmed:

- src/forager_forecast/records/__init__.py:1-13 lists four modules (gbif_download, filters, counts, sampler), describes gbif_download as "the GBIF download predicate T2 shares with T1", and does not mention t1_record, t1_simple_csv or gbif/.
- T1's module docstrings. Two are decayed, both on the same claim and both from before the move: records/t1_record.py:4-5 ("the GBIF download that would feed this has not been requested") and records/gbif_download.py:1 ("prepared and not yet requested"; lines 10-12, on the 403 and 401 probes of 2026-09-18, are still true). The download was requested on 2026-09-19 UTC. The gbif_download docstring also now says nothing about the DWCA `request_template` it carries.
- docs/pulls/t1-fungi-two-boxes-2015-2025.doi.json:63-64 names src/forager_forecast/gbif/ and forager_forecast.gbif_download; docs/pulls/gbif-fungi-north-america-2015-2025.doi.json:60 names `request_body()` and `curl_argv`, both now deleted. Provenance; they describe what was run, and stay.

Added by this review, from `grep -rnE 'records\.py|simple_csv\.py|forager_forecast\.simple_csv|forager_forecast\.gbif_download|forager_forecast/gbif/|test_records\.py|test_simple_csv|test_gbif_download|test_records_observed'` over docs/planning, README.md, src, scripts, tests, docs/pulls and docs/dispatch (docs/audits excluded as point-in-time by its own README):

- docs/planning/handoffs/2026-09-20-coder-handoff.md:84-96 lists the old paths and the eleven import sites by old name; docs/planning/handoffs/2026-09-19-planner-handoff.md:111 describes records.py as shadowed. Both are dated handoffs that D41 lets take appended corrections; the coder handoff is what the next coder reads first, so a one-line dated correction there is worth more than the docstrings.
- docs/dispatch/2026-09-20-d32-merge-pass-stage-1-amendment-rev2.md:34 names records.py; byte-identical by D41, no action.
- tests/test_records_gbif_download.py:102-104 cites "the stage 2b ready report", which is not in the repository (see State above).

Fix now or in the follow-up: the follow-up. D32's unification task chooses one Record type and will re-cut the records package, so its package docstring is rewritten then; fixing it now would be edited twice. The two "not yet requested" sentences predate this move and belong with that rewrite. This reviewer did not change them: they sit on a branch this review may not touch, and the protocol's small-gap allowance covers the review's own commit only.

### 9. D46: holds

The cell code is not changed by the move: src/forager_forecast/cells.py is not in the 20-path diff, and cell_weeks.py's only change is the import at line 15. For the follow-up task: T1's nearest-point assignment is `cell_for` at cells.py:44-50, which rounds tenths with `ROUND_HALF_UP` in `_tenths` (cells.py:41), docstring "whose centre is nearest to the coordinate"; T1's duplicate step calls it from records/t1_record.py:90. T2's round-down is `weather_cell` at records/filters.py:102-107 (`math.floor`), used by `duplicate_key` at :116-124. Both remain live on the branch, half a cell apart as D46 says; D46 retires the floor in the follow-up, not here.

## Protocol checks not covered above

- Terms (1): `git diff 27abc03 eb3b907 | grep -niE 'fruiting probability|probability|calibrated|percent'` is empty.
- Decisions (2): D42 "no other change to function bodies" is met except for the one body change D45 forces; D45 "not its continent predicate" is met (check 3); D46 untouched (check 9); D44's two folds are on main already (bc7863a) and the move adds none.
- Fixed choices (3): the predicate JSON is byte-identical at its new path (check 1); t1_design.py is not in the diff.
- Scope (4): 20 code and test paths, no document, no data.
- Record (5): gap. The move has no report file and no index row in the repository, and the stage 2b dispatch that ordered it is not filed; the commit message is the only in-repo account. D41 wants the dispatch in docs/dispatch/ with an index row. Proposed fix: file the stage 2b dispatch and its report before or with the T1 merge.
- Data hygiene (6): six added blobs, largest 6,131 bytes; no data.
- Evidence (7): the commit message's claims were each checked above; one is short by two paths (check 6).
- Headline numbers (9): 97 / 147 reproduced from a clean checkout (check 5).

## Gaps

- No filed dispatch and no filed report for stage 2b (Record, above).
- The two-of-three-missing credential case is observed, not tested (check 4 note).
- docs/pulls/gbif-fungi-north-america-2015-2025.json is no longer guarded by any test; acceptable for a superseded query, stated so nothing later assumes it is.
- The unified module now holds two request shapes: `build_download_request` with `DOWNLOAD_FORMAT = "SIMPLE_CSV"` (records/gbif_download.py:27, :96-104) and `request_template` with DWCA (:107-121). D42 asked for both to be carried; D26's redo will use one. Left for the follow-up task, noted so the follow-up retires one on purpose.

## Conventions

Line cites are to eb3b907 unless a revision is named. Observed means a command run in this session; read means the file at that line; relayed means the dispatch's account of the builder's report, which is not in the repo. Counts of test functions are `pytest --collect-only` node ids with parameter suffixes stripped and de-duplicated; items are pytest's own total.

## Not checked

- docs/planning/START_HERE.md's fixed terms were not re-read; the terms grep on the diff stands in for it.
- Nothing was run against the download archives; they sit in another session's worktrees and the move reads none.
- Whether 4b22c8d reproduces data/t2/counts/withheld_wordings.txt; the script was read, not run (the dispatch asked "reads only", which was confirmed).
- D20's fallback-interpreter sentence was read only in the grep excerpt that names 3.12.

## Verdict

**The move may land on main as is.** Every moved file is content-identical to its original apart from the eleven import lines; the unified gbif_download is additions only over T1's; the one body change is the predicate parameter D45 requires and its guard fails on revert; the continent predicate is reachable from nowhere; PREDICATE_PATH resolves; 97 functions pass from a clean checkout and reconcile to the builder's count; and the merge preview into bc7863a is conflict-free. The findings above (unfiled dispatch and report, decayed docstrings, the two request shapes, the handoff's old paths) are follow-up items, none a reason to hold the merge. Under D40 the merge waits for the owner's written authorisation naming t1-calendar-smoke-test, and D32 requires no-ff.

Reviewer changed only this file and its index row.
