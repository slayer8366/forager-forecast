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
