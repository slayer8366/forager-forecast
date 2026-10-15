# Dispatch: put the scored PNW pilot map on the live site

Written by the planner (Rowan Waymark), 2026-10-11. Approval: Forager RECORD -817 ("put the map on a live site when ready", with -814's labels). Runs after scoring step 4 has published. Merging to the site's main goes on the owner's word, given in the planner's window. Assumed base: zynergy-site main at 734b2a6 (clone ~/Zynergy/zynergy-site, which needs a local git identity copied from Forager). Verify against the remote. Every claim below is a premise to re-check.

Writing rule for everything you write: describe other products, services and device makers generically or by what they do. Don't discuss the rule; just write that way.

## Task

0. **Verify, then report by message:** the base; the target folder Forager/forecast/data/pnw-pilot/current/; the files you will copy (manifest.json and cantharellus.geojson from the scoring output) with sizes and sha256; what the page's banner will read from the manifest.
1. On a new branch from main, copy the two files in and push. Wait for the preview deployment by a background loop that exits on a result, not by polling in the conversation.
2. Run ~/Zynergy/device-evidence/2026-10-10-pilot-map/check.py against the preview at 1366x860 and 390x844. Read the banner by eye from screenshots kept outside the repo: pilot; validated false; reviewed as the pass-2 review says; beats_calendar; week 2026-W41; attribution (the GBIF citation plus the Copernicus text for the products read); and the land-route gate note, if the scoring step added one.
3. Report to the planner with the preview URL, the check output and what the banner says. Stop there. The merge comes on the owner's word, with a backup bundle first and a RECORD merge entry after.

## Stops

Any banner field missing or wrong; the preview failing its check; a file over the site's limits; a wrong premise.

## Not in scope

Merging; the forecast code; the Forager app.

## Amendment (Forager RECORD -877, -878)

- The base moved: zynergy-site main is now cb596aad (PR #10: own street map, slider, demo text). Cut from it.
- In the same site change, two text fixes, verbatim from the owner's ruling: in the intro, "the weekly chance of chanterelles being found" becomes "the weekly chance of chanterelles being reported"; in the guide, "Not validated and not reviewed" becomes "Not validated. Its figures were checked by an independent review." Re-read the surrounding sentences so each still reads correctly, and report any other line those two edits leave inconsistent.
- The merge is on the owner's word (text changes go beyond -817's data-drop approval).
- Production adds a hosting-analytics script that the site's script-src refuses. It predates PR #10 (RECORD -877). Don't fix it in this change, and don't count its console error as this change's failure; report it separately.
