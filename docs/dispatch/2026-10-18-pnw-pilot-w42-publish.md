# Dispatch: publish the PNW pilot for 2026-W42, late

Written by the forecast planner (Alder Bearing), 2026-10-18 (UTC 2026-10-19), for Ash Transect (`docs/process/coder-profile.md` on main). Recorded as intent 2026-09-28-2006 in this repository's RECORD.md (branch forecast-record).

## Approval

- Forager RECORD -1034, the owner, 2026-10-15: "Publish this week's pilot meanwhile". The route is set there: the same pilot model, unchanged, scored for 2026-W42 by the W41 route; forecast branch `pnw-pilot-w42`, not merged to main (D40); the site drop as a PR on zynergy-site branch `pnw-pilot-w42-drop`.
- RECORD 2026-09-28-2005 (forecast record), the owner, 2026-10-18: "Published W42 late", confirmed in the planner's window with "Yes to all". The planner had restated it as: the dispatch; your download change, the download and the scoring, model unchanged; the site PR and the planner's preview check; then the owner's word to merge. **That "yes" is the owner's go for the download in step 1.** The merge is not part of this dispatch and comes back to the owner.

## Base and premises (re-check each before acting)

- **Branch** `pnw-pilot-w42`, worktree `~/Zynergy/forager-forecast-pnw-w42`, head `1305244` (read by the planner, 2026-10-19 UTC). It is cut from main `a79d667`. Main is now `b0bc10a4`, which adds only two planning documents (`git diff --stat f99dbcbf b0bc10a4`), so no merge from main is needed. Verify against the remote.
- **The weather is there.** At 2026-10-18T17:00:57Z the catalogue (`https://cds.climate.copernicus.eu/api/catalogue/v1/collections/<name>`, `extent.temporal`) gave both `reanalysis-era5-land` and `reanalysis-era5-single-levels` an end of 2026-10-12T00:00:00Z, read by the planner. W42's window is 2026-07-14 to 2026-10-11 plus the 2026-10-12 00:00 rain stamp (`docs/audits/2026-10-10-pnw-pilot-scoring-report.md:503-505`).
- **The pull scripts are fixed to W41:** `scripts/pnw_cds_hourly_pull.py:57-58` (`SCORING_MONTHS`, `LAST_DAY = {(2026, 10): 4}`, read) and `scripts/pnw_cds_precip_hourly.py:127-141` (`scoring_chunks`, cited by the scoring report at line 516, not re-read by the planner).
- **A name collision:** the store's `hourly-era5land-2026-10.*` files hold 2026-10-01 to 04, and a W42 pull of October under the same name would replace them and their request record (scoring report, lines 518-520).
- **W41 reproduced from its inputs** on 2026-10-15 (scoring report, lines 491-501), with the command and flags given there: `--kind full --week 2026-W41 --beats-calendar false --reviewed true --t1-result <W41's t1_result>`.
- **The citation access dates** in `attribution_details` come from the store's request records, so they will move for W42 (lines 521-523).
- **The site:** zynergy-site main is at `319871c` (read 2026-10-19 UTC); the live files are `Forager/forecast/data/pnw-pilot/current/manifest.json` and `cantharellus.geojson`. The W41 drop's dispatch is `docs/dispatch/2026-10-11-pnw-pilot-site-drop.md` on this branch; follow its steps 1 to 3 for the drop, with week 2026-W42.

## Task

0. **Verify, then report and stop.** Report the base, the premises above (each confirmed or wrong, with file and line), the exact W41 flag values you will reuse (each quoted from W41's manifest or the scoring report, with the line), and your mechanism for the pull change. Write the mechanism prediction first. One constraint on it, the planner's call: **W41's inputs are never overwritten.** The W42 October files get their own names, and W41 must still reproduce, byte for byte as on 2026-10-15, after the pull.
1. **The pull** (on the report's acceptance, which the planner gives by resuming you):
   - the download-only change to the two scripts, tests first where the scripts have tests, each seen failing for its own reason;
   - the download under the coder profile's rules: one fetch at a time, at low priority, each checked against what the publisher states, stored read-only, registered in `docs/planning/DATA_REGISTER.md`;
   - then re-run the W41 reproduction and report its hashes against the 2026-10-15 ones.
   - Commit and push after each step.
2. **Stop before scoring.** The scoring run is a heavy job, and t6b-night is running. Report that you are ready. The planner pauses t6b-night and resumes you.
3. **Score W42** with the W41 command and flags but `--week 2026-W42`, under `systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0`, at Nice 10. Check the output against W41's: the same cell counts (2,618 scored, 231 from a land neighbour, 498 sea, 0 incomplete) or the difference explained; `pilot` true; `validated` false; `reviewed` and `beats_calendar` as W41's; and every manifest field the same as W41's except the week, the dates, the weather window and source, the access dates, `published_at` and the cell values. Any other field that differs is a stop. Report at once when the run ends, so the planner can resume t6b-night.
4. **The site drop:** on zynergy-site, branch `pnw-pilot-w42-drop` from `origin/main`, copy the two files in and open a PR. Wait for the preview with a background loop that exits on a result. Run the W41 drop's check (`~/Zynergy/device-evidence/2026-10-10-pilot-map/check.py`) against the preview at 1366x860 and 390x844, and read the banner from screenshots kept outside both repositories. **Stop there.** Don't merge.
5. **Report:** append a 2026-W42 section to `docs/audits/2026-10-10-pnw-pilot-scoring-report.md` on this branch, and return a report under the coder profile's headings, with the PR URLs, the preview URL, the check output and what the banner says.

## Stops

- Anything in the coder profile's stop list.
- Any change to the model, its copy or its labels; any manifest field differing from W41's beyond those listed in step 3.
- W41 failing to reproduce after the pull.
- A download failing its stated check, or the catalogue no longer covering the window.
- The preview failing its check, or a banner field missing or wrong.

## Not in scope

- Merging either branch: the owner's word, on the planner's request.
- t6b-night: the planner pauses and resumes it. Don't touch it.
- T8, the Forager app, the record and the audits index.
