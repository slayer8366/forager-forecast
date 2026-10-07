# T6b verify-first report: continental soil and host-tree layers

Answers the "Verify first" items of `docs/dispatch/2026-10-06-t6b-continental-layers.md` (Forager
RECORD -612). Written 2026-10-07 01:00 UTC (2026-10-06 local) by the T6b coder session (D38), branch
`t6b-continental-layers`, worktree `~/Zynergy/forager-forecast-t6b`. Base `origin/main` `36cc647`.
Evidence is in `2026-10-07-t6b-verify/`.

**Nothing has been built and no continental fetch or run has started.** One trial tile was fetched
and run, as the dispatch allows. There was no GBIF request, no climate pull, no fit, no secret, no
merge, and nothing in the Forager app repo. "Observed" means a command ran here and its output is
committed. "Read" means a file or page was opened in this session. "Inferred" and "from memory" are
marked where they appear.

## What landed

| Commit | What |
|---|---|
| `fb4ac19` | The ten cells per layer, fixed by rule before any value was read (item 6) |
| `cabf255` | Trial tile script, logs, hashes and summary; the three request records in `docs/pulls/`; the edge-origin probe; the source pages read |
| this commit | This report and its index row |

## The machine (observed before and during the trial)

- Flash drive mounted at `/run/media/zynergy-labs/2ebd084f-…/`, **21 GB free**. `forecast-data/t6b/`
  did not exist before this session. It now holds `trial/`, which is 16 MB.
- Internal disk: 3.4 GB free before and after. The worktree's `.venv` came from uv's cache by hard
  links, so `df` did not move.
- RAM 11 GiB. Every trial step ran under `systemd-run --user --scope -q -p MemoryMax=5G
  -p MemorySwapMax=0`, each in its own process, one at a time, with nothing else heavy running.

## 1. Base and cites

- **Base:** `origin/main` = `36cc647`, and the branch is that commit plus the dispatch (`24c2ff1`).
- **Confirmed:**
  - `MIN_VALID_FRACTION = 0.5` is at `src/forager_forecast/t4_layer.py:82` (D74).
  - SPEC's masks: "Mexico and the Arctic in phase 1 … stay masked" (`SPEC.md:28`) and Alaska
    (`:30`, D31, D86).
  - D80, D81, D84 to D92 and D100 say what the dispatch says they say (`DECISIONS.md`).
  - T4's run-time figures (126 s for 2,973,360 cells, about 4.5 hours continental) are in T4's
    completion report, section 4, item 4.
  - TreeMap on the drive: raster 5,258,231,492 bytes and zip 5,240,617,359 bytes. The zip's sha256
    `348264eb…abb7` equals the catalogue's (T5). My trial cut records the same hash.
  - The next free decision ID is D111. D110 is the newest row.
- **One correction.** The dispatch says "The T5 review flagged that SCANFI's ten classes summing to
  its total was shown on the border strip only." That flag is in the **T5 Amendment 3 review**
  (`2026-10-06-t5-amendment-3-review.md`, the last bullet of "Gaps", and "For the owner" item 3). The
  first T5 review (F3) said the sum had not been checked at all.
- **Not checked:** Forager RECORD -610, -612 and -587 (Forager records, not read here).

## 2. The study-area mask: **STOP for the owner (the Arctic line), and one stop for the planner (the side rule)**

### 2a. Country lines and their source

| Option | Licence as stated at source (read today) | Scale | Notes |
|---|---|---|---|
| **A. CEC North American Atlas, Political Boundaries 2021** (recommended) | Metadata, "Use limitations": "This material is licensed under CC BY 4.0, allowing non-exclusive rights to distribute, remix, adapt, and build upon the material in any medium or format, including for commercial purposes, so long as attribution is given to the creator." Its Terms of use.doc says CC BY 4.0 "If the author of this data is the CEC". | 1:10,000,000 | One dataset for all three countries, built from "political boundaries published by each country in 2021". States and provinces are separate polygons, so Alaska and Hawaii drop out cleanly. Same atlas and the same licence wording as the CEC ecoregions already in the register (`DATA_REGISTER.md`, CEC ecoregions row). The metadata warns: "boundary lines at the local level can be inaccurate in some locations". |
| B. Natural Earth 1:10m admin-0 and admin-1 | "All versions of Natural Earth raster + vector map data found on this website are in the public domain." | 1:10m | Cleanest licence. Same coarse scale. |
| C. US Census plus Statistics Canada files | **Not checked at source.** The two Census pages I opened state no licence in their text. | finer | Two national sources that would not meet exactly at the border. Blocked under D31 until a licence is read. |

The pages are quoted in `2026-10-07-t6b-verify/source_pages_read.txt`. No boundary file has been
downloaded. **A licence reading for the owner:** CEC credits Statistics Canada, the US Census Bureau and
INEGI as sources, while its metadata states CC BY 4.0 for the data itself. I read that as a licence
stated at source, the same reading already used for the ecoregions row. If the owner reads it
otherwise, option B has no such question.

- **Alaska line:** the Alaska state polygon from the same dataset.
- **Mexico line:** the Mexico country polygon (D47).
- **Not on record and proposed here, a reading for the owner:** Hawaii, Puerto Rico and the US
  Virgin Islands are also masked. They are not named anywhere, but TreeMap covers the conterminous
  US only, which is the same reason Alaska is masked (D31, D86). The study area would then be the 48
  states plus DC, and Canada south of the Arctic line.
- **A cell is in the study area** when its centre lies inside it, as T4's rectangle and T5's strip
  did. Both are tested by cell centre.

### 2b. The Arctic line: the owner's choice

Nothing on record defines it. Written for the owner:

> SPEC says the Arctic stays masked because no verified tree layer covers it. Canada's tree map
> (SCANFI) was trained on survey photos covering "all of Canada's non-arctic landmass", and it also
> fills some northern areas beyond that sampling, in northern Quebec and the northwest, which it
> flags as extrapolated. So "the Arctic" can be drawn in four ways:
>
> - **1. The treeline (Arctic ecozones). Recommended.** Mask the two northernmost natural regions on
>   the continental ecoregion map the project already uses: "Tundra" and "Arctic Cordillera". This
>   **includes** every forested area, including the northern boreal forest and taiga in the Yukon,
>   the Northwest Territories, northern Quebec and Labrador. It **excludes** the open tundra and the
>   Arctic islands, where there are no host trees. It uses a map already cleared in the data register
>   (CC BY 4.0), and the same regions are the units the forecast is published by, so no region is
>   half shown. It costs about a fifth more Canadian area than option 2, so a longer run (section 5).
> - **2. 60 degrees north,** the line along the territories' southern border. **Includes** all
>   provinces up to 60 N, which is most of the boreal forest. **Excludes** the Yukon, the Northwest
>   Territories and Nunavut entirely, including real forest along the Mackenzie and Yukon rivers, and
>   the top of Quebec and Labrador. It is the simplest line and the shortest run.
> - **3. Wherever Canada's tree map has a value.** **Includes** everything SCANFI maps, including
>   its extrapolated northern areas. **Excludes** whatever SCANFI leaves blank. Nobody knows exactly
>   where that line falls until SCANFI is read at low resolution once, which has not been done. It
>   follows the tree data most literally, but the extrapolated edges are the weakest part of that map.
> - **4. The Arctic Circle (66.6 N).** **Includes** wide open tundra south of the circle, such as
>   most of Nunavut's Kivalliq and northern Quebec. **Excludes** the forest of the Mackenzie delta
>   north of it. Not recommended: it follows neither the trees nor the data.
>
> **Why the line matters beyond the map:** T5's rule reads "no data" in the tree map as "no trees"
> (0% cover). Wherever the mask reaches past the area the tree map actually covers, those cells would
> show as treeless rather than blank. Option 1 keeps the mask inside the forest, and I will count and
> report any cells inside the mask where the tree map has nothing at all.

The CEC Level I region names "Tundra" and "Arctic Cordillera" are from memory and are checked
against the file before use. The register row records levels I to III and the licence, not the names.

### 2c. The side rule: which source a cell takes (a T5 rule; **stop for the planner**)

- T5 decides the side by the cell centre's latitude, 49 N or north is Canada
  (`t5_layer.py`, module docstring and `_cell_latitudes`). That is right only where the border is the
  49th parallel, from Lake of the Woods west to Boundary Bay. East of 95.15 W it would put southern
  Ontario and Quebec on the US side. Some new rule is therefore unavoidable.
- **Observed on the trial tile** (`trial_observe.log.txt`):
  - TreeMap has data up to 49.0013 N (4,545 of 3.4 million pixels north of 49 N).
  - SCANFI has data down to 48.9986 N (2,844 of 4.0 million pixels south of 49 N).
  - So each source stops at its own country's surveyed line, within about 150 m.
- **Options:**
  - **S1.** The chosen country polygon everywhere, by cell centre.
  - **S2, recommended.** T5's 49 N rule unchanged where the border is the parallel, and the polygon
    only east of Lake of the Woods (and around Point Roberts, which the parallel already gets right).
    Every cell T5 built keeps its side.
  - **S3.** SCANFI's own data footprint as "Canada" at 30 m. It is the most exact line, but whether
    SCANFI marks Canadian lakes as no data is not known.
- **Why it matters:** with a 1:10M polygon, a cell put on the wrong side reads the other source's "no
  data", which T5's rule turns into 0% cover. The worst places are the river and lake borders (St.
  Lawrence, St. Croix, the Great Lakes connecting rivers). The build would count the cells where the
  assigned source has no pixel at all and report them.

### 2d. A finding for the record: water reads as 0% tree cover

- Under T5's rule a no-data tree pixel is no crown, and every pixel on a cell's own side is valid.
- So lakes and coastal sea inside the mask carry total cover 0 with a valid fraction of 1, and every
  share empty (under 10%).
- On the trial tile, every in-box cell was "valid" for trees (33,324 US, 33,121 Canada), against
  65,838 of 66,445 for soil.
- So the host-tree layer's valid-cell count will exceed the land area by roughly the water area.
- I propose no change; a land and water mask would change T5's rule and is the owner's call. The
  report will give the count against land area, as the Verify asks, with this stated.

## 3. Extent and tiles

- **Lattice:** T4's master grid, unchanged.
- **Tiles:** tiles of N × N cells anchored at the lattice origin. Tile (i, j) covers
  `col ∈ [N·i, N·i + N)` and `row ∈ [N·j, N·j + N)`, so a tile's cells never depend on the mask or the
  extent. Only tiles that touch the mask are run.
- **Extent:** the master window is the bounding box of the mask snapped to the lattice. Approximate
  boxes from known extreme points (observed by projection; the true box comes from the polygon):
  - 48 states: 17,446 × 11,934 cells, x −2,234,250 to 2,127,250 m, y −1,691,750 to 1,291,750 m.
  - Plus Canada to 60 N: 21,246 × 18,232 cells (387 million), top y 2,866,250 m.
  - Plus Canada to about 69.5 N (the treeline option reaches the Mackenzie delta): 21,246 × 21,626
    cells (459 million), top y about 3,714,750 m.
  - All of these sit inside the cell-id range of ±8,192 km.

### The trial tile (observed)

- **Where:** 48.71 to 49.29 N, 114.94 to 114.06 W (Glacier and Waterton, mountain forest), across
  49 N, so all three sources were read. It holds none of the ten cells (rule committed first).
- **How it ran:** through T4's and T5's own entry points (`fetch_natives`, `build_master`,
  `cut_treemap`, `fetch_scanfi`, `build_master`), each step in its own capped process.
- **Size:** master window 293 × 316 = 92,588 cells.

| Step | Wall time | Peak memory (max RSS) |
|---|---|---|
| SoilGrids fetch, 9 windows of 363 × 334 native pixels | 280.3 s (about 31 s per layer) | 158 MB |
| Soil build (regrid 3.46 s, which is 37 µs per cell) | 3.7 s | 145 MB |
| TreeMap cut, including streaming the tree table and plot covers at three scales | 12.3 s | 442 MB |
| SCANFI fetch, 11 windows of 2,794 × 2,851 pixels | 141.4 s (about 13 s per layer) | 139 MB |
| Host-tree build, both sources over the whole window | 173.8 s (1.88 ms per cell) | **1.93 GB** |

Host-tree memory is about **21 kB per master cell**: 1.93 GB / 92,588 here, and 4.995 GB / 233,700 on
T5's strip (T5 completion report, section 9). It is linear in area, and native float64 arrays
dominate it. Soil memory is small: T4 used 862 MB for 2.97 million cells.

### Proposed tile sizes

- **Host trees: 256 × 256 cells (64 km).** Estimated peak about 1.4 GB with both sources (inferred,
  linear), well under the 5 GB cap. 512 × 512 would be about 5.5 GB with both sources, which does not
  fit.
- **Soil: 2048 × 2048 cells (512 km).** Estimated peak about 1.2 GB, scaled from T4's 862 MB (inferred).
  Soil fetch time is per window, not per area: T4's window of 2.97 million cells took about 3.3 minutes
  for nine layers, and the trial's 92,588 took 4.7 minutes. So soil wants few, large windows.

### Overlap

- **No master-cell overlap is needed.** The exact regrid is local to a cell: its value depends only on
  its own corner quad and the native pixels it touches (`regrid.py`).
- What must overlap is each tile's **native read window**. It has to hold every native pixel any of the
  tile's cells touches. The existing margins are 2 native pixels (500 m) for SoilGrids
  (`soilgrids.native_bounds_for`) and 300 m (10 pixels) for TreeMap and SCANFI
  (`t5_layer.native_bounds`). The regrid raises if a cell reaches past its window, so too small a
  margin fails loudly rather than leaving a silent gap.
- **That alone does not give "exactly".** Observed in `edge_origin_probe.out.txt`: the same 4,096
  cells regridded from the same pixels, but with the native subset starting 1 to 11 pixels over, differ
  in up to 777 of 12,288 values, by at most 4.4e-15.
  - The cause is the arithmetic in subset-relative pixel coordinates (`regrid.py`,
    `u = (nx - a.c) / a.a`).
  - In this probe they agreed after float32 storage, but nothing guarantees that at a rounding edge.
  - **So the build computes native pixel positions against each source's full-raster origin.** That
    makes a cell's arithmetic the same in any tile. The tile-edge test checks it bit for bit, on
    synthetic data first, then on real data.
  - This is an implementation change, not a rule change.

## 4. Sources and sizes

**SoilGrids (3 depths × 3 statistics):**
- Windowed reads per soil tile, as T4 did.
- Native subsets are about 4 bytes per master cell (T4: 12 MB for 2.97 million cells; trial: 0.52 MB
  for 92,588). That is about 1.5 GB for the continent. **I propose keeping them**, as T4 did, so a
  rebuild needs no refetch.
- The nine VRTs carry the same ETag and Last-Modified (2 June 2020) as T4's checksum-verified VRTs
  (observed). ISRIC publishes checksums for VRTs only, not for the pixel tiles (T4). The build
  re-downloads the checksum file and the VRTs once and checks them, as T4 did.

**TreeMap 2023:**
- Already on the drive (5.26 GB raster plus the zip), and cut locally.
- The current code streams the whole tree table on every cut. That costs 12 s per tile, which is
  about 7.7 hours over the US.
- The build would compute plot covers once for every plot and keep that one table. The formula and
  rules are unchanged (D87 to D91).

**SCANFI v2 2025:**
- The eleven whole-Canada files total **18.78 GB** (Content-Length, observed). The total layer alone
  is 4.20 GB.
- Whole files will not fit beside the outputs in 21 GB, so the reads are windowed.
- Native subsets are about 140 bytes per master cell (13 MB per trial window), which is too much to
  keep continent-wide (about 14 to 17 GB). **They are discarded after each window,** with each
  window's sha256, ETag and pixel window kept in its request record.
- The natives of the tiles holding the ten cells and the tile-edge check band are kept.
- No publisher checksum for SCANFI was found (none in T5's records, and none in the readme or the
  catalogue record). The ETags and Last-Modified (4 February 2026) equal T5's for all eleven layers
  (observed).

**Requests:**
- The trial's three request records are in `docs/pulls/t6b-trial-*.request.json`, byte-identical to
  the drive's copies.
- In the run, every window's record goes into a per-source request log on the drive, and a copy goes
  under `docs/pulls/`.

**Outputs:**
- Measured on the trial: soil master 7.8 bytes per cell, host trees 13.3 bytes per cell (dense forest,
  so an upper-side figure).
- Over the processed cells (about 250 to 290 million), that is about 2 to 2.3 GB for soil and 3.3 to
  3.8 GB for host trees.
- Per-tile files are mosaicked into one raster per layer. Peak disk is about twice that, 11 to 12 GB,
  plus transient natives. Then the per-tile files are deleted after the mosaic's hash and a cell-by-cell
  comparison.
- **That fits in 21 GB with about 8 GB to spare.** Nothing large goes on the internal disk.

## 5. Run time, extrapolated from the trial (single process, per layer)

**Assumptions:**
- Land areas are from memory, unverified: the 48 states about 7.66 million km²; Canada to 60 N about
  5.2 million km²; Canada outside the Arctic ecozones about 6.4 million km².
- Whole tiles add about 20% over land (inferred).
- One-source tiles regrid at half the two-source rate (inferred, not measured).

| Layer | Mask option | Work | Estimate |
|---|---|---|---|
| Soil | 60 N | at most 99 windows × (4.7 min fetch + 2.6 min regrid) | **8 to 12 h** (T4 extrapolated 4.5 h for the regrid alone; the regrid share here is about 2.6 h, and per-window fetch is the rest) |
| Soil | treeline | at most 121 windows | **10 to 15 h** |
| Host trees, US | any | about 147 million cells, 2,245 tiles × (0.94 ms per cell + 12 s cut) | **about 46 h** |
| Host trees, Canada | 60 N | about 100 million cells, 1,523 tiles × (0.94 ms per cell + 141 s fetch) | **about 86 h** |
| Host trees, Canada | treeline | about 123 million cells, 1,875 tiles | **about 105 h** |

**Total with the code as it stands:** about 5.5 days for 60 N and 6.3 days for the treeline, plus
soil. That is far beyond T4's 4.5 hours, which covered soil only. The time goes to per-window fetch
overhead and to the 30 m regrid.

Changes that keep every rule but cut the time (not measured; **the planner's call**, since they bear
on "one heavy job"):
1. **SCANFI super-windows:** fetch one window per 4 × 4 tiles and run its 16 tiles from the drive. If
   fetch cost is mostly per request, as the trial suggests (13 s per layer whatever the window), that
   cuts Canadian fetch from about 60 to 73 hours to a few hours.
2. **Two worker processes inside the one 5 GB scope** (about 1.4 GB each). That halves compute: about
   19 h for the US and 13 to 16 h for Canada.
3. Plot covers computed once (section 4); scale 1.0 only.

**With 1 to 3:** host trees take about 1.5 to 2 days, and soil 8 to 15 hours. **The first
super-window of the run would be timed and reported before the rest continues.**

**Surrogate scales:** T5 built 0.7, 1.0 and 1.3 as a seam sensitivity test. I propose that T6b builds
1.0 only. That does not change a rule, but the planner should confirm.

## 6. The ten cells per layer

- Fixed and committed at `fb4ac19` before any value was read (`2026-10-07-t6b-verify/ten-cell-rule.md`
  and `ten_cells.json`).
- **The cells:**
  - coast (Oregon Coast Range);
  - mountains (Colorado Rockies);
  - prairie, both sides (Kansas, Saskatchewan);
  - boreal (Manitoba, 55 N, south of every Arctic option);
  - both sides of 49 N (Selkirks, 117.2 W);
  - the Appalachians;
  - masked (Chihuahua, Mexico, masked under every option);
  - no data (mid Lake Michigan, US water).
- **Soil:** T4's method and T4's 0.01 pH.
- **Host trees:** "T4's tolerance carried to these units", one tenth of each source's own step, which
  is my reading:
  - cover 0.1 points;
  - shares 0.001;
  - valid fraction 0.001;
  - flags exact.
  - Checked by an independent exact area recompute, because a point sampler cannot reach 0.001 on
    30 m pixels.
- No "at threshold" exemption (T4 review finding 4).

## Stops and decisions wanted

**For the owner:**
1. The **Arctic line** (section 2b). I recommend option 1, the treeline (CEC Tundra and Arctic
   Cordillera).
2. **Hawaii and the territories** masked with Alaska. I recommend yes.
3. The **boundary dataset**: CEC Political Boundaries 2021 (CC BY 4.0 in its metadata) or Natural
   Earth (public domain). I recommend CEC.

**For the planner:**
4. The **side rule** (section 2c), which changes T5's 49 N rule outside the stretch T5 ran on. I
   recommend S2.
5. The **speed-ups** and the run-time budget (section 5).
6. **Surrogate scale 1.0 only.**
7. The **host-tree tolerances** in the ten-cell rule.

**No stop on memory, disk or licence otherwise:**
- A 256-cell tree tile and a 2048-cell soil tile both fit well under the cap.
- The disk fits on the drive.
- Every source is already registered.

Decision rows will start at D111 once these are ruled.

## Not checked

- SCANFI's actual northern data limit. It needs one low-resolution read of SCANFI, which was not made.
- Whether SCANFI marks Canadian lakes as no data.
- The CEC Level I names, read from the file.
- The land areas behind section 5 (from memory).
- The one-source regrid rate (inferred as half).
- How SCANFI fetch time scales with window area.
- Forager RECORDs -587, -610 and -612.
- No boundary file was downloaded.
