# Pulls queue: Ash's hand-back

**Written by Ash Transect; saved by the forecast planner (Alder Bearing),** as with the T6b check and T8b step 1.
Word for word below the line, with the first heading level changed only.

---

## Pulls queue (dispatch 2026-10-26-pulls): running; first files verified; Daymet stopped at a login

The queue is running as the user unit `forecast-pulls`. Its first two files, the CEC zips, downloaded with sha256 equal to the earlier pulls' and are extracted. NALCMS was streaming when I handed back (1.27 GB of 3.36 GB at 06:12 PDT).

**Wrong premises and stops, first:**
1. **Daymet (Part B item 2): a GET needs a login, so I stopped it.** This is the dispatch's own stop.
   - At 2026-10-26T12:40:57Z, a 1 KB range GET of `daymet_v4_daily_na_prcp_2014.nc` went 302 to `urs.earthdata.nasa.gov/oauth/authorize`, then 401 "HTTP Basic: Access denied." No data byte arrived.
   - A HEAD is still answered without a login, which is what step 1 saw.
   - I made no account and accepted no terms. Daymet is not in the queue, and I didn't build the box-cut code.
   - Evidence: `docs/audits/2026-10-26-pulls/daymet-login-check.txt` (t8b-build).
2. **The unit may not outlive a logout.** `loginctl` shows `Linger=no`, so if the owner's last login session ends, systemd stops the user's units, this one included. Turning linger on is a system setting I didn't change; that's the owner's call. Rerunning the queue resumes it: verified files are skipped and partial files are fetched again.
3. **Smaller differences from the dispatch's figures:**
   - `/mnt/work` had 5.4 GB free, not 8 GB.
   - The drive had 207,392,735,232 B free (193 GiB), which matches the dispatch's "194 GB" read as GiB. So I set the 20 GB floor at 20 GiB, the stricter reading.

## Checking on it
- **Status:** `systemctl --user status forecast-pulls`
- **Log:** `/run/media/zynergy-labs/forager-storage/forecast-data/pulls/queue.log`. Lines are tagged `[queue]`, `[A]` or `[B]`; the last line gives the stop reason or exit code.
- **Pause:** `touch /run/media/zynergy-labs/forager-storage/forecast-data/PAUSE`.
- **Order:**
  1. CEC zips, each extracted straight away. I moved this extraction ahead of NALCMS so the member paths were checked early.
  2. NALCMS.
  3. TreeMap zip, then its `.tif` and `.vat.dbf`.
  4. SCANFI, 11 layers, one per call.
  5. ERA5-Land, 135 months.
- **The queue stops itself on:** a sha256, MD5 or size mismatch (the file is renamed `.mismatch`), a login wall, a licence refusal, less than 20 GiB free counting the file about to arrive, a PAUSE file, or network errors after the retries.
- Started with `systemd-run --user --unit=forecast-pulls -p MemoryMax=2G -p MemorySwapMax=0 -p Nice=10 bash ~/.cache/forager-wt/t8b-build/scripts/pulls_queue.sh`.
- Both venvs and the uv cache are on the drive at `forecast-data/pulls-env` (471 MB).
- t6b-night isn't running, and no fit is running. `t8-fit-runner` shows as failed, an old unit I didn't touch.

## What has verified so far (from the log)
- **cec_political.zip:** 184,774,593 B, sha256 29f3aec7…0c28, the same as `docs/pulls/t6b-cec-political-boundaries-2021.request.json`. The ETag is unchanged.
- **cec_ecoregions_l3.zip:** 35,236,046 B, sha256 a99b4967…3338. Part B item 4 uses this file, at `forecast-data/t6b/sources/cec_ecoregions_l3.zip`.
- **Extraction:** 17 files from each zip, each CRC-checked, all under `t6b/sources/`.
  - The member paths, which were never recorded before, are now in the extraction records: `politicalboundaries_shapefile/NA_PoliticalDivisions/data/boundaries_p_2021_v3.shp` and `terr_ecoregions_v2_level_iii_shapefile/NA_TerrEcoregions_III/data/NA_Terrestrial_Ecoregions_v2_level3.shp`.
  - Both land exactly where `scripts/t6b_run.py:81-88` reads them.
- The four records are committed in `docs/pulls/t6b-rebuild-cec-*.{request,extract}.json`.
- **Not verified yet:** NALCMS, TreeMap (including whether its box.com link downloads without a login; a login wall would stop the queue there), SCANFI and ERA5-Land. Records for later files are written next to each file on the drive, and someone needs to copy them to `docs/pulls/`.

## Commits (from `git ls-remote`)
**t6b-rebuild, at e918d99256ad8669bec6dbcb737d91c18818b7d1:**
- `0726e8c`: the queue's checks (`pulls_queue.py`), zip extraction (`zip_extract.py`), Part A steps (`t6b_pulls.py`, `scripts/t6b_pulls.py`), with tests first.
- `6fd902d`: revert checks and the full test-suite run after the change.
- `e918d99`: the CEC records.

**t8b-build, at 137a3c7c4836c5c7fa556ef2933a514f6952fe1c:**
- `1635765`: item 1.
  - All twenty readings are in `RULED`, each citing "D160 (4)". D159 itself left no reading open.
  - New `US_CELLS_ONLY_LINE` / `BESIDE_LINES = {"us-cells-only": "D160 (4)"}`.
  - **Not fixed:** which cells count as US. No code builds that line yet; it needs a reading before it's built.
  - The four refusal tests in other files now empty `RULED` first through a new `unrule_all`, so each refusal is still exercised. That is a change to existing tests.
- `a2da7ad`: the ERA5-Land pull (`t8b/cds_pull.py`, `scripts/t8b_era5land_pull.py`), the queue driver (`scripts/pulls_queue.sh`) and the Daymet login evidence.
  - The pull sends one daily-statistics request per month, 2014-10 to 2025-12, and checks each delivery against the store's `file:size` and MD5.
  - If the store already holds a matching job, the pull adopts it instead of resubmitting.
- `137a3c7`: item 5, two new register rows.
  - Daymet V4 R1: CC0 under the EOSDIS guidance per D160 (3), with ECCC credited. This row corrects `:10`, which is left as written; it is marked "not downloaded".
  - ERA5-Land layer 2 and 2 m fields: CC BY 4.0.
  - I re-read both licences at source at 2026-10-26T13:11Z and quoted them with their URLs.

## Tests
- **t6b-rebuild:** 616 before, 653 after (37 new). Over stubs, all 37 failed for their own reason (36 NotImplementedError, 1 regex miss on an empty message).
- **t8b-build:** 767 before, 790 after (23 new). Over stubs, 6 design tests failed on assertions and 17 pull tests on NotImplementedError.
- **Ruff** is clean on both branches.
- **Revert checks:** each was run on a scratch copy, with the import log read first, and afterwards the worktree still held the change each time.
  - Removing the sha256 comparison, the PAUSE stop, the SCANFI on-file sha256 or the MD5 comparison each fails its own tests.
  - Emptying `RULED` fails the 5 ruled-state tests.
  - The first sha256 and PAUSE runs also showed a "targets" test failure. That came from my copy missing `scripts/`, not from the revert, so I re-ran both with `scripts/` copied and those are the logs committed.
  - Logs are in `docs/audits/2026-10-26-pulls/` on both branches.

## Decisions I made beyond the dispatch
- **SCANFI:** I don't resume a partial file (the dispatch says partials are re-fetched). The reserve is the queue's 20 GiB floor instead of the script's 8 GB. Only 5 of the 11 layers have a sha256 on file; the other 6 get only the download's size check.
- **TreeMap:** the zip is checked against the catalogue's sha256. The `.vat.dbf` is checked against 3f0208e0…77d3. The `.tif` gets only the zip's CRC check, because no sha256 for it is on file.
- **Probes:** one 1 KB Daymet range GET and one HEAD. Scratch on `/mnt/work` is deleted.
