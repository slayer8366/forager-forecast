# Handoff to the next coder

Written 2026-09-20 about 21:10 PDT by the coder session that ran from 2026-09-19 to 2026-09-20 on the
machine holding the project credentials and the archive. The owner paused the session to wrap up.

**Every repository fact below was read at 2026-09-20 21:08 PDT and is a claim about the past.** Fetch and
re-check before acting on any hash, path or count. Where this file and the repository disagree, the
repository wins, and this file takes an appended correction under D41.

## Read this first

- **One repository: slayer8366/forager-forecast.** Nothing here concerns the Forager app repo. A session
  may start in a Forager worktree as its default directory; use explicit paths into the forecast clones.
- **You are the writer under D38** if you run on this machine (main, DECISIONS.md line 9). One session
  writes to a branch at a time; when more than one runs, the dispatch names the writer.
- **Never merge into main without the owner's written authorisation naming the branch.** That is D40. It
  is filed on docs-homes-handoffs-dispatches and not yet on main, but the owner has ruled it; follow it.
  The merge report records the authorisation's wording and time.
- **Every dispatch opens with a state clause.** Sideways movement (the expected commit is not an
  ancestor of the new tip) means stop and report. Forward movement means carry on and say so.
- **Put the read time at the top of every report.**

## The machine

| What | Where |
|---|---|
| Working clone | `~/Zynergy/forager-forecast-t0b`, with `core.hooksPath=.githooks` so the large-file guard runs on commit |
| Task and review worktrees | `~/Zynergy/forager-forecast-t1-calendar-smoke-test`, `-t1-run-review`, `-t2-record-audit`, `-t2-run-review`, `-t3-verify-data-layers`. These are **worktrees of the t0b clone**, not separate clones (`git worktree list`) |
| Another session's clone | `~/Zynergy/forager-forecast`, on review-protocol. Do not write there |
| GBIF credentials | `~/.config/forager-forecast/gbif.env`: `GBIF_USER`, `GBIF_PWD`, `GBIF_EMAIL`. Load by sourcing. Never print a value |
| Copernicus credentials | `~/.cdsapirc`: `url` (public endpoint) and `key` (a secret, a 36-character token). Never print |
| Archive | the gitignored `data/` under the T1 worktree (158M) and the T2 worktree (1.4G) |
| Python | `uv` at `~/.local/bin/uv`, `pixi` at `~/.pixi/bin/pixi`. The project pins `requires-python = "==3.14.*"` and ruff `target-version = "py314"` |

**The git identity is shared.** Owner commits and agent commits carry the same author. Only the
`Co-Authored-By` trailer tells them apart, and only on agent commits.

## State at 21:08 PDT

| Branch | Tip | State |
|---|---|---|
| main | 1d27f08 | highest row D39 |
| docs-homes-handoffs-dispatches | b888c4a before this commit | unmerged; carries D40 to D43, the two README homes, docs/planning/RELEASE_CHECKLIST.md; merges clean into main |
| t1-calendar-smoke-test | 163950e | unmerged; stage 1 Parts A and C done, review of record merged in |
| t2-record-audit | 932b9c9 | unmerged; same |
| t1-credentialed-run-review | e9fbdf5 | unmerged, untouched; review of record |
| t2-credentialed-run-review | 9491ace | unmerged, untouched; review of record |

Twelve other branches are fully merged into main (test: `git merge-base --is-ancestor B origin/main`).
Every worktree was clean with nothing unpushed.

## Waiting on the owner

1. **Written authorisation to merge docs-homes-handoffs-dispatches.** Until it lands, **D40 to D43 are not
   on main**, including D42, which is the authority stage 2b runs on.
2. **A ruling on the D25 to D31 folds.** D32, accepted by D34, calls them "one-line changes". Several are
   not. The owner rules before stage 2b; the next dispatch gathers the facts for it.

## The next dispatch: received, paused, not started

`2026-09-20-cleanup-and-d24-d31-status.md`, at
`~/.claude/uploads/d15fa33b-c0a9-50f3-9485-298cc1ad5030/023f43ea-2026-09-20-cleanup-and-d24-d31-status.md`.
The owner paused the session before any step of it ran. It expects docs-homes-handoffs-dispatches at
b888c4a; this handoff's commit moves that branch forward, which its state clause allows.

Its Part 1 asks you to file three stopped revisions with closeout notes under D41. **This session received
all three**, and they are on disk:

- D40 to D43 filing dispatch, revision 1: `…/7eb4a741-2026-09-20-file-d40-to-d43.md`. Stopped at item 2:
  D41 as worded forbade the handoff corrections the handoffs README describes. Superseded by revision 2.
- D40 to D43 filing dispatch, revision 2: `…/625c003b-2026-09-20-file-d40-to-d43-rev2.md`. Stopped at item
  2: handoffs/README.md line 15 stated the alternative D41 rejects, and dispatch/README.md said D41 was
  still to be written. Superseded by revision 3, filed at b888c4a.
- Stage 1 amendment, revision 1: `…/7b503b0d-2026-09-20-d32-merge-pass-stage-1-amendment.md`. Stopped at
  its precondition 1: D38 and D39 were not yet on main. Superseded by revision 2, filed on main.

(`…` is `~/.claude/uploads/d15fa33b-c0a9-50f3-9485-298cc1ad5030`.) Drop the eight-character hex prefix
when filing. Its Part 2 is read-only: the status of D24's verify-first items and D25 to D31 per branch.

## What stage 2b needs to know

All filed on main at `docs/audits/2026-09-20-d32-stage-1-part-d-report.md` unless marked otherwise.

- **`Record` is a different type on each branch.** T1's `src/forager_forecast/records.py` defines a frozen
  dataclass; T2's `src/forager_forecast/records/filters.py` declares `Record = Mapping[str, str]`.
  `FilterStep` exists in both with different meanings. D42 keeps both until D32's follow-up task.
- **`records.py` is shadowed** by the `records/` package in any merged tree; the package wins.
- **The two `gbif_download.py` files are independent implementations**, not copies: +97/-98 over 125 and
  124 lines, sharing only `credentials_from_env`, and that with different bodies. **Neither has a
  production importer**; each is imported only by its own test. D42 unifies them with T1's as base and
  T2's predicate and request-template functions carried over. Only T1's `submit_download_request` has run
  against GBIF.
- **Imports the move breaks**: `scripts/t1_count_table.py:25`, `scripts/t1_render_tables.py:19`,
  `src/forager_forecast/cell_weeks.py:15`, `src/forager_forecast/simple_csv.py:26`,
  `tests/test_cell_weeks.py:13`, `tests/test_records.py:3`, `tests/test_records_observed.py:5`,
  `tests/test_simple_csv.py:8`, `tests/test_gbif_download.py:5`. Read at 19:47 PDT, not in the Part D
  report.
- **Conflicts, main into each task branch**: `docs/audits/README.md`,
  `docs/dispatch/2026-09-18-t1-t2-credentialed-run.md` (add/add), `docs/planning/START_HERE.md`; T2 also
  `docs/planning/TASKS.md`.
  - The dispatch add/add: each task branch's copy is main's copy plus two appended notes, a byte-exact
    superset, so take the task side.
  - START_HERE.md: both sides only add rows. Keep all.
  - **TASKS.md: both sides changed the same rows, and taking either side loses a true status.** Take T2's
    status from the branch and T3's from main.
  - README.md: keep every row. Assert the result equals the union of both sides.
- **Review scope**: D42 has the move's independent review also cover 64146f7 (a docstring) and 4b22c8d (a
  65-line tally script), which settles whether D18's "every task" reaches post-review commits.

## Practices that saved or cost time

- **D32's own row still opens "Proposed."** It was accepted by D34 at line 13. Quote them together.
- **Run a positive control before trusting a negative scan.** Every credential scan this session first
  found a known value.
- **Leak-scan staged files** against both credential files before any commit that files a report or
  evidence. Usernames and emails are permitted identifiers under D36 and D39; passwords and keys are not.
- **Say what one unit of a count is.** This session reported thirteen merged branches when there were
  twelve, by counting `refs/remotes/origin/HEAD` as a branch.
- **Code formatting vanishes in the relay.** Ask for values in plain sentences.
- **Write convention documents after the row that rules them.** Both README stops on 2026-09-20 came from
  README text written before D41 existed.

## Not verified by this session

- No test suite was run. No `uv sync` was done. CI was not checked on any branch.
- D28 and D29 were only probed for tokens, never read as implemented.
- Whether any Open-Meteo equivalence test exists. That is item 8 of the next dispatch.
- The Copernicus register row is not written. Most of its content is in
  `docs/planning/evidence/cds-credentials-report.md`; the "Citation and attribution" wording is not.

## Correction 2026-09-20, appended by the coder session that wrote this file

**This file's location is provisional. Designating its home is your first task.** The owner's words, given
in chat at about 21:15 PDT and relayed to this session, not read from any file: "That's fine. Have the
next coder designate a new spot for it. This is your workspace so I'll allow you to choose the most
convenient pathway."

What prompted it: this is a coder-to-coder handoff, and `docs/planning/handoffs/README.md` and D41 cover
planning handoffs, written planner to planner. The owner has delegated the choice of a home for coder
handoffs to the coders.

What that means for you:

- Choose the home. The owner's delegation is the authority; quote it when you record the choice.
- Move this file there with `git mv`, so its history follows, and give it a README or a sentence in an
  existing one saying what lives there, in the style of the two README homes.
- Record the move with a new row in `docs/audits/README.md`. Keep every existing row. Whether the old row
  is repointed, as the stage 1 self-check renames were, is your call; say which you did.
- Nothing above this correction changes.

A suggestion, not a choice: `docs/planning/handoffs/coder/`. It keeps every handoff under one folder that
the existing README can cover with one added sentence, and a later reader looking for handoffs finds both
kinds in one place. A top-level `docs/handoffs/` is the alternative if coder handoffs should sit apart
from planning.
