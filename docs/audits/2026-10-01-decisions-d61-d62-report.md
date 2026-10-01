# D61 and D62 filed: Forager is not sold, the full model ships, the repository opens up

**Date:** 2026-10-01.
**Type:** filing report. The rulings were given in chat by the owner, in the Forager planner session; no
dispatch file exists for them and none is filed here.
**Base:** main 876156b6dea613e95730f41e3e5f870aecdd5995, on branch decisions-d61-d62. One commit: the two
rows, three dated notes in the release checklist, this report, one index row and one session-log row.
**Supersedes:** none in docs/audits. The rows' own Supersedes cells say what they replace in the log.

Every claim names a commit, a file and line, or a command whose output was read, or is marked inferred.
Observed means this session ran the command; read means a file was opened. State claims were read
between 16:40 and 17:00 PDT on 2026-10-01 (23:40 to 24:00 UTC).

## What was filed

- **D61.** Forager will not be sold, and the forecast it ships is the full model, on records of every
  licence. D29's gate is answered. D29's two-track analysis stands. D48's exclusion no longer decides
  what ships.
- **D62.** The repository is to become public. The row records the ruling and does not carry it out.
- **Release checklist.** A dated note under item 6 (the ruling exists), under item 5 (the licence is
  still not chosen) and under item 3 (the history check comes before the visibility change, as a
  reading open to correction). No item was added, edited or removed.

## The owner's words, and how each is known

All times are 2026-10-01.

1. 15:37 PDT (22:37 UTC): "Actually we are switching to the non-commercial model. I can't find a way to
   charge for this app and get what I'm looking for out of it. So let's proceed with the open source
   model". Read from the transcript of the earlier Forager planner session on this machine, not heard by
   the session writing this report.
2. The planner's four questions in reply, read from the same transcript: which forecast model ships (A
   the full model using all records, B keep the commercial-safe one); whether "open source" means
   licensing the app's code; "Does the forecast repo open up too? It is private with no licence today.";
   whether there is any plan to take donations.
3. 16:43 PDT (23:43 UTC), given to this session: "1 A, full model", "2 No, just keeping no proprietary
   software", "3 yes", "4 I'm considering donations and research grants for cost upkeep".
4. 16:48 PDT (23:48 UTC), given to this session, after it read answer 2 back and asked whether to write
   the superseding entries in both repositories: "1 Yes", "2 stops at what's in the app, but my goal is
   to use open source databases and projects for my app. I just won't explicitly mention that unless
   asked", "3 go ahead and write them".

Answers 2 in both messages are about Forager's own code and what is inside the app. Under D59 they are
Forager's, and they are recorded in Forager's RECORD.md decision 2026-09-28-397 (slayer8366/Forager,
branch records-noncommercial-ruling at 85b12b5), not ruled here.

## Verify first

1. **Main.** Observed. `git fetch origin` in the clone; origin/main is 876156b. `git branch -r
   --no-merged origin/main` printed nothing, so no pushed branch held a row above D60.
2. **Highest D.** Read. D60 at line 8 of docs/planning/DECISIONS.md at 876156b; the IDs run D60 to D1
   with none missing. D61 and D62 were free.
3. **Row shape.** Observed. `awk -F'|' '/^\| D/ && NF!=8'` printed no rows before the edit and none
   after it.
4. **Date convention.** Rows are dated local Pacific (docs/audits/2026-09-19-decisions-d38-d39-report.md,
   "Date convention"). The local date when written was 2026-10-01.
5. **The rows quoted.** Read in full at 876156b: D29 (line 39), D22 (line 46), D48 (line 20), D17 and D36.
   The wording D61 and D62 quote from them was copied from those lines.
6. **The ruling of 2026-09-28 was never filed here.** Observed. No row above D60 exists, and
   `git grep -n -i -E "commercial-safe|selling the app|open-meteo subscription" origin/main -- docs`
   finds the phrase only in D29, D33 and reports older than 2026-09-28. The handoff that carried it is
   slayer8366/Forager prompts/preserved/2026-09-28-08.md, read there. It is not filed in this
   repository by this commit.
7. **Visibility and licence today.** Observed with `gh repo view`: slayer8366/forager-forecast is
   PRIVATE with no licence; slayer8366/Forager is PUBLIC with no licence.
8. **An email address in a filed report.** Observed by a count, the value not printed:
   docs/planning/evidence/cds-credentials-report.md line 37 contains an "@". D36's Reason names that
   report and two others as carrying account identifiers.

## What was not done

- **The repository was not made public.** D62 says why it waits.
- **No history check was run** (release checklist item 3).
- **SPEC.md was not touched.** Its open question at lines 123 to 126 and its FABDEM line (85) still read
  as before D61. A sync needs its own dispatch, as D24 to D34 had.
- **START_HERE.md and TASKS.md** were not changed beyond one session-log row.
- **The 2026-09-28 handoff was not filed** under docs/planning/handoffs/. D61 quotes its ruling and
  names where it lives.
- **Nothing was merged.** Under D40 the merge into main needs the owner's written authorisation naming
  the branch decisions-d61-d62.

## Inferred, and open to correction

- That "open up" in the planner's third question, and the owner's "yes", mean the repository becomes
  public on GitHub. The question's own second sentence, "It is private with no licence today", is the
  basis.
- That the history check belongs before the visibility change. D36 puts it before release; a public
  repository exposes every commit on every ref, whether or not anything has been released.
- That D48's per-record licence field is still worth filing once its exclusion no longer applies.
  Attribution under CC BY and CC BY-NC needs to know which records carry which licence.

## Not legal advice

Whether a free app that takes donations or research grants stays non-commercial under CC BY-NC 4.0, and
under Open-Meteo's free terms, was not checked with anyone able to answer it. D61 says so in its own
Decision cell.
