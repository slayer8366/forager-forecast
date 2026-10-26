# Dispatch: T6b rebuild, step 1 — point it at the new drive and check, no pulls and no run

Written by the forecast planner (Alder Bearing), 2026-10-25, for Ash Transect (forecast coder, Opus). The flash
drive holding T6b's store was corrupted and reformatted, and everything on it is gone (forecast RECORD
2026-09-28-2053). The owner chose "Rebuild on the drive" (-2054) and gave the go for this step: "Yes". Branch
`t6b-rebuild`, cut from `t6b-progress-save` at 621421b, the code the last runs used. Read
`docs/process/coder-profile.md` on main first (for example `~/.cache/forager-wt/new-data-survey`, read-only to you),
then `~/Zynergy/Forager/CLAUDE.md`.

**The new drive.** The same stick, reformatted by the planner on the owner's word as ext4, label `forecast-data`,
UUID e4918208-9d78-4126-aa96-728ebf200edc, mounted at `/run/media/zynergy-labs/forecast-data`, owned by
zynergy-labs, 54 GB free, empty apart from `lost+found`. The old path
`/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190` no longer exists. The label gives a mount path that
survives the next reformat, which the UUID one didn't. Check all of this yourself before relying on it.

**What survives** (check each): the manifest copy `/mnt/work/Zynergy/forecast-data/t6b/manifest.jsonl.gz`
(sha256 9cf29560…, matching `docs/audits/2026-10-07-t6b-run/manifest_summary.json`); the run log and summary on
this branch; T4, T6, T7 and GBIF data under `~/Zynergy/forecast-data`. Lost: the whole t6b store, `forecast-data/t5`
(TreeMap 2023 CONUS, 9.9 GB) and `forecast-data/pnw`.

**Do:**
1. Move every reference to the old drive path in code that runs (scripts and src, not old audit files) to one
   setting that points at the new mount. Tests first, as the profile requires.
2. Check, against the new drive, everything T6b's run relies on: the PAUSE file, writing and appending the
   manifest, the way tiles are written and renamed, any symlinks (T5's `data/t5` was one), making the finished
   store read-only, and the progress save. Use small scratch files on the drive under `forecast-data/t6b-check/`,
   and delete them after.
3. List everything that must be fetched again before a full run (TreeMap 2023, T6b's sources, the SCANFI layers,
   anything else), each with its source URL, its size and the checksum on file to verify it against. Say which
   ones the trees, scanfi-layers and soil stages need.
4. Say whether the old manifest copy can or should be used for anything (for example, comparing each rebuilt
   tile's checksum with the one recorded before the loss). Don't use it to skip building tiles.
5. Estimate the rebuild in nights, at one worker and at two, from the run log's own rates. Name the rates you used.

**Don't:** download any source data. Don't start `t6b-night` or any run, build any tiles, or touch
`~/Zynergy/forecast-data` beyond reading it. Don't edit the record or decisions. Don't write anything large under
`/` (about 1 GB free); scratch goes on `/mnt/work/scratch/t6b-rebuild/` or the drive. Keep any process under 2 GB
(`systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0 nice -n 10`). Juniper is running a read-only
survey at the same time, so keep memory use low.

**Report:** `docs/audits/2026-10-25-t6b-rebuild-check/report.md` on this branch. Commit and push as you go. Commit
messages end with "Co-Authored-By: Claude <noreply@anthropic.com>". Start with any premises here that were wrong,
then items 1 to 5, each marked read, run or inferred, with file and line. End with what you couldn't check and the
exact commands the first run would use. The pulls and that run each need the owner's word; the planner asks.
