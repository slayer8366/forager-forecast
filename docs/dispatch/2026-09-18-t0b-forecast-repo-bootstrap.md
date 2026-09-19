# T0b. Bootstrap the dedicated forecast repo

## State this was written against

- Written 2026-09-18 by Claude in the planning chat. The owner accepted a dedicated repo that day
  (D15, recorded with the owner's ruling as D17 in the planning doc).
- Planning pack: zynergy-site, branch claude/forager-forecast-planning-pack, at Forager/mushroom-forecast/,
  commits b707cbe, 851b96d, c8e8ce3 on top of 0688e4d. Agent-reported. Claude checked only that
  START_HERE.md serves on the Pages preview.
- Forager facts below come from the read-only pulse against origin/main 175b050. Agent-reported.
- Claude has not seen the new repo. It may not exist yet.
- This supersedes the unfinished parts of T0 (.gitignore and layout). What T0 already landed stands.

Scope: stand up the repo, move the pack, add guards, prove the weather source. No record pulls, no model code.

## Owner only, before the agent starts

- Create the empty repo and tell the agent its name. Suggested: forager-forecast. Private for now (D15).
  No template and no auto-generated README.

## Verify first, and report before changing anything

1. The new repo's name, visibility, default branch, and head commit or "empty".
2. That the pack on the site branch is still what was committed: per-file sha256 against your earlier
   record. START_HERE.md and TASKS.md carry your later edits, and those newer versions are the ones to copy.
3. Which Python versions this machine has. Confirm or disprove: "Python 3.11 or newer is available, and
   GDAL, rasterio and pyproj install cleanly in a fresh environment." If not, report and stop.
4. The record form in Forager: read the header of docs/audits/README.md and one September pulse file,
   and list the header fields you will reuse.

## Then do

- Copy the pack into the new repo root with its layout unchanged (docs/planning, docs/dispatch, scripts).
  Prove the copy is byte-identical, then commit it on its own.
- Add docs/audits/ with an index README in Forager's form: dated rows, supersede instead of edit, base
  commit in every header, file-and-line claims. First rows: the T0 report, the Forager pulse answer
  (file it as 2026-09-18-forager-repo-pulse.md), and this dispatch.
- Add .gitignore before any data exists: data, downloads, caches, models, tiles, *.pmtiles, *.tif, *.nc,
  *.parquet, virtual environments, __pycache__, notebook checkpoints, .env and any secrets.
- Add a guard that fails when a staged file is larger than 1 MB, as a pre-commit hook and as a CI step.
- Add the Python skeleton: pyproject with a pinned Python, a lock file, src/, tests/, and one CI
  workflow that runs lint and tests only. It must not download data.
- Copy, do not import, Forager's scripts/verify-open-meteo-historical-fields.sh and
  scripts/verify-inaturalist-access.sh. Put the source path and commit 175b050 in each header. Extend the
  Open-Meteo check to the four T1 variables (daily mean temperature, precipitation, soil temperature
  0 to 7 cm, soil moisture 0 to 7 cm) at one point inside each T1 box, and report the result.
- Append the amendment below to docs/dispatch/2026-09-18-t1-calendar-smoke-test.md. Append, do not rewrite.
- Add a session-log row to START_HERE.md and mark T0 as superseded by T0b in TASKS.md.

### Amendment text for the T1 dispatch

> Amendment, 2026-09-18. Adds to "Verify first" item 2 and changes nothing else. Forager already has
> live checks for the Open-Meteo archive with backoff on 429 and for iNaturalist access (copied into
> scripts/ from Forager at 175b050). Start from those. Known from the Forager pulse: the app's archive
> client requests daily precipitation only, so soil variables on the archive endpoint are still
> unconfirmed until T0b reports. Forager's rule-of-thumb lag window is 7 to 21 days
> (domain/FruitingPatternAssumptions.kt:54). T1's fixed window list already spans it. In the report,
> say whether the top weather features fall inside or outside 7 to 21 days. Do not change the window list.

## Do not touch

- The Forager repo. Read only. The owner intends to build the forecast into the app later and will
  supersede the README when that ships (D17). That is a future dispatch, not this one.
- The guard that bars Forager's fruiting-lag visualizer from feeding any ranking. D17 does not lift it.
- Any row in DECISIONS.md, the Fixed terms, or a requirement in SPEC.md.
- Cloudflare: both accounts, the forager-maps bucket and the forager-pmtiles Worker.
- The site branch. Do not merge it and do not delete it. Report when it is safe for the owner to close.

## Already considered and rejected

- A folder inside Forager: data is committed there, there is no LFS, the repo is public with no license,
  and every PR runs the Android build (D15).
- A submodule or subtree between the repos: the only link is published tiles and a manifest.
- A public repo today: rejected until the licensing question in SPEC.md is settled.
If you think any of this is wrong, say why in the report instead of doing the alternative.

## Evidence to return

- Commit hashes and a tree listing. The sha256 comparison result.
- The large-file guard shown failing on a test file, then passing once it is removed.
- The CI run result. The output of both verify scripts, including the four T1 variables.
- A Conventions line: what you checked in Forager's records and whether you followed it.
- What you did not check.

## Person only

- Create the repo (above). Close the site branch once the agent reports the pack is safe in the new repo.
- The license for the new repo, which waits on the commercial-use question.
