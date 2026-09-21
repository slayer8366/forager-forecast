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

3. **History check.** Scan every commit reachable from any ref for every secret value of the old and new
   GBIF and Copernicus accounts, with a positive control, before release.
   Source: D36.

4. **Copy the "Citation and attribution" wording** for each of the four Copernicus datasets into what
   ships, since CC BY requires attribution, and confirm the licence version on the three datasets where
   4.0 is inferred.
   Source: docs/planning/evidence/cds-credentials-report.md, the licence bullets (lines 23 to 24 and
   55 to 58).

5. **Choose the project's licence.**
   Source: D22, "The license is not chosen yet and will be decided before release."

6. **Obtain the owner's ruling on commercial use**, and until it exists confirm that nothing derived from
   CC BY-NC records is in what ships.
   Source: D29; D22.

7. **Verify that every ecoregion that ships has a filed held-out evaluation beating the calendar
   baseline.** This is a verification of a rule that applies at all times, not a new gate: D5 governs
   every publication, and this item only confirms it held at release.
   Source: D5.
