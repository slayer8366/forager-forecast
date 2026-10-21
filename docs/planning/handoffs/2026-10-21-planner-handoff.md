# Forecast planner handoff, 2026-10-21 (15:35 PDT)

Written by the forecast planner (Alder Bearing) for the next forecast planner session. The owner is moving to
another account because this account's weekly session limit is nearly reached. Read this, then
`~/Zynergy/Forager/CLAUDE.md`. The record is RECORD.md on this branch (forecast-record), entries up to
2026-09-28-2040, and the next free ID is 2026-09-28-2041. Check every claim below against its source before acting
on it.

## URGENT FIRST: the laptop's root disk is full

At 2026-10-21 15:35 PDT, `/` (nvme0n1p5, 67 GB) showed 0 bytes free, and `/mnt/work` had 1.7 GB. This file could
not be written into the forecast-record worktree, because that worktree is under `~/.cache` on `/`. It was
committed with git plumbing instead, since git's data is under `~/Zynergy` on `/mnt/work`. So the worktree at
`~/.cache/forager-wt/forecast-record` will show this file as deleted. Run `git checkout -- docs/planning/handoffs/`
there once space is freed.

Nothing was deleted to free space; the owner hasn't been asked yet. Session transcripts (`~/.claude`) and
`~/.cache` live on `/`, so sessions may fail until space is freed. t6b writes its tiles to the flash drive, but its
progress save writes to `/mnt/work`.

## Where things stand

**T8 is finished. The verdict is FAIL: the second PNW "no".**
- The bar on t1_1000m fails C1 to C4: C1 −0.01108, C2 −0.00138, C3 p = 0.870, C4 +0.00215 with its interval
  above zero. Every no-verdict part agrees.
- Under D133 (7) this is the PNW finding. Nothing weather-based is published for the PNW, and there is no third
  weather test on these records without new data and the owner's word. SPEC R2 (`docs/planning/SPEC.md:63`)
  also blocks a forecast map.
- Results: branch **t8-build**, `docs/audits/2026-10-21-t8-fit/` (results.md, headline-bar.md, review-fable.md,
  review-sonnet.md), head a8c2c49.
- Outputs: `~/Zynergy/forecast-data/t8/{count,fit}/`, read-only, with SHA256SUMS.
- Both Sorrel reviews confirm the verdict by recomputation. Both say the wording must be "this fixed additive
  design showed no weather gain", not "weather has no effect":
  - C2's loss is carried by the 2021 fold: 56-day rain on the NW Olympic coast was above every training year's,
    and the natural splines extrapolated linearly.
  - C1's gap is mostly model form: T1's calendar is a tree model.
- Record: -2023 to -2040. Rulings: D133 to D137 (on t8-build).

**The count's jump check** read "undetermined", with no reporting-led and no surge-consistent condition met
(count-report.md).

**t6b-night is running** the trees stage, lower 48 first (owner, -2040). It started 2026-10-21 14:15 PDT and
stops at 07:00 PDT on 10-22.
- Command: `t6b_run.py --until 07:00 --stages trees --workers 2 --box 24,49,-125,-66`, run from
  `~/Zynergy/forager-forecast-host-genera-build` (branch t6b-progress-save, 83bd659), with unit properties
  5G, swap off and Nice 10. The full systemd-run line is in the 2026-10-18 handoff, :44.
- 2,289 tiles are in the box; about 283 of them (PNW) were already built.
- Overall 3,775 of 4,058 tree tiles are left: 2,033 Canadian and 1,742 old-layout US rebuilds. That is two to
  four nights (Juniper's read-only check, summarised in -2040).
- After the lower 48 is done, run Alaska, Hawaii and Canada by dropping `--box`, so the code's own order
  applies.
- The planner may restart t6b itself after 07:00 when the unit is inactive and no PAUSE file exists (-2003).
  Tell the owner when you do.

## Open, waiting on the owner

1. **Free disk space on `/`.** The owner decides what goes.
2. **The owner's last question was "Can the PNW be published?"** Answer given: not as a forecast (SPEC R2,
   D133 (7)). Three options were offered, with no reply yet:
   - (a) a plain write-up of the PNW finding, the planner's next task anyway;
   - (b) a "usual season" map with no forecast claim, which would be a new product decision;
   - (c) new data, then a new test.

   The planner asked whether to draft (a) first or look at (b).
3. **t8-build is unmerged.** It holds the code, D134 to D137, the dispatches, and the audits. Merging to main
   needs the owner's word. Back up main first, as with PR #11 (-2026).
4. **forecast-record is unmerged,** as before.

## Known small items, no action taken

- jump.py:85-87 has a stale comment about the GBIF API (review-fable.md finding 5).
- `loyo_additive`'s `years=` parameter has no caller (Ash's step-1 report).
- In the ecoregion "none" block, 19% of units have cell centres in water. Both reviewers inferred this; it was
  not checked against a coastline file.
- Nobody has checked whether the 2024–25 jump is partly a change in coordinate-uncertainty reporting
  (review-sonnet.md finding 6).

## How this session ran, for the next one

- **Coder sessions were forced to hand back mid-run,** so long chains ran as detached systemd units: the
  runner `scripts/t8_fit_runner.sh` on t8-build. Prefer that shape for anything over an hour.
- **An uncapped T8 test ran the laptop out of memory** on 2026-10-19 (19:53 PDT), killing other sessions. Every
  run since has a systemd memory cap with swap off. Memory is tight: about 3 GB available, with swap full,
  mostly from the desktop app and Firefox.
- **No scheduled tasks remain** for this work. The daily t6b check was deleted (-2037), and the one-off checks
  have fired.
