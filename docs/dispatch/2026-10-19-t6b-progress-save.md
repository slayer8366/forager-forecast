# Dispatch: t6b-night's nightly save keeps a small summary in git, and the full manifest outside it

Written by the forecast planner (Alder Bearing), 2026-10-19, for Ash Transect (`docs/process/coder-profile.md` on main). It will be recorded as an intent in this repository's RECORD.md (branch forecast-record) before you start.

## Approval and hold

- **The owner, 2026-10-19:** "I'll take your recommendations", answering "t6b-night's broken progress save: have Ash fix it first (Recommended)". The recommendation as put: "Ash changes t6b's progress save so that GitHub gets only a small summary each night. The full record stays on the flash drive, with a checksum in the repository so it can be verified." And from the same message: "The size limit itself stays where it is either way, as Ash's profile requires."
- **Hold:** the owner is building the Forager production release on this laptop, and asked that the laptop coder pause ("Have the laptop coder pause for a bit", relayed by Rowan Waymark, 2026-10-19). **Don't start until the planner resumes you after the owner says go.**

## What happened (read by the planner, 2026-10-19)

- t6b-night was paused for the W42 scoring at 2026-10-19T05:12:40Z. Its section ended normally ("section end: 16106 unit lines in the manifest", journal 22:12:52 PDT). Then its commit was refused: "LARGE FILE: docs/audits/2026-10-07-t6b-run/manifest.jsonl.gz is 1105301 bytes, limit is 1048576 bytes", and `t6b_run.py` exited with `CalledProcessError` from `commit_progress` (`scripts/t6b_run.py:553`, called at `:656`).
- `commit_progress` (`scripts/t6b_run.py:535-560`) gzips the whole manifest into the evidence folder (`copy_manifest_evidence`, `src/forager_forecast/t6b_run.py:87-102`; `EVIDENCE_MANIFEST = "manifest.jsonl.gz"` at `:84`), and then `git add`s the folder and commits it. The manifest grows every section, so its gzip has now crossed the guard and will stay over it.
- **No tile work was lost.** The manifest on the flash drive (`<drive>/forecast-data/t6b/manifest.jsonl`, 6,485,571 bytes at 22:12 PDT) records this section's 2,814 tiles, and 8,869 are left.
- **The runner's worktree,** `~/Zynergy/forager-forecast-host-genera-build` (branch `t6b-host-genera`, HEAD bf9c315 = origin), has three staged, uncommitted files left from the failed commit: the over-size `manifest.jsonl.gz`, `run.log.txt` and `sections.jsonl` under `docs/audits/2026-10-07-t6b-run/`.
- **This branch,** `t6b-progress-save`, is cut from `origin/t6b-host-genera` at bf9c315. Verify all of the above against the remote and the files.

## Task

0. **Verify, then report and stop.** Report the premises above, each confirmed or wrong, with file and line. Report your mechanism prediction and your own intent. Say how the runner's worktree will pick up the change. Say what you'll do with the three staged files: keep `run.log.txt` and `sections.jsonl`, which carry the lost section's summary, and never commit the over-size gzip.
1. **The change**, under the planner's constraints:
   - **What git gets each section:** a small summary, in place of the gzipped manifest. That's the manifest's sha256, its byte size and line count, and the counts of units by stage and status. The existing `sections.jsonl` and `run.log.txt` handling stays as it is.
   - **The full manifest:** it stays where it is, on the flash drive. Also write a gzipped copy outside every repository, under `/mnt/work/Zynergy/forecast-data/t6b/` (create it), replaced each section. The sha256 in git must match the manifest that copy was made from, so a reader can verify either one.
   - **The committed `manifest.jsonl.gz`:** stop updating it, and leave it in the tree as it was last committed (history isn't rewritten). Say in the evidence folder's README, or the nearest equivalent, that it is frozen at bf9c315 and where the live copy now lives.
   - **A failed commit must never end a section as a crash.** If the commit or push fails for any reason, the run logs it and exits non-zero after everything outside git is written. The next section must not be blocked by files left staged from a failure.
   - Tests first, each seen failing for its own reason, including one where the summary is checked against the manifest it came from. One revert check under CLAUDE.md's runner rules.
   - Don't raise the large-file guard, and don't exempt any file from it.
2. **Bring the runner's worktree to the change** and clear the three staged files as planned in step 0. Run one short section against the real manifest, but only if the planner has passed on the owner's go for it; otherwise stop before this step. Don't start t6b-night's nightly run: the planner restarts it.
3. **Report** under the coder profile's headings, with the commits, the tests, the revert check, the summary written, and its sha256 checked against the flash-drive manifest.

## Stops

- Anything in the coder profile's stop list.
- Any change to what t6b computes or how it chooses units. This dispatch covers only how a section's progress is saved.
- The flash-drive manifest failing to match its own summary.
- The guard needing to change.

## Not in scope

- The tiles, the layers and the manifest's format.
- Merging this branch, which is the owner's word (D40). The runner may run from this branch until then, if step 0 shows that's the clean way.
- T8, W42, the site.
