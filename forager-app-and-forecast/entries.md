# Entries covering both the Forager app and the forecast

Copies of the 40 entries in Forager's record (slayer8366/Forager, RECORD.md, branch records-after-173, commit 35c14780) that concern both the Forager app and forager-forecast, or sit on the boundary between them. Each is byte for byte as it stands there, with its original ID, in its original order. Forager keeps every original, unchanged. See `README.md` in this folder.

## Entries

---

**Kind:** dispatch-note
**ID:** 2026-09-23-06
**Dispatch-file:** preserved/2026-09-23-03.md
**Type:** pulse
**Outcome:** answered
**Report:** none: the pulse ended without a hand-back; the planner received no report

---

**Kind:** intent
**ID:** 2026-09-23-16
**Timestamp:** 2026-09-23T05:09:11Z
**Title:** Claim six colliding preserved prompts from two other checkouts under new names; PR this branch to Forager main
**Dispatch-file:** preserved/2026-09-23-09.md
**Change:** Copy six untracked preserved prompts byte for byte into prompts/preserved/ on this branch under the next free names after this dispatch's own 2026-09-23-09.md, in order of their Preserved timestamps: E (bridge-cse_016CLyXZt76dm7Hr3APUi1Sz 2026-09-23-01.md) to 2026-09-23-10.md, F (same checkout, 2026-09-23-02.md) to -11, A (bridge-cse_019uZR3mJKzHkDaCv5fGnsuk 2026-09-23-01.md) to -12, B (same, -02) to -13, C (same, -03) to -14, D (same, -04) to -15; append one dispatch-note per copy, IDs 2026-09-23-17 to -22, each naming the original checkout, name and SHA-256 and saying the original is a superseded copy that must not be swept again; close this intent; open a PR from this branch to Forager main. Before this intent, and under the same dispatch's planner amendment, 2026-09-23-07 was closed by 2026-09-23-15 after its checks passed and ~/Zynergy/forager-forecast-merge-d55 was removed. Finding (owner ruling "Record only"; the fix goes to the kit's backlog): dispatch_guard.py takes root from the session's own git rev-parse --show-toplevel (.claude/hooks/dispatch_guard.py:127) and numbers each prompt as one past the highest <date>-NN.md in that checkout's prompts/preserved/ only (:62-66), so parallel sessions in different worktrees each take the same numbers.
**Scope boundary:** In Forager: RECORD.md and prompts/preserved/ on branch worktree-bridge-cse_01Md1NYxk9qgG8y6g7CiSm3y, pushed, and a PR to main that the owner merges. The two other checkouts are read-only: their originals are neither edited, moved nor deleted. No hook, test, settings or checker change. In forager-forecast: only the worktree removal already done under the amendment; no file touched.
**Baseline:** Forager branch at 841ac87 (equal to its origin), record IDs to 2026-09-23-14 with 2026-09-23-07 the only open intent, preserved prompts committed to 2026-09-23-08.md with 2026-09-23-09.md (this dispatch) untracked; Forager origin/main 624173b; git diff --stat origin/main...HEAD touches RECORD.md and prompts/preserved/ only. The six originals hash E 7c878986f7829d34d6f53aed3c7335eebdaeb58c0160da4570715dcf91279a5c, F f5ad31a43f20cdea4b5ee7a77f42640ad8dabc94356bf94a838ffa409073cd69, A e1e6d9906a42f3bc74525a0d9ed4e8349b8e72c41c238815d7b81fdbd331bbc8, B c0b1139be7731af1f1f56b5ac38a255bdc9036bd57bece939c7c85b47b592f81, C 965fdefa17532a7a2cc023544d6ae8fd76ea52c91fb97893109b683711949bda, D 18a6944b1353cae0cbda5e65ddaa8f1ca885995e2be4590d961ff50441110676, and their headers match the dispatch's table.
**Prediction (outcome — planner):** The six take 2026-09-23-08 to -13 in order E, F, A, B, C, D if the branch has not passed -07 (the planner's amendment expects the next numbers after the branch's highest prompt instead, since it has); the branch's diff against main is RECORD.md and prompts/preserved/ only; both checkers pass after the notes; the PR merges into main cleanly because main has not moved from 624173b. Graded against the tree: the first part does not hold as written, because the branch holds -08 committed and -09 is this dispatch, so the names are -10 to -15, which the amendment anticipated; the second holds (checked above); the others are graded in the terminal.
**Prediction (mechanism — coder):** cp gives byte-identical copies, so each copy's sha256sum equals its original's. check_prompts.py binds by Dispatch-file name only, with no content comparison, so the six notes plus this intent leave it with zero unclaimed files. check_record.py accepts extra fields on a dispatch-note (only NOTE_FORBIDDEN is rejected, check_record.py:107-131), so a Notes field passes. The PR is mergeable because main at 624173b is an ancestor of this branch (branch commits sit on it) and none of the added files exists on main.
**Finish line:** All six copied under -10 to -15 with matching hashes; six dispatch-notes 2026-09-23-17 to -22; this intent closed by a terminal entry; both checkers pass; the branch is pushed; a PR from it to Forager main is open; a report is delivered.
**Abort conditions:** An original's header no longer matches or its hash changes before copying; a copy's hash differs from its original; main moves with changes to RECORD.md or prompts/preserved/; a checker fails for a reason other than a prompt about to be claimed; any file outside RECORD.md and prompts/preserved/ would change on the branch; a new unclaimed preserved prompt appears whose outcome is unseen.

---

**Kind:** dispatch-note
**ID:** 2026-09-26-20
**Dispatch-file:** preserved/2026-09-26-11.md
**Type:** build
**Outcome:** stopped
**Report:** none in the repository; its coder's hand-back went to the planner. The reason, as preserved/2026-09-26-12.md relays it: the dispatch put a paraphrase of forager-forecast's D57 in quotation marks. Read here: its line 61 quotes "Forager-app is a placeholder for research, and the existing Forager app is the end result", which does not appear in D57 at docs/planning/DECISIONS.md:11 on forecast main 876156b.
**Notes:** The planner's build dispatch correcting three memory files and the memory index and recording the owner's decision B, preserved 2026-09-26T04:47:26Z at a3d7417. Its coder stopped before writing an intent (coder.md item 8). Consistent with that, read here: the worktree .claude/worktrees/record-memory-and-protection was on local branch record-memory-and-protection at d3e7382, clean, with no commits of its own, and the four memory files' sha256 equal those preserved/2026-09-26-12.md cites as that coder read them. Re-sent with D57 quoted exactly as preserved/2026-09-26-12.md, which carries no Repeat-of line and is recorded by its own intent. Store copy: byte-for-byte from the untracked prompts/preserved/2026-09-26-11.md in the checkout .claude/worktrees/bridge-cse_013QR4ELV3wyYrUUyVCEmDwt, kept under the hook's name, 7401 bytes, sha256 4129e3f337831d4b3fd2c554ef063a432a93c32e6234a10042a8c09b769a89b5, cmp-identical; that original is claimed here and must not be swept again.

---

**Kind:** intent
**ID:** 2026-09-26-21
**Timestamp:** 2026-09-26T04:53:46Z
**Title:** Mark Forager-app and forager-forecast as research repos and Forager as the product in the owner's memory files; record decision B (no protection on main)
**Dispatch-file:** preserved/2026-09-26-12.md
**Change:** Four of the owner's memory files in /home/zynergy-labs/.claude/projects/-home-zynergy-labs-Zynergy-Forager/memory/, outside the repository and not committed, edited with the Edit tool as the dispatch states them. forager-app-repo.md: the frontmatter description set to the dispatch's text, and the body's first paragraph (the "rebuilt from scratch" paragraph, with "The older app at `~/Zynergy/Forager` is kept as prior art only. Read it, don't build on it.") replaced by the dispatch's paragraph quoting D57. forager-forecast-repo.md and forager-forecast-local-clone.md: the dispatch's one-sentence paragraph inserted directly after the frontmatter's closing `---`. MEMORY.md: the forager-app-repo.md line's hook text after the em dash replaced, and `(research) ` inserted at the start of the two forecast lines' hook text. Recorded here with the owner's decision B.
**Scope boundary:** From the dispatch: only those four memory files, and in them only the stated lines; each read in full first; no other memory file changed or deleted. In the repository: RECORD.md and prompts/preserved/ on branch record-memory-and-protection, three record commits in order (the sweep dc63038, pushed; this store copy with this intent; the terminal after the memory edits), pushed with -u origin record-memory-and-protection, then a PR into main, not merged. Out of scope: any other memory file or line; GitHub settings; the camera strip PRs; merging anything; the kit repository; writing anything in forager-forecast or Forager-app (reading D57 is in scope). The stale "ends at D54" and "unmerged" claims in the forecast memory's index line and body are not changed.
**Baseline:** origin/main at d3e73825542cdded9668cda3dfe4ab994ed20161, the PR #118 merge (parents af12a69603ab38295099ef27f0b3114c2a9ccd74 and 1e9d9413bc465a3a054382555963f802b5c2a7a0), after git fetch; the worktree .claude/worktrees/record-memory-and-protection on local branch record-memory-and-protection at d3e7382, clean, no commits of its own. At d3e7382: .claude/kit.json backup_dir "~/Zynergy/forager-repo-backups"; docs/audits/2026-09-26-recordkeeping-protocol-shift.md present; RECORD.md ends with terminal 2026-09-26-18, no intent open; check_record.py PASS (history walk 36 commits), check_prompts.py PASS (37 and 37). ~/Zynergy/forager-repo-backups empty, no INDEX.md. Memory sha256 before any edit, each equal to the dispatch's: forager-app-repo.md 4c29bdbd87177d6bdcb991eb7a1df497a30f64e53cae5638fc4a7d193f0117db; forager-forecast-repo.md 05ed4165e5fbf9a43c4fb5d69c8c6568ac5907160afe93e8c081c2bd11c5e659; forager-forecast-local-clone.md 937835844b1b745e675652e79c618fae557f86cb22c9cee9ae8329539a5e8aa7; MEMORY.md 2707ea968c12fc0c738efc5ba941e7770df271b1eacfefff34a32d2de6d23c36. D57 read through gh api at forecast main 876156b6dea613e95730f41e3e5f870aecdd5995 (the remote's main head), docs/planning/DECISIONS.md line 11: the dispatch's quotation occurs in it exactly once. The planner worktree's untracked -02 to -10 are cmp-identical to main's claimed copies; -11 and -12 were the only unclaimed store files. The store copy's HEAD line is a3d7417, the planner worktree's head when the hook saved it, not this branch's base.
**Prediction (outcome — planner):** From the dispatch: 1. the sweep writes one merge entry (PR 118, Merge-commit d3e7382, Pre-merge af12a69, Base main, Head kit-v0.2-install, Backup none, Merged-by owner, Carries 2026-09-26-01 to -18) and one stopped dispatch-note for -11; 2. both checkers pass after each record commit; 3. the memory edits change only the stated lines, and the three memory files keep valid frontmatter; 4. CI is green on the PR's final commit.
**Prediction (mechanism — coder):** (a) Prediction 1 is already observed in dc63038: check_record.py PASS, 62 entries, history walk 36; check_prompts.py PASS, 38 and 38. (b) With this commit, check_record.py passes with 63 entries and this intent open, history walk 37 commits (dc63038 added); check_prompts.py 39 and 39, preserved/2026-09-26-12.md claimed by this Dispatch-file, its name's date equal to its Preserved date 2026-09-26T04:50:46Z. (c) Each Edit replaces one exact, unique string, so diff against the copies saved in the session scratchpad before editing shows: forager-app-repo.md, lines 3 and 11 changed and nothing else (the metadata block, including its modified timestamp, untouched); each forecast file, two lines added after line 7's blank line (the sentence and a blank line), lines 1 to 7 unchanged; MEMORY.md, lines 4, 5 and 7 changed, still 11 lines. (d) Frontmatter stays valid: yaml.safe_load of the block between the first two `---` lines returns name, description and metadata for all three files before and after, because only forager-app-repo.md's description value changes and the new value is kept inside the existing double quotes and holds no double quote or backslash. (e) After the terminal, check_record.py passes with 64 entries, no intent open, history walk 38; check_prompts.py 39 and 39. (f) CI: ci.yml has no path filter, so every push runs the Android build and test, which reads neither RECORD.md nor prompts/; it goes green on the final commit as it did on d3e7382, and runs on earlier commits may be cancelled by cancel-in-progress on non-main refs. (g) The memory edits touch nothing in the repository, so git status shows no change from them.
**Finish line:** From the dispatch: the three record commits pushed; the four memory files edited as stated; CI green on the final commit; the PR open. The terminal records each memory file's sha256 before and after and the exact lines changed.
**Abort conditions:** From the dispatch: a premise mismatch, including a memory file hash differing from the dispatch's; D57's text differing from the quotation; an unclaimed store file other than -11 and this dispatch's copy; a checker failure; a guard blocking a step (quoted); two failed attempts at one step.
**Notes:** Decision B, the owner's decision: no GitHub protection on Forager's main. The owner's words, planner session 2026-09-26: "No protection, add memory corrections markings". This answers decision B, protection on main, which intent 2026-09-26-12 left to the owner. Nothing is changed on GitHub. The owner's other words the dispatch quotes, same session: "Forager-app is the research repo"; "The forecast repo is also research, branched from the forager-app repo." D57 is cited only in the owner's words it records: "Forager-app is a placeholder app for researching advanced methods, such as this project here, to integrate into the already existing Forager app as the ultimate end result. So prepare for actual Forager integration as you plan the forager-app." This re-sends preserved/2026-09-26-11.md, whose coder stopped before its intent (dispatch-note 2026-09-26-20); this copy carries no Repeat-of line and changes D57's quotation, so it is recorded as its own dispatch citing the original (coder.md item 11). Store copy: byte-for-byte (cp) from the untracked prompts/preserved/2026-09-26-12.md in the checkout .claude/worktrees/bridge-cse_013QR4ELV3wyYrUUyVCEmDwt, kept under the hook's name, 9655 bytes, sha256 0e7230a36824661dee488ef948c85fdb0b191e66d7c44642b2b655a95d3590f7, cmp-identical; that original is claimed here and must not be swept again. Merge not authorised: this session's guards are Forager's pre-kit hooks, which deny gh pr merge; the owner merges. Record and memory edits are written with the Edit tool, and git runs one command per Bash call, per the dispatch.

---

**Kind:** continuation
**ID:** 2026-09-26-22
**Timestamp:** 2026-09-26T05:00:51Z
**Continues:** 2026-09-26-21
**Dispatch-file:** preserved/2026-09-26-13.md
**Reason:** The owner's ruling on the extra metadata the memory tool wrote. As the dispatch quotes it, from the planner session on 2026-09-26: asked how to handle it, the owner chose "Accept it (Recommended)", whose option read "Treat it as the memory system's normal stamping, record it as a deviation, then write the closing entry and open the PR." The coder of 2026-09-26-21 stopped after the memory edits and before its terminal, having found frontmatter changes the dispatch had not stated. This dispatch writes that terminal and opens the PR.
**Changes:** None to 2026-09-26-21's scope boundary, predictions or finish line.
**Notes:** Premises checked before this entry, all holding: git ls-remote gives origin/record-memory-and-protection 42b7066da540e7f2008f071e89169d632192f941 and origin/main d3e73825542cdded9668cda3dfe4ab994ed20161; the worktree .claude/worktrees/record-memory-and-protection is clean and level with its remote; no PR exists for the branch (gh pr list --head record-memory-and-protection --state all: []). Memory sha256 now, each equal to the dispatch's: forager-app-repo.md 0dc2ca810b9bdfe6e94fb63636ca1768c143585acd768087aae8ee69b8d42702; forager-forecast-repo.md 8e39af1fb6971e9daf94ed7a945f190693c0da68f9c2ad5027c62eaf0536be3b; forager-forecast-local-clone.md a7900ae15f86ae61c127ed309f4515f83b18befcad4e07f0821a961487c98286; MEMORY.md 1e1c457daf75e950dd8606b84b18a9a86e01b26c5945ec329ad1ebcf31007b01. The pre-edit copies the previous coder saved in the session scratchpad (mem-before/) hash to 2026-09-26-21's Baseline values, and diff against them shows the stated edits plus exactly the unstated stamping the dispatch lists: forager-app-repo.md's metadata `modified` 2026-09-21T04:03:24.248Z to 2026-09-26T04:54:50.204Z, its node_type and originSessionId (995801e2-3212-5c9b-a94f-5df2a96b3fcf) already present before; each forecast file's description newly double-quoted, and node_type: memory, originSessionId: f9fe2a33-605c-54a7-933d-22f7af6314c0 and a `modified` timestamp added. yaml.safe_load parses all three frontmatter blocks. ci.yml:8-14 triggers on push to main and on pull_request only. The only unclaimed file in the planner worktree's prompts/preserved/ is 2026-09-26-13.md; -02 to -12 there are cmp-identical to this branch's claimed copies. Checkers at 42b7066 before this entry: check_record.py PASS, 63 entries, 2026-09-26-21 open, history walk 38; check_prompts.py PASS, 39 and 39. Mechanism prediction (coder): (i) with this commit, check_record.py passes with 64 entries and 2026-09-26-21 still open, since a continuation closes nothing (check_record.py:181-183, _check_continues), history walk 38 (HEAD 42b7066, the walk counting commits that touch RECORD.md, check_record.py:657-665); check_prompts.py 40 and 40, this store copy claimed by this Dispatch-file, its name's date equal to its Preserved date 2026-09-26T04:59:01Z. (ii) Pushing this commit starts no CI run, since the branch has no PR and is not main; opening the PR starts one pull_request run on this commit. (iii) The terminal's pre-commit run: check_record.py 65 entries, no intent open, history walk 39; check_prompts.py 40 and 40. 2026-09-26-21's prediction (e) named 64 entries and a walk of 38 after its terminal; this continuation adds one entry and one commit to both. (iv) The terminal's push starts a second pull_request run, which cancels the first if still in progress (ci.yml:23-25); CI builds and tests the Android app, reads neither RECORD.md nor prompts/, and goes green as on d3e7382 (run 36218526676, success). (v) Nothing in this dispatch writes to the memory directory, so the four hashes at the end equal those above. Store copy: byte-for-byte (cp) from the untracked prompts/preserved/2026-09-26-13.md in the checkout .claude/worktrees/bridge-cse_013QR4ELV3wyYrUUyVCEmDwt, kept under the hook's name, 6726 bytes, sha256 b859cc4df514542495dc22ead369991ad7f23ccf86b6381cf8a1788ef09abfc0, cmp-identical; that original is claimed here and must not be swept again. The store copy's HEAD line is a3d7417, the planner worktree's head when the hook saved it, not this branch's base. Merge not authorised: this session's guards are Forager's pre-kit hooks, which deny gh pr merge; the owner merges.

---

**Kind:** terminal
**ID:** 2026-09-26-23
**Timestamp:** 2026-09-26T05:07:54Z
**Closes:** 2026-09-26-21
**Outcome:** completed
**Observed:** The stated edits, each in the owner's memory directory outside the repository, as diffed against the pre-edit copies the coder of 2026-09-26-21 saved in the session scratchpad (mem-before/). forager-app-repo.md: the description changed to "~/Zynergy/Forager-app (slayer8366/Forager-app) is the research repo, not the product; the existing Forager app at ~/Zynergy/Forager is the end result; never run its build and the emulator together". The body's first paragraph (the "rebuilt from scratch" paragraph with "kept as prior art only. Read it, don't build on it.") was replaced by the dispatch's paragraph naming Forager-app a research repo and ~/Zynergy/Forager the product and end result (owner, 2026-09-26), and quoting D57's owner words. forager-forecast-repo.md and forager-forecast-local-clone.md: after the frontmatter, a blank line and "forager-forecast is a research repo, branched from the Forager-app research repo; the Forager repo at `~/Zynergy/Forager` is the product (owner, 2026-09-26)." MEMORY.md: line 7's hook text became "research repo, not the product; ~/Zynergy/Forager is the end result; never run its build and the emulator together", and "(research) " was inserted at the start of lines 4 and 5's hook text; still 11 lines. The sha256 before and after, the before values as in 2026-09-26-21's Baseline: forager-app-repo.md 4c29bdbd87177d6bdcb991eb7a1df497a30f64e53cae5638fc4a7d193f0117db to 0dc2ca810b9bdfe6e94fb63636ca1768c143585acd768087aae8ee69b8d42702; forager-forecast-repo.md 05ed4165e5fbf9a43c4fb5d69c8c6568ac5907160afe93e8c081c2bd11c5e659 to 8e39af1fb6971e9daf94ed7a945f190693c0da68f9c2ad5027c62eaf0536be3b; forager-forecast-local-clone.md 937835844b1b745e675652e79c618fae557f86cb22c9cee9ae8329539a5e8aa7 to a7900ae15f86ae61c127ed309f4515f83b18befcad4e07f0821a961487c98286; MEMORY.md 2707ea968c12fc0c738efc5ba941e7770df271b1eacfefff34a32d2de6d23c36 to 1e1c457daf75e950dd8606b84b18a9a86e01b26c5945ec329ad1ebcf31007b01. The after values were read at the start of continuation 2026-09-26-22's dispatch and again just before this entry, unchanged. D57 was checked at forecast main 876156b6dea613e95730f41e3e5f870aecdd5995, docs/planning/DECISIONS.md:11: the quotation occurs in it exactly once (2026-09-26-21's Baseline). Decision B is recorded in 2026-09-26-21's Notes with the owner's words "No protection, add memory corrections markings"; nothing was changed on GitHub. The first `merge` entry, 2026-09-26-19 for PR #118 (Merge-commit d3e7382, Pre-merge af12a69, Backup none, Merged-by owner, Carries 2026-09-26-01 to -18), was written in the sweep dc63038. Commits on record-memory-and-protection, each pushed: dc63038 the sweep; 42b7066 intent 2026-09-26-21; 57ccfb2 continuation 2026-09-26-22 with store copy preserved/2026-09-26-13.md (6726 bytes, sha256 b859cc4df514542495dc22ead369991ad7f23ccf86b6381cf8a1788ef09abfc0, cmp-identical to the planner worktree's original). Pushing 57ccfb2 started no CI run (gh run list --branch record-memory-and-protection: []). PR https://github.com/slayer8366/Forager/pull/119 opened into main, OPEN, MERGEABLE; gh pr create --body-file on the first attempt, and the live body read back equals the file except for one trailing newline added by --jq. CI runs on the PR: run 36219605090 "CI", event pull_request, on 57ccfb2, success. Checkers before 57ccfb2: check_record.py PASS, 64 entries, 2026-09-26-21 open, history walk 38; check_prompts.py PASS, 40 and 40. Because of continuation 2026-09-26-22, 2026-09-26-21's prediction (e) counts are one higher: 65 entries and a history walk of 39 before this commit, not 64 and 38. The checkers and CI on this commit are reported in the hand-back.
**Deviations:** (1) The memory tool wrote frontmatter changes that the dispatch had not stated, beyond the dispatched edits. forager-app-repo.md: its metadata `modified` changed from 2026-09-21T04:03:24.248Z to 2026-09-26T04:54:50.204Z (its node_type and originSessionId 995801e2-3212-5c9b-a94f-5df2a96b3fcf were already present). Both forecast files: the description is now in double quotes, with the same parsed value; `node_type: memory` was added; `originSessionId: f9fe2a33-605c-54a7-933d-22f7af6314c0` was added; a `modified` timestamp was added (2026-09-26T04:54:51.852Z on forager-forecast-repo.md, 2026-09-26T04:54:53.656Z on forager-forecast-local-clone.md). All three files still parse with yaml.safe_load. Accepted by the owner's ruling, as preserved/2026-09-26-13.md quotes it from the planner session on 2026-09-26: "Accept it (Recommended)", the option reading "Treat it as the memory system's normal stamping, record it as a deviation, then write the closing entry and open the PR." (2) The originSessionId added to the two forecast files is false provenance. It names the planner session, which did not create those files. (3) The previous coder's mechanism prediction (c) and planner prediction 3 did not hold as worded. (c) said forager-app-repo.md would change only on lines 3 and 11, "the metadata block, including its modified timestamp, untouched", and each forecast file only by two added lines, with lines 1 to 7 unchanged. Line 8 of forager-app-repo.md changed, and each forecast file's line 3 changed and three metadata lines were added. Prediction 3 said the edits change only the stated lines. Its second half, valid frontmatter, held. (4) Prediction (f)'s CI premise was wrong: ci.yml triggers on push to main and on pull_request only (ci.yml:8-14), not on every push, so the branch had no CI run until the PR opened. This terminal is written before CI on its own commit has run; that result is reported in the hand-back.

---

**Kind:** merge
**ID:** 2026-09-26-24
**Timestamp:** 2026-09-26T05:16:15Z
**PR:** 119
**Head:** record-memory-and-protection
**Base:** main
**Merge-commit:** 76905d4993813caaead1caad5db6fd18da5c97e8
**Pre-merge:** d3e73825542cdded9668cda3dfe4ab994ed20161
**Backup:** none
**Merged-by:** owner
**Carries:** 2026-09-26-19, 2026-09-26-20, 2026-09-26-21, 2026-09-26-22, 2026-09-26-23
**Notes:** Written in the sweep of the dispatch preserved as preserved/2026-09-26-12.md by its hook and re-filed as preserved/2026-09-26-15.md. The only merge on main's first-parent chain newer than d3e7382, the newest merge a `merge` entry records (2026-09-26-19): git log --first-parent --merges af12a69..origin/main lists 76905d4 and d3e7382. 76905d4 is not an ancestor of af12a69 (git merge-base --is-ancestor exits 1), so it falls after the cutoff in docs/audits/2026-09-26-recordkeeping-protocol-shift.md. Merge-commit and Pre-merge from git log --format='%H %P' -1 76905d4 (parents d3e73825542cdded9668cda3dfe4ab994ed20161 and b9c8f7998d2166fe90ef507eaf9f72c33ada6e2f). PR, Head, Base, Timestamp (mergedAt) from gh pr view 119 --json number,headRefName,baseRefName,mergeCommit,mergedAt: 119, record-memory-and-protection, main, mergeCommit 76905d4993813caaead1caad5db6fd18da5c97e8, 2026-09-26T05:16:15Z; state MERGED, mergedBy slayer8366. Backup none and Merged-by owner: ~/Zynergy/forager-repo-backups exists and is empty, with no INDEX.md, so no line names #119. Carries: the IDs git diff d3e7382 76905d4 -- RECORD.md adds, 2026-09-26-19 to 2026-09-26-23.

---

**Kind:** intent
**ID:** 2026-09-28-03
**Timestamp:** 2026-09-28T03:40:00Z
**Title:** L0b, the map layer framework's user-facing half: the Layers sheet on all three hosts, every saved record on the Maps tab, DataStore persistence, the legend chip, the forecast-cell stored-data interface, two synthetic colour layers behind a debug-only Diagnostics switch
**Dispatch-file:** preserved/2026-09-28-03.md
**Change:** B1 a Material3 Layers sheet ("Map type", "Overlays") replacing MapModePicker's popover on the compact Maps tab, the wide layout and the entry map's fullscreen button, colour rows with opacity and drag-to-reorder, one stored set of choices for both maps, the button description updated; B2 a new domain use case drawing every saved (non-draft) find, every track in Records, every located album photo and every offline region on the Maps tab, on by default; B3 per-layer visibility, colour-field opacity and order in map_preferences under map.layer keys; B4 a collapsible legend chip bottom-right above MapLibre's attribution button (above the add button in the wide layout); B5 a forecast-cell store interface with pure parsing and validation and an explicit "no forecast data"; B6 two deterministic synthetic colour layers from the debug source set only, a Diagnostics toggle in a debug-only DataStore file, the release twin reporting no forecast data; B7 the two layers in the colour-field group.
**Scope boundary:** Branch journal-redesign only. ui/map, the three hosts and their state holders, domain for the new use case and interfaces, data/repository, wiring in AppContainer and MainActivity, app/src/debug and app/src/release, tests. Not Room, the Seasonal panel, M1 bubbles or tap UI, J8, any downloader or network, basemap persistence, the held flaky tests, the phone, the record, index, CLAUDE.md, plans or prompts.
**Baseline:** journal-redesign at the commit carrying this entry (docs-only child of 379eb05; app tree identical to f62eb3e). CI on f62eb3e: 2112 / 1 / 24 skipped, the held album-Undo test; planner's local run on 1476e97, the same app tree: 253 classes / 2112 / 0 / 0 / 24.
**Prediction (outcome — planner):** 1. No Room migration. 2. The four classes pinning the button description change and no other existing assertion does. 3. The suite grows by 70 to 140 tests. 4. MapOverlayContent's existing record fields carry the Maps-tab overlays with no tenth MapSlot parameter.
**Prediction (mechanism — coder):** not authored
**Finish line:** B1-B7 pushed with the completion report and a device-only list; tests first, revert checks each compiling, coordinate-touch UI tests, release compile evidence with no synthetic class in release, D58 over every commit; full suite with held flaky failures reported as such; the planner re-runs the suite and writes the terminal; L0b's device check is its own dispatch.
**Abort conditions:** A wrong premise that changes what to build; a record kind with no determinable saved state; a Room migration; a tenth MapSlot parameter; a tests-first test passing at base; a non-compiling revert build; a non-held test failing; a map touch not reaching the map after two attempts; a synthetic class in release output; Maven 429s; an OOM kill; two failed fixes on one symptom; an open design question.
**Notes:** Written by the planner by hand. The owner's rulings this session, recorded in the plan ("L0b rulings (owner, 2026-09-28)" and "Ruling 3 clarified"), verbatim: "Also show all finds etc.", "On by default", "Saved entries only (Recommended)" then "Every saved record (Recommended)", "Same sheet (Recommended)", "Bottom-right, above the 'i' (Recommended)", "Debug-only source (Recommended)", "Two synthetic layers (Recommended)", "One stage". Planner choices not ruled by the owner, open to change: the sheet's copy (labels, "Layers: <basemap> map. Choose the map type and overlays."), the synthetic layer names and the "Synthetic test data" credit, the key names, drag-to-reorder with TalkBack move actions (a widely used backcountry map app and a topographic mapping app convention). Premises from docs/audits/2026-09-28-l0b-premise-pulse.md. Runs in parallel with the device check 2026-09-28-02, which uses no Gradle.

---

**Kind:** continuation
**ID:** 2026-09-28-05
**Timestamp:** 2026-09-28T04:35:00Z
**Continues:** 2026-09-28-03
**Dispatch-file:** preserved/2026-09-28-05.md
**Reason:** the owner asked the planner to read forager-forecast for what the layering is for ("Look at forager-forecast repo for details on what the layering is for"); B4 to B6 were held by a first planner message (verbatim: "Hold B4 (legend chip), B5 (forecast-cell interface) and B6 (synthetic layers), including their tests-first commits, until a second planner message releases them") while the read ran (docs/audits/2026-09-28-forager-forecast-layering-read.md, at forager-forecast 876156b).
**Changes:** B5 keyed by group, week and 1 degree block, cells centred on 0.1 degree multiples and assigned by centre, applicable-false cells flagged or omitted and drawn as nothing; B6's two layers become chance layers in the real format for two groups, "Test forecast: chanterelles (synthetic data)" and "Test forecast: chicken of the woods (synthetic data)", the fixed term never attached to them, lowest ramp colour distinct from an empty cell; B4's expanded legend carries per layer the ramp with 0% and 100%, "Week of <week>, weather to <weather_through>", "no forecast here", and once the reference-class sentence verbatim from Forager-app SightingChance.kt:33-35 at 0172c33; no tap UI (M1). Scope boundary, predictions and finish line unchanged.
**Notes:** Owner's answers, verbatim: "Real format, 'test data' name (Recommended)", "A second group (Recommended)", "In M1, with the bubbles (Recommended)", "Use that wording (Recommended)"; recorded in the plan, "L0b forecast-facing rulings, after reading forager-forecast (owner, 2026-09-28)". Sent to the running coder by SendMessage; written by the planner by hand.

---

**Kind:** dispatch-note
**ID:** 2026-09-28-08
**Dispatch-file:** preserved/2026-09-28-08.md
**Type:** handoff
**Outcome:** issued
**Report:** none
**Notes:** Written at 2026-09-28T04:12:54Z (read from the clock). The owner's commercial-use ruling, verbatim: "I'll be selling the app, but that particular feature will be free. What license do you recommend?", then "Commercial-safe model. I'll get an open-meteo subscription for their service". Recorded for this repository in the plan ("Commercial use: the owner's ruling (2026-09-28)"); the handoff carries it to forager-forecast, whose D29 and D22 it answers, for the owner to take there. Open-Meteo's move to subscriber endpoints is recorded as needed before release, not scheduled. **Correction to 2026-09-28-07:** its store copy's Preserved line (04:15:00Z) was an estimate and is later than the entry's own clock-read Timestamp (04:12:00Z), so that entry's note that the store copy "was written minutes before this entry" is wrong about the stated time; the store copy was written at about 04:11Z, just before its commit ad5026b. Written by the planner by hand.

---

**Kind:** terminal
**ID:** 2026-09-28-15
**Timestamp:** 2026-09-28T09:49:34Z
**Closes:** 2026-09-28-03
**Outcome:** completed
**Observed:** (1) On journal-redesign: verification 09bf96b; tests first 55114ee; fe07702 (records use case, layer preferences, forecast cells, synthetic store, legend model, colour fields); after a machine restart, the uncommitted WIP preserved by the planner at 11ef6e2 (never compiled; 35 test compile errors), compile-fixed as tests first round 2 at d9dd1d8; 45c82cd, 93da312, 34487da (B1-B7, F4 threading, the Layers sheet on all three hosts, legend, DataStore persistence in map_preferences via the existing repository, debug-only synthetic store and Diagnostics switch, release twin reporting no forecast data); under continuation -11, 035fff4 and 5cd7033 (N1: expanded legend capped at 96 dp, contents scroll), 2e89091 (comments), report 8cfc22c, merged at af846cc. Report docs/audits/2026-09-28-map-layers-l0b-completion-report.md. (2) Revert checks: R01, R01b and R02b-R21, twenty-two in all, each compiling and failing with a message specific to its edit, restored from saved copies; includes the round-1 classes never checked before (R17-R19). (3) Release: compileReleaseKotlin and mergeDexRelease succeed; dexdump finds 0 SyntheticForecast classes in release dex against 15 in debug (positive control); assembleRelease not run (no signing identity here). (4) Suites: coder at 2e89091 266 / 2183 / 0 / 0 / 24; planner at af846cc, results cleared, LC_ALL=C.UTF-8, 0 "e: " lines, counts from JUnit XML: 266 / 2183 / 0 / 0 / 24. The held flaky family passed in both runs; not evidence it is fixed. CI on journal-redesign, latest runs: af846cc in_progress fe0f0d7 completed cancelled 2c6d513 completed cancelled;. (5) Planner predictions: 1 held (no Room migration); 2 wrong in part (F3's three popover tests replaced, Q3's assertion changed, MapLayerRegistryTest, MapLayerFeatureIdTest and MapLayerStateTest re-pinned); 3 held (+71); 4 held (no tenth MapSlot parameter).
**Deviations:** (1) A machine restart stopped the first coder mid-build; the WIP was preserved uncompiled by the planner and verified by the next coder. (2) A tests-first test that passed at base was extended to fail first rather than stopped on. (3) The F3 replacement tests landed one commit after the popover's removal. (4) Revert R02 did not compile (a badly chosen edit), an abort; per the planner's ruling in -11 it was replaced by a compiling edit (OPACITY_SUFFIX to VISIBLE_SUFFIX). (5) Scope widened by -07 (four files, parameter threading only). (6) Release proof stops at merged dex, not a signed APK.
**Notes:** Device-only for L0b's device check (report, Device-only): real layer hiding and opacity with no style reload; hidden layers excluded from tap queries (carried from L0a); the cell layer under the markers; the legend's inset placement at both rotations and in fullscreen, and whether the fixed 96 dp cap still leaves the cluster room with real insets; the sheet's insets; persistence across a force-stop; where MapLibre's "i" lands against the nav and rail. Flags carried: MapModePicker left with no caller, still imported at AvailabilitySettingsUi.kt:66 and AvailabilityMapControlsUi.kt:78 (out of scope), unused import at AvailabilityScreen.kt:312, the name in comments and in mapModePickerEnabled; the entry map's Layers button still hides while offline tiles are on. D58: zero hits over the diff since 6235a86 and every commit message. Next: L0b's device check (needs a new build installed on the S22), then M1. Written by the planner by hand.

---

**Kind:** dispatch-note
**ID:** 2026-09-28-260
**Timestamp:** 2026-09-30T01:26:26Z
**Dispatch:** none (a parked idea)
**Reason:** the owner raised a free companion app carrying the full forecast without commercial licensing, asked whether donations would stand in, then said "Park it".
**Changes:**
- **The plan records it as parked** until after PR #140 merges: docs/plans/journal-redesign.md, "A free companion app with the full forecast: parked". It holds the planner's not-legal-advice reading and four open questions: Open-Meteo's terms, a legal read on CC BY-NC, iNaturalist's terms, and forager-forecast D57.
- **Nothing is dispatched.** The commercial-use ruling for Forager is unchanged.
**Notes:** Written by the planner by hand.

---

**Kind:** decision
**ID:** 2026-09-28-397
**Timestamp:** 2026-10-01T23:52:24Z
**Subject:** Forager will not be sold. The owner's commercial-use ruling of 2026-09-28 is superseded.
**Supersedes:** the ruling recorded in dispatch-note 2026-09-28-08 and in docs/plans/journal-redesign.md, "Commercial use: the owner's ruling (2026-09-28)". Neither is edited; this entry and the plan's new section "Not for sale: the owner's ruling (2026-10-01)" stand over them.
**The owner, verbatim, in order (2026-10-01):**
1. At 22:37Z: "Actually we are switching to the non-commercial model. I can't find a way to charge for this app and get what I'm looking for out of it. So let's proceed with the open source model".
2. At 23:43Z, to four questions from the planner (which forecast model ships: A the full model on all records, or B keep the commercial-safe one; does "open source" mean licensing the app's code; does the forecast repository open up too; any plan to take donations): "1 A, full model", "2 No, just keeping no proprietary software", "3 yes", "4 I'm considering donations and research grants for cost upkeep".
3. At 23:48Z, to the planner's reading of answer 2 (no licence is added, and "open source" means no proprietary parts inside the app), to whether that stops at what is inside the app or also covers the services around it (Google Play, GitHub, Cloudflare), and to whether to write these entries: "1 Yes", "2 stops at what's in the app, but my goal is to use open source databases and projects for my app. I just won't explicitly mention that unless asked", "3 go ahead and write them".
**What is decided:**
- **The app is not sold.**
- **The forecast Forager ships is the full model,** built on all records, the non-commercially licensed (CC BY-NC) ones included. The commercial-safe model (CC0 and CC BY records only) is no longer the one that ships.
- **No licence is added to this repository's code.** It is public with no licence file (checked at e0239399). "Open source model" means the app is built without proprietary software inside it.
- **That stops at what is in the app.** The services around it are not covered. The owner's goal is open-source databases and projects for the app.
- **The forecast repository opens up.** A ruling, not yet carried out; it is carried to slayer8366/forager-forecast's own decision log in the same session.
- **Donations and research grants are under consideration** for running costs. Not decided.
**The planner's readings, not confirmed by the owner:**
- "I just won't explicitly mention that unless asked": the README and the store listing do not describe the app as open source. Code that is public with no licence is not reusable by others, so the description would also be wrong as things stand.
- The free companion app parked in dispatch-note 2026-09-28-260 was a way to carry the full forecast without selling it. Forager now does that itself. The owner has not said the idea is withdrawn.
**What it changes in what is already recorded here** (none of it edited):
- **The plan's forecast gate** (docs/plans/journal-redesign.md:450, "until the owner rules on commercial use") is answered: the owner has ruled, and the full model may ship. Every other gate on a real forecast layer stands.
- **The plan's closing line** (journal-redesign.md:1279, "Forager ships the commercial-safe model and moves to a paid Open-Meteo subscription before release") no longer holds.
- **The Open-Meteo subscription** was ruled because the app would be sold. That reason is gone. Whether the owner still takes one is not said. The move to subscriber endpoints "before it is sold" (journal-redesign.md:539) has no trigger left.
- **Decision 2026-09-28-338's "before release" choice** between a commercial tile provider and the app's own tiles was tied to the sale, as is docs/plans/own-map-tiles.md:22 ("Forager will be sold"). The own-tiles plan itself is not withdrawn by this entry. The policy line -338 quotes names "those that seek donations" beside commercial services, so it applies again if donations are taken while the app still fetches from tile.openstreetmap.org.
- **Attribution** now has to cover the CC BY-NC records as well as the CC BY ones (journal-redesign.md:538 names the CC BY ones).
- **iNaturalist's API and photo terms** (journal-redesign.md:540, "for a commercial app") are still unchecked, now for a free app.
**Checked against "no proprietary software" at e0239399, by the planner:**
- **Read:** every library the app declares (gradle/libs.versions.toml:70-121) and links (app/build.gradle.kts:481-519) is open source: AndroidX, Compose, Room, DataStore, WorkManager, CameraX, Retrofit, OkHttp, kotlinx serialization and coroutines, MapLibre, and mil.nga mgrs. A search of the build files and the version catalog finds no Google Play Services, Firebase or ML Kit coordinate.
- **Not checked:** the libraries those pull in. No lock or verification file exists, and no Gradle run was made.
- **Services the app's main code names:** api.inaturalist.org, api.open-meteo.com and archive-api.open-meteo.com, tile.openstreetmap.org, a.tile.opentopomap.org, basemap.nationalmap.gov, and the owner's own PMTiles Worker. These are outside the scope the owner set.
**Open-Meteo's free terms, as a reader returned them on 2026-10-01** from open-meteo.com/en/terms (fetched through a summarising tool, so the quotations are not read from the raw page; no date is shown on it): non-commercial use includes "Using our service for private or non-profit websites or apps that do not have subscriptions or advertising"; commercial use includes "Operating websites or apps that have subscriptions or display advertisements"; "Less than 10'000 API calls per day, 5'000 per hour and 600 per minute". Donations and grants are not mentioned in what was returned. Whether the call limits count per app or per device is not determined.
**Not legal advice, and not settled:** whether a free app that takes donations or grants stays non-commercial under CC BY-NC 4.0, and under Open-Meteo's and OpenStreetMap's terms. The four open questions under the parked companion app (journal-redesign.md:1267-1277) are the same questions and are still open.
**Notes:** Written by the planner by hand, on branch records-noncommercial-ruling cut from main at e0239399, pushed and not merged. Pull request #143 (records-after-142 into main, RECORD.md only, head 6c4e905fa086e48759597d440b74f5baa946f673) was merged as e023939970ef7c98a1e64589640e3802c299f054 at 2026-10-01T20:53:39Z, read from GitHub, on the owner's "Open a PR for the records branch and merge it", with backup 2026-10-01-03; that merge has no entry of its own, and this note stands in for one.

---

**Kind:** intent
**ID:** 2026-09-28-571
**Timestamp:** 2026-10-06T06:10:00Z
**Title:** s22-combined-check: the S22 steps left open by -549 (units) and -527 (fix provider), on one debug build of main f4b6b98e
**Dispatch-file:** preserved/2026-10-06-05.md
**Context:** the owner, asked in the planner's window which new tasks to dispatch: "There was a coder who needed to do a device check, let's finish that before any new builds"; then "Start new agents, resume the work". Read as the go for the one build this check needs. The open steps are in -561's and -563's "Not shown"; -570's S26 fresh-folder check stays waiting on the S26 being connected.
**Also on that word:** a resume was queued to the forecast D32 reviewer (offline Remote Control session; delivery waits for its machine), for -565's review under D18.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -572.

---

**Kind:** continuation
**ID:** 2026-09-28-576
**Timestamp:** 2026-10-06T08:20:00Z
**Continues:** 2026-09-28-575
**D26's verify report and two stops** (forager-forecast d26-shared-download at 6b8a1ab, `docs/audits/2026-10-06-d26-verify-report.md`; D68 to D71 and the 109 to 117 correction are filed at 64ffb20). GBIF's country-borders tag is `GADM_LEVEL_0_GID`. On GBIF's live index it selects 2,432,070 US and Canada records, against 2,493,712 by the `country` field. 61,508 US/CA records carry no tag; they are inland, and 89% have uncertainty of 20 km or more. That leaves 29,904 records inside the T1 boxes untagged (PNW 9,211, East 20,693), about 3,178 of them under 20 km. Disk: an estimated 1.41 to 1.44 GB zipped, with 1.86 GB free when measured.
**The owner, verbatim:** on the boundary, "Tag, else country field (Recommended)": the tag where present, and the publisher's `country` where the tag is missing; records tagged as another country stay out. This narrows D71, and the writer files it as a new decision row that quotes D71. On the copies: "Yes, copy them to one data folder". The planner copied 0005709 and 0005714 to `~/Zynergy/forecast-data/gbif/` with SHA256SUMS, both matching their DOI records. On disk: "Remove the originals and old work folders". After `sha256sum -c` passed on the copies, the planner deleted the two original zips (in the t1-calendar-smoke-test and t2-record-audit worktrees' `data/`). It removed nine Forager worktrees under `.claude/worktrees/`, each clean, with its HEAD on a remote branch; their branch refs are kept. It kept `pr-140-wrap-up-5049ce`, whose three README commits (to b0101543) are on no remote branch. Free disk is now 5.8 GB.
**Planner's go to the writer:** build option A, accept the proposed rename of `rest_of_north_america` to `outside_t1_boxes`, and run the one download, read in place, with no full extraction.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -577.

---

**Kind:** terminal
**ID:** 2026-09-28-584
**Timestamp:** 2026-10-06T11:30:00Z
**Closes:** 2026-09-28-578 (preserved 2026-10-06-07), with Amendment 1 (-579); and 2026-09-28-575 (preserved 2026-10-06-06)
**Outcome:** both completed and merged.
**arrived-alone (-578, -579):** branch at 428c6096: 0a752a4a red (13 of 144 failing on main's code, all on the status line), 18cda007 green, b1f888a5 merging main 730a7a12, and the report `docs/navigation/2026-10-06-arrived-alone-report.md`. 8 status-line assertions changed as ruled, 4 tests renamed, 6 new tests, 6 revert checks, full suite 3,823 tests and 0 failures. The coder disclosed that its "before" run was not a pure main baseline. The planner's own check of `git diff origin/main...origin/arrived-alone`: no `@Ignore`; 8 removed assertion lines, each replaced by the ruled value; app changes in `NavigationReadout.kt` and `NavigationHud.kt` only. PR #180 merged as ef269025 on green CI (9 m 48 s), main backed up as 2026-10-06-07, on the owner's "Merge the arrived-alone PR once checks pass". Not yet seen on a phone.
**D26 (-575, -576):** forager-forecast d26-shared-download at 28d7907. One GBIF download, 0012112-260928105237408, DOI 10.15468/dl.8jxmeb, 2,493,578 records, 1,434,032,123 bytes, provisional. Acceptance: 1,194,729 of 0005709's 1,195,034 keys are present; the 305 missing return 404 on GBIF; 29,792 untagged are kept by the fallback. The independent review (d26-review dfd5d1d) holds and re-ran every headline. Finding 1 was for the owner, the old records' `superseded_by`. The owner, verbatim: "Fill in the field (Recommended)". Then, to "do you authorise merging `d26-shared-download` into forecast main, together with its review branch `d26-review`?": "Merge both (Recommended)". The planner filed D73 and filled both fields on branch d26-merge, then merged it into forecast main as 614b262 (from ad64fef). 219 passed before the push. The review's four minor items go into the next forecast task.
**T4:** completed on t4-master-grid at b78ab5c. The zoom-9 archive passes 10 of 10 cells (largest difference 0.00062 pH); tests 162 functions, 266 collected. The independent review has started. The builder's 0.5 valid-fraction threshold awaits a ruling.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -585.

---

**Kind:** continuation
**ID:** 2026-09-28-597
**Timestamp:** 2026-10-06T17:40:00Z
**Continues:** 2026-09-28-592
**-592 built; PR #181's CI red; the laptop's restarts.** The session's container restarted twice during this work. The kernel log shows a global OOM killing a forager-forecast T5 build process (3.9 GB RSS) while an app full suite ran beside it, on this 11 GB laptop. From then on, one heavy job at a time. The owner: "When I get my new laptop, that'll change. But for now, sensible ordering". The sundown-line branch was finished by a third session at 494a1754. Alert-moment guards: 9 of 9 green on main ef269025 and on the branch. 24 revert checks. Full suite 3,890 tests, 0 failures, 24 skipped (main 3,823 + 67). Two existing settings tests now scroll to their text, because the new section pushes it below the fold. The ViewModel's unrendered countdown is retired, with its five tests replaced where the value is now computed; the planner checked this. PR #181 was opened. The owner: "Merge #181 once checks pass". Its CI failed: 3,890 tests, 1 failed. `SundownSettingsTest` "real touches across each row change it, and both settings survive a recreated repository" hit a ComposeTimeoutException at `SundownSettingsTest.kt:186` (`waitUntil(5_000) { stored.lastOrNull() == 45 }`). It passes locally, and an unexplained timeout was noted in the draft report. Not merged. Treated as this PR's fault to root-cause, not a flake to re-run. The owner agreed the order: "Sounds good on the order". T5's rebuild finishes alone first; then a coder diagnoses and fixes, pushes, and #181 merges on green.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -598.

---

**Kind:** intent
**ID:** 2026-09-28-614
**Timestamp:** 2026-10-07T01:08:19Z
**Title:** s22-check-sundown-and-approaching: PR #180 and PR #181 on the S22
**Dispatch-file:** preserved/2026-10-06-15.md
**Context:** the owner, asked which navigation work comes first: "Phone check first (Recommended)". On when T6b runs: "I'll tell you each night". The check is ordered cheap first: install; Settings > Sundown, with persistence; the sunset line's 2 h 30 min window and its move into the HUD; Approaching and Arrived outdoors with the owner; insets as an observation. The build waits until T6b's first short section ends, one heavy job at a time, under the 5 GB cap.
**Not yet sent.**
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -615.

---

**Kind:** continuation
**ID:** 2026-09-28-622
**Timestamp:** 2026-10-07T03:49:06Z
**Continues:** 2026-09-28-621, 2026-09-28-620
**The landscape failure's cause, the owner's call, and the SCANFI download.** The landscape coder (worktree /tmp/claude-1000/landscape-centre-dusk) reproduced 2 S10 failures on main 4db24110 at 03:39Z. Cause (A), a test defect: the HUD's sundown line reads AvailabilityScreen's `currentTime`, which defaults to the system clock (AvailabilityCompactMapUi.kt:1012), and the B2 test passes no clock. With the fixture near Portland, the line shows from about 23:15Z through the night, so S10 passes only between about 14:15Z and 23:15Z. Probes: line off gives 124 dp, line on 160 dp (legacy graphics); native graphics give 80 dp and 96 dp. Inferred real clearance on the S22 at ROTATION_90 with the line: about 2 dp above the central third, against about 18 dp before the line, from a pre-line device dump plus 16 dp.
**The owner, verbatim:** asked about the 2 dp margin, "Leave it, check on the phone (Recommended)". The test is fixed (clock pinned; a line-shown S10 case under native graphics), and the S22 check gains a step: the HUD with the line, in landscape, against the centre. The declined options were moving the line beside the HUD and joining it to the coordinates row.
**SCANFI download (-620):** the user service t6b-scanfi-download (1 GB cap, nice 19, idle I/O) started 20:32 PDT at about 3 MB/s, against 77 kB/s on the night of 10-06 02:42Z. It pauses before the "otherConiferous" layer to keep an 8 GB reserve. T6b is at 908a18b with the night order mask, plots, soil, trees; 451 tests; 25 of 27 revert checks bite.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -623.

---

**Kind:** continuation
**ID:** 2026-09-28-644
**Timestamp:** 2026-10-07T17:22:45Z
**Continues:** 2026-09-28-643, 2026-09-28-642
**S22 day check, step 1 (desk), and two fixes queued.** Report on s22-day-check at d8da9dbd. 1.0.2874+gaa79f25a was installed; the database migrated 17 to 18. Off-track reminder: all desk items pass (the tick box and its persistence; the Restricted prompt once; App info and Back; no prompt when off, on a repeat, or when allowed). GPX import: the picker, multi-track ("Imported 2 tracks"), no times, route-only, broken file, Open with, Share, and Open with during a recording (service unchanged) all pass. Walk waypoints: a '+' waypoint is listed under "Waypoints on this track", row > details > Back > walk > Back passes; dots not yet seen on a recorded walk (0 indoor points). Findings: (1) the "Imported" label beside a long title is squeezed to one letter per line; (2) Back after Open with or Share steps through Forager's screens to Maps, as the owner's "Invisible doorway" option described; (3) at font scale 2.0 in landscape, the top strip and the HUD overlap the search bar and "No origin waypoint…" clips to "No", while the HUD bottom (408 px) stays clear of the central third. The dispatch's "128 dp = 360 px" was the planner's error: it is 480 px at 600 dpi. The coder set Restricted without reading the prior battery mode; after its restore the page shows "Unrestricted". The T6b runner fix (retry with backoff, defer and continue) is pushed at be17b71: 460 tests, 32 of 34 revert checks bite; tonight's soil and US trees need about 3.9 GB of the 6.1 GB free.
**The owner, verbatim:** the battery mode, "Set it to Optimized (Recommended)". The large-font overlap, "Log it, fix next (Recommended)". The squeezed label, "Fix it (Recommended)": the label stays on one line and the title shortens with "…". The two fixes go to one small dispatch after today's check.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -645.

---

**Kind:** continuation
**ID:** 2026-09-28-748
**Timestamp:** 2026-10-08T20:27:32Z
**Continues:** 2026-09-28-747
**Standing instruction: T6b uses the downtime.** The owner, verbatim: "Keep running it when there's downtime. Pause it when I request a build. Otherwise may as well put the downtime to use." From now on t6b-night runs whenever no Gradle build is running or queued, with its --until set late. Before a build the planner sets the PAUSE file and waits for the unit to go inactive; after the build and merge it removes PAUSE and restarts. Each start and pause is recorded. This needs no further ask.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -749.

---

**Kind:** decision
**ID:** 2026-09-28-765
**Timestamp:** 2026-10-09T02:37:48Z
**Title:** The weekend plan for a Monday release: T tasks tonight, the L walk tomorrow, then T6b
**The owner, verbatim:** "We can wrap up the T sections of navigation tonight, and tomorrow after my walk we can finish the L section. Production can cool down a bit in the laptop and we'll focus fire T6b before the weekend is over. Target release date is Monday".
**Answers:**
- T17: "Build and measure tonight". (Offered: after Monday, recommended; build tonight with no claim.)
- T20: "After our own tiles (Recommended)".
- L by Monday: "Walk, read logs, L7 (Recommended)". The filter (L4) is built and tuned after Monday, off the live map.
**Also:** T19 is closed by a code read. The disclaimer's wording is not in the app; it survives only as a comment, Theme.kt:81 on main c81b326d. T11's check is done (t11-hud-landscape 577532e9, report docs/navigation/2026-10-09-t11-hud-landscape-check.md), and its options go to the owner. T6b was restarted after the T11 check (--until 07:00).
**Notes:** Next free ID -766.

---

**Kind:** decision
**ID:** 2026-09-28-771
**Timestamp:** 2026-10-09T06:16:15Z
**Title:** Priorities to Monday: the forecast system first; location fusion is not rushed
**The owner, verbatim:** "This update cycle is mostly coded already, so what's left are the data collection field trips. On the other hand, FLS doesn't need to rush, we'll want to actually invest proper time in this, so if this extends beyond release a bit, then no harm. I'll be meeting with Alan Rockefeller this Monday at the OMS meeting, so I'll want to focus on the forecast system to finish by then anyway".
**Reading:** the planner takes "FLS" to mean the location-fusion track (plan track L), unconfirmed. L may slip past the release; it gets proper time, not a rush. The focus to Monday 2026-10-12 is the forecast system (T6b and what follows), finished for the owner's meeting. -765's "L by Monday" is relaxed accordingly.
**Notes:** Next free ID -772.

---

**Kind:** observation
**ID:** 2026-09-28-802
**Timestamp:** 2026-10-10T14:06:46Z
**Title:** After the laptop restart: new work partition, flash drive cleared for T6b, T6b SCANFI stage started
**Context:** The owner restarted the laptop after -801 and added a 58.7 GB work partition (/mnt/work); ~/Zynergy is bind-mounted from it and ~/.gradle and ~/Android are symlinks to it. The T6b flash drive was not mounted after the restart; the planner mounted it (udisksctl, same path). It was 96% full (2.5 GB free). Every T6b stage that runs by default had finished at 2026-10-09T21:36-07:00 (soil 89/89, trees 2015/2015, trees-us-half 92/92); what is left is the explicit scanfi-layers stage (D118), of which six of eleven layers are already on the drive (9.1 GB together). A fresh back-by-fires coder was started from f7eb14b3 with Gradle cleared (T6b was paused and had no work in its default stages).
**The owner, verbatim:** "Move some files from the flash drive to make room for T6b if needed". Then, to (1) remove the originals (the deletion was refused by the permission system for the planner and left to the owner) and (2) start the SCANFI stage: "1 finished / 2 go".
**Done:** six folders copied to /mnt/work/from-flash and checked against the originals by file count, apparent bytes and per-file checksum, all matching (device-evidence 7.10 GB, forager-repo-backups 3.03 GB, engine-spike 1.95 GB, apks 0.74 GB, map-style 0.37 GB, label-check 0.16 GB). The owner removed the originals; each now is a symlink on the drive to its copy. The drive has 15 GB free. avd (11 GB) and forecast-data stay on the drive. T6b started at 2026-10-10T07:05:54-07:00 as unit t6b-night (5G cap, Nice=10), stages scanfi-layers,trees, workers 2, until 23:00, log night-2026-10-10.log on the drive.
**Found:** T6b's end-of-section evidence commit has failed since the 2026-10-09T20:18 section: the forecast repo's large-file hook refuses docs/audits/2026-10-07-t6b-run/manifest.jsonl (1,469,819 bytes, limit 1,048,576). The data on the drive is intact; three evidence files are staged and uncommitted in ~/Zynergy/forager-forecast-t6b. The same failure will recur at the end of this section. Put to the owner; not changed.
**Notes:** Next free ID -803.

---

**Kind:** decision
**ID:** 2026-09-28-835
**Timestamp:** 2026-10-10T20:58:04Z
**Title:** Two border tiles added to T6b's PNW run; the beta cleanup built and PR #211 opened
**Context:** The T6b layer review (forager-forecast t6b-pnw-review 5be7eb7, S1): with only the box's 8 tiles, the 49 N seam check can run on 6 of its 25 transects; the other 19 sample into 256_-27_20 and 256_-28_20, US-half tiles whose Canadian cells lie north of 49 N. The box's own 102,543 Canadian cells are islands with no land seam. US side and soil: 296 box tiles listed and ok, 23 of 23 sampled hashes match, 10 independent recomputes agree.
**The owner, verbatim:** "Add the 2 tiles (Recommended)" (offered: run it on 6 lines, labelled).
**Done:** T6b paused for the beta build at 13:22:57 PDT (26 of 88 units done) and resumed by the planner at 13:57 PDT on 10 tiles (the 8 plus 256_-27_20 and 256_-28_20), --until 01:30, from forager-forecast t6b-pnw-scanfi (4ac4cab, the tile filter, whole layers kept); the edge fix merged into t6b-continental-layers as cfbf50d. Beta cleanup (-830) built on beta-diagnostics-out (f6522161 tests first, c1ab617d, 683e6cc9, ca60c540 the divider fix, 8eb87743 report); targeted debug 65/65 and release 7/7; four revert checks and a whole-change revert each fail only their own tests; 23 debug-dependent test files moved unchanged to src/testDebug, which CI's testDebugUnitTest runs (ci.yml:163, checked by the planner); no assembleRelease (signing stays in the owner's checkout). PR #211 opened; merge on the owner's word.
**Notes:** Next free ID -836.

---

**Kind:** merge
**ID:** 2026-09-28-836
**Timestamp:** 2026-10-10T21:09:39Z
**PR:** 211
**Head:** beta-diagnostics-out
**Base:** main
**Merge-commit:** 53f573ae32081e875072bb3efb39ba719503d8c3
**Pre-merge:** 0b561481661961cc7c589b517d7a40eaaecc4d26
**Backup:** 2026-10-10-03
**Observed:** pull request #211 (the last beta's cleanup, -830: the Crash logs row, crash capture and the alert record files out of release builds; Settings ends at Backup with no stray divider) was merged as 53f573ae, pinned to head 8eb87743, on green CI at that head (run 38085796090), read from GitHub, on the owner's "Merge now (Recommended)". The signed release build for Play is the owner's to make from main in their own checkout (signing stays there).
**Also:** the pilot's land pull slowed (about 6 months an hour, the store's per-user cap of 5 confirmed); the builder projects the all-years T1 result at about 19:00 to 20:00 UTC Sunday. The planner's call: the live map gets the all-years model only; a 2019 to 2025 model, labelled as such, is fitted when its years land (about 09:00 to 10:00 UTC Sunday) for the scoring output and the site preview only, as a tested fallback. D33's year range is not changed.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -837.

---

**Kind:** handoff
**ID:** 2026-09-28-910
**Timestamp:** 2026-10-12T04:02:30Z
**Title:** Planner handoff to the next session
**Handoff-file:** prompts/preserved/2026-10-12-planner-handoff.md (this branch). The owner, verbatim: "Write a handoff for the next session. The context window limit is nearly reached so I'll be switching over".
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -911.

---

**Kind:** handoff
**ID:** 2026-09-28-944
**Timestamp:** 2026-10-12T12:01:46Z
**Title:** Planner handoff to the next session
**Handoff-file:** prompts/preserved/2026-10-12-planner-handoff-2.md (this branch). The owner, verbatim: "Write a handoff for the next session please. I'll do it there".
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -945.

---

**Kind:** observation
**ID:** 2026-09-28-965
**Timestamp:** 2026-10-13T17:11:33Z
**Title:** Alan Rockefeller's permission to use his GitHub repositories (owner)
**The owner, verbatim:** "Alan Rockefeller gave me his github and said I can use anything on it. I want to see what we can use from his repository: www.github.com/AlanRockefeller", and, told a written note would settle GPL-licensed code: "I have his permission to use anything".
**What it means:** code and ideas from github.com/AlanRockefeller may be used in Forager, forager-forecast and the future companion app, on the owner's word that Alan gave permission. His copyright notices are kept, and credit is given where his code is used. A read-only survey of the relevant repositories is under way; nothing is taken yet.
**Notes:** Written by the planner by hand, on branch records-after-173. The permission was given to the owner in person; there is no written copy in any repository. Next free ID -966.

---

**Kind:** handoff
**ID:** 2026-09-28-1000
**Timestamp:** 2026-10-14T21:25:57Z
**Title:** Planner handoff to the next session
**Handoff-file:** prompts/preserved/2026-10-14-planner-handoff.md (this branch). The owner, verbatim: "Write a handoff for the next session please".
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -1001.

---

**Kind:** decision
**ID:** 2026-09-28-1022
**Timestamp:** 2026-10-15T03:42:09Z
**Title:** Laptop disk clean-up: flash copies moved to the root drive, finished forecast worktrees removed, Gradle cache and old temp files cleared (owner)
**The owner, verbatim:** to the planner's four options: "1 sounds good on file moving / 2 yes clear out work that is already backed up to the repo / 3 clear it / 4 sounds good / I'll take your recommendations on those".
**Done by the planner:** (1) /mnt/work/from-flash (19,596 files, 13 GB) copied to ~/from-flash on the root drive, listings and sha256 checksums matched, original removed; /mnt/work/from-flash is now a symlink to ~/from-flash so the flash drive's own symlinks resolve. (2) 26 forecast worktrees removed with git worktree remove (no force), each clean and with HEAD on forecast main; .venv removed from 9 more that hold ignored data or logs (kept) and from the separate clone forager-forecast-t0b (0 unpushed commits, 0 stashes); forager-forecast-t4-review left (one uncommitted change). (3) the Gradle cache (caches, wrapper, daemon, workers, native, kotlin-profile; 3.1 GB) cleared; its android and notifications folders kept. (4) 612 /tmp entries older than a day, owned by the planner's user and not in use by any process, removed (3.3 GB); /tmp/pilot-cr, served by a running local web server, kept.
**Result:** work drive 2.9 GB free to 23 GB; /tmp 80% to 21%; root drive 25 GB to 12 GB free. Listings and checksums in ~/cleanup-2026-10-15/ (outside any repository).
**Kept on the planner's recommendation:** device evidence, repository backups (9 GB), the Android SDK (6.1 GB, needed to install builds on phones).
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -1023.

---

**Kind:** decision
**ID:** 2026-09-28-1033
**Timestamp:** 2026-10-15T04:43:42Z
**Continues:** 2026-09-28-1032
**Title:** Host trees for the T6b layers: both genus sets and a host total in one pass, Canada's gap stated, each band earns its place under D121; PNW first (owner, provisional as -1030)
**The owner, verbatim:** to the planner's six recommendations: "All recommended".
**What it sets, provisionally until review, with a warning before any point of no return (-1030):** (1) add tier A (Larix, Betula, Populus, Alnus, tanoak and chinquapin, Arbutus) and tier B (Fagus, Carya, Tilia, Ostrya and Carpinus) and an ectomycorrhizal-host total band in one pass; tier B needs D116 amended by a new row; (2) Canada: the genera SCANFI folds into broadleaf are flagged not available, and the licence of a second Canadian source (NRCan's forest-attribute maps) is read at its source for the continental roll-out; (3) the new bands enter the fit under D121, each kept only if it improves held-out years; (4) aspen's crown-width coefficients stand in for genera without their own (as D89(2)); (5) order: the PNW box first (one night), then the rest of the US; old tiles kept until the new ones are verified, then removed on the owner's word; (6) T5's genus list unchanged, a T6b-only list. Also taken as accepted: the stage 2 coder's reading that a crashed or unreadable clean check shows the -1003 message (-1031). Any build must fix the verify report's F1 (tiles counted done by key and hash only) and F2 (the plot table reused unless its rulings string changes).
**Not a go:** building the change needs the owner's go.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -1034.

---

**Kind:** intent
**ID:** 2026-09-28-1048
**Timestamp:** 2026-10-15T19:19:51Z
**Continues:** 2026-09-28-1046
**Title:** RAW stage 3, piece 1: a burst-rate and lock probe on the dev build, nothing saved (owner); the rest-of-US tree rebuild not authorised
**Dispatch-file:** preserved/2026-10-15-06.md
**The owner, verbatim:** to two questions (1: start the rest-of-US tree rebuild, about 35 hours; 2: write up stage 3 piece 1 and start a coder): "Both, go", then, after the planner had begun on 1: "Not 1", "2 go, not 1".
**What happened on 1:** the planner's command to switch the continental section to the tree rebuild was refused by the owner mid-run. Its first step had run: PAUSE was touched and t6b-night stopped cleanly at 12:18 PDT (SCANFI-layer stage, section end 3,692 unit lines). No tree unit ran (0 tree units after noon). The planner removed PAUSE and restarted t6b-night as it was (new code, --stages scanfi-layers, --workers 2, --until 07:00) at 12:18:36 PDT. The rest-of-US rebuild stays unauthorised.
**Change (2):** a dev-only probe (a second commit on dev, under app/src/debug) that, triggered over adb with the camera open, runs four runs of 8 back-to-back captures (RAW+JPEG and RAW-only, each with AE and AWB unlocked and locked) and logs per-frame timing, sensor timestamps, exposure, ISO, boost, AE/AWB/AF states, focus distance, black and white levels, copy time and a sharpness figure, plus per-run heap, the sensor's minimum frame duration and stall; frames discarded; the camera restored to the user's format. Branch raw-stage3-probe from origin/dev 4c278251, PR into dev, unmerged. Tests first, revert checks, CI only.
**Finish line:** the coder's report; the planner merges into dev, runs the probe on the S22 then the S26 in bright and dim light, and tabulates the rate for the owner before piece 2 (-1046 Q2).
**Abort conditions:** main must change; any visible change in a release build; the camera left dead or in the wrong format; two failed attempts.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -1049.

---

**Kind:** handoff
**ID:** 2026-09-28-1072
**Timestamp:** 2026-10-16T02:03:09Z
**Title:** Restore points in all three repositories, and a planner handoff to restart from (owner)
**The owner, verbatim:** "Back up the repo into a branch so we can restart here".
**Done:** snapshot branches pushed at the heads of 2026-10-16T02:02Z: Forager snapshot-2026-10-15-main (402489ae), -dev (296a3420), -records-after-173 (56fe3b2a); forager-forecast snapshot-2026-10-15-main (b9127e58), -t7-build (169cd63e), -t6b-host-genera (b0a0e889); zynergy-site snapshot-2026-10-15-main (b22cca5a). Handoff-file: prompts/preserved/2026-10-15-planner-handoff.md (this branch), replacing 2026-10-14-planner-handoff.md as the start point; that file's next-free-ID line went stale after -1047 and is superseded here, not edited.
**Notes:** Written by the planner by hand, on branch records-after-173. The snapshot of records-after-173 predates this entry and the handoff file. Next free ID -1073.

---

**Kind:** handoff
**ID:** 2026-09-28-1084
**Timestamp:** 2026-10-16T11:43:00Z
**Title:** Planner handoff to a new session, with three subagents still running (owner)
**Handoff-file:** prompts/preserved/2026-10-16-planner-handoff.md (this branch), replacing 2026-10-15-planner-handoff.md as the start point. The owner, verbatim: "Let's hand off to a new session".
**Running at handoff:** the T7 full run (forecast t7-build at dccb1f4: V9 counted, one fold timed at 646 s, an 18.7-hour fit projected and proceeding); the camera-reach probe (Forager camera-reach at d12c7bad); the engine A prototype (camera-engine-a, not yet pushed). Their reports reach only the old session; the handoff says how to check and resume each. The W42 reminder (Saturday 17:00Z) is bound to the old session; the daily t6b-night restart after 07:00 PDT is a manual step; both are in the handoff with commands.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -1085.

---

**Kind:** decision
**ID:** 2026-09-28-1134
**Timestamp:** 2026-10-17T02:37:22Z
**Continues:** 2026-09-28-1133, 2026-09-28-1128
**Title:** Auditors and independent reviewers run on a different model from the one that coded the work, Fable here; a second T7 review runs on Fable beside the Opus one; the first promotion merges on its Opus audit (owner)
**The owner, verbatim:** "Auditor sessions can be ran by the planner in a separate session, or by the operator in another window. It shouldn't be held by the same coder model that implemented it." Then, of "model": "Opus model, Fable, Sonnet, Haiku, for example. It's useful because the same model shares blind spots." To the planner's questions:
- the audit model: "Fable for us, but in general just another model altogether. Maybe ChatGPT or Gemini if the user has no claude subscription";
- the running T7 review: "Let it finish, add a second";
- the promotion: "Merge on the Opus audit".
**What it sets:**
- An auditor or independent reviewer is a separate session, started by the planner or opened by the operator in another window, and runs on a different model from the coder. Forager's coders are Opus, so its auditors and reviewers run on Fable. As a general rule (for E-GD): any other model, including another provider's where no Claude subscription is available.
- The Opus T7 review (-1128) finishes. A second T7 review runs on Fable, independently, without reading the first, and the two are compared.
- PR #239 merges on its Opus audit (-1132). The rule applies from the next audit.
**Disclosed by the planner:** the QA philosophy's drafting audit (-1092), the promotion audit (-1132) and the running T7 review (-1128) were all Opus subagents, the same model as the coders, before this rule.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -1135.

---

**Kind:** decision
**ID:** 2026-09-28-1171
**Timestamp:** 2026-10-17T08:02:03Z
**Continues:** 2026-09-28-1168
**Title:** Direction: plan to use the federal trail data gathered for T7 part B for Forager's trail navigation (owner); scope only, not a go
**The owner, verbatim:** "Let's also plan to use the trail maps for trail navigation".
**What it sets:** the trail lines fetched for T7 part B (-1168) are a candidate data source for the app's trail navigation, which belongs to the next update (-904). Before any build, the planner brings a short plan to the owner.
**The planner's check, read from Forager main:**
- docs/navigation/2026-10-01-navigator-completion-plan.md names no trail data source;
- docs/plans/own-map-tiles.md uses OpenStreetMap for the basemap.
**For the plan to weigh:**
- **Licences, for the app** (attribution text in the app, written as each licence requires): Forest Service roads and trails CC BY 4.0; BLM public domain; USGS NTD "None", with acknowledgment appreciated.
- **Gaps:**
  - Umatilla and Wallowa-Whitman publish almost no trail geometry;
  - the state and volunteer segments were dropped for T7 (-1168), and for the app they would need their terms confirmed;
  - coverage is the US only.
- **Routing:** federal trail lines may not join up as a routable network, so whether a route can be followed end to end needs checking.
- **Packaging:** whether trails ship inside the app's own offline map tiles (own-map-tiles) or as a separate layer.
- **Comparison:** against OpenStreetMap's trails, which are richer but ODbL. Share-alike applies to a derived database, not to the app.
- **Separation:** the copies under /mnt/work belong to the forecast. The app would need its own fetch, kept apart from the forecast data.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -1172.

---

**Kind:** handoff
**ID:** 2026-09-28-1179
**Timestamp:** 2026-10-17T09:32:22Z
**Title:** Planner handoff to a new session (owner)
**Handoff-file:** prompts/preserved/2026-10-17-planner-handoff.md (this branch), replacing 2026-10-16-planner-handoff.md as the start point.
**The owner, verbatim:** "Context window is getting full, so we will have to hand this off to another session window. I'll meet you over there".
**At handoff:**
- **Running:** no helper; t6b-night until 07:00 PDT.
- **Awaiting the owner:**
  - forecast PRs #3 and #4 into t7-build;
  - the T7 re-fit (the second point of no return);
  - the lens-fix device run;
  - the known-bugs list.
- **Reminders bound to this session,** which the new one must re-create: the 07:02 PDT t6b restart and the 10:00 PDT W42 check.
- **Open-intents check at handoff:** -1149 (lens fixes) is open and in progress. Every other intent from this session is closed.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -1180.

---

**Kind:** decision
**ID:** 2026-09-28-1180
**Timestamp:** 2026-10-17T09:38:54Z
**Continues:** 2026-09-28-1179, 2026-09-28-1149
**Title:** Forecast PRs #3 and #4 merge into t7-build; the lens-fix device run is tomorrow (owner)
**The owner, verbatim:** "1 merge PR #3 and PR #4 into t7-build"; "2 it will be ran tomorrow".
**What it sets:**
- **T7:** part C (PR #3, the saprotroph count) and part B (PR #4, the access layer) go into t7-build, naming each PR as D40 asks. The re-fit is still -1030's second point of no return and is asked separately.
- **Camera (-1149):** the owner runs the Phase 2a device check on 2026-10-18, using the APK in `~/Zynergy/device-evidence/2026-10-17-lens-fixes-2a-apk/` and Hazel's steps in her Phase 2a report. -1149 stays open.
**Notes:** Written by the planner by hand, on branch records-after-173. Next free ID -1181.

---

**Kind:** handoff
**ID:** 2026-09-28-1251
**Timestamp:** 2026-10-18T05:40:18Z
**Title:** Forecast work moves to a forecast planner, with its own record in forager-forecast (owner)
**The owner, verbatim:**
- "A planner may be necessary to talk with in the forecast repo instead of directly to a coder, since it's a different repo altogether. Open a new planner session, and begin a Forager-forecast planner profile for the repo. They can write the plans for Ash";
- "Its own record in forager-forecast (Recommended)";
- "All forecast work (Recommended)".
**Handoff-file:** forager-forecast docs/planning/handoffs/2026-10-18-planner-handoff.md (branch forecast-planner-profile b5566229), beside the begun profile docs/process/planner-profile.md. Both are on that branch and go to main on the owner's word (D40).
**At handoff:**
- **The new session:** session_01BeCyTz4uLqzv9n1u8R42ht, "Forecast planner (forager-forecast)", on the laptop bridge. Its first act is to propose three names and set up the forecast's own record.
- **Moved to it:** T8 (Ash's draft plan, paused WIP on t8-plan d6f916ae); the W42 publish check (Rowan's reminder deleted); the t6b-night restarts; T7's record (the decision row, the audits index rows, draft PR #5); the debt to Dr Põlme (-1169).
- **Ash** was paused by Rowan and has finished.
- **Stays with Rowan:** the Forager app, the production release, this RECORD.md, and vector maps beyond the US (-1243).
- **The open-intents check:** -1248 (the T8 plan) moves with T8 to the forecast planner and is closed here by handover, not as done. The open app intents are -1226 (the three tabs, PR #252, Hazel at work), the lint phone check and the T7 device checks (-1212, -1213), and the camera lens fixes (-1149).
**Notes:** Written by the planner by hand, on branch records-after-173. From here on, forecast entries are in the forecast's own record, and this file cites them by that record's IDs. Next free ID -1252.
