# D40 to D43 filed, the two README homes corrected, and the release checklist created

**Date:** 2026-09-20.
**Type:** filing report for docs/dispatch/2026-09-20-file-d40-to-d43-rev3.md.
**Base:** docs-homes-handoffs-dispatches at 2dd4930, off main 1d27f08.
**Supersedes:** nothing. Revisions 1 and 2 of the dispatch were stopped before committing and are not
filed; see "Decisions taken here".
**Read time:** 2026-09-20 20:39 PDT for the branch tips, re-read before commit.

## What landed

| File | Change |
|---|---|
| `docs/planning/DECISIONS.md` | D43, D42, D41, D40 inserted under the table header in the file's newest-first order, verbatim from the dispatch |
| `docs/planning/handoffs/README.md` | line 15 replaced |
| `docs/dispatch/README.md` | lines 28 to 29 replaced; one sentence added under naming |
| `docs/planning/RELEASE_CHECKLIST.md` | created, seven items, each with its source |
| `docs/dispatch/2026-09-20-file-d40-to-d43-rev3.md` | the dispatch, byte-identical to the upload |
| `docs/audits/README.md` | three index rows |
| this report | |

## The four rows

Filed exactly as written. Each has eight pipe-separated fields, matching the six-column header, checked
before insertion. Stripping the four inserted lines restores the base byte for byte, so D1 to D39 are
unchanged. 39 rows before, 43 after.

## The two README replacements, as edits before review

These are **edits before review, not changes to the record.** The branch is unmerged and neither README
has been reviewed or reached main, so replacing a sentence in either is correcting a draft, not
rewriting a filed document.

- `docs/planning/handoffs/README.md` line 15. Old: "- **Filed as received, byte-identical**, like a
  dispatch, and verified the same way." New: "- **Filed as received.** The file is byte-identical to
  what was received at the moment it is filed, verified with `cmp`, and afterwards changes only by
  appended corrections." Why: the old line stated, nearly word for word, the alternative D41 names and
  rejects, "Filing handoffs byte-identical like dispatches", and it was inconsistent with the same file's
  line 17.
- `docs/dispatch/README.md` lines 28 to 29. Old: "This split was the owner's ruling of 2026-09-20; the
  decision row for it is still to be written." New: "This split is ruled in D41." Why: filing D41 in the
  same commit would have made the old sentence false.

Both replacements are the wording this session proposed at 2026-09-20 20:12 PDT, which the dispatch
authorises verbatim. One rendering note: the dispatch's copy of the first replacement reads "verified
with cmp", without code formatting around `cmp`. The proposal had it, and the rest of both READMEs format
command names that way, so it is filed with the formatting. The words are identical.

**Re-read against D41 after both edits: clean.** Every rule-bearing sentence in both files is either stated
in D41 outright (locations, the index row, `YYYY-MM-DD-<slug>.md` naming for the day written,
byte-identical dispatches, corrections as separate files, the closeout exception, handoff corrections
appended with who and how) or falls under D41's closing sentence, "The README in each folder states the
detail" (filing the corrected dispatch too, no second index, treating a handoff's repository facts as
premises to re-check, the fixed `planner-handoff` slug). Nothing contradicts it.

## The relay suffix

One sentence added to `docs/dispatch/README.md` under naming: a dispatch is filed under the name its
writer gave it, and a suffix added by the upload or relay, such as `-1`, is dropped and noted in the
index row.

**Recorded here, as the dispatch asks:** `docs/dispatch/2026-09-20-stage-1-step-1-unblock.md` arrived as
`...-stage-1-step-1-unblock-1.md` and was filed under the writer's name, without the `-1`. Its content is
byte-identical to the upload; only the filename differs, and that difference was not noted in its index
row at the time, because the rule did not yet exist.

## The release checklist

`docs/planning/RELEASE_CHECKLIST.md` implements D36's clause "the release checklist carries the account
swap and a history check", so it needed no new ruling. Its header states it is append-only in the same
way as DECISIONS.md, and that an item is ticked with a dated line naming the commit or report that did
it. Seven items, each naming its source, and none without one:

1. Swap GBIF to the business account and redo every download. Source: D36; the GBIF report, lines 20
   and 71.
2. Swap the Copernicus account to a business login; re-running stored ERA5 requests is optional. Source:
   D36; D43.
3. History check of every commit reachable from any ref, for every secret of old and new accounts, with
   a positive control. Source: D36.
4. Copy the Copernicus "Citation and attribution" wording, and confirm the licence version on the three
   datasets where 4.0 is inferred. Source: the CDS report, lines 23 to 24 and 55 to 58.
5. Choose the project's licence. Source: D22.
6. Obtain the commercial-use ruling, and until then confirm nothing CC BY-NC-derived ships. Source: D29;
   D22.
7. Verify every shipping ecoregion has a filed held-out evaluation beating the calendar baseline, stated
   as a verification of a standing rule, not a new gate. Source: D5.

The dispatch gave the two evidence-file sources as "This is a test account", "Moving to the business
account later" and "the licence bullets". Line numbers were added beside each, read from the filed files,
so each source can be checked without searching. The wording is otherwise as given.

**No further release gate found while writing it.** The dispatch asked not to repeat the row search; no
row outside D5, D22, D29, D36 and D43 came up in the course of writing the items.

## Decisions taken here, and what was rejected

- **Revisions 1 and 2 of the dispatch are not filed.** Both were stopped at their item 2 before any
  commit, so neither was acted on. Under D41 as now filed, a dispatch closed without being acted on
  carries a dated closeout note; filing them would mean filing two unactioned dispatches with notes. The
  dispatch asks only that this revision be filed, and the precedent of 2026-09-20's stage 1 amendment,
  whose revision 1 was likewise stopped and never filed, points the same way. Rejected: filing both with
  closeout notes, which is beyond the dispatch's scope. Recorded as an owner item, because revision 3's
  opening line refers to both and neither is in the repository.
- **Numbered checklist items.** Each item carries a stable number, so a tick line can name the item it
  ticks. Append-only means new items take the next number and no number is reused.

## Owner items

- Authorise the merge of docs-homes-handoffs-dispatches into main under D40, naming the branch.
- Whether revisions 1 and 2 of this dispatch should be filed with closeout notes under D41.

## Not checked

- CI on this branch (documents only).
- That every item on the checklist is complete. It carries what its sources set, and D5, D22, D29, D36
  and D43 are the rows found; a release gate set somewhere other than DECISIONS.md or a filed report
  would not be on it.

Conventions: the filing form of docs/audits/2026-09-19-decisions-d38-d39-report.md was followed; index
rows were kept to about the length of the rows shortened at 4114474. Em dashes avoided.
