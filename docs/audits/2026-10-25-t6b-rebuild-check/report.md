# T6b rebuild check, report (dispatch 2026-10-25-t6b-rebuild-check)

**Written by Ash Transect (forecast coder); saved by the forecast planner (Alder Bearing).** Ash's file tool refused
to write report files from a helper session, and Ash didn't work around it. The owner, 2026-10-25, answering "Ash's
report text couldn't be saved by Ash. Should I save it?": "Yes, save it as Ash's (Recommended)". Everything below
this line is Ash's hand-back, word for word. The planner changed only the heading levels, so it nests under this
title.

---

**T6b rebuild check: finished, apart from one blocker for the first run and a report file I couldn't create.** The drive path is now one setting, the new drive passed 16 of 16 checks, and the re-fetch list and night estimates are below. Nothing was downloaded, no run was started and no tiles were built.

**Final pushed commit:** `54a6f6dfcee72fd3815a4fbe37f59e629f1d942c` on t6b-rebuild, confirmed with `git ls-remote origin t6b-rebuild`. Commits on top of the dispatch (a1208db): `a00e120` (item 1), `7d57603` (item 2), `54a6f6d` (items 3 to 5 evidence).

**The report file isn't on the branch.** The dispatch asks for `docs/audits/2026-10-25-t6b-rebuild-check/report.md`, but my file-writing tool refused it: subagents may not write report files. I didn't work around that. Everything the report would hold is in this message. The scripts and outputs behind each figure are committed in that folder, so you or Alder can commit this text as `report.md`.

**Tests:** 609 passed before, 616 after (7 new in `tests/test_t6b_drive.py`). Run with `uv run --frozen pytest` under `systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0 nice -n 10`. Ruff is clean on scripts, src, tests and the new audit folder. Over the whole repository, ruff has 2 E501 errors and 1 format difference, all in an evidence script that was already like that at 621421b (`docs/audits/2026-10-15-t6b-host-genera-build/plot_table_real.py`); I left it alone.

## Wrong premises, and one blocker
1. **"Making the finished store read-only"** names a step the code doesn't have. Nothing in `scripts/t6b_run.py` or `src/forager_forecast/t6b_*.py` changes a file mode. I could only check that ext4 enforces read-only, which it does.
2. **T6b never used T5's `data/t5` link.** The runner reads TreeMap at `DRIVE/"t5"/"treemap2023"` directly (`scripts/t6b_run.py:90`). The only `data/t5` link left is in the forager-forecast-t5-review worktree. It now points at the missing old path; I didn't touch it.
3. **The `9cf29560…` sha256 is of the decompressed manifest.** The gzip file itself hashes to `69ed1674…`. Decompressed, it matches the summary on sha256, bytes (11,829,884) and lines (29,185). This is a clarification, not an error.
4. **The 2G cap can't hold the run.** The last section peaked at 4.2 GB under its 5G cap (journal, 2026-10-23). Two tree workers were killed for running out of memory at 5G (RECORD -2041).
5. **Blocker before any first run:** the first section's progress save would overwrite the only copy of the old manifest.
   - `MANIFEST_COPY_DIR` is `/mnt/work/Zynergy/forecast-data/t6b` (`scripts/t6b_run.py:103`), and `save_manifest_outside` replaces `manifest.jsonl.gz` there (`src/forager_forecast/t6b_run.py:145-159`).
   - `~/Zynergy` is bind-mounted from `/mnt/work/Zynergy`, so the file under `~/Zynergy/forecast-data/t6b` is the same file (same inode).
   - The default `--evidence` folder (`:100`) would likewise replace the old run's working copies of `run.log.txt` and `manifest_summary.json`. Git keeps their history.
   - Options for the planner:
     - (a) copy the old gzip aside, read-only, which is a write under `~/Zynergy/forecast-data` and needs the owner's word;
     - (b) add a flag for where the runner writes its copy (new code, with tests).
     - Either way, pass a new `--evidence` folder.

Everything else in the dispatch checked out:
- The drive is ext4, label forecast-data, UUID e4918208-…, mounted read-write at `/run/media/zynergy-labs/forecast-data` with `errors=remount-ro`.
- It's owned by zynergy-labs (mode 700), holds only `lost+found`, and has 57,458,769,920 bytes free (53.5 GiB).
- The old path is gone.
- T4, T6, T7, T8 and GBIF are present under `~/Zynergy/forecast-data`.

## Items 1 to 5
1. **One setting for the drive (run).**
   - `src/forager_forecast/drive.py:13` sets `DRIVE = Path("/run/media/zynergy-labs/forecast-data")`.
   - The five scripts that named the old mount now import it: `t6b_run`, `t6b_fetch_sources`, `t6b_fetch_scanfi_layers`, `pnw_build`, `pnw_checks`. No module under src/ named it.
   - Tests first: with only the setting added, 6 of the 7 tests still failed, each for its own reason.
   - Revert check: putting the old literal back in a scratch copy of `t6b_run.py` (it compiled) failed exactly the two tests about that file. The worktree file was checked afterwards and still holds the change.
   - **A call I made beyond the dispatch:** the mount itself replaces the old `forecast-data/` folder. The store is `<mount>/t6b`, with no `<mount>/forecast-data/t6b`. If you want the extra level, it's one line in `drive.py`.
2. **The new drive (run).** `drive_check.py` drives the runner's own functions on small files under `<drive>/t6b-check`. Run 3 passed 16 of 16:
   - the mount, and the free-space check;
   - two-worker writes as `.partial` then renamed, with fsynced manifest lines;
   - resume by hash, and redoing a changed tile;
   - a stray `.partial` file isn't counted as a tile;
   - PAUSE at the start, and PAUSE mid-section (the tile in hand finishes);
   - appending to the manifest, and moving superseded tiles aside;
   - symlinks on the drive and into it from `/mnt/work`;
   - read-only refusal, with reads still working;
   - the progress save, committed and pushed to a scratch bare remote through the large-file hook.

   Runs 1 and 2 failed because of bugs in my check script, not the drive. Both are fixed and the run 2 output is committed. The 19 scratch paths were deleted (listed in `deleted-from-drive.txt`); the drive again holds only `lost+found`.
3. **Re-fetch list (read, plus HEAD requests).** The table is further down. By stage:
   - the mask stage, which every other stage needs, uses both CEC files;
   - plots uses the TreeMap zip and its `.vat.dbf`;
   - trees and trees-us-half use the TreeMap raster and NALCMS;
   - scanfi-layers uses NALCMS and the 11 SCANFI layers;
   - soil fetches its SoilGrids windows itself during the run, so that stage is itself a pull.

   Two steps have no code path: extracting the CEC zips to the folders the runner reads (`scripts/t6b_run.py:81-88`), and downloading and extracting TreeMap. The member paths inside those zips are recorded nowhere.
4. **The old manifest (inferred).** Use it read-only to check the rebuild, never as the live manifest and never to skip a tile.
   - Tile bytes look reproducible: no times or paths go into the tags, and three SCANFI `.npz` files written at different times hash the same (`3d12821d…`). So each rebuilt unit's sha256 can be compared with its last ok line under layout `t6b-bands-f4e9b848ba51`.
   - Cheap early checks: mask `2a71f873…`, `plots.npz` `6cc68b02…`, and the committed `tiles_trees.json` and `tiles_soil.json`.
   - Expected differences: a source changed upstream (SoilGrids is read from "latest"), or a border tile built by a different route, since `fill_canadian_cells` tiles carry extra tags.
   - At the loss the store held 89 soil, 22,473 SCANFI-layer, 2,289 trees and 92 trees-us-half units.
   - No comparison script exists yet; it would be new code.
5. **Night estimates (inferred).** See the table below.

## Re-fetch list
HEAD requests were sent 2026-10-26 03:2x to 03:38 UTC; they fetch no data.

| Source | URL | Size | Checksum on file | HEAD now |
|---|---|---|---|---|
| CEC Political Boundaries 2021 (zip) | cec.org …/0_01_political_boundaries/politicalboundaries_shapefile.zip | 184,774,593 B | sha256 29f3aec7…, ETag "b036fc1-65b8a5e998dc0" | unchanged |
| CEC Ecoregions L3 (zip) | cec.org …/1_06_3_terr_ecoregions_iii/terr_ecoregions_v2_level_iii_shapefile.zip | 35,236,046 B | sha256 a99b4967… | unchanged |
| NALCMS 2020 30 m (GeoTIFF member of a 3,947,704,951 B zip) | cec.org …/land_cover_2020v2_30m_tif.zip | 3,363,872,655 B | CRC-32 52c3bc0a, sha256 0d6b497a…, zip ETag "eb4d3277-65b8af17735c0" | zip unchanged |
| TreeMap 2023 (`RDS-2026-0038.zip`) | `https://usfs-public.box.com/shared/static/xlaazfhic3ugd1yetoxcicjgtl2t3mry.zip` (catalogue RDS-2026-0038) | 4.87 GB | sha256 348264eb…abb7 (the catalogue's own) | catalogue page re-read: same size and sha256 |
| TreeMap raster and `.vat.dbf` (extracted from that zip) | – | not recorded | `.vat.dbf` 3f0208e0…; none for the `.tif` (the zip's CRC can check it) | – |
| SCANFI v2 2025, all 11 layers | ftp.maps.canada.ca …/SCANFI/v2/SCANFI_spsCC_<layer>_2025_v2_20260119.tif and SCANFI_att_closure_… | 19.0 GB together | see the next table | see the next table |
| SoilGrids pH windows (fetched per tile during the run) | files.isric.org/soilgrids/latest/data | not recorded | none; each tile's request record was on the lost drive | – |

SCANFI by layer:

| Layer | Bytes | sha256 on file | HEAD now |
|---|---|---|---|
| balsamFir | 1,161,699,718 | none | same length |
| broadleaf | not on file | none | 2,680,330,226 |
| jackPine | not on file | none | 1,615,259,150 |
| otherConiferous | 2,584,284,940 | 164e9250… | timed out |
| ponderosaPine | 82,404,500 | 1d5d289e… | timed out |
| tamarack | 1,870,843,730 | dfcfc8ad… | timed out |
| whiteRedPine | 275,422,498 | cc5598a6… | timed out |
| att_closure | 4,203,303,371 | 84e7490d… | timed out |
| blackSpruce, douglasFir, lodgepolePine | about 4.5 GB together (inferred) | none | timed out |

The SCANFI server answered 3 of 11 HEADs; I stopped after two attempts. Only 5 of the 11 layers have a sha256 on file.

## Night estimates
Rates, from the manifest's 44 section lines, each matched to its worker count in `run.log.txt`:

| Stage | 1 worker | 2 workers |
|---|---|---|
| scanfi-layers | about 83 units/h (not measured: from the mean unit time, 43.4 s) | 165.2 units/h (21,329 units in 464,833 s, 2026-10-15 to 10-20) |
| trees (current layout) | 59.2 units/h (2,157 units in 131,077 s) | not measured; killed for memory at 5G, so taken at the 1-worker rate |
| soil | about 10.9 units/h (inferred) | 20.4 units/h (52 units in 9,177 s) |
| mask and plots | 441 s and 17 s | same |

A "night" of 23.9 h is how t6b-night ran from 10-15 (about 07:05 to 07:00). The 9 h column assumes real nights.
- **A, rebuild to the state at the loss:**
  - 1 worker: 317.8 h, 13.3 nights (35.3 nights of 9 h).
  - 2 workers (trees at 1): 179.2 h, 7.5 nights (19.9).
- **B, the whole continent (A plus the 1,769 Canadian tree tiles never built):**
  - 1 worker: 347.7 h, 14.5 nights (38.6).
  - 2 workers: 209.1 h, 8.7 nights (23.2).
- Add about 2 h of downloads.

## What I couldn't check
- The member paths inside the CEC and TreeMap zips, and how they were extracted before.
- The current length and ETag of 8 SCANFI layers (the server timed out).
- The store's final size: the manifest has hashes but no file sizes.
- Whether rebuilt tiles are really byte-identical.
- How the drive behaves when unmounted, pulled out or hitting errors mid-run, and its speed under load. I didn't unmount it.
- One-worker rates for scanfi-layers and soil, and a two-worker rate for current-layout trees.
- Where the run's venv will live. This worktree is on `/`. The old run worked from `~/Zynergy/forager-forecast-host-genera-build` on `/mnt/work`, whose scripts still name the old path.

## Other things I did beyond the dispatch
- The HEAD requests and one read of the TreeMap catalogue page. Neither downloads data, but I'm flagging them under "no pulls".
- The venv and uv cache were built under `/mnt/work/scratch/t6b-rebuild`. That folder (714 MB) is now deleted.
- `/` read 25 MB free at the end. This task's own footprint on `/` is the worktree (16 MB); all scratch was on `/mnt/work`. `~/.cache/forager-wt` holds 142 entries from other sessions.

## First run (each step needs the owner's word)
Settle the blocker above first. Pulls, one at a time:
- `nice -n 19 ionice -c3 .venv/bin/python scripts/t6b_fetch_sources.py vectors`
- the same with `nalcms`
- TreeMap by hand to `<drive>/t5/treemap2023/RDS-2026-0038.zip`, then extract its `.tif` and `.vat.dbf` there
- extract the two CEC zips under `<drive>/t6b/sources/`
- optionally `scripts/t6b_fetch_scanfi_layers.py --reserve-gb 8`

The run, in the 2026-10-18 handoff's form (the new PAUSE path is `/run/media/zynergy-labs/forecast-data/t6b/PAUSE`):
```
systemctl --user reset-failed t6b-night; systemd-run --user --unit=t6b-night -p MemoryMax=5G -p MemorySwapMax=0 -p Nice=10 --working-directory=$PWD $PWD/.venv/bin/python scripts/t6b_run.py --until 07:00 --stages mask,plots,soil,scanfi-layers,trees --workers 2 --evidence docs/audits/<new-run-folder>
```
Trees sections need `--workers 1`. The stage order, cap and worker count are the planner's call.

Files are in `~/.cache/forager-wt/t6b-rebuild/docs/audits/2026-10-25-t6b-rebuild-check/`:
- drive_check.py
- drive_check.run2.out.txt
- drive_check.run3.out.txt
- manifest_read.py
- manifest_read.out.txt
- failing-first-setting-only.txt
- revert-t6b_run-old-literal.txt
- source-heads-1.txt
- source-heads-2-scanfi-retry.txt
- deleted-from-drive.txt
