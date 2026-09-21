# Cowork's two credential reports filed, and D36's citations corroborated

**Date:** 2026-09-20.
**Type:** filing report for docs/dispatch/2026-09-20-file-cowork-credential-reports.md as corrected by
docs/dispatch/2026-09-20-file-cowork-reports-item-5-correction.md.
**Base:** d32-stage-1-records at bb15fbb, off main cb0bca8.
**Supersedes:** nothing.
**Read time for every state claim:** 2026-09-20 17:59 PDT for the scan, 18:03 PDT for the branch tips.

## The three reports D36 cites, and where each now lives

D36's Reason cell (docs/planning/DECISIONS.md line 9 on main cb0bca8) names three reports. All three are
now in the repository, two of them for the first time.

| Report D36 cites | Where it lives |
|---|---|
| "the T1 run report quotes a credential variable's value" | `docs/audits/2026-09-18-t1-credentialed-run-report.md`, on t1-calendar-smoke-test and t1-credentialed-run-review. Already in the repository before this filing. |
| "Cowork's GBIF report names the username" | `docs/planning/evidence/gbif-credentials-report.md`, filed here. |
| "Cowork's Copernicus report names the account email" | `docs/planning/evidence/cds-credentials-report.md`, filed here. |

**D36's row on main is unedited.** Nothing in this filing touches DECISIONS.md on any branch. The row
stays exactly as merged at cb0bca8.

## D36's Reason cell, corroborated against actual values

Each of the three citations was previously readable only as a claim. All three are now checked against
the real credential values rather than by eye, by literal comparison, at the 17:59 PDT scan:

- The T1 run report holds the `GBIF_USER` value at line 52.
- The GBIF report holds the `GBIF_USER` value at lines 32, 34 and 47.
- The Copernicus report holds the `GBIF_EMAIL` value at line 37.

All three of D36's premises hold. None was overstated.

## The leak scan, as run

**Method.** The five credential values, being `GBIF_USER`, `GBIF_PWD` and `GBIF_EMAIL` from
`~/.config/forager-forecast/gbif.env` and the `url` and `key` entries from `~/.cdsapirc`, were held in
memory and tested as literal substrings against every line of both reports. No value was written into
any file, commit message or report, here or anywhere.

**Positive control.** The same scanner was run first over a blob known to contain a value:
`docs/audits/2026-09-18-t1-credentialed-run-report.md` at e9fbdf5. It returned `GBIF_USER` at line 52,
which is the known location. The scanner was therefore shown able to report a hit before any negative
result from it was accepted.

**Result, three hits, all identifiers or public.**

| File | Value | Lines | Classification under D36 |
|---|---|---|---|
| `gbif-credentials-report.md` | `GBIF_USER` | 32, 34, 47 | account identifier, permitted |
| `cds-credentials-report.md` | `GBIF_EMAIL` | 37 | account identifier, permitted |
| `cds-credentials-report.md` | the `url` entry | 50 | the store's documented public API address, not a credential |

**No secret is in either file.** `GBIF_PWD` and the Copernicus `key` appear in neither, at any line.
Both reports name the account they describe, which is what D36 requires of an identifier: the GBIF
report states "This is a test account" at line 20, and the Copernicus report identifies the ECMWF
account at line 37.

**The UUID-shaped string is not the key.** Line 42 of the Copernicus report prints a proof-request ID
that is 36 characters and UUID-shaped, the same shape the same report attributes to the token at line
40. The two were compared directly against the real key: they are not equal, neither is a substring of
the other, and the key does not appear anywhere in that report at any line. The string is a request
identifier, as labelled.

## The "asked twice" count now has its source in the repository

Line 102 of `docs/planning/evidence/cds-credentials-report.md` reads, in its "Not checked" list:
"Whether this account is a test account to be redone later, as the GBIF one is. Asked twice, not
answered." That is the source for the correction appended on this branch to
`docs/audits/2026-09-19-decisions-d38-d39-report.md`, which replaced a chat-derived "asked three times".
The figure can now be checked against a filed document rather than taken on relay.

## What the reports confirm, and one asymmetry

Nothing in either report contradicts anything filed on any branch. The Copernicus licence finding at
lines 56 to 58, "CC-BY licence" on all four datasets with no version named, 4.0 observed only on
ERA5-Land's pop-up and inferred for the other three, matches the correction bullet already in
docs/planning/SPEC.md on main.

The asymmetry worth recording: the GBIF account is stated to be a test account, at line 20, with a redo
procedure at lines 71 to 82. Whether the Copernicus account is a test account was asked twice and never
answered. Every GBIF DOI is marked provisional on that basis. No equivalent provisional marking exists
for Copernicus pulls, and none has been needed yet because no bulk pull has run.

## Not checked

- Anything inside either report beyond the credential scan and the claims quoted above. Neither report
  was audited for correctness; they are filed as received.
- The four Copernicus dataset ids, the request shape and the `cdsapi` pin against the store itself. The
  Copernicus register row that the open-work list calls for is not written here.

Conventions: the filing form of docs/audits/2026-09-19-decisions-d38-d39-report.md was followed, and
index rows were kept to about the length of the rows shortened at 4114474. Em dashes avoided.
