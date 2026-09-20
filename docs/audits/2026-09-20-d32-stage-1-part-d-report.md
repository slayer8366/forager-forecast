# D32 merge pass, stage 1: Part D inventory, filed

**Date:** 2026-09-20.
**Type:** Part D report for docs/dispatch/2026-09-19-d32-merge-pass-stage-1.md, as amended by
docs/dispatch/2026-09-20-d32-merge-pass-stage-1-amendment-rev2.md.
**Base:** main cb0bca8, on branch d32-stage-1-records.
**Supersedes:** nothing. Part D first ran read-only at 2026-09-19 22:37 PDT and its results were never
committed. This report is that inventory, with the parts the amendment named re-read.
**Writer:** this session, under D38 (docs/planning/DECISIONS.md line 9 on main cb0bca8), being the
session on the machine holding ~/.config/forager-forecast/ and the archive.

**Read times.** Everything marked **re-read** was run at 2026-09-20 14:34 PDT against origin/main
cb0bca8 and the four branch tips below. Everything marked **carried** is from the 2026-09-19 22:37 PDT
read and was not re-run. No item is unmarked.

Preconditions, re-read: D39 at line 8 and D38 at line 9 of docs/planning/DECISIONS.md on main cb0bca8.
Four tips unmoved from the 22:37 read: t1-calendar-smoke-test 9f6c132, t1-credentialed-run-review
e9fbdf5, t2-record-audit 4b22c8d, t2-credentialed-run-review 9491ace.

## Item 1. Commits made after the independent reviews were cut (re-read)

One unit of this table is a commit on the task branch after the point its review branch was cut,
excluding neither the self-check nor the code commits. The cut points are the merge bases: 691bef3 for
T1, b4ff6e3 for T2.

| Branch | Commit | Files, added/deleted | What it is |
|---|---|---|---|
| t1-calendar-smoke-test | 2c540e2 | `docs/audits/2026-09-18-t1-credentialed-run-review.md` +394/-0; `docs/audits/README.md` +1/-0 | The builder self-check. Part A's rename target. |
| t1-calendar-smoke-test | 64146f7 | `scripts/t1_count_table.py` +1/-1; `src/forager_forecast/gbif_download.py` +3/-2 | Parenthesises an `except` clause; rewrites one docstring. |
| t1-calendar-smoke-test | 9f6c132 | `scripts/t1_count_table.py` +1/-1 | `ruff format` after that edit. |
| t2-record-audit | f8adaa4 | `docs/audits/2026-09-18-t2-credentialed-run-review.md` +321/-0; `docs/audits/README.md` +1/-0 | The builder self-check. Part A's rename target. |
| t2-record-audit | 4b22c8d | `scripts/t2_withheld_wordings.py` +65/-0 | A 65-line tally script. Reads only. |

**9f6c132 is cosmetic, and its message is accurate (carried).** It restores the pre-fix blob e0bdce7
exactly, which looks like a revert of 64146f7. It is not. `pyproject.toml` sets
`requires-python = "==3.14.*"` and `[tool.ruff] target-version = "py314"`, and PEP 758 makes an
unparenthesised `except` tuple legal from 3.14, so ruff format removes the parentheses as redundant. The
net diff 691bef3..9f6c132 does not touch `scripts/t1_count_table.py` at all. The only surviving code
change from the two T1 commits is the `gbif_download.py` docstring. 64146f7 was fixing a non-bug: the
independent review's check 10 flagged that line as unverified on Python 3.12, and the project does not
target 3.12.

**"Unreviewed" is the right word, narrowly (carried).** Both independent reviewers saw the tips move and
wrote it up, but both declared the new commits out of scope. T1's header amendment: "This review's scope
stays 34933e8..691bef3; 64146f7 is a code change after that base and is not covered by either review as
written." T2's: "Neither is in the range this review covers (02af2c0..b4ff6e3)." Description by a
reviewer who has excluded the commit from scope is not review under D18. What is genuinely unreviewed is
a three-line docstring change and a 65-line script.

## Item 2. Files T1 would move into T2's package under D32 (line counts re-read)

D32's wording: "T1's record-handling code, which now includes a CSV loader and two scripts, moves into
the package that T2 laid out, with its tests, as its own commit with its own review."

One unit of the line counts below is a newline-terminated line in the file at the branch tip named.

| T1 file, current path | Lines | Its tests | Lines | Collides with |
|---|---|---|---|---|
| `src/forager_forecast/records.py` | 136 | `tests/test_records.py` | 105 | `src/forager_forecast/records/` (package) |
| | | `tests/test_records_observed.py` | 59 | |
| `src/forager_forecast/simple_csv.py` | 159 | `tests/test_simple_csv.py` | 144 | nothing |
| `src/forager_forecast/gbif_download.py` | 125 | `tests/test_gbif_download.py` | 98 | `src/forager_forecast/records/gbif_download.py` |
| `scripts/t1_count_table.py` | 157 | none | | `scripts/t2_count_table.py` (parallel name, no clash) |
| `scripts/t1_render_tables.py` | 102 | none | | `scripts/t2_render_tables.py` (parallel name, no clash) |

The T2 package they land beside, for sizing: `records/__init__.py` 12, `records/counts.py` 113,
`records/filters.py` 225, `records/gbif_download.py` 124, `records/licenses.py` 69,
`records/sampler.py` 158.

**Shadowing, re-read.** The read-only merge tree of the two task branches is
1ccbb9edebad6435f0de12075cba53cf74496924. It contains both `src/forager_forecast/records.py` and
`src/forager_forecast/records/__init__.py`, and both `src/forager_forecast/gbif_download.py` and
`src/forager_forecast/records/gbif_download.py`. Git reports no conflict on any of them. Python resolves
`forager_forecast.records` to the package, so T1's module would be imported by nothing and its two test
files would exercise a file the package has hidden. This is what D32's rejected alternative "merge first
and refactor later (lands the shadowed module on main)" describes.

**The two `gbif_download.py` files are not two copies of one module (re-read, new since 22:37).** The
22:37 report called this duplication and left the divergence unchecked. Checked now: the diff between
them is +97/-98 over files of 125 and 124 lines, and they share exactly one top-level name,
`credentials_from_env`. T1's defines `MissingGbifCredentials`, `GbifCredentials`, `credentials_from_env`,
`load_t`, `expected_t`, `build_download_request`, `submit_download_request`. T2's defines `predicate`,
`request_template`, `request_template_json`, `Credentials`, `MissingCredentials`, `credentials_from_env`,
`request_body`, `curl_argv`. These are two independent implementations that happen to share a filename,
not a fork. "Keep one and delete the other" is therefore not available as a mechanical step: stage 2 has
to decide which behaviours survive, and T1's `submit_download_request` is the only one of the two that
posts to the endpoint.

## Item 3. Where the merges conflict (re-read)

Predicted with `git merge-tree`, read-only, no commit made. One unit is a path git reports as
conflicting.

| Merge | Conflicting paths |
|---|---|
| t1-calendar-smoke-test <- t1-credentialed-run-review | `docs/audits/2026-09-18-t1-credentialed-run-review.md` (add/add); `docs/audits/README.md` (content) |
| t2-record-audit <- t2-credentialed-run-review | `docs/audits/2026-09-18-t2-credentialed-run-review.md` (add/add); `docs/audits/README.md` (content) |
| t1-calendar-smoke-test <- t2-record-audit | `docs/audits/README.md`; `docs/planning/START_HERE.md`; `docs/planning/TASKS.md` (all content) |

Four files change on both task branches against their base f96d557; the fourth,
`docs/dispatch/2026-09-18-t1-t2-credentialed-run.md`, is byte-identical on both (blob 9ceb685) and merges
clean. The two add/add conflicts are the D35 collision, and Part A's renames are what clear them.

## Item 4. D25 to D31, already folded in or still to fold (carried, probe markings kept)

Rows marked **probe** confirmed only that a token is present in the named file. Presence of a word is
not compliance, and those rows were not verified against the implementing code. Rows not marked probe
were read.

| D | t1-calendar-smoke-test | t2-record-audit |
|---|---|---|
| D25 | **Present.** `open_meteo.py` pins `models`, `elevation` and `cell_selection` at lines 58 to 60. | **Not applicable.** No `open_meteo.py` on the branch. |
| D26 | **To fold in.** No DWCA path; T1's download is the two-box CSV. | **To fold in.** The existing pull is continent-selected (`docs/pulls/gbif-fungi-north-america-2015-2025.json`), which D26 forbids. A new download, not a fold. |
| D27 | **Present (event key).** `records.py:96` builds `(record.taxon_key, cell.lat_tenths, cell.lon_tenths, record.event_date)`. Re-read 14:34. | **Missing taxon.** `records/filters.py:115-123` returns `observer\|cell\|day`, and its docstring says "Observer, 0.1 degree cell and day". D27 requires taxon in the observer-duplicate key. Re-read 14:34. |
| D28 | **To fold in. Probe.** The date rule is in `records.py`; no day-of-month table found. | **To fold in. Probe.** The rule is in `records/filters.py`; no by-dataset day-of-month table found. |
| D29 | **Probe only.** Licence handling in four files. Gate artefacts not verified. | **Probe only.** `records/licenses.py` and two scripts. Gate artefacts not verified. |
| D30 | **To fold in.** The frozen script on this branch predates D30; the mandated header is on main only. | Same as T1. |
| D31 | **To fold in.** Seed 20260918 in no code on the branch. | **To fold in.** Present only in `docs/planning/START_HERE.md`, not in code. |

D30's second half, a new verify script pinned to era5_seamless and the D25 parameters, exists on no
branch at all. It is a separate build, not a fold into either branch.

## Not checked

- Whether D28's and D29's requirements are satisfied rather than mentioned. Those four cells are probes.
- CI on any branch.
- Anything requiring the archive or a credential file.
- The T2 roll-up figure's derivability, which is Part C's stop-or-proceed test and is reported separately.

Conventions: the report shape of docs/audits/2026-09-19-decisions-d38-d39-report.md and
docs/audits/2026-09-19-decisions-d35-d37-report.md were read and followed; index rows were kept to about
the length of the rows shortened in 4114474. Em dashes avoided, as in every earlier filing.
