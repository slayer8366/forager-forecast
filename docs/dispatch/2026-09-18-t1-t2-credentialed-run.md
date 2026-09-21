# T1 and T2 follow-up: read Cowork's GBIF report, prove the credentials, pull records, count, stop

## State this was written against

- Written 2026-09-18 by Claude in the planning chat. forager-forecast main at f96d557, with branches
  t1-calendar-smoke-test and t2-record-audit holding verify-first work, prepared code and the fixed
  download predicate. Agent-reported. Claude has not read the repo.
- Cowork reports that a GBIF account exists and that its credentials are stored on this machine. Its
  report, gbif-credentials-report.md, is said to sit in the owner's Labs folder next to a script.
  Neither Claude nor the owner has read that report.
- The dispatch Cowork worked from set ~/.config/forager-forecast/gbif.env with GBIF_USER, GBIF_PWD and
  GBIF_EMAIL. Cowork reports four differences from that dispatch. Claude does not know what they are.
- From memory, not checked: GBIF limits how many downloads one account may run at the same time.

Scope: find and read the report, prove the credentials, request the downloads, produce the count
tables, then stop. No model is fit in this run.

## Verify first, and report before requesting any download

1. Find the report (for example: find ~ -name gbif-credentials-report.md). Read all of it. In your own
   report, list its four differences from the dispatch and its unchecked items. Where the report and
   this dispatch disagree about where credentials live or how to load them, follow the report and say so.
2. Confirm the credentials file exists, sits outside every repo and worktree, has mode 600, and defines
   the three names. Do not print any value.
3. Make one authenticated request and report its status code. The password must not appear in the
   command you show.
4. Does the report call this a test account? If yes, apply its rules in full: store the query next to
   each DOI, mark those DOIs as provisional, and pin no record counts in any test.

## Then do

- T1: submit the download using the predicate already fixed on the branch. Do not change it now. Keep
  the license field. Produce the counts table by box, year and filter step, and a second table by
  license. Confirm or disprove: "each box has at least 1,000 usable Cantharellus records across at least
  8 years." Report and stop. Modelling waits for the owner.
- T2: reuse T1's download where the predicate allows it, otherwise request its own. Produce the count
  tables, including by license, and the seeded 200-record hand-check CSV.
- Request downloads one at a time unless you have confirmed the account's limit.
- Downloads go under the ignored data folder. Each DOI is recorded with its query.

## Do not touch

- The password is never printed, logged, committed or pasted into a report. Do not echo the environment.
- No substitute for GBIF downloads: not the search API, not the iNaturalist API (Spec, Constraints).
- The predicate, boxes, year range and window list. They were fixed before any counts were seen.
- DECISIONS.md rows, Fixed terms, SPEC requirements. No data in git.

## Evidence to return

- Each DOI with its stored query, marked provisional if the account is a test account.
- The count tables, the verdict on the 1,000-record premise, and the large-file guard result.
- A Conventions line, and what you did not check. A second agent reviews each report before anything
  that depends on it starts.

## Person only

- The owner answers Cowork's two open points: which email the account uses, and whether sign-up showed
  a CAPTCHA and a terms checkbox.
- The T2 photo hand check.

**Filed to a branch off main, 2026-09-20.** This dispatch had existed only on the two task
branches, t1-calendar-smoke-test and t2-record-audit, byte-identical on both (blob 9ceb685). It is now
filed at docs/dispatch/2026-09-18-t1-t2-credentialed-run.md on branch d32-stage-1-records, by commit
84edf09, with its index row. That branch is pending the owner's merge, so the dispatch is not yet on
main. Nothing in this file is edited.

**Correction 2026-09-20 to the note above.** The sentence "That branch is pending the owner's merge, so the dispatch is not yet on main" is superseded. Branch d32-stage-1-records was merged into main by 1d27f08, so this dispatch is now filed on main at docs/dispatch/2026-09-18-t1-t2-credentialed-run.md. The note above is left exactly as written.
