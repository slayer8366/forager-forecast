# T4 completion report: the master grid and SoilGrids pH to a zoom-9 PMTiles archive

Answers `docs/dispatch/2026-10-06-t4-master-grid.md`. Written 2026-10-06 (UTC) by the coder session on
the credentials machine (D38), branch `t4-master-grid`, worktree `~/Zynergy/forager-forecast-t4`, base
`origin/main` `ad64fef` (unmoved at every fetch this session). Unmerged; review under D18 is next,
then the owner's authorisation under D40. No secret appears here. Nothing in `records/` and nothing in
the Forager repository was touched. No GBIF, Climate Data Store or Open-Meteo request; one SoilGrids
fetch, after the planner relayed "D26 download finished".

"Observed" means a command ran and its output is quoted or committed. "Inferred" is marked.

## 1. What landed

| Commit | What |
|---|---|
| `177a41c` | Verify-first report (`2026-10-06-t4-verify-report.md`), three stops, proposals, synthetic MBTiles/PMTiles probe |
| `81c6cd8` | D80 (depth), D81 (range, approximate, where the bands live), D82 (area), the owner's answers relayed by the planner (Forager RECORD -582); IDs assigned by the planner, D73 to D79 reserved for D26 |
| `7a1eea2` | `grid.py` (master grid, cell id), `regrid.py` (exact area-weighted regrid), their tests; `pmtiles==3.8.1` pinned |
| `a01d6c2` | `soilgrids.py`, `tiles.py`, `t4_layer.py`, `scripts/t4_build.py`, `scripts/t4_ten_cells.py`, tests; GDAL probes and synthetic-run evidence |
| `e7636f8` | Revert runner and its results (18 checks) |
| `5ee5737` | VRT files checked against ISRIC's published sha256 before the windowed reads |
| `b75faf1` | Native files refused unless in SoilGrids' Homolosine |
| this commit | Real-data evidence, the request copy in `docs/pulls/`, this report, index row, TASKS.md, START_HERE.md |

## 2. Verify items

All answered in `2026-10-06-t4-verify-report.md` (cites confirmed with file and line, base unmoved,
tooling, sizes). The three stops were ruled as D80 to D82. The planner accepted the grid, the access
route, the resampling, the request copy and the pmtiles pin. One accepted proposal changed during the
build (section 4).

## 3. The grid definition (`src/forager_forecast/grid.py`)

- CRS ESRI:102008, 250 m cells, lattice on the projection's false origin (0, 0) (lon -96, lat 40).
- `col = floor(x / 250)`, `row = floor(y / 250)`, row increasing north; a point on an edge goes east
  or north, as D63 does for weather cells.
- Cell id: `((row + 32768) << 16) | (col + 32768)`, unsigned 32-bit, valid for |x|, |y| under
  8,192 km; outside it the code raises. Example, tested: Seattle (47.6062 N, 122.3321 W) is
  col -7373, row 4624, id 2,450,547,507.
- A raster on the grid has bounds snapped outward to the lattice and rows north to south;
  `GridWindow` converts between raster pixels and cells.
- Datum: longitude and latitude are read as NAD83 (EPSG:4269), a null shift, the same as PROJ's
  "NAD83 to WGS 84 (1)". SoilGrids' Homolosine is read the same way (`soilgrids.grid_to_homolosine`).
  **Coverage gap:** reverting this pin to EPSG:4326 makes no test fail (revert check 4), because
  offline PROJ 9.8.1 picks the null operation either way. The pin guards against a different PROJ
  setup (network grids on, another PROJ version) choosing another operation; no test here can show
  that, so the pin is untested. A test would need PROJ with network grids enabled, which this
  repository does not use.

## 4. What changed from the accepted plan, and why

**GDAL's `average` warp was replaced by an exact area-weighted regrid** (`src/forager_forecast/regrid.py`).
The proposal assumed GDAL's average is the area-weighted mean. Measured before relying on it, on
synthetic noise in the real geometry (Homolosine 250 m to ESRI:102008 250 m over western Washington):
GDAL's average differed from exact polygon area weights by **up to 0.50 pH, mean 0.09** (300 cells);
on a pure shift it agreed to 1e-6. A master cell lands in Homolosine as a quad about 285 m by 219 m,
rotated about 13 degrees, and GDAL approximates its footprint. GDAL's bilinear differed from exact
centre interpolation by up to 0.97, and its nearest put 2.5% of cells on a neighbouring pixel. The
probes and their output are in `2026-10-06-t4-verify/gdal_*_probe.py.txt` and `gdal_probes.out.txt`.
The planner accepted exact weights on 2026-10-06 with four conditions, all met:

1. Known-answer tests (`tests/test_regrid.py`). A uniform field comes back equal to float precision
   (rtol 1e-14). A cell split 100 m / 150 m gives 6.4 and 5.6. A cell partly over no data uses valid
   pixels only, with valid fractions 0.4 and 0.6. The pure shift agrees with GDAL's average to 1e-6.
2. **The valid-area fraction is recorded per cell and per statistic** as master-grid bands 4 to 6.
   A cell under `MIN_VALID_FRACTION = 0.5` is no data. The 0.5 is the builder's choice; the
   fractions are kept so a later layer can choose differently without a refetch. On the real data,
   43,706 cells inside the rectangle had some valid soil but under half and were set to no data.
3. No geometry dependency: the polygon clipping is numpy. The one new dependency is `pmtiles==3.8.1`
   (Protomaps, BSD-3-Clause, pure Python), which converts the MBTiles GDAL writes into PMTiles.
4. Run time, test area: 2,973,360 cells, regrid **126 s** on real data (120 s synthetic), build
   2 min 10 s wall, 862 MB peak memory, one core. Continental would be roughly 130 times the area,
   about 4.5 hours single-threaded, and the native array would have to be tiled to fit in memory
   (inferred, not measured).

The Mercator step is also not GDAL's warper: each zoom-9 pixel takes the master cell under its centre,
computed with pyproj (`tiles.master_to_mercator_nearest`), for the same 2.5% reason. Overview zooms 5
to 8 are GDAL `average`, display only, and nothing is checked against them.

## 5. The data and the archive

- **Fetch** (observed, 2026-10-06 08:16 UTC): ISRIC's `checksum.sha256.txt` downloaded, then each of
  the nine VRTs (0-5, 5-15, 15-30 cm by mean, Q0.05, Q0.95) downloaded and compared with it: 9 of 9
  match. ISRIC publishes checksums for the VRT and OVR files only. **The GeoTIFF tiles the windows are
  read from have no published checksum**, so the pixel data itself is not checked against the
  publisher. What is recorded instead: each VRT's ETag and Last-Modified (all 2020-06-02), the pixel
  window (1,995 by 2,059 native pixels, col 27004, row 11446), and the sha256 of every stored subset.
  All nine share one native grid (checked by the build). No-data value -32768 (read from the source).
  The request is `data/t4/native/request.json`, copied byte-identical to
  `docs/pulls/soilgrids-phh2o-western-washington-0-30cm.request.json`; account "anonymous".
  The native CRS in the files is "Interrupted_Goode_Homolosine" on WGS84; it gives the same
  coordinates as `+proj=igh +datum=WGS84` to the millimetre (observed), and the build now refuses a
  file where it does not.
- **Master grid** `data/t4/master.tif`, sha256 `9fe55bc2…72f`: 6 Float32 bands (mean, Q0.05
  approximate, Q0.95 approximate, three valid fractions), window -2,099,250 to -1,709,250 by 890,750
  to 1,367,250 m. Of 1,884,904 cells whose centre is in the D82 rectangle, 1,301,966 carry a value.
  Mean pH 3.79 to 6.98, median 5.27. Q0.05 ≤ mean ≤ Q0.95 holds in every valid cell (observed).
  The approximate label is in the band names and band tags (D81).
- **Archive** `data/t4/archive/soil-ph-0-30cm.pmtiles`:
  - sha256 `84905e335c0390b2b7c32348ace86fc25fa372101b53530ea9af6c4d1ea0ee34`
  - 891,388 bytes
  - **min zoom 5, max zoom 9**, PNG, 78 tiles
  - header and metadata in `2026-10-06-t4-build/archive_header_real.txt`

  Each pixel is a grey byte equal to `floor(pH × 10 + 0.5)`, with alpha 0 for no data. The metadata
  carries:
  - the encoding
  - ISRIC's attribution verbatim
  - the grid
  - the extent
  - the valid-fraction threshold
  - the statement that Q0.05 and Q0.95 are approximate and live on the master grid only, not in the
    archive (D81)

  The archive's bounds (127.3 to 119.5 W, 44.6 to 49.8 N) are wider than the rectangle because the
  master window is a box in Albers. Cells outside the rectangle are transparent.
  No forbidden term, no "chance", no percent in the metadata (D58, R8; 0 hits, observed).
- **Disk:** `data/t4` is 58 MB: 31 MB VRTs, 12 MB native subsets, 15 MB master grid, 1.8 MB
  archive plus its intermediate MBTiles. Free space read 4.5 GB before (from the planner) and 4.2 GB
  after; another session runs on this machine, so that difference is not all T4's.

## 6. The ten-cell check

Script `scripts/t4_ten_cells.py`, which imports nothing from `forager_forecast`. The cells were fixed
in the verify report before any value was seen:

- eight at the centres of a 4 × 2 lattice over the rectangle
- Kalaloch (coast)
- Paradise, Mount Rainier (high)

For each cell the script:
- samples it at 40 × 40 points
- takes each point to Homolosine with pyproj
- looks the point up in the stored native pixels
- recomputes the 0 to 30 cm blend itself

It then compares that with the master grid. Separately, it decodes the zoom-9 archive pixel containing
the cell centre and compares it with the master cell under that pixel's own centre.

**Tolerance, sized for the blended value:**
- Master vs source: 0.01 pH. On worst-case noise data the sampler differed from the exact regrid by
  at most 0.0031 pH over 2,000 cells (p99 0.0019; `2026-10-06-t4-build/synthetic_full_extent.out.txt`).
  The tolerance sits about three times above that and well below the source's own 0.1 pH step.
- Archive vs master: exact, after the byte encoding.

Negative controls on synthetic outputs (`ten_cell_controls.out.txt`):
- ±0.02 pH fails on the edited cell and statistic only.
- +0.009 passes.
- A stale archive fails on the archive check.

**Result on real data: 10 of 10 pass** (`2026-10-06-t4-build/ten_cells_real.json`).

| Cell | col, row | Mean: source → master (pH) | Q0.05 | Q0.95 | Valid fraction | Archive grey vs expected |
|---|---|---|---|---|---|---|
| lattice 1 (48.125 N, 124.5 W) | -7890, 5033 | 4.9769 → 4.9769 | 3.8841 → 3.8840 | 6.2553 → 6.2558 | 1.000 | 50 = 50 |
| lattice 2 (48.125, 123.5) | -7621, 4951 | 5.7779 → 5.7780 | 4.2735 → 4.2735 | 7.7625 → 7.7625 | 0.742 | 58 = 58 |
| lattice 3 (48.125, 122.5) | -7351, 4872 | no data → no data | no data | no data | 0.000 | transparent = transparent |
| lattice 4 (48.125, 121.5) | -7081, 4796 | 4.9514 → 4.9513 | 3.9793 → 3.9792 | 6.3912 → 6.3912 | 1.000 | 50 = 50 |
| lattice 5 (46.375, 124.5) | -8134, 4244 | no data → no data | no data | no data | 0.000 | transparent = transparent |
| lattice 6 (46.375, 123.5) | -7857, 4160 | 4.9416 → 4.9417 | 3.8692 → 3.8692 | 5.7923 → 5.7923 | 1.000 | 50 = 50 |
| lattice 7 (46.375, 122.5) | -7579, 4078 | 5.2615 → 5.2616 | 4.5668 → 4.5668 | 5.9239 → 5.9239 | 1.000 | 53 = 53 |
| lattice 8 (46.375, 121.5) | -7300, 4000 | 5.3473 → 5.3473 | 4.2826 → 4.2826 | 6.2879 → 6.2879 | 1.000 | 54 = 54 |
| coastal: Kalaloch | -7928, 4787 | 4.7756 → 4.7759 | 3.5722 → 3.5722 | 6.3429 → 6.3436 | 0.916 / 0.915 | transparent = transparent (pixel centre in neighbour -7929, no data) |
| high: Paradise | -7314, 4205 | 5.0247 → 5.0247 | 4.1119 → 4.1118 | 6.0582 → 6.0582 | 1.000 | 50 = 50 |

Largest master-vs-source difference: 0.00062 pH (Kalaloch, Q0.95).

Notes on the table:
- **Lattice 5 lies in the Pacific off the Long Beach peninsula** (inferred from its coordinates).
- **Lattice 3 is no data in the source for a reason not determined here.** It may be water in Puget
  Sound or masked land; it was not looked up.
- **Kalaloch shows how the archive differs from the grid:** its own cell has a value, but the zoom-9
  pixel containing that point is centred in the cell to the west, which is ocean. So the map shows no
  value there. This is what nearest at a coarser display resolution does along a coast.
- Paradise (about 1,650 m) carries a value, so the glacier mask did not reach that cell.

## 7. Tests and revert checks

- Suite: before 213 collected from 117 test functions; after **266 collected from 162 test functions**
  (`git grep -c '^def test_' -- tests`, summed), all passing. `ruff check` and `ruff format --check`
  clean. (A message to the planner earlier today gave "136"; that count missed three test files not
  yet committed. 162 is the committed tree.)
- Tests reach the behaviour through the real entry points: `fetch_natives`, `build_master`,
  `build_archive`, as `scripts/t4_build.py` calls them, on synthetic Homolosine GeoTIFFs written by
  the tests.
- **Revert checks: 20.** 18 run by `2026-10-06-t4-build/revert.py.txt`, results in
  `revert_results.json`, plus 2 by hand for the last two guards (commit message of `b75faf1`).
  - Each one applies a single edit, runs the named test files, restores from a copy saved before
    editing, and confirms the file is byte-identical to the copy and to HEAD.
  - The runner refuses a run with collection or import errors, or one where the interpreter did not
    load the edited source.
  - **19 fail with failures specific to their edit.** Examples: rounding instead of floor in
    `cell_at` fails the known-point and edge tests; dropping the valid-fraction threshold fails only
    the sliver test; a zoom-10 pixel size fails the zoom tests with `assert 10 == 9`.
  - **One does not fail: the datum pin** (section 3), reported as a coverage gap.
- A stale run was caught. The runner's first pass made two same-sized edits within one second, Python
  ran cached bytecode, and the coverage-error revert reported the previous edit's three failures. It
  was caught because those failures named tests that edit could not break. Run by hand, the same
  revert fails only `test_a_master_cell_beyond_the_native_raster_is_an_error_not_a_silent_gap`. The
  runner now clears `__pycache__`, disables bytecode writing and confirms the edit is loaded. Only
  the corrected run is cited.

## 8. Not verified

- **The datum pin** (section 3): no test fails when it is reverted.
- **The pixel data against the publisher:** ISRIC gives checksums for VRTs only, not for the tiles.
- **pmtiles.io in a browser:** not opened, since this session has no browser. The archive's header was
  read with the pinned `pmtiles` reader, which is the same header the viewer reads (inferred). The Go
  `pmtiles show` CLI is not installed.
- **Why lattice 3 is no data.**
- **Overview zooms 5 to 8:** not checked against anything.
- **The continental run-time and memory figure:** extrapolated, not measured.
- **The 0.5 valid-fraction threshold:** the builder's choice, and no row rules on it.
- **Whether thickness-weighted 0 to 30 cm pH is the right habitat covariate:** that is D80's
  question, not this build's.

## 9. For the review and the owner

- The branch is ready for the D18 review.
- Open for the owner: the 0.5 valid-fraction threshold (section 4, item 2); the untested datum pin
  (section 3); the continental run time (section 4, item 4).
