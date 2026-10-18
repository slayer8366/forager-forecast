# Planner handoff, 2026-10-18: forecast work moves from Rowan to the forecast planner

Written by Rowan Waymark (the Forager planner) at 2026-10-18 UTC, for the first forecast planner session. The owner, verbatim (Forager RECORD -1251):
- "A planner may be necessary to talk with in the forecast repo instead of directly to a coder, since it's a different repo altogether. Open a new planner session, and begin a Forager-forecast planner profile for the repo. They can write the plans for Ash";
- "Its own record in forager-forecast (Recommended)";
- "All forecast work (Recommended)". That option read: T8, the W42 publish check, the t6b-night restarts, the T7 record branches and PR #5; the forecast planner owns forager-forecast and the site's forecast pages.

Every fact below was read on 2026-10-18 from the source named. Re-check each before acting.

## Your first actions

1. **Read your profile,** `docs/process/planner-profile.md` (branch `forecast-planner-profile`; it is not on main until the owner merges it).
2. **Propose three names for yourself** to the owner, each with a line on why it fits, in the team's pattern: a tree or plant, then a field-craft or landscape word. Avoid the existing names: Rowan Waymark, Hazel Cairnwright, Ash Transect, Elder Ford, Sorrel Tally, Juniper Sounding. Write the chosen name into the profile.
3. **Set up this repository's record:** its file, ID scheme and branch, following E-GD's `RECORDING.md`. The first entry is a handoff entry citing Forager RECORD -1251. Forager's RECORD.md (branch `records-after-173`) holds everything before; cite it as "Forager RECORD -NNNN".
4. **Re-create the reminders below** in your own session. Rowan's reminders don't reach you.

## State (2026-10-18 UTC)

- **main** `f99dbcbf`, Ash Transect's profile merged (forecast PR #6). **t7-build** `5c1a9df1`, parts A to C merged.

### T7: stopped for the PNW as posed (Forager RECORD -1247)
- **The re-fit** (`t7-refit` `da1f2078`, **draft PR #5**, unmerged) failed P10b on conditions 2 and 3; conditions 1 and 4 passed (-1229, -1230).
- **The reviews:** Sorrel on Fable (`t7-refit-review` `4d890d7`) and on Sonnet (`t7-refit-review-2` `2152446`) reproduced every figure and agree. Rowan's comparison is in -1246; the earlier reviews are on `t7-fit-review` and `t7-fit-review-2`.
- **Owner's ruling:** "Stop T7 as posed; keep the record (Recommended)". Nothing is shown. The leads, which are not plans, are the bolete and tooth genera, the within-block signals and the specimen result.
- **Not done yet:**
  - a DECISIONS.md row recording the stop (it needs a branch and the owner's word to merge);
  - the audits index rows for the re-fit report and both reviews;
  - what happens to draft PR #5, which is the owner's call.

### T8: the second, stricter PNW weather test (Forager RECORD -1248 to -1250)
- **The premise:** T1 found weather slightly *worse* than the calendar in the PNW: Brier skill −0.0035 [−0.0066, −0.0001], `docs/audits/2026-10-10-pnw-pilot-t1-report.md:288-298`. Ash stopped on it (-1249).
- **Owner's ruling:** "A: Second, stricter PNW weather test (Recommended)". Concretely:
  - first explain the 2024–25 chanterelle jump;
  - effort enters from T6;
  - a few weather measures, fixed in advance;
  - the plan must beat T1's calendar on the same weeks, with its interval above zero.
- **Ash's draft plan:** `t8-plan` `d6f916ae`, `docs/dispatch/2026-10-17-t8-trigger-plan.md`, marked "WIP, paused". Ash reports it is drafted in full with 13 decisions, but not self-checked: some line citations weren't re-read.
- **The dispatch** it answers: `docs/dispatch/2026-10-17-t8-plan-dispatch.md` on the same branch.
- **Next:** the plan is now yours to finish, or to have Ash finish under your dispatch. Then bring the owner its decisions. Nothing has been downloaded, counted or fitted.

### W42 publish (Forager RECORD -1034, -1035)
- **Pending on the weather archive.** At 2026-10-17 17:00 UTC, both `reanalysis-era5-land` and `reanalysis-era5-single-levels` ended at 2026-10-11T00:00Z; W42 needs data through 2026-10-12T00:00Z. Read from the Copernicus catalogue: `https://cds.climate.copernicus.eu/api/catalogue/v1/collections/<name>`, `extent.temporal`.
- **Check again** on 2026-10-18, about 10:00 PDT (17:00 UTC).
- **If the data are there,** bring the owner the route one step at a time: forecast branch `pnw-pilot-w42`, then the site PR on `pnw-pilot-w42-drop`, then the merge.
- **Rowan's reminder** for this check is deleted, so set your own.

### t6b-night (the continental SCANFI layers)
- **Running now,** until 07:00 PDT.
- **Restart it daily after 07:00 PDT,** after checking it is inactive and that the PAUSE file `/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b/PAUSE` is absent. From `~/Zynergy/forager-forecast-host-genera-build`:
  ```
  systemctl --user reset-failed t6b-night; systemd-run --user --unit=t6b-night -p MemoryMax=5G -p MemorySwapMax=0 -p Nice=10 --working-directory=$PWD $PWD/.venv/bin/python scripts/t6b_run.py --until 07:00 --stages scanfi-layers --workers 2
  ```
- **The owner's standing wish** (Rowan's memory "t6b runs in downtime"): keep T6b running whenever no build needs the laptop; pause before builds and resume after. The owner asked to be reminded to be patient while it pauses.
- **Progress estimate,** from the 2026-10-17 handoff and inferred: about 140 units an hour, about 15,900 units left.

### Owed and open
- **Dr Sergei Põlme** (FungalTraits) is owed a link when the first PNW forecast results are published (Forager RECORD -1169).
- **Site PR #3** (`site-legal-pages-2026-09-29`) is old and held. It isn't forecast work; leave it to Rowan or the owner.
- **The scratch and review branches** from today stay until a tidiness pass on the owner's word: `t7-part-a/b/c`, `t7-refit`, the reviews, `scratch-tabs-*` (those are Forager's).

## What stays with Rowan
- The Forager app, the production release (in progress tonight) and Forager's RECORD.
- **Expanding the vector maps beyond the US** (the owner's side note in Forager RECORD -1243) is app and map-service work, so it stays with Rowan.

## The team you share
- **Ash Transect** codes for you (Opus), as a subagent you start with its profile and the dispatch.
- **Sorrel Tally** reviews, on Fable and Sonnet. **Juniper Sounding** researches. Give each its name and profile in its prompt.

## Correction, appended 2026-10-18 by Rowan Waymark

Under "T8", the line "Next: the plan is now yours to finish, or to have Ash finish under your dispatch" is wrong. The owner, 2026-10-17: "The separation is role is between planner and coder, not repo. The EGD standard is that whoever writes the code shouldn't write the plan and vice versa". So the plan is yours to write. Ash's paused draft on `t8-plan` was written by the coder, against that standard, at Rowan's dispatch (-1248). Treat it as Ash's findings to read, not as a plan to finish. The text above is left as written.
