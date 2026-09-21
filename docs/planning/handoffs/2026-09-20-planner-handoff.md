# Hand-off to the next planner

Written 2026-09-20 (PDT) by the planning session that ran that day, after the report read at 23:34 PDT.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

## Read this first

You have not read the repo. Every repo fact below was relayed by the coder on the credentials machine and pasted by the owner. Treat each hash, path and count as a premise to re-check. Where a copy and the repo disagree, the repo wins, and this file gets an appended correction, never an edit (D41).

Working rules that held: send a read-only pulse before writing a plan that depends on repo state; date a dispatch by the report it answers, not by a clock you do not have; put everything meant for the coder in a file, and keep chat for the owner; quote a row before ruling on it, and never restate one from a summary.

## State, as of 2026-09-20 23:34 PDT

- main is 228fc20. DECISIONS.md runs D1 to D54 with no gaps. D54 is the highest row.
- Every remote branch is merged into main, including the four task and review branches. The D32 merge pass is complete: T2 landed at bc7863a, T1 at 42f0743, the move's review of record at 47204f7.
- The audits index is at 73 data rows.
- Homes exist and are ruled (D41): dispatches in docs/dispatch/, handoffs in docs/planning/handoffs/, evidence in docs/planning/evidence/. A release checklist exists at docs/planning/RELEASE_CHECKLIST.md with seven items, none ticked.
- The coder session on the credentials machine is the writer for every task branch (D38). Merges to main happen only on the owner's written authorisation naming the branch (D40); the merge commit message is the record (D50).

## What was ruled today, one line each

D38 ownership by machine, one writer per branch. D39 accepts D36 as written; "says which account it names" is a whole-document property. D40 merges need written authorisation naming the branch. D41 document homes and correction rules. D42 how the T1 code move is done; two Record types coexist until the follow-up task. D43 the Copernicus account is a test account, swapped at release. D44 only two D25 to D31 items were one-line folds; the rest are tasks. D45 corrects D42: carry T2's DWCA request template, not its continent predicate. D46 nearest-point cell assignment. D47 geometry is the United States and Canada; Mexico is out. D48 licence filtering is per record. D49 coder handoffs beside planner handoffs. D50 a merge commit message is the merge's report. D51 corrects D46's method: confirm grid points from delivered data. D52 every pull records request time and account, and pins the UTC day. D53 attribution wording, with the four page defects and how each is filled. D54 precipitation from ERA5 at 0.25° as the store's daily sum, temperature and soil from ERA5-Land at 0.1°, matched to each grid separately.

## What is next, in order

1. **The D32 follow-up task.** Unify the two filter pipelines and choose one Record type. Its verify-first inputs are in docs/audits/2026-09-20-d32-stage-2b-report.md. Add: the nearest-point check under D51 now runs against two grids, 0.1° and 0.25°, each from its delivered coordinates; ERA5 delivers longitudes in 0 to 360, and T1's cell code uses −180 to 180 (planner research note, filed); the two request builders SIMPLE_CSV and DWCA, one to retire when D26's download is designed; the move commit understated file-relative paths by two, tests/test_large_file_guard.py line 14 and two frozen pack scripts, both unaffected. This task needs its own independent review (D18).
2. **D26's download**, geometry-selected, United States and Canada (D47), using the unified gbif_download with a new geometry predicate passed to request_template. Then D27 in full (taxon in the key is folded; the rest is not), D28's day-of-month table, D29's dataset list per DOI, in that order, since each waits on D26's data.
3. **D30's new verify script and D31's seed and grid.** The grid contents are an unmade decision; it needs a proposal before the owner can rule.
4. **The equivalence test** (D24). Its precipitation comparison is now defined by D54: the store's daily sum against Open-Meteo's precipitation_sum, both UTC. Its temperature and soil comparison waits on the follow-up task's grid check. The handoff of 2026-09-19 records an open Open-Meteo issue on elevation=nan; the test should look for that offset in mountainous boxes.

## Waiting on the owner

- The project licence (D22) and the commercial-use ruling (D29). Both are release checklist items and neither is urgent tonight.
- D28's day-of-month table, once D26's data exists.
- D31's tuning grid, once proposed.

## Things that cost time today, so you do not pay again

- **Restating a row from a summary put a false clause into a draft ruling.** D36's rotation clause was paraphrased from the handoff and was wrong. Quote the row.
- **A stop condition written loosely stopped the right work.** "Any credential value" blocked filing the very reports D36 cites; the rule meant "any secret". Say which.
- **A count without its unit was wrong twice.** "Asked three times" and "thirteen branches". State the unit and the test.
- **Two dispatches crossed with events.** A "state has moved" clause now says what to do when the state moved forward: carry on and say so.
- **The planner has no clock.** Every "about HH:MM" it wrote was a guess. Date by the report read.
- **A gate on one cell missed the reason in another.** D19's Decision cell only names the source; its Reason and Alternatives rejected the planner's draft by name. Gate on the whole row.
- **Code blocks and inline code vanish in the relay.** Quote in sentences.

## Facts worth having in hand

- The GBIF account is a test account; every download is redone under a business account; DOIs stay provisional; record counts are not pinned in tests. The Copernicus account is the same (D43); ERA5 pulls need no redo.
- CC BY 4.0 is observed on all four Copernicus datasets. The attribution wording is filed in Cowork's report in docs/planning/evidence/, with four page defects and D53's handling of each.
- The ERA5-Land daily-statistics product omits accumulated variables; that is why D54 takes rain from ERA5 single levels.
- The store's daily statistics are computed at request time from whatever hourly data exists; two pulls of one request can differ. D52 records the request time for that reason.
- No climate data has been pulled by project code on any branch. The only store request ever made was Cowork's deleted 25 KB proof.

## First thing to do

Send a read-only pulse: origin/main, the highest D row, and whether any branch exists besides main. If main is 228fc20 and D54 is highest, write the follow-up task's dispatch from the stage 2b report's inputs and the additions above. If anything differs, the owner or the coder has moved since this was written, and this file gets a correction before anything else.
