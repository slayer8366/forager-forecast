# Release checklist

Append-only, in the same way as DECISIONS.md: no line is edited or removed after the day it is written.
An item is ticked by adding a dated line beneath it naming the commit or report that did it. A new item
is added with its source, and nothing goes on this list without one.

This file implements D36's clause "the release checklist carries the account swap and a history check".
It is not a ruling. Every item below restates an obligation that an existing decision row or filed
report already sets, and names that source.

## Items

1. **Swap GBIF to the business account and redo every download under it**, marking the new DOIs as
   superseding the provisional ones.
   Source: D36; docs/planning/evidence/gbif-credentials-report.md, "This is a test account" (line 20)
   and "Moving to the business account later" (line 71).

2. **Swap the Copernicus Climate Data Store account to a business login.** Re-running the stored ERA5
   requests under the new key is optional, since the data does not depend on the account.
   Source: D36; D43.
   2026-09-20: the only Climate Data Store pull to date is the proof retrieval of 2026-09-19, deleted
   unopened (docs/planning/evidence/cds-credentials-report.md). So no CDS output predates the store's
   25 February 2026 change to area extraction, described in
   docs/planning/evidence/2026-09-20-cowork-attribution-licence-grid-report.md, "What a release must
   carry".

3. **History check.** Scan every commit reachable from any ref for every secret value of the old and new
   GBIF and Copernicus accounts, with a positive control, before release.
   Source: D36.
   2026-10-01: D62 rules that the repository is to become public. Claude's reading in D62, open to
   correction: this check runs before the visibility changes, since that is when every commit on every
   ref becomes readable.
   2026-10-01, later: the owner made the repository public at about 19:04 PDT. The check was run after
   that, for the test accounts' values, on all 26 remote refs: no secret found, positive control found
   (docs/audits/2026-10-01-decisions-d61-d62-report.md, appended section). Not ticked: the business
   accounts' values do not exist yet.

4. **Copy the "Citation and attribution" wording** for each of the four Copernicus datasets into what
   ships, since CC BY requires attribution, and confirm the licence version on the three datasets where
   4.0 is inferred.
   Source: docs/planning/evidence/cds-credentials-report.md, the licence bullets (lines 23 to 24 and
   55 to 58).
   2026-09-20: the licence version is observed as CC BY 4.0 on all four datasets (docs/planning/evidence/2026-09-20-cowork-attribution-licence-grid-report.md, Part 2). The
   attribution wording is obtained (docs/planning/evidence/2026-09-20-cowork-attribution-licence-grid-report.md, Part 1) and awaits the owner's ruling on the four page
   defects that report names.
   2026-09-20, same commit: that ruling is D53, so the wording is ruled and awaits only being copied
   into what ships.

5. **Choose the project's licence.**
   Source: D22, "The license is not chosen yet and will be decided before release."
   2026-10-01: still not chosen. D62 rules that the repository is to become public, and D61 that the
   full model ships in a free Forager; neither chooses a licence.

6. **Obtain the owner's ruling on commercial use**, and until it exists confirm that nothing derived from
   CC BY-NC records is in what ships.
   Source: D29; D22.
   2026-10-01: the owner has ruled (D61). Forager is not sold and ships the full model, so output
   derived from CC BY-NC records may be in what ships. Filed with
   docs/audits/2026-10-01-decisions-d61-d62-report.md.

7. **Verify that every ecoregion that ships has a filed held-out evaluation beating the calendar
   baseline.** This is a verification of a rule that applies at all times, not a new gate: D5 governs
   every publication, and this item only confirms it held at release.
   Source: D5.
