# RECORD.md

forager-forecast's own record of dispatched work, decisions and what
happened, kept by the forecast planner (Alder Bearing,
`docs/process/planner-profile.md`). It follows E-GD's RECORDING.md
(github.com/slayer8366/E-GD-Philosophy, branch Test-1). Each piece of work
opens with an intent entry, written before anything is built, carrying its
scope boundary, baseline, both predictions, finish line and abort conditions,
and closes with exactly one terminal or an outcome carrying Closes. Every
entry carries its Kind, its ID and a Timestamp read from `date -u`, and ends
by saying who wrote it, on which branch, and the next free ID.

Everything recorded about the forecast before this file began is in
Forager's record (slayer8366/Forager, RECORD.md, branch records-after-173),
where it stays. It is cited here as "Forager RECORD -NNNN". An unprefixed ID
in this file means an entry in this file.

IDs keep Forager's form, 2026-09-28-NNNN, and this record's run starts at
2026-09-28-2001, so that no ID names one entry here and a different one in
Forager. Forager keeps the numbers below 2000.

This file is append-only. Nothing committed is edited or removed; a
correction is a new entry that points at the one it corrects.

## Entries

---

**Kind:** handoff
**ID:** 2026-09-28-2001
**Timestamp:** 2026-10-18T13:01:04Z
**Title:** forager-forecast's own record begins; forecast planning passes from Rowan Waymark to the forecast planner (owner)
**The owner, verbatim** (Forager RECORD -1251, 2026-10-17): "A planner may be necessary to talk with in the forecast repo instead of directly to a coder, since it's a different repo altogether. Open a new planner session, and begin a Forager-forecast planner profile for the repo. They can write the plans for Ash"; "Its own record in forager-forecast (Recommended)"; "All forecast work (Recommended)".
**Handoff-file:** docs/planning/handoffs/2026-10-18-planner-handoff.md (on main since b0bc10a4), with its appended correction: the planner writes T8's plan; Ash's paused draft (t8-plan d6f916ae) is read as Ash's findings.
**How this record is set up:**
- **What the owner was told before answering:** the recommendation "A new, empty record in forager-forecast. Its first entry points to Forager's record for everything before it … For new IDs I'd use a block Forager won't reach, starting at -2001".
- **The owner, verbatim, 2026-10-18:** "I'll take your recommendation, but migrate the Forager records that pertain to the Forager forecast repo"; then, asked whether the migrated entries move or are copied: "migration is undone and no longer happening".
- **What it sets:** this file, RECORD.md at the root, one file at this size; branch forecast-record, to main on the owner's word (D40); IDs from 2026-09-28-2001; earlier forecast history stays in Forager and is cited there.
**Taken over from Forager's record:** T8's plan (Forager RECORD -1248, closed there as partial by -1252, the plan deferred to this role); the W42 publish check (Forager RECORD -1034, -1035); the t6b-night restarts; T7's unrecorded leftovers (the DECISIONS.md stop row, the audits index rows, draft PR #5) (Forager RECORD -1247); the link owed to Dr Sergei Põlme (Forager RECORD -1169).
**Open intents in this record:** none. T8's plan will open one here when it starts.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2002.

---

**Kind:** decision
**ID:** 2026-09-28-2002
**Timestamp:** 2026-10-18T13:01:04Z
**Title:** The forecast planner is Alder Bearing (owner)
**What the owner was told before answering:** three names in the team's pattern: Alder Bearing, Bracken Tideline, Larch Benchmark.
**The owner, verbatim, 2026-10-18:** "welcome aboard, Alder".
**What it sets:** the role's name, written into docs/process/planner-profile.md at c0728eda.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2003.

---

**Kind:** decision
**ID:** 2026-09-28-2003
**Timestamp:** 2026-10-18T13:01:04Z
**Title:** The planner restarts t6b-night itself each morning when the checks are clean (owner)
**What the owner was told before answering:** "Your standing wish is to keep it running whenever no build needs the laptop. Once the checks come back clean, may I restart it myself each morning and tell you afterwards?" The checks: the unit inactive, the PAUSE file absent, no build needing the laptop.
**The owner, verbatim, 2026-10-18:** "You may start it yourself."
**What it sets:** after 07:00 PDT, with those three checks clean, the planner restarts t6b-night with the command in the handoff file, then tells the owner. If any check fails, the planner asks instead.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2004.

---

**Kind:** merge
**ID:** 2026-09-28-2004
**Timestamp:** 2026-10-18T13:01:04Z
**PR:** 7
**Head:** forecast-planner-profile (c0728edaedc8ceb7840a7d9181d09b4a0b507b38)
**Base:** main
**Merge-commit:** b0bc10a4fc5d2ab8e9b3f77dd5b348f0f6803bc6
**Pre-merge:** f99dbcbf4000133334bac2fd8256a171d9b63224
**Backup:** ~/Zynergy/forager-repo-backups/forecast-main-20261018T123822Z-f99dbcbf.bundle; `git bundle verify` okay, read by the forecast planner.
**Merged-by:** Rowan Waymark, on the owner's word in Rowan's window, "Merge into main", at 2026-10-18T12:41:35Z (GitHub). The forecast planner did not hear that word itself and relays Rowan's message.
**Carries:** docs/process/planner-profile.md and docs/planning/handoffs/2026-10-18-planner-handoff.md, documents only; `git diff --stat f99dbcbf b0bc10a4` shows those two files and nothing else.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2005.

---

**Kind:** decision
**ID:** 2026-09-28-2005
**Timestamp:** 2026-10-19T04:47:17Z
**Title:** W42 published late; the finished forecast worktrees removed; the borderline records copied into the both-projects folder (owner)
**What the owner was told before answering:** (1) W42's weather arrived but its week ended 2026-10-18, so publishing now is late; options: publish late (recommended), skip to W43, or pause weekly publishing until T8 to T10. (2) Remove the finished forecast worktrees, each clean and pushed, about 8 GB. (3) Where the 27 borderline items in the Forager copy go.
**The owner, verbatim, 2026-10-18,** typed in Rowan Waymark's window and relayed by Rowan: "1 Published W42 late / 2 go ahead / 3 they belong to both repos". Restated in the forecast planner's window as: (1) the dispatch, Ash's download change, download and scoring with the model unchanged, the site PR and the planner's preview check, then the owner's word to merge, with this yes as the go for the download; (2) remove the folders, re-checking each just before; (3) all 27 borderline items copied into the both-projects folder in forager-forecast, staying in Forager as they are. The owner, in this window: "Yes to all".
**What it sets:** the W42 publish under intent 2026-09-28-2006; the clean-up (observation 2026-09-28-2008); the borderline items' place in the copy under intent 2026-09-28-2007.
**Not authorised by this:** the merge of either W42 branch, which comes back to the owner.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2006.

---

**Kind:** intent
**ID:** 2026-09-28-2006
**Timestamp:** 2026-10-19T04:47:17Z
**Title:** Publish the PNW pilot for 2026-W42, late, by the W41 route
**Dispatch-file:** docs/dispatch/2026-10-18-pnw-pilot-w42-publish.md (branch pnw-pilot-w42, 0f4bda9)
**Change:** a download-only change to the two pull scripts, the W42 weather pull, a W42 scoring run with the model unchanged, and a site PR on zynergy-site branch pnw-pilot-w42-drop. Continues Forager RECORD -1034 and -1035.
**Scope boundary:** no change to the model, its copy or its labels; W41's inputs never overwritten; no merge of either branch; t6b-night paused and resumed by the planner only.
**Baseline:** W41 is live (manifest sha256 074879ff…4043) and reproduced byte for byte on 2026-10-15 (docs/audits/2026-10-10-pnw-pilot-scoring-report.md:491-501). The archive covers W42's window since 2026-10-18T17:00:57Z.
**Prediction if it works:** W42 scores with the same cell counts as W41 (2,618 scored, 231 from a land neighbour, 498 sea, 0 incomplete), and the manifest differs from W41's only in the week, dates, weather window and source, access dates, published_at and cell values. W41 still reproduces after the pull.
**Prediction if it fails:** a manifest field beyond those differs, the cell counts change unexplained, the pull fails its check, or W41 stops reproducing.
**Finish line:** the site PR open with its preview passing the W41 drop's check, and the banner read, reported to the owner for the merge word.
**Abort conditions:** any stop in the dispatch; the model needing a change; the owner withdrawing the publish.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Ash Transect (Opus) codes it. Next free ID 2026-09-28-2007.

---

**Kind:** intent
**ID:** 2026-09-28-2007
**Timestamp:** 2026-10-19T04:47:17Z
**Title:** Copy the forecast records from Forager into forager-forecast, Forager unchanged (owner)
**The owner, verbatim, 2026-10-18:** "So hust copy the records"; to the four questions on how, "All recommended. For 2: have a Forager app and forecast project folder for all mixed app details. I want to keep this open for people to use and that just tidies it up for them"; and on the borderline items, "they belong to both repos" (2026-09-28-2005).
**Change:** verbatim copies, keeping their IDs, from Forager at 35c14780 (records-after-173): forecast-only RECORD entries into records/from-forager.md; forecast-only preserved files into docs/preserved/; entries, preserved files and docs covering both projects, and every borderline item, into forager-app-and-forecast/ with a README for outside readers.
**Scope boundary:** nothing in Forager changes; no entry is edited, split or renumbered; this RECORD.md is not touched beyond its own entries.
**Baseline:** the sort, by four read-only helpers, each count checked by the planner against the source: 1,431 entries (213 forecast, 22 both, 18 borderline, 1,178 app); 401 preserved files (20 forecast, 6 both, 7 borderline); Forager's other docs (1 both, 2 borderline).
**Prediction if it works:** 213 entries in records/from-forager.md and 40 in forager-app-and-forecast/entries.md; 20 files in docs/preserved/ and 13 in forager-app-and-forecast/preserved/, plus 3 docs; each copy byte-identical to its source.
**Prediction if it fails:** a count differs from the sort, or a copy is not byte-identical.
**Finish line:** the copies on a branch, the counts and byte checks reported to the owner, the merge on the owner's word.
**Abort conditions:** the owner withdrawing the copy; an entry that cannot be copied whole.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2008.

---

**Kind:** observation
**ID:** 2026-09-28-2008
**Timestamp:** 2026-10-19T04:47:17Z
**Title:** Fifteen finished forecast worktrees removed; the work drive from 3.7 GB to 12 GB free
**Notes:** On the owner's "go ahead" (2026-09-28-2005). Each was re-checked just before removal (no uncommitted change, 0 commits not on origin), then removed with `git worktree remove`, with no force: t7-part-a, t7-part-b, t7-part-c, t7-refit, t7-refit-review, t7-refit-review-2, t7-fit-review, t7-fit-review-2, t7-verify (t7-pnw-verify), merge-b (merge-2026-10-15b), t6b-run (t6b-run-2026-10-15), t4 (t4-master-grid), t5 (t5-host-trees), t6 (t6-observation-layer), host-genera-review (t6b-host-genera-review). Their branches remain, locally and on GitHub. t7-build's .pytest-tmp (796 MB of test scratch) was also cleared. /mnt/work went from 3.7 GB to 12 GB free (df). **A miscount:** the planner told the owner "17 folders"; the categories it named come to 19, with four T7 planning folders (t7-mycorrhizal-plan, t7-proposals, t7-searches, t7-strengthen-plan, about 13 MB each). Those four were not removed. Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2009.

---

**Kind:** outcome
**ID:** 2026-09-28-2009
**Timestamp:** 2026-10-19T05:21:40Z
**Continues:** 2026-09-28-2006
**Title:** W42 scored and on the site PR's preview; waiting on the owner's merge word
**Observed:**
- **The pull and scoring,** Ash Transect's report (pnw-pilot-w42, head d94e3ea): W42's weather is in its own read-only store, cds-2026-W42. Each of the three downloads matches the size and checksum the publisher states. W41's cds/ has all 143 files unchanged, and W41 reproduces with its manifest at 074879ff…4043. W42 scored, with the model unchanged and the prediction met: 2,618 cells scored, 231 from a land neighbour, 498 sea, 0 incomplete. Its manifest differs from W41's only in the fields Amendment 1 lists; chance_min, median and max are 0.0072, 0.04255 and 0.1598. Suite: 601 passed. The five revert checks bite.
- **The site:** zynergy-site PR #18 (pnw-pilot-w42-drop, 4da0360), two files only. Ash's preview check passed 71 of 71, with 8 skipped. The planner read the preview's two files and their hashes equal Ash's output (manifest 667372cc…, geojson 0a5c734e…); PR check SUCCESS, mergeable; manifest pilot true, validated false, reviewed true, beats_calendar false, weather_through 2026-10-11.
- **Deviations:** the dispatch's premise and line errors were corrected in Amendment 1. The W41 reproduction ran for about 8 seconds alongside t6b-night, under the 5G cap. Ash added a guard against writing through links in the shared rain aggregate.
- **Found:** t6b-night, paused for the scoring at 2026-10-19T05:12:40Z, failed its section commit, because its gzipped manifest copy (1,105,301 bytes) is over the 1 MiB guard. The tiles are safe in the manifest on the flash drive: 2,814 this section, 8,869 left. The fix is with the owner.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2010.

---

**Kind:** merge
**ID:** 2026-09-28-2010
**Timestamp:** 2026-10-19T10:40:21Z
**PR:** zynergy-site 18
**Head:** pnw-pilot-w42-drop (4da0360)
**Base:** zynergy-site main
**Merge-commit:** 585edaa8e3f954e042bc7f2566eb71a9890a131f
**Pre-merge:** 319871ca6c2eb3b748b1563937986c9840df33b6
**Backup:** ~/Zynergy/forager-repo-backups/zynergy-site-main-20261019T103912Z-319871ca.bundle, `git bundle verify` okay, sha256 beside it, a line appended to INDEX.md.
**Merged-by:** the forecast planner (Alder Bearing), on the owner's word in this window, 2026-10-19: "I'll take your recommendations", answering "Merge PR #18, putting W42 live? (Recommended)", which was put as the point of no return.
**Carries:** Forager/forecast/data/pnw-pilot/current/manifest.json and cantharellus.geojson for 2026-W42. GitHub merged it at 2026-10-19T10:39:28Z. Production (zynergy-labs.com) was serving both files about 30 seconds later, with hashes equal to Ash's output: manifest 667372cc…, geojson 0a5c734e…. Read by the planner.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2011.

---

**Kind:** terminal
**ID:** 2026-09-28-2011
**Timestamp:** 2026-10-19T10:40:21Z
**Closes:** 2026-09-28-2006
**Outcome:** done
**Observed:** W42 is live on the site with the model unchanged (2026-09-28-2009, -2010). Both predictions were checked: the cell counts equal W41's; the manifest differs only in the listed fields; W41 still reproduces.
**Deviations:** the dispatch premises corrected in Amendment 1; the 8-second W41 reproduction alongside t6b-night; the link guard Ash added to the shared rain aggregate. pnw-pilot-w42 stays unmerged to main, as W41's branch did (D40).
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2012.

---

**Kind:** intent
**ID:** 2026-09-28-2012
**Timestamp:** 2026-10-19T10:41:43Z
**Title:** t6b-night's nightly save: a small summary in git, the full manifest outside it
**Dispatch-file:** docs/dispatch/2026-10-19-t6b-progress-save.md (branch t6b-progress-save, c3697be)
**The owner, verbatim, 2026-10-19:** "I'll take your recommendations", answering "have Ash fix it first (Recommended)"; the hold: "Have the laptop coder pause for a bit" (relayed by Rowan Waymark).
**Change:** commit_progress commits, in place of the gzipped manifest, the manifest's sha256, size, line count and unit counts by stage and status. A gzipped copy is written outside every repository under /mnt/work/Zynergy/forecast-data/t6b/. A failed commit no longer crashes the section or leaves a block on the next one.
**Scope boundary:** nothing t6b computes or chooses; no change to the large-file guard; the committed manifest.jsonl.gz frozen, not removed; no nightly run started by the coder.
**Baseline:** the section commit refused at 2026-10-19T05:12:54Z (manifest.jsonl.gz 1,105,301 bytes over the 1,048,576 guard); 2,814 tiles done that section and 8,869 left, as the flash-drive manifest records; three staged files left in the runner's worktree.
**Prediction if it works:** the next section's commit is a few kilobytes, passes the guard, and its sha256 matches the flash-drive manifest.
**Prediction if it fails:** the commit still trips the guard, the sha256 doesn't match, or a failed commit still ends the run before the files outside git are written.
**Finish line:** Ash's report with the tests, the revert check and the summary checked against the manifest; then the planner restarts t6b-night.
**Abort conditions:** the dispatch's stops; the owner withdrawing it.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Held, not started, while the owner builds the Forager release on the laptop. Next free ID 2026-09-28-2013.

---

**Kind:** outcome
**ID:** 2026-09-28-2013
**Timestamp:** 2026-10-19T11:23:52Z
**Continues:** 2026-09-28-2012
**Title:** t6b's progress save fixed: a 991-byte summary in git, checked against the manifest; the lost section committed
**Observed:**
- **Ash Transect's report,** branch t6b-progress-save, head f7ccc87, which is also the runner worktree's HEAD and origin's. git now gets manifest_summary.json, and the full gzip goes to /mnt/work/Zynergy/forecast-data/t6b/manifest.jsonl.gz. Only named paths are committed. A failed commit or push is logged and exits non-zero; before this, the push failure was swallowed (scripts/t6b_run.py:561). The committed manifest.jsonl.gz is frozen at bf9c315, as its new README says. The guard is unchanged.
- **Tests:** 5 new tests, each failing on the old save. One failed for a reason other than its own, and the revert check (a whole-index commit) shows it bites. Suite: 609 passed. Ruff is red in one existing file, docs/audits/2026-10-15-t6b-host-genera-build/plot_table_real.py, which was already red at bf9c315 and is not this change.
- **The lost 2026-10-18 section** was committed as 99f6d93, after copies went to recovery-2026-10-19/ with SHA256SUMS.
- **A 10-minute check section,** t6b-check, 04:12 to 04:22 PDT: 30 units, exit 0, commit f7ccc87 a few kilobytes and pushed. The planner read the summary's sha256, ca33bbac…cece, and it equals both the flash-drive manifest's and the decompressed copy's.
- **Counts:** 8,839 units left of 22,473 (units are tile layers; the planner told the owner "tiles" earlier, corrected in chat).
**Deviations:** the planner cited 2026-09-28-2003 as covering Ash's check run. Ash noted that -2003 covers only the planner's own morning restarts. The check run rests on the owner's "Build is done. Continue" relayed with the dispatch, and that is how it is recorded.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. t6b-night's nightly restart is held while the planner asks Rowan whether two resident Gradle JVMs (about 3.7 GB) are idle. Next free ID 2026-09-28-2014.

---

**Kind:** merge
**ID:** 2026-09-28-2014
**Timestamp:** 2026-10-19T12:20:42Z
**PR:** 8
**Head:** forecast-record (bc19726)
**Base:** main
**Merge-commit:** 3650dbe571b0ba2d1a5a90119306d4f4d74e59d2
**Pre-merge:** b0bc10a4fc5d2ab8e9b3f77dd5b348f0f6803bc6
**Backup:** ~/Zynergy/forager-repo-backups/forecast-main-20261019T121954Z-b0bc10a4.bundle, `git bundle verify` okay, sha256 beside it, a line in INDEX.md. It covers this merge and -2015.
**Merged-by:** the forecast planner (Alder Bearing), on the owner's word in this window, 2026-10-19: "Merge 8 and 9 into main". GitHub merged it at 2026-10-19T12:20:09Z, with its check SUCCESS.
**Carries:** RECORD.md, entries 2026-09-28-2001 to -2013.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record, fast-forwarded to main after the merge. Next free ID 2026-09-28-2015.

---

**Kind:** merge
**ID:** 2026-09-28-2015
**Timestamp:** 2026-10-19T12:20:42Z
**PR:** 9
**Head:** forager-copy (98808ac)
**Base:** main
**Merge-commit:** eb59931d18d0d2948f2c27c9e1afd71802a88988
**Pre-merge:** 3650dbe571b0ba2d1a5a90119306d4f4d74e59d2
**Backup:** ~/Zynergy/forager-repo-backups/forecast-main-20261019T121954Z-b0bc10a4.bundle (taken before -2014; no other change landed between the two merges).
**Merged-by:** the forecast planner (Alder Bearing), on the same word: "Merge 8 and 9 into main". GitHub merged it at 2026-10-19T12:20:18Z, with its check SUCCESS.
**Carries:** records/from-forager.md, docs/preserved/, forager-app-and-forecast/; 40 files on main under those paths, read by the planner.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2016.

---

**Kind:** terminal
**ID:** 2026-09-28-2016
**Timestamp:** 2026-10-19T12:20:42Z
**Closes:** 2026-09-28-2007
**Outcome:** done
**Observed:** the copy is on main (-2015). The prediction was met exactly: 213 entries in records/from-forager.md and 40 in forager-app-and-forecast/entries.md; 20 forecast dispatches in docs/preserved/; 13 preserved files and 3 docs in forager-app-and-forecast/. Each file and each entry was checked byte-identical against Forager at 35c14780 before the commit (98808ac). Forager is unchanged.
**Deviations:** none.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2017.

---

**Kind:** terminal
**ID:** 2026-09-28-2017
**Timestamp:** 2026-10-19T14:12:08Z
**Closes:** 2026-09-28-2012
**Outcome:** done
**Observed:** the first nightly section under the fix ended at 07:00:38 PDT on 2026-10-19: 503 units, 0 failed, 8,336 left. It logged "progress save: committed and pushed 3061a8f", which is on origin/t6b-progress-save with the runner's tree clean. The planner read the summary's sha256, c00063fa…1b1a, and it equals the flash-drive manifest's. The prediction is met: the commit passed the guard, and the sha256 matches. t6b-night restarted at about 07:12 PDT for the next section. Memory peak 2.8 GB under the 5 GB cap.
**Deviations:** the check-run citation recorded in -2013.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. t6b-progress-save is unmerged; the runner runs from it until the owner's word (D40). Next free ID 2026-09-28-2018.

---

**Kind:** correction
**ID:** 2026-09-28-2018
**Timestamp:** 2026-10-19T20:20:57Z
**Corrects:** 2026-09-28-2008
**Title:** The worktree clean-up deleted T6's stored effort surface and T4's master grid, which were not in git
**Notes:** -2008, and the planner's proposal to the owner before it, said removing the folders lost nothing. That was wrong. The planner checked each worktree for uncommitted and unpushed work, and checked git-ignored files only in the large worktrees. In t4, t5 and t6 it did not check them. data/ is git-ignored (.gitignore, "Data never enters this repository"), and git worktree remove deletes ignored files without asking.
- **Lost:** T6's stored effort surface, data/t6/all/ and data/t6/cc/ in ~/Zynergy/forager-forecast-t6 (D107; T6 completion report :37-38, which files its sha256 values in 2026-10-06-t6-fit/stored_surface_sha256.txt). Also T4's master grid and archive, data/t4/ in ~/Zynergy/forager-forecast-t4 (58 MB; T4 completion report :94-118). No other copy was found: a search of ~/Zynergy and the T6b drive for effort_manifest.json found none.
- **Not lost:** T5's data/t5 was a symlink to the flash drive (T5 verify report :16-17), and its 9.9 GB there is intact. D26's zip is in forager-forecast-d26, which was kept.
- **What depends on them:** T7's scripts read T6's surface from the removed path (forager-forecast-t7-build scripts/t7_fit.py:76, scripts/t7_v9_counts.py:90). T8's plan needs it as effort. No reader of T4's grid was found outside its own build script. t6b-night does not read either.
- **The way back:** T6's surface can be rebuilt by re-running T6's fit at its code commit ef3269f from D26's zip, and checked against the filed sha256 values. That re-runs a count and a fit, so it needs the owner's word. T4's grid needs a re-download from ISRIC, which also needs the owner's word.
- **The lesson,** for this planner: a worktree's git state does not cover its git-ignored data. Before removing one, list its ignored files, and treat any data/ found there as data, not scratch.
Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2019.

---

**Kind:** merge
**ID:** 2026-09-28-2019
**Timestamp:** 2026-10-19T21:32:05Z
**PR:** 10
**Head:** coder-profile-scratch (ef286fc)
**Base:** main
**Merge-commit:** 80f61a8caca366685c4b3e4482a72e2d28e45edf
**Pre-merge:** eb59931d18d0d2948f2c27c9e1afd71802a88988
**Backup:** ~/Zynergy/forager-repo-backups/forecast-main-20261019T213147Z-eb59931d.bundle, `git bundle verify` okay, sha256 beside it, a line in INDEX.md.
**Merged-by:** the forecast planner (Alder Bearing), on the owner's word in this window, 2026-10-19: "Merge 10". GitHub merged it at 2026-10-19T21:31:50Z, with its check SUCCESS. The owner had first answered "Merge it (Recommended)" in Rowan Waymark's window.
**Carries:** docs/process/coder-profile.md. The role table names Alder Bearing as planner and this repository's RECORD.md as the record. A new line says scratch goes in /mnt/work/scratch/<branch>/, never /tmp (Forager RECORD -1374). Ash writes in neither record.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2020.

---

**Kind:** intent
**ID:** 2026-09-28-2020
**Timestamp:** 2026-10-19T21:33:14Z
**Title:** Rebuild T6's stored effort surface at ef3269f, and re-download and rebuild T4's master grid and pH archive, each checked against its filed record (owner)
**Dispatch-file:** docs/dispatch/2026-10-19-t6-rebuild.md (branch t6-rebuild, 177fdb0); docs/dispatch/2026-10-19-t4-rebuild.md (branch t4-rebuild, 4c6edab), run after T6
**The owner, 2026-10-19, in the planner's window:** a go to rebuild T6's effort surface, provided that Ash stops and reports if the rebuilt files do not match the checksums exactly. Then, on T4, verbatim: "Re-download T4 actually".
**Change:** T6's count and fit re-run from D26's zip with the code at ef3269f, the surface going to ~/Zynergy/forecast-data/t6/. Then T4's ISRIC fetch and build re-run into ~/Zynergy/forecast-data/t4/. Both are outside every repository, and made read-only.
**Scope boundary:** no code change; nothing re-run with changes; a changed T4 source not adopted without the owner; T7's scripts and T8 untouched; t6b-night paused and resumed by the planner only.
**Baseline:** the deletion, per correction 2026-09-28-2018. For T6, the filed hashes in docs/audits/2026-10-06-t6-fit/stored_surface_sha256.txt (10 files). For T4, the request record docs/pulls/soilgrids-phh2o-western-washington-0-30cm.request.json (ETags and subset sha256) and the completion report's master.tif and archive hashes.
**Prediction if it works:** all eight T6 CSVs match their filed sha256 exactly, with each manifest matching too or differing only in a time of writing. T4's nine VRTs match ISRIC's checksums, and every subset, master.tif and the archive match theirs.
**Prediction if it fails:** a T6 CSV hash differs, meaning the fit is not reproducible from these inputs. Or a T4 subset differs, meaning the publisher's data changed since 2026-10-06. Either goes to the owner.
**Finish line:** both sets of hashes matched and the evidence filed, or a reported difference for the owner.
**Abort conditions:** the dispatches' stops.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2021.

---

**Kind:** outcome
**ID:** 2026-09-28-2021
**Timestamp:** 2026-10-19T21:46:41Z
**Continues:** 2026-09-28-2020
**Title:** T6's effort surface rebuilt byte for byte and stored outside every repository
**Observed:**
- **Ash Transect's report,** branch t6-rebuild (b2bf40e, b9e22b2): the count (3 min 26 s) and the fit (2 min 38 s) ran at ef3269f from D26's zip. The zip's sha256 was checked first (c0d5f6a1…b26c, equal to docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json:11).
- **The hashes:** all 10 stored files match the filed values, 8 CSVs and 2 manifests, first in scratch and again in ~/Zynergy/forecast-data/t6/. The manifests carry no time of writing; Ash predicted both hashes before the run. In steps.json and the two results files, only seconds and peak_rss_kb differ. A tamper control showed the comparison detects a one-digit change.
- **Read-only:** files 0444, folders 0555.
- **The planner's own check:** sha256sum -c of the filed list against ~/Zynergy/forecast-data/t6/, 10 of 10 OK.
**Deviations:** Ash's harness refused to write the report file, so the report is this entry and Ash's message. T7's scripts still name the old path (scripts/t7_fit.py:76 on t7-build); T7 is stopped, and they are left as they are.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. T4's rebuild is next, with t6b-night still paused. Next free ID 2026-09-28-2022.

---

**Kind:** terminal
**ID:** 2026-09-28-2022
**Timestamp:** 2026-10-19T22:05:08Z
**Closes:** 2026-09-28-2020
**Outcome:** done
**Observed:**
- **T6:** rebuilt byte for byte, all 10 files, and stored read-only in ~/Zynergy/forecast-data/t6/ (2026-09-28-2021).
- **T4:** Ash Transect's report, branch t4-rebuild (2d51bfd, c0296e2), with no code changed. The ISRIC fetch ran 21:52 to 21:57 UTC and the build to about 22:01. The nine VRTs match both ISRIC's checksum file and the 2026-10-06 values. request.json is equal on every field except requested_at. The nine subsets, re-written in scratch with their filed tags, match their filed sha256, so ISRIC's pixels in T4's window are unchanged. The ten-cell output is byte-identical to ten_cells_real.json. The store is ~/Zynergy/forecast-data/t4/, 58 MB, read-only. A data-register row was added, with ISRIC's licence quoted as read at fetch time.
- **The planner's own read:** master.tif 9fe55bc2…, 14,685,784 bytes; the archive 84905e33…, 891,388 bytes; both equal the filed values.
- **t6b-night** restarted at 15:04 PDT, after both rebuilds.
**Deviations:**
- **-2020's prediction was wrong for T4's subsets.** fetch_layer stamps the fetch time into each subset's tags (src/forager_forecast/soilgrids.py:137, :170), so a re-fetch can't match the raw hashes. Ash found this before fetching, and the dispatch's Amendment 1 changed the check to re-tagged copies plus master.tif, the archive and the ten cells.
- **Ash's first comparison script** took the CRS from the GeoTIFF, not the VRT, and matched 0 of 9. A positive control on the real files located the cause, and the corrected script matched 9 of 9. Both versions are filed. The planner accepted the correction: it fixed a check, not the data.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2023.

---

**Kind:** intent
**ID:** 2026-09-28-2023
**Timestamp:** 2026-10-19T22:32:51Z
**Title:** Write T8's plan: a second, stricter PNW test of whether weather beats the calendar (the forecast planner)
**The owner, verbatim:** "A: Second, stricter PNW weather test (Recommended)" (Forager RECORD -1250); 2026-10-19, in this window: "Go on T8 plan". On who writes it: "The EGD standard is that whoever writes the code shouldn't write the plan and vice versa" (2026-10-17, relayed by Rowan Waymark).
**Change:** one plan document, written by the planner, ending in numbered decisions for the owner, each with a recommendation. Ash's paused draft (t8-plan d6f916a) is read as findings. Every figure is re-read from its source, or checked by a read-only helper on a model other than Ash's.
**Scope boundary:** the plan only. No download, count, fit or publish. No code. Nothing on main.
**Baseline:** T1's PNW result, Brier skill −0.0035 [−0.0066, −0.0001], verdict "worse" (docs/audits/2026-10-10-pnw-pilot-t1-report.md:288-298). Forager RECORD -1249 and -1250. Forager RECORD -1248, closed there as partial by -1252, with the plan passed to this role.
**Prediction if it works:** a plan of about 8 owner decisions, with T1's units, effort from T6, a few weather measures fixed in advance, and a bar fixed before any result. The biggest choice is how strict the turnout guard is.
**Prediction if it fails:** a premise found wrong that changes T8's shape, brought to the owner as a stop.
**Finish line:** the plan pushed, and its decisions put to the owner.
**Abort conditions:** the owner withdrawing T8; a premise that needs a count or fit to settle, which becomes a decision instead.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2024.

---

**Kind:** decision
**ID:** 2026-09-28-2024
**Timestamp:** 2026-10-20T01:02:33Z
**Continues:** 2026-09-28-2023
**Title:** T8's plan accepted as written: all eight decisions as recommended (owner)
**What the owner was told before answering:** the plan's eight decisions, each with its recommendation (docs/dispatch/2026-10-19-t8-plan.md, section 10, on t8-plan-alder 4cd0bd4), with decision 5, the turnout guard, named as the one real trade-off.
**The owner, verbatim, 2026-10-19:** "All recommended".
**What it sets:** decision row D133 (t8-plan-alder), quoting the eight rulings. It sets aside SPEC.md:44 and TASKS.md:89 for this test, and makes T9 depend on T8 alone for the PNW.
**Not authorised by this:** the build. The go is asked separately, and so are the two points of no return: counting, and fitting.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2025.

---

**Kind:** terminal
**ID:** 2026-09-28-2025
**Timestamp:** 2026-10-20T01:02:33Z
**Closes:** 2026-09-28-2023
**Outcome:** done
**Observed:** the plan was pushed (t8-plan-alder 4cd0bd4) with eight decisions, and the owner accepted all eight (-2024). The prediction held: about 8 decisions, with the turnout guard as the biggest choice. Juniper Sounding (Fable) checked the figures and found three citation errors, all fixed before the push: D121 gives about 1,200 records, not 1,100; T6's run time is at :174-175; the weather arrays carry _points and _values suffixes.
**Deviations:** none.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2026.

---

**Kind:** merge
**ID:** 2026-09-28-2026
**Timestamp:** 2026-10-20T02:14:47Z
**PR:** 11
**Head:** t8-plan-alder (a480374)
**Base:** main
**Merge-commit:** 82fa9e4f1903ad1431dfad2dd3601d0bc2ebc976
**Pre-merge:** 80f61a8caca366685c4b3e4482a72e2d28e45edf
**Backup:** ~/Zynergy/forager-repo-backups/forecast-main-20261020T021422Z-80f61a8c.bundle, `git bundle verify` okay, sha256 beside it, a line in INDEX.md.
**Merged-by:** the forecast planner (Alder Bearing), on the owner's word in this window, 2026-10-19: "Merge the plan branch to main when ready". GitHub merged it at 2026-10-20T02:14:40Z, with its check SUCCESS.
**Carries:** docs/dispatch/2026-10-19-t8-plan.md and decision row D133.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2027.

---

**Kind:** intent
**ID:** 2026-09-28-2027
**Timestamp:** 2026-10-20T02:16:03Z
**Title:** Build T8 up to the count: its rules, code and tests over synthetic data (step 1 of the plan's order)
**Dispatch-file:** docs/dispatch/2026-10-20-t8-build.md (branch t8-build, f72dbc7)
**The owner, verbatim, 2026-10-19:** "Yes, start it.", answering "Shall I write the dispatch and start Ash on step 1?".
**Change:** code and tests for the jump check, the unit table, the weather measures, the models, the bar and the report-beside items, as the plan (docs/dispatch/2026-10-19-t8-plan.md) and D133 set them.
**Scope boundary:** no real records, outcomes or weather read; no count; no fit; no decision rows; nothing on main.
**Baseline:** the plan and D133 on main 82fa9e4. T6's counts copied out of scratch by the planner to ~/Zynergy/forecast-data/t6-counts/, read-only, with SHA256SUMS (5 files).
**Prediction if it works:** every condition C1 to C4 shown to bite on synthetic data, by tests and by revert checks, with the count and fit commands ready.
**Prediction if it fails:** a plan rule that can't be built as written, which comes back as a stop.
**Finish line:** Ash's step-1 report, then a stop for the owner's word to count.
**Abort conditions:** the dispatch's stops.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2028.

---

**Kind:** terminal
**ID:** 2026-09-28-2028
**Timestamp:** 2026-10-20T03:41:04Z
**Closes:** 2026-09-28-2027
**Outcome:** done
**Observed:** step 1 is built on t8-build (d9c12ba; Ash's report filed at docs/audits/2026-10-20-t8-step1/report.md, 09c4408). The full suite passed (686 tests), and C1 to C4 and the two identity checks were each revert-checked. The prediction held, with one finding the prediction didn't foresee. Every statsmodels fit left reference cycles that held its arrays, so memory grew with each fit. The first session's test run reached 7.4 GB at 2026-10-20T02:53Z, and the laptop ran out of memory: that killed the session, the forecast planner session and the app planner's helpers. The planner killed a rerun at 3.7 GB (03:01Z). Fixed in 2a47ccc, which collects the cycles; the test was seen failing first (1974c35). The suite's peak is now 914 MB. It would have hit the real fits harder. Step 1 took three resumed sessions; the first one's unfinished work was committed as found (c98773b) and kept.
**Deviations:** 19 readings that the plan left open came back as a stop: 8 for the count and 11 for the fit. The plan should have settled them; that's the planner's miss. Genus keys are read from the zip, not the GBIF API, so the count makes no network call.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2029.

---

**Kind:** decision
**ID:** 2026-09-28-2029
**Timestamp:** 2026-10-20T03:41:04Z
**Continues:** 2026-09-28-2027
**Title:** The count's eight open readings ruled (owner)
**What the owner was told before answering:** the jump years, with three options. The planner recommended 2024 and 2025 each, over Ash's 2023 to 2024 only. Then the other seven count readings, with Ash's proposals stated in plain words.
**The owner, verbatim, 2026-10-20:** "2024 and 2025 each (Recommended)"; "Accept all 7 (Recommended)".
**What it sets:** decision row D134 (t8-build).
**Not authorised by this:** the fit. Its 11 readings are still open.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2030.

---

**Kind:** intent
**ID:** 2026-09-28-2030
**Timestamp:** 2026-10-20T03:41:04Z
**Title:** Build in D134, then run T8's count: the jump check and the lichen attach (the first point of no return)
**The owner, verbatim, 2026-10-20:** "Yes, run the count", answering "Once these are ruled and written down, may Ash run the count? It's the first point of no return: about 5 minutes, under 1.5 GB of memory, with a hard memory cap."
**Change:** Ash enters D134 in RULED, changes the J-rise code to take both years, and then runs scripts/t8_count.py once under a 3 GB cap.
**Scope boundary:** no fit, and no weather read. The fit readings stay unruled.
**Baseline:** t8-build after D134. Inputs: D26's zip (sha256 checked by the script), T1's units, T6's counts.
**Prediction if it works:** the count reproduces T1's three unit lists exactly, and the jump check returns one of the three labels for each year.
**Prediction if it fails:** an identity refusal, where the units differ from T1's, which comes back as a stop.
**Finish line:** Ash's count report; the label goes to the owner.
**Abort conditions:** any refusal; memory over the cap; any network call.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2031.

---

**Kind:** terminal
**ID:** 2026-09-28-2031
**Timestamp:** 2026-10-20T03:57:24Z
**Closes:** 2026-09-28-2030
**Outcome:** stopped
**Observed:** the count ran once (03:46:58Z, t8-build 053c98c, 3 min 48 s, 1.4 GB peak, under the 3 GB cap). The zip's sha256 matched, and 252,818 of 2,493,578 rows fell in the box. It then refused with `CountRefused: J5 genus names without exactly one genusKey in the zip: {'Amanita': [2526057, 6005964, 7237597]}`. Nothing was written and no network call was made. The refusal came before T1's units, so neither prediction was tested. J-rise was built in first (e93177a), and its tests were seen failing first (1d1e1a7).
**Deviations:** none. The refusal is the abort condition working.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2032.

---

**Kind:** decision
**ID:** 2026-09-28-2032
**Timestamp:** 2026-10-20T03:57:24Z
**Continues:** 2026-09-28-2031
**Title:** Amanita counted under all three keys; the same dataset in both comparisons (owner)
**What the owner was told before answering:** that GBIF's taxonomy shows all three keys are the mushroom Amanita, one accepted and two doubtful duplicates. The alternatives were the accepted key only, or swapping the genus. Then the dataset reading: the same dataset in both years, or any in each year.
**The owner, verbatim, 2026-10-20:** "Count all three (Recommended)"; "Same source both years (Recommended)"; "Yes, rerun", answering "With those settled, may Ash fix the code and rerun the count once? About 4 minutes, 1.4 GB."
**What it sets:** D135 (t8-build).
**Not authorised by this:** the fit.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2033.

---

**Kind:** intent
**ID:** 2026-09-28-2033
**Timestamp:** 2026-10-20T03:57:24Z
**Title:** Build in D135, then rerun T8's count once
**Change:** Amanita's three keys fixed in code; the same-dataset condition across both comparisons; tests seen failing first; then one run of scripts/t8_count.py under a 3 GB cap.
**Scope boundary:** as in -2030: no fit, no weather, no network.
**Baseline:** t8-build after D135.
**Prediction if it works:** the count reproduces T1's three unit lists exactly, and the jump check returns a label for each comparison and overall.
**Prediction if it fails:** an identity refusal, or another refusal at the genus step, which comes back as a stop.
**Finish line:** Ash's count report.
**Abort conditions:** any refusal; memory over the cap; any network call.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2034.

---

**Kind:** terminal
**ID:** 2026-09-28-2034
**Timestamp:** 2026-10-20T04:10:19Z
**Closes:** 2026-09-28-2033
**Outcome:** done
**Observed:** the count ran once (04:04:18Z to 04:08:09Z, t8-build 0cb9566, 325.8 MB peak, no network). All three of T1's unit lists were reproduced exactly: 52,718, 56,927 and 9,640 units. 24.9% of headline units are lichen-positive. The jump check reads undetermined, overall and for 2024 and 2025 each. Observers rose from 73 to 241 and 230, no reporting-led condition holds, and only 1 of 6 genera (Hydnum) rose 1.5x. The outputs are read-only in ~/Zynergy/forecast-data/t8/count/ with SHA256SUMS, and the planner checked the sha256 values. The report is at docs/audits/2026-10-20-t8-step1/count-report.md. The "if it works" prediction held. The summary is not committed, because it holds per-cell rises and the repository is public.
**Deviations:** none.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2035.

---

**Kind:** decision
**ID:** 2026-09-28-2035
**Timestamp:** 2026-10-20T04:14:32Z
**Continues:** 2026-09-28-2034
**Title:** T8's eleven fit readings ruled, and the go to fit after t6b-night (owner)
**What the owner was told before answering:** the nine routine settings, each stated in plain words. The challenger's shuffle check, named as the one trade-off: keep the tuning and say it is slightly generous, report it only, or re-tune every swap (days). When to fit: after t6b-night, pause t6b now, or not yet.
**The owner, verbatim, 2026-10-20:** "Accept all nine (Recommended)"; "Keep tuning, say so (Recommended)"; "After t6b-night (Recommended)", answering "The fits are your second point of no return: about 5 to 10 hours of computing, run one at a time. When should they run?"
**What it sets:** D136 (t8-build). The second point of no return is passed, with the fits to start only once t6b-night has finished.
**Not authorised by this:** publishing anything; any third weather test.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2036.

---

**Kind:** intent
**ID:** 2026-09-28-2036
**Timestamp:** 2026-10-20T04:14:32Z
**Title:** Build in D136, then, once t6b-night has finished, run T8's fits one at a time
**Change:** Ash enters D136 in RULED and adds the challenger's "slightly generous" label, with tests, then stops. After t6b-night finishes, the fits run in the order of Ash's step-1 report: bar, forecast, alone, challenger and ecoregion on t1_1000m, then bar on t1_5000m and t1_1000m_cc. Each runs under a 3 GB cap.
**Scope boundary:** nothing published; no change to any ruled reading; no fit beside t6b-night.
**Baseline:** t8-build after D136; the count outputs in ~/Zynergy/forecast-data/t8/count/ (SHA256SUMS).
**Prediction if it works:** a verdict from the bar on the headline list (pass, or fail with the failing condition named), and every report-beside item labelled no verdict.
**Prediction if it fails:** an identity refusal, a hit on the cap, or tied spline knots in an ecoregion block, any of which comes back as a stop.
**Finish line:** Ash's fit report, then the two independent reviews (Sorrel, on Fable and on Sonnet).
**Abort conditions:** any refusal; memory over the cap; t6b-night running at the same time.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2037.

---

**Kind:** decision
**ID:** 2026-09-28-2037
**Timestamp:** 2026-10-21T14:24:07Z
**Continues:** 2026-09-28-2036
**Title:** T8's fits start now, before t6b's remaining stages (owner)
**What the owner was told before answering:** t6b-night's scanfi-layers stage finished at 2026-10-21T12:57Z ("4092 ok, 0 failed, 0 left, all units done", host-genera-build 83bd659), and the unit is no longer running. The trees stage probably still has Canadian work left, inferred from tree_unit in scripts/t6b_run.py and not measured. The options: fits now and t6b after, t6b first, or hold both.
**The owner, verbatim, 2026-10-21:** "T8 fits now, t6b after (Recommended)".
**What it sets:** -2036's start condition ("once t6b-night has finished") now reads: the fits start now, one at a time, and t6b's next stage resumes only after them. Nothing runs side by side.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2038.

---

**Kind:** decision
**ID:** 2026-09-28-2038
**Timestamp:** 2026-10-21T19:31:43Z
**Continues:** 2026-09-28-2036
**Title:** The 5,000 m side run drops its 33 cells outside T6's frame (owner)
**What the owner was told before answering:** the fit runner stopped at 17:54Z on t1_5000m bar with NoEffortValue (33 cells not in T6's frame). The headline bar and the forecast, alone, challenger and ecoregion parts on t1_1000m had finished, and their outputs were locked read-only with SHA256SUMS. The options: drop the 33 cells, skip the run, or stop both remaining side runs.
**The owner, verbatim, 2026-10-21:** "Drop those 33 cells (Recommended)".
**What it sets:** D137 (t8-build).
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2039.

---

**Kind:** terminal
**ID:** 2026-09-28-2039
**Timestamp:** 2026-10-21T21:01:46Z
**Closes:** 2026-09-28-2036
**Outcome:** done
**Observed:** all seven fit parts ran, one at a time, each under a 3 GB cap (peaks 862 to 915 MB). The headline bar on t1_1000m FAILS all of C1 to C4. C1 −0.01108 [−0.01762, −0.00503]; C2 −0.00138 [−0.00405, +0.00086]; C3 p = 0.870; C4 +0.00215 [+0.00027, +0.00394], so weather "predicts" lichen reports. Every no-verdict part points the same way. The forecast timing fails C1 to C4. The challenger fails C1 to C3 with C3 labelled generous, and passes C4. The 5,000 m list fails C1 to C4 after D137's drop of 34 units. The cc list fails C1 to C3. The "if it works" prediction held: a verdict with the failing conditions named. Results are at docs/audits/2026-10-21-t8-fit/results.md (t8-build); the outputs are read-only, with SHA256SUMS for all 14 files.
**Deviations:** the 5,000 m run stopped once on NoEffortValue, settled by the owner (-2038, D137). The fit sessions were forced to hand back several times, so the chain was finished by a session-independent runner (scripts/t8_fit_runner.sh, 88fac57 and c48be9f). 19% of ecoregion units fall in no CEC polygon; not yet explained.
**What follows (D133 (7)):** this is the second "no" for the PNW, and it is the PNW finding. Nothing weather-based is published for the PNW, and there is no third weather test on these records without new data and the owner's word. Next are the two independent Sorrel reviews.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2040.

---

**Kind:** decision
**ID:** 2026-09-28-2040
**Timestamp:** 2026-10-21T21:17:30Z
**Continues:** 2026-09-28-2039
**Title:** T8's two reviews started, t6b resumed, and the rest of the US first in t6b's tree stage (owner)
**What the owner was told before answering:** (1) the reviews (Sorrel on Fable and on Sonnet, read-only) and t6b's resume, with both recommended. (2) After Juniper Sounding's read-only check, which found only the trees stage has work, 3,775 of 4,058 tiles (2,033 Canadian never built whole, 1,742 US tiles of the old band layout, rebuilt with the old ones moved aside and kept), about 1.5 to 3 days: the order, rest of US first, the code's north-first order, or Canada first. The planner said its earlier "about two more nights" was the layer stage only; the trees stage was not measured then.
**The owner, verbatim, 2026-10-21:** "Start both (Recommended)"; "Rest of US first (Recommended)".
**What it sets:** the reviews' dispatch is docs/dispatch/2026-10-21-t8-review.md (t8-build fb14478). t6b-night was restarted at 21:15Z from host-genera-build 83bd659 as `t6b_run.py --until 07:00 --stages trees --workers 2 --box 24,49,-125,-66` under the handoff's unit properties (5G, swap off, Nice 10). The box is the lower 48. Alaska and Hawaii can't be in one box with it without taking in Canada, so they run in the sections after, together with Canada, by the code's order; the planner's call within the owner's "rest of the US first".
**Review outcome:** both reviews confirm the headline FAIL by recomputation, and neither finds a departure from the plan or a leak (review-fable.md, review-sonnet.md, t8-build 80efc95, 54b745a). Both find C2's loss carried by the 2021 fold's spline extrapolation, and C1's gap mostly model form. Both found that the per-year table, AUC and reliability were missing from results.md; they were appended at a8c2c49.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2041.

---

**Kind:** decision
**ID:** 2026-09-28-2041
**Timestamp:** 2026-10-22T04:03:11Z
**Continues:** 2026-09-28-2040
**Title:** t6b-night was killed out of memory 23 minutes after -2040's restart; restarted with one worker (owner)
**Corrects:** the 2026-10-21 handoff (77ad3b2), which says t6b-night "is running" until 07:00 PDT. It was not: `systemctl --user status t6b-night` read "failed (Result: oom-kill) since Wed 2026-10-21 14:38:56 PDT", duration 23 min 28 s, memory peak 4.3G, about an hour before the handoff was written. How far it got in the box was not measured.
**What the owner was told before answering:** the kill above; that the handoff's standing permission to restart covers only after 07:00 PDT; that memory was tight (`free -h`: 8.1Gi available, swap 2.3 of 4.0Gi used). The options: restart with one worker (half the memory, about half the speed, still stopping at 07:00), restart as before with two, or leave it off tonight.
**The owner, verbatim, 2026-10-21:** "Restart, 1 worker (Recommended)".
**What it sets:** t6b-night was restarted at 2026-10-22T04:02Z from host-genera-build 83bd659, no PAUSE file present, as `t6b_run.py --until 07:00 --stages trees --workers 1 --box 24,49,-125,-66` under the same unit properties (MemoryMax=5G, MemorySwapMax=0, Nice=10). Active 20 s after start.
**Also observed:** `/` showed 6.1G free and `/mnt/work` 2.2G at 2026-10-22T04:00Z (`df -h`), against the handoff's 0 and 1.7 GB; who freed it was not asked. The handoff file the full disk left as deleted in the forecast-record worktree was restored with `git checkout -- docs/planning/handoffs/`, as the handoff said to.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2042.

---

**Kind:** decision
**ID:** 2026-09-28-2042
**Timestamp:** 2026-10-22T04:03:11Z
**Continues:** 2026-09-28-2039
**Title:** The PNW answer goes forward as a plain write-up of the finding first (owner)
**What the owner was told before answering:** the handoff's answer to "Can the PNW be published?": not as a forecast (SPEC R2, D133 (7)). The options: (a) a plain write-up of what the PNW test found, no map, needing no new product decision; (b) a "usual season" map with no forecast claim, a new product decision with a plan first; (c) new data, then a third test, needing the owner's word before anything is pulled; or hold.
**The owner, verbatim, 2026-10-21:** "(a) Write-up first (Recommended)".
**What it sets:** the planner drafts the write-up next, under its own intent, using the wording both T8 reviews required ("this fixed additive design showed no weather gain", not "weather has no effect"). Publishing it anywhere is a point of no return (-1030) and needs the owner's word, asked then. (b) and (c) are neither taken nor ruled out.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2043.

---

**Kind:** intent
**ID:** 2026-09-28-2043
**Timestamp:** 2026-10-22T04:10:23Z
**Continues:** 2026-09-28-2042
**Title:** Draft the plain write-up of the PNW finding
**Scope boundary:** one Markdown file, `docs/audits/2026-10-21-pnw-finding.md`, on a new branch `pnw-finding-writeup` cut from t8-build a8c2c49, because every figure it cites lives there. Prose only, written by the planner: no code, no script, nothing re-run or re-computed, no output file read beyond what results.md, headline-bar.md, the two reviews, count-report.md, the T1 report and DECISIONS.md already state. Not merged, not published, not linked from the site or Forager; each of those is a point of no return (-1030) for the owner's word.
**Baseline:** no write-up exists. The finding is spread across T1's report (pnw-pilot-t1-report.md:288-298), T8's results.md and its two reviews, count-report.md, and D133 (7).
**Prediction if it works:** a file a non-specialist can read in a few minutes: what was asked, what was tested, what came out, what it does and does not mean, and what could change it. Every figure is cited to its file. The reviews' wording holds ("this fixed additive design showed no weather gain", not "weather has no effect"), and none of D58's forbidden terms appear.
**Prediction if it fails:** a claim that can't be cited from the files above, which is then marked as not checked or dropped, not stated.
**Finish line:** the draft committed and pushed to pnw-finding-writeup, and put to the owner to read.
**Abort conditions:** a source contradicts another on a figure the write-up needs; that goes to the owner first.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2044.

---

**Kind:** merge
**ID:** 2026-09-28-2044
**Timestamp:** 2026-10-22T04:19:11Z
**PR:** 12
**Head:** t8-build (a8c2c49)
**Base:** main
**Merge-commit:** 7c11635690c371cfb14b7a0a7924fa18616978d7
**Pre-merge:** 82fa9e4f1903ad1431dfad2dd3601d0bc2ebc976
**Backup:** ~/Zynergy/forager-repo-backups/forecast-main-20261022T041209Z-82fa9e4f.bundle, `git bundle verify` okay, sha256 beside it, a line in INDEX.md.
**Merged-by:** the forecast planner (Alder Bearing), on the owner's word in this window, 2026-10-21: "merge t8-build and forecast-record to main". GitHub merged it at 2026-10-22T04:18:27Z, with its check SUCCESS (4m47s).
**Carries:** T8's code (src/forager_forecast/t8/, its scripts and tests), D134 to D137, the T8 dispatches, docs/audits/2026-10-20-t8-step1/ and docs/audits/2026-10-21-t8-fit/ (results and both reviews).
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2045.

---

**Kind:** merge
**ID:** 2026-09-28-2045
**Timestamp:** 2026-10-22T04:19:11Z
**PR:** 13
**Head:** forecast-record (0e16249)
**Base:** main
**Merge-commit:** 02756bb77417d3bfd684aae09f5e46068cde3d3a
**Pre-merge:** 7c11635690c371cfb14b7a0a7924fa18616978d7
**Backup:** the same bundle as -2044 (main before both merges).
**Merged-by:** the forecast planner (Alder Bearing), on the same word as -2044. GitHub merged it at 2026-10-22T04:18:41Z, with its check SUCCESS (2m52s, run against the pre-#12 base; the two branches touch no file in common).
**Carries:** RECORD.md through 2026-09-28-2043 and docs/planning/handoffs/2026-10-21-planner-handoff.md. This entry and later ones stay on forecast-record until its next merge.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2046.

---

**Kind:** note
**ID:** 2026-09-28-2046
**Timestamp:** 2026-10-22T14:01:41Z
**Continues:** 2026-09-28-2041
**Title:** t6b-night's one-worker night: 478 tiles, none failed; restarted for the day with one worker
**Observed:** the section run from -2041 ended at its stop time, 2026-10-22T07:00 PDT: "trees: 478 ok, 0 deferred, 0 failed, 1409 left" (host-genera-build a237798, its own progress-save commit). About 50 tiles an hour, so the 1,409 left in the lower-48 box take about 28 more running hours (inferred from that rate).
**What it sets:** t6b-night restarted at 2026-10-22T14:01Z from host-genera-build a237798, no PAUSE file present, with -2041's command and unit properties (one worker). It is under the standing restart permission (-2003), which keeps the owner's one-worker choice of -2041; the owner was told.
**Notes:** Written by the forecast planner (Alder Bearing) by hand, on branch forecast-record. Next free ID 2026-09-28-2047.
