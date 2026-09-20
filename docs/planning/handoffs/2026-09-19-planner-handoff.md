# Hand-off to the next planner

Written 2026-09-19 (PDT) by the planning session that ran that day.
Project: forager-forecast. Repo: slayer8366/forager-forecast.

## Read this first

You have not read the repo and you probably cannot. Every repo fact below was relayed by an agent and
pasted by the owner. Treat each hash and path as a claim to be re-checked, not as knowledge. The planning
doc's Decision log, Spec and Data register are copies. Where a copy and the repo disagree, the repo wins,
and the copy gets an appended correction rather than an edit.

Working rules that held all day and are worth keeping: append and never overwrite, mark every fact with
how it was known, and send a read-only pulse before writing a plan that depends on repo state.

## State, as of 2026-09-19 about 22:00 PDT

Relayed from two independent read-only state checks that agreed.

- main is 3625a55. DECISIONS.md runs D1 to D37 with no gaps, at docs/planning/DECISIONS.md.
- SPEC.md carries thirteen bullets added since the sync: ten from the spec-sync dispatch and three
  corrections from its amendment. Zero deleted lines.
- The audit index is at 21 data rows.
- Eleven branches merged. Four unmerged, and they are exactly the work the D32 merge pass must land:
  t1-calendar-smoke-test 9f6c132, t1-credentialed-run-review e9fbdf5, t2-record-audit 4b22c8d,
  t2-credentialed-run-review 9491ace.
- D38 exists only in the planning doc. It is in no repo file.
- The two Cowork credential reports are outside the repo, held for the D36 ruling.

## What is waiting on the owner, and nothing moves until it lands

**D36** (proposed). Secrets never appear in reports, commits, logs or chat; account identifiers may,
where the report says which account they name; a committed secret is rotated at once and annotated, never
edited out. Version 1 said "reports never carry credential values", which three existing reports already
broke. Version 3 added the rotation clause.

**D38** (proposed). Ownership under D35 is a role tied to the machine holding the credentials and the
archive, not to a chat session, so a restart does not orphan a branch. Document-only commits may be
assigned elsewhere by the owner, recorded in that report.

**Rule D36 before the merge pass, not after.** The GBIF_USER value sits at line 52 of the T1 run report
and line 157 of the T1 independent review, on unmerged branches, on no commit reachable from main. Before
the merge it is a file edit. After the merge it is a history rewrite. That is the only irreversible
ordering in the current queue.

## The dispatch that is drafted and not sent

2026-09-19-d32-merge-pass-stage-1.md. It stops unless both rulings are quoted from DECISIONS.md first.
Four parts: the two self-check renames under D35 and D38; applying D36 to the two occurrences; appended
corrections for two findings, including a T2 by-licence roll-up at line 318 that over-counts by 153
records; and an inventory that makes stage 2 writable.

Stage 2 is deliberately unwritten. The code move, the one-line folds from D25 to D31, and the two merges
all depend on results that do not exist yet.

## Open work, none of it blocking the merge pass

- A register row for the Copernicus store, with the four dataset ids, each licence field, and the
  attribution wording under "Citation and attribution", which nobody has copied. CC BY requires it.
- D24's remaining verify-first items: the precipitation accumulation convention and UTC day boundaries.
- The equivalence test against pinned Open-Meteo requests. It gates any fit. Fold in one expectation: an
  open issue in the open-meteo repository reports elevation=nan returning an elevation of 0 rather than
  the grid-cell height, and if the API treats nan as sea level the test will show a systematic offset in
  the mountainous boxes.
- The D26 geometry redo, with the record-key reconciliation against T1's first CSV download.
- The D28 day-of-month table by dataset, which the owner rules on before any fit.
- The D29 dataset list and by-licence counts filed beside each DOI.
- The seed 20260918 and the 20-configuration tuning grid committed before any candidate is seen.
- A new pinned verify script to replace the frozen T0b one.

## Things that cost time today, so you do not pay again

- **Code blocks vanish in the relay.** Five sends arrived empty: a table header, a commit list, and the
  D25 parameter names three times. Ask for values inside an ordinary sentence, and for an underscore
  spelled out in words.
- **Say what one unit of a count is a unit of.** "Eight commits" meant commits whose tree contains a
  value, of which two introduced it. The agents now do this unprompted and it has caught real ambiguity.
- **A relayed state is true when written and stale when you act on it.** Ask reports to carry their read
  time. One report described a branch as unmerged that had merged before the reply was written.
- **Do not fold a decision's substance into a citation.** A bullet that said a licence was CC BY 4.0 and
  cited D24 put a from-memory fact into the spec as established. The reviewer caught it. That was a
  planner error, not a builder one, and the fix was a correction beneath the wrong line.

## Facts worth having in hand

- The two D25 parameters are elevation set to nan and cell_selection set to nearest. Both were checked
  against Open-Meteo's documentation and do what D25 claims.
- The GBIF account is a test account. Every download is redone under a business account later, DOIs stay
  provisional, and record counts are not pinned in tests.
- The Copernicus licence field reads "CC-BY licence" on all four datasets and names no version. 4.0 is
  observed on ERA5-Land's pop-up and inferred for the other three.
- Whether the Copernicus account is a test account has been asked twice and never answered.

## First thing to do

Send a read-only pulse before writing anything. Ask for origin/main, the highest D row, whether D36 and
D38 have been ruled, and the four unmerged branch heads. If the rulings have landed, the stage 1 dispatch
is ready to hand over. If they have not, the queue has not moved and the owner is the blocker.

## Corrections appended 2026-09-19 about 23:15 PDT

Appended by the next planning session. Nothing above is edited. Every repo fact below was relayed by the agent on the credentials machine, read between 22:37 and 23:04 PDT, and has not been read directly by a planner.

- **D36 summary above is wrong.** Version 3 does not add rotation at once. Its closing clause, quoted from line 9 of DECISIONS.md on main 3625a55: "A secret already committed is not edited out. A dated note is appended saying where it is, and the release checklist carries the account swap and a history check."
- **"Rule D36 before the merge pass" and "the only irreversible ordering" are superseded.** The value at the named lines matches GBIF_USER, a username, which D36 treats as an account identifier. D36 also forbids editing a committed secret out, so merge order never changes the remedy.
- **"Two occurrences" miscounts.** The value sits in three (branch, file) pairs across two documents: the T1 run report on both T1 branches, and the independent review on t1-credentialed-run-review.
- **The line 157 occurrence is in the review of record,** which the do-not-touch list protects. The review also cites line 58 for the fix; the value has been at line 52 in all eight commits that contain it. Recorded as a planning note only. The review stays untouched.
- **"The dispatch that is drafted and not sent":** it reached the agent, who stopped at the preconditions.
- **Post-review commits:** two on T1 (64146f7, 9f6c132) and one on T2 (4b22c8d). 9f6c132 is cosmetic; the net diff from 691bef3 leaves t1_count_table.py unchanged. What remains unreviewed is the gbif_download.py docstring and the 65-line T2 tally script.
- **"One-line folds from D25 to D31" is wrong.** On T2, D26 needs a new download and D27 needs taxon added to the duplicate key in records/filters.py. D30's verify script is a separate build on neither branch. D28 and D29 are token probes only.
- **Stage 2 inputs now exist.** Part D ran read-only: records.py is shadowed by the records package in the merged tree; gbif_download.py exists twice as two live modules; the add/add conflicts are the D35 collision, which Part A's renames clear.
- **D38 is no longer planning-doc only.** D38 and D39 (the ruling on D36) are filed at dcc3a76 on branch decisions-d38-d39, off 3625a55, not yet merged. The Reason, Alternatives considered and Supersedes columns were transcribed by the agent from planner chat and need owner review before merge.
- **Revised stage 1:** Parts A and C, with the session on the credentials machine named as writer. Part B is dropped under D39.
- **Unanswered, third time:** whether the Copernicus account is a test account.

## Correction appended 2026-09-19, after the section above

- **"Unanswered, third time" above is wrong.** Corrected by the owner. The only count on record is this handoff's own "asked twice and never answered", from the prior session. This session listed the question as an owner item but never put it to the owner as a question, so it added no ask. The question is still open.
