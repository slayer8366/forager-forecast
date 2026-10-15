# T6b build and first run section: what landed, what the section measured, and three stops

Written 2026-10-07 02:35 UTC (2026-10-06 19:35 local) by the T6b coder session (D38), branch
`t6b-continental-layers`, base `origin/main` `36cc647`. It answers the planner's go relayed with
Forager RECORD -613, filed as D111 to D115. It is an interim report, not the completion report:
the run has not finished.

**In short:** the build is in, with tests first, a strict revert runner and the full suite run
under the cap. The first section built the study-area mask and two soil tiles. It then hit three
things that stop the host-tree run, and none of them was fixed by guessing:
1. 73 TreeMap genera are in neither of T5's class lists.
2. Arctic coastal slivers are left in the study area.
3. The SCANFI windowed fetch ran about twenty times slower than in the trial.

**Neither a full-run time nor the first large window's time can be given.** The super-window fetch
was stopped at 15 minutes with one of eleven layers done (section 3), and no tree tile ran.

## 1. What landed

| Commit | What |
|---|---|
| `72ac5d1` | D111 to D115, register rows (CEC Political Boundaries 2021; NALCMS in T6b), source fetcher and its tests, CEC request records |
| `4b3e758` | Regrid with pixel positions against the source's full-raster origin (D115 item 5) |
| `881649d` | Study-area mask and side rule (D111, D113, D115 item 1); NALCMS request record |
| `1796b38` | Soil and host-tree layers per tile: mask, water (D112), side, origin placement, super-window fetch, plot table once |
| `d9faff0` | Sectioned runner (D114) and `scripts/t6b_run.py` |
| `7622db3` | Soil-mask and plot-table tests (absolute values) |
| `d302172` | Strict revert runner and results |
| `f7c82ec`, `f87caa4`, `343721e` | The runner's own end-of-section commits |
| `e2a8ee0` | Soil: regrid only the box holding a tile's study cells (section finding) |
| `436bcab`, `ceacdea` | Per-stage tile limits, `--tree-groups` |

**Sources fetched, all to the flash drive:**

| Source | What was fetched | Check |
|---|---|---|
| CEC Political Boundaries 2021 | shapefile zip, 184.8 MB | sha256 in its request record |
| CEC Terrestrial Ecoregions level III | shapefile zip, 35.2 MB | sha256 in its request record |
| NALCMS 2020 30 m | GeoTIFF member only, 3,363,872,655 bytes, streamed out of the 3.95 GB zip in 274 s | CRC-32 `52c3bc0a` equal to the zip's |

The NALCMS raster declares no-data 127. D112 names 18 (Water) and 0 (unmapped); 127 is treated the
same as 0.

**Names read from the source files:**
- Ecoregion level I: "Tundra" is LEVEL1 2 (606 polygons) and "Arctic Cordillera" is LEVEL1 1 (60).
- NALCMS: 18 is "Water" and 19 is "Snow and Ice" (attribute table).

## 2. Tests and revert checks

**Tests first.** Each was seen red before its code:
- source extraction and mask tests: at collection;
- the origin regrid: on import;
- the layer tests were written against code already present. Their bite is shown by the reverts.

Layer tests run on synthetic sources in the real projections:
- TreeMap EPSG:5070, SCANFI LCC, NALCMS LAEA, SoilGrids Homolosine;
- one 16-cell tile against four 8-cell tiles: equal bit for bit for soil and trees, values and flags;
- Arctic cells blank;
- sides and not-available flags;
- water is no data where a dry run has cover;
- the plot table against T5's `plot_cover` and CANOPYPCT.

Runner tests:
- the pause file;
- the stop time, checked before each tile;
- an interrupted tile and a damaged tile are run again;
- a group is prepared once and cleaned after its last tile;
- two workers.

**Full suite under the cap:** before 416 passed, 292 test functions. After 440 passed, 315 functions.
Peak memory 534 MB. Ruff clean.

**Revert runner** (`2026-10-07-t6b-build/revert.py.txt`): T5's strict runner with saved-copy
restore, `__pycache__` cleared, `PYTHONDONTWRITEBYTECODE=1`, and a refusal when the edit is unseen or
collection errors.
- 15 checks. Every run was citable and every file was restored equal to HEAD.
- **13 bite**, each with a message specific to its edit (`revert_results.json`).
- The 2 labelled "may not bite" before the run did not: the CRC comparison and window-relative pixel
  centres.
- **One coverage note.** The origin-placement revert fails only the regrid unit test, which is
  float64. The synthetic tile-equality tests still agree after float32 storage, which matches what
  the verify probe found on real data.

## 3. The first section (planner's limit 45 minutes; actual compute about 54 minutes in four starts)

| Part | Local time | Result |
|---|---|---|
| Mask (D111, D113), 22,528 × 26,624 cells | 18:32 to 18:39 | Built in 428 s. Cells by centre: US 48 states and DC 124,869,475; Canada 158,108,060; Alaska, Hawaii, PR, USVI 9,502,670; Mexico 18,755,374; Arctic 45,190,392. **Study cells: 241,229,862** (about 15.08 million km²). |
| Plot table | 18:39 | **Stopped: `UnknownGenus: genus 'Carya'`** (stop 1) |
| Soil, 2 tiles of 2048 cells, 2 workers | 18:40 to 18:48 | First try: NaN window bounds, because a northern tile reaches a gap of the interrupted Homolosine. Fixed (`e2a8ee0`); both tiles then done in 179 s and 274 s. These are tiny edge tiles (2,917 and 1,350 study cells), so the times are fetch time, not a full window. |
| Tree tile list | 18:48 to 18:57 | 4,788 tree tiles with study cells, 2,771 with Canadian cells (cached) |
| Trees, northernmost super-window | 18:58 | **Stopped: NaN SCANFI bounds** for super-window `1024_1_17`, at y above 4,352 km (stop 2) |
| Trees, the Manitoba super-window (`1024_-1_6`), the first large window | 19:05 to 19:21 and after | One layer, balsam fir, took **15 minutes** for a 256 km window (12.8 MB). The network ran at about 30 kB/s with the process idle on I/O. Stopped by hand at about 19:27; nothing from it is cited. |

Every start ran under `MemoryMax=5G MemorySwapMax=0`. Peak memory per start was 1.32 GB (mask),
0.30 GB (soil), 0.11 GB (trees) and 0.25 GB.

## 4. Stops

**Stop 1. 73 genera in TreeMap 2023 are in neither of T5's class lists.**
- `crown_cover.is_conifer` refuses an unknown genus, by design (T5).
- Size: 296,075 of 2,388,297 tree rows, and 190,829 of 1,710,284 live trees of 5 in and up (about
  11%). Examples: *Carya*, *Liquidambar*, *Fagus*, *Nyssa*, *Liriodendron*, *Taxodium*, palms, and
  "Tree" (unknown). The full list is in `2026-10-07-t6b-run/genus_classes.out.txt`.
- No US tree tile can run until this is ruled.
- **Proposed:** classify an unlisted genus by FIA's own species-code convention: SPCD under 300 is
  softwood (conifer), 300 and over is hardwood (broadleaf).
  - Checked here: the convention agrees with every genus T5 already lists.
  - It puts *Taxodium* (221, 222) with the conifers and the other 71 named genera with the
    broadleaf.
  - "Tree" mixes 299 and 998 (unknown dead conifer and hardwood), which carry no crown, with 999
    ("other or unknown live tree"), which would count as broadleaf.
- This changes T5's refusal rule, so it is the planner's or owner's call.

**Stop 2. Arctic coastal slivers stay in the study area.**
- 991,716 of the 241,229,862 study cells have their centre in no CEC ecoregion polygon
  (`eco_gap_count.out.txt`).
- **Every** study cell north of 70 N is one of them (173,114), which is why D111's mask misses them.
  The political and ecoregion coastlines differ (inferred from the counts; not looked at on a map).
- One super-window of them reaches past the Albers projection's valid range (NaN fetch bounds).
- The other about 818,600 sit along coasts from 20 N up.
- **Options:**
  - (a) A cell is in the study area only if its centre is in a non-Arctic ecoregion. This drops all
    991,716, about 0.4% of the area, including the coastal cells further south.
  - (b) As (a), but only north of 60 N.
  - (c) Keep them and skip any tile whose bounds are undefined.
- (a) is my recommendation: it is the plainest reading of D111, with one line per decision.

**Stop 3. The SCANFI windowed fetch is too slow to plan around.**
- The trial fetched 64 km windows at about 13 s per layer. Tonight a 256 km window took 15 minutes
  per layer, about 30 kB/s.
- At that rate a super-window takes about 2.75 hours, and the roughly 175 to 230 Canadian
  super-windows would take hundreds of hours.
- **Options:**
  - (a) One short probe of GDAL's HTTP settings (merging consecutive ranges, larger chunks) on one
    layer window, then re-time.
  - (b) Download each SCANFI layer whole, one at a time. They are 0.08 to 4.2 GB, 18.8 GB in all, and
    the drive has 17 GB free. Regrid it continent-wide as its own class, then delete it. This is a
    code change that keeps every rule, because the regrid is linear. The CEC server gave about
    9.7 MB/s for NALCMS; the Canadian server's whole-file speed is not measured.
  - (c) Smaller super-windows.
- The run cannot be timed until one of these is measured.

## 5. Time for a full run

| Layer | Estimate | Basis |
|---|---|---|
| Soil | **about 4 to 6 hours** | 110 tiles. Fetch is about 3 to 4.5 minutes per window with 2 at once (this section and the trial), plus the regrid at 37 µs per cell over about 241 million study cells across 2 workers (about 1.3 h). The full 512 km window was not timed here; only edge tiles ran. |
| Host trees, compute | **about 40 to 45 hours** with 2 workers | 4,788 tiles at about 1 ms per cell (the trial's two-source rate halved). Inferred; no production tree tile has run. |
| Host trees, SCANFI fetch | **not known** | Between a few hours (the trial's rate, or whole files) and hundreds (tonight's rate) |

## 6. Not done or not verified

- No host-tree tile has run.
- No tile-edge check on real data.
- No ten-cell check.
- No mosaic.
- The trial's rate for one-source tree tiles is inferred, not measured.
- The cause of the slow SCANFI fetch (the server, or GDAL's request pattern) is not known.
- The Manitoba super-window holds one finished layer file and no request record, so the next
  section fetches the whole super-window again.
- Coastline mismatch as the cause of stop 2 is inferred from the counts.
- Drive use: `forecast-data/t6b` is 3.7 GB, and 17 GB is free.

## 7. Appended 2026-10-07 03:20 UTC: the rulings on the three stops, and the changes made (no run)

Sections 1 to 6 above stand as written, with one correction below. The planner relayed the rulings
as Forager RECORD -615.

**Section 1's length.** The planner asked for one short section of no more than 45 minutes. Section 1
ran about 54 minutes of compute across four starts (18:32 to 19:04 local, then 19:05 to about 19:27).
It overran.

**Correction to stop 3's "about twenty times slower".** That figure compared time per layer across
windows of different sizes.
- Per pixel of window, the trial read about 0.61 million pixels a second (about 8 million pixels in
  13 s). The 256 km window read about 0.084 million a second (about 76 million in 900 s).
- That is about seven times slower, not twenty. The decision does not change.

**Rows filed:**
- **D116** (the owner): a genus outside T5's lists is classed by its FIA species code, under 300 as a
  conifer and 300 and over as broadleaf. It counts toward the conifer and broadleaf totals only,
  never as a host, and every such tree is counted.
- **D117** (the owner): a cell is in the study area only if it lies inside a non-Arctic ecoregion.
- **D118** (the planner): the SCANFI route.

**The probe** (D118, about 5.5 minutes, `2026-10-07-t6b-run/gdal_probe.out.txt`): the same 128 km
window of the ponderosa pine layer.

| GDAL settings | Rate |
|---|---|
| Default | 0.082 Mpx/s, 9 kB/s received |
| Tuned | 0.191 Mpx/s, 86 kB/s received |
| The trial, for comparison | about 0.61 Mpx/s |

The tuned rate is not near the trial's, so the whole-layer route is built. The server's bulk rate was
also measured, at 02:42 UTC: 77,515 bytes a second on a 50 MB range, with about 10 s to the first
byte.

**Changes, tests first** (each new test was seen red before its code):
- `crown_cover`: an optional FIA-code class (D116). T5's calls are unchanged, and T5's refusal still
  raises without a code.
- The mask's second band is now the ecoregion code: none, Arctic or other (D117). A coastal sliver in
  no polygon is out. The mask carries a version, and the runner moves a mask, plot table, tile lists,
  tiles and manifest of an older version aside (kept, under `superseded/`) before rebuilding. The two
  soil tiles of section 1 will be redone.
- SCANFI from whole layer files (D118): each layer is regridded over every Canadian tree tile and
  stored per tile as float32, and the tree tile sums the classes.
  - It matches the window route to float32 rounding, with flags exactly equal.
  - One tile against four tiles agrees bit for bit.
  - Downloads are resumable and stop at the section's stop time.
  - Free space is checked before each layer.
  - Each layer's request and sha256 are recorded.
  - The layer file is deleted once all its tiles are done.
- The trees stage now offers only tiles whose sources are ready. Windowed SCANFI reads, which are no
  longer used by the runner, keep the tuned settings.

**Revert runner:** 25 checks (`revert_results_2.json`).
- **23 bite**, each with a message specific to its edit.
- The same 2 labelled "may not bite" do not.
- Every run was citable and every file was restored equal to HEAD.

**Full suite under the cap:** 449 passed, 324 test functions (from 440 and 315), peak 534 MB. Ruff is
clean.

**What the whole-layer route costs** (inferred, not measured):
- **Downloads:** 18.8 GB. At tonight's 77 kB/s that is about 68 hours. At the CEC server's 9.7 MB/s
  it would be about 32 minutes. The SCANFI server's daytime rate is unknown.
- **Compute:** each Canadian tile now runs eleven single-layer regrids instead of two grouped ones,
  about 5.5 times the geometry work. On the trial's rate (about 0.47 ms per cell per regrid call)
  that is about 130 hours for the Canadian tiles with two workers, against about 25 on the window
  route. This is the main cost of the route that fits the disk. The window route needs all eleven
  layers at once, about 19 to 20 GB of native windows, which does not fit the 17 GB free.

**Next section, when the owner starts one:**
- mask rebuild (about 7 minutes);
- plot table (time unknown);
- tile lists (about 10 minutes);
- then the stages in the order mask, plots, scanfi-layers, trees, soil, or any subset with
  `--stages`.

No run section was started after section 1.

Correction, appended 2026-10-07 03:13 UTC: section 7's heading gives 03:20 UTC; it was written at 03:12 UTC by the clock (`date -u`). Nothing else changes.

## 8. Appended 2026-10-07 03:49 UTC: the order of work (Forager RECORD -620) and the SCANFI download job

The owner's order, as the planner relays it: "US and soil first (Recommended)". Night sections run
the stages mask, plots, soil, then trees. The trees stage offers only tiles whose sources are ready,
which until the SCANFI layers are regridded means the US-only tiles. SCANFI's layers download as a
separate job, download only. Canadian tree compute comes last.

**Changes, tests first.** The two new tests were red on import before `download_layers` existed.
- `t6b_sources.download_layers` and `scripts/t6b_fetch_scanfi_layers.py`, a download-only job:
  - one layer at a time;
  - a layer already on the drive with its request record is skipped, and a partial download resumes;
  - before each layer, free space must cover the rest of the layer plus a reserve, 8 GB by default,
    kept for the night sections' outputs; otherwise the job stops there;
  - each finished layer gets its request record and sha256 in `forecast-data/t6b/requests/`;
  - its paths are the ones the `scanfi-layers` stage reads, and that stage deletes each layer once
    regridded.
- `scripts/t6b_run.py` now defaults to `--stages mask,plots,soil,trees`.
- Revert runner: 27 checks, 25 bite. The same 2 labelled "may not bite" do not
  (`revert_results_3.json`).
- Full suite under the cap: 451 passed, 326 test functions, peak 534 MB.

**The job.** Started 2026-10-06 20:32 local (03:32 UTC) as the user service `t6b-scanfi-download`:
- memory cap 1 GB, no swap, nice 19, idle I/O class;
- log at `forecast-data/t6b/scanfi_download.log`, copied here as `2026-10-07-t6b-run/scanfi_download.log.txt`;
- `free -h` beforehand showed 7.6 GiB available.

| Layer | Bytes | Time | Rate |
|---|---|---|---|
| balsam fir | 1,161,699,718 | 378 s | 3,069 kB/s, complete |
| black spruce | 1,551,892,480 of 3,312,829,290 | 20:38:36 to 20:47:17 local | about 2.98 MB/s, still downloading |

At about 3 MB/s all eleven layers (18.8 GB) would take about 1 h 45 min. That is about forty times
the 77 kB/s measured at 02:42 UTC, so the server's rate varies widely. The rate was not measured in
daytime: this job started in the evening.

**It will stop at the reserve.** 17 GB was free at the start. With an 8 GB reserve the job is
expected to stop before "otherConiferous", after about 12.3 GB (balsam fir to lodgepole pine,
inferred from the layer sizes). The other four layers follow once the `scanfi-layers` stage has
regridded and deleted earlier ones. No compute section was started.

Correction, appended 2026-10-07 03:48 UTC: section 8's heading gives 03:49 UTC; it was written at 03:47 UTC by the clock. Nothing else changes.

## 9. Appended 2026-10-07 16:58 UTC: the network fix after night section 2 (Forager RECORD -641)

**What happened** (as the planner relays it; the log is on the drive at
`forecast-data/t6b/night-2026-10-07.log` and copied as `2026-10-07-t6b-run/night-2026-10-07.log.txt`):
- Night section 2 ran from 02:23 to 04:18 PDT, under the cap.
- The mask was rebuilt in 441 s. The plot table was built in 18 s: 13,364 trees capped, 0
  non-positive widths.
- 37 of 89 soil tiles finished, median 346 s with two workers.
- The laptop's Wi-Fi dropped at about 03:40. At 04:18 a soil worker raised `URLError: Temporary
  failure in name resolution`. It propagated through `fut.result()` and ended the whole section.

**The fix** (the planner's call; no rule change):
- **Retry:** a fetch's network error is retried after 30 s, 2, 5 and 15 minutes, never waiting
  past `--until`. Network errors are a URL error, a timeout, a dropped connection, an HTTP 5xx, or
  a GDAL read error naming curl, HTTP or a connection. An HTTP 4xx is not one.
- **Deferral:** a tile that still fails gets a manifest line with `"status": "deferred"` and its
  errors, and the section carries on. A deferred tile never counts as done, and the next section
  takes deferred tiles first.
- **Real bugs still stop the section:** any other exception stops it, as before.
- **Counts:** section summaries and the end-of-section commit give ok, deferred and remaining.
- The SCANFI download job retries and resumes the same way.

**Tests and checks:**
- Seven new tests were written before the code and were red on the missing arguments: a stub that
  fails twice and then succeeds; a 503 retried and a 404 not; a tile that keeps failing is deferred
  and the section continues; deferred tiles go first next time; a real bug still stops the section;
  no wait past the stop time; two workers.
- A test that a layer download retries and resumes was also written first.
- **One test came after the code:** that a GDAL read error counts only when it is a network one.
- Revert runner: 34 checks, 32 bite. The same 2 labelled "may not bite" do not
  (`revert_results_4.json`).
- Full suite under the cap: 460 passed, 335 test functions, peak 531 MB.

**State found on the drive:**
- 38 soil tile files but 37 manifest lines. The tile in flight when the section ended has a file
  and no line, so it will be redone.
- 41 soil native folders. Those without a request record are fetched again.

**Will tonight's outputs fit?** 6.1 GB is free.

| Output | Estimate | Basis |
|---|---|---|
| Soil, the remaining tiles | about 2.2 GB | measured per study cell on the 37 done: 10.3 B of output and 5.3 B of native windows, over about 140 million remaining cells (about 240 million study cells less the 99.8 million done) |
| US tree tiles | at most about 1.65 GB | the trial's 13.3 B per cell, measured in dense forest, so an upper figure, over about 124 million cells |
| **Total** | **about 3.9 GB** | leaves about 2 GB |

- **It fits.**
- The final mosaics, and the four SCANFI layers not yet downloaded, need room freed first: the
  scanfi-layers stage deletes each layer once it is regridded.
- The download job, if restarted with its 8 GB reserve, stops at once, as intended.

No section was started.
