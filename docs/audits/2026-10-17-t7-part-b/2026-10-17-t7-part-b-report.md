# T7 part B: the 250 m distance-to-road-and-trail layer for the PNW box

Written 2026-10-17 (UTC) by Hazel Cairnwright, the coder, under `docs/dispatch/2026-10-17-t7-part-b.md`
(branch t7-strengthen-plan; Forager RECORD -1163, the go and the owner's rulings in -1168), on branch
`t7-part-b` from `origin/t7-part-a` at b85bbc66. Each claim is marked **read** (seen in a file or at
source, with where), **run** (produced by a command whose output is filed here), or **inferred**.

## What was built

- `/mnt/work/Zynergy/forecast-data/access/pnw-2026-10-17/access_pnw.tif` (read-only): three float32
  bands on the T7 grid (ESRI:102008, 250 m, the window of `pnw.pnw_window()`): `dist_road_m`,
  `dist_trail_m`, `dist_any_m`, in metres on the grid plane. sha256
  7748fe0b5018a823ef0e41c64b0a8a0f3675951026461c8a39a0f5aa9682d38a (run, `manifest.json`).
- `trails_unpublished_pnw.tif` (read-only): uint8, 1 in the Umatilla and Wallowa-Whitman national
  forests by cell centre, where the trail and combined bands are NaN (the owner's ruling 1).
- `manifest.json`: every input's URL, size, sha256 and check; the rules; the intermediates' sha256s;
  the code commit that ran (5d4c94f, clean); 3,046 s; 0 cells without a line within 2,000 km in
  either band (run). Copied here with `prepare.json` (counts kept and dropped per source),
  `spot_check.json`, `coverage_by_block.json`, the fetch records (`fetch/`) and the build log.
- Definition and sources: D148 to D150 in `docs/planning/DECISIONS.md`; sources in DATA_REGISTER.md.
- Wiring: `t7/predictors.read_tile(..., access_path=, access_bands=)`; `ACCESS_MAIN_BANDS =
  ("dist_road_m",)`, `ACCESS_SIDE_BANDS = ("dist_trail_m", "dist_any_m")`; off by default and held
  apart from `FEATURES`, so a run that does not ask reads exactly what it read before (tested). No
  fit was run.
- Attribution: `pnw.SOURCES["access"]`, the same text as the layer's `attribution` tag (run: equal).

## Coverage by level III block

Over T7's table cells (eligible under P4, codes 1 and 2; 6,967,248 cells, read from
`/mnt/work/Zynergy/forecast-data/t7/fit/table.npz`). Every one has a road value; 6,749,073
have a trail value; 218,175 are in the two forests whose trails are unpublished
(run, `coverage_by_block.json`). Distances in metres, grid plane.

| Level III block | Cells | With road value | With trail value | Trails unpublished | Road median | Road p90 | Trail median |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10.1.2 Columbia Plateau | 51,199 | 51,199 | 51,024 | 175 | 272 | 880 | 12,334 |
| 10.1.3 Northern Basin and Range | 165,860 | 165,860 | 165,860 | 0 | 613 | 1,989 | 5,206 |
| 10.1.4 Wyoming Basin | 4,235 | 4,235 | 4,235 | 0 | 305 | 913 | 11,055 |
| 10.1.5 Central Basin and Range | 98,474 | 98,474 | 98,474 | 0 | 870 | 2,523 | 28,451 |
| 10.1.6 Colorado Plateaus | 438 | 438 | 438 | 0 | 293 | 745 | 4,796 |
| 10.1.8 Snake River Plain | 12,087 | 12,087 | 12,087 | 0 | 275 | 938 | 5,946 |
| 11.1.1 Central California Foothills and Coastal Mountains | 41,646 | 41,646 | 41,646 | 0 | 359 | 1,311 | 9,919 |
| 11.1.2 Central California Valley | 387 | 387 | 387 | 0 | 251 | 674 | 4,787 |
| 6.2.10 Middle Rockies | 641,227 | 641,227 | 641,227 | 0 | 562 | 2,938 | 1,450 |
| 6.2.11 Klamath Mountains | 555,392 | 555,392 | 555,392 | 0 | 309 | 2,183 | 3,016 |
| 6.2.12 Sierra Nevada | 24,836 | 24,836 | 24,836 | 0 | 207 | 783 | 1,782 |
| 6.2.13 Wasatch and Uinta Mountains | 150,917 | 150,917 | 150,917 | 0 | 472 | 1,590 | 1,382 |
| 6.2.15 Idaho Batholith | 623,264 | 623,264 | 623,264 | 0 | 1,117 | 9,785 | 948 |
| 6.2.3 Columbia Mountains/Northern Rockies | 1,066,705 | 1,066,705 | 1,066,705 | 0 | 234 | 1,259 | 2,762 |
| 6.2.4 Canadian Rockies | 229,458 | 229,458 | 229,458 | 0 | 2,104 | 15,022 | 994 |
| 6.2.5 North Cascades | 391,684 | 391,684 | 391,684 | 0 | 1,026 | 9,545 | 1,359 |
| 6.2.7 Cascades | 831,218 | 831,218 | 831,218 | 0 | 209 | 1,564 | 2,016 |
| 6.2.8 Eastern Cascades Slopes and Foothills | 491,038 | 491,038 | 491,038 | 0 | 157 | 643 | 5,222 |
| 6.2.9 Blue Mountains | 614,578 | 614,578 | 396,578 | 218,000 | 212 | 1,430 | 4,310 |
| 7.1.7 Strait of Georgia/Puget Lowland | 165,945 | 165,945 | 165,945 | 0 | 160 | 617 | 18,895 |
| 7.1.8 Coastal Range | 693,248 | 693,248 | 693,248 | 0 | 223 | 978 | 10,486 |
| 7.1.9 Willamette Valley | 94,209 | 94,209 | 94,209 | 0 | 198 | 600 | 10,360 |
| 9.3.1 Northwestern Glaciated Plains | 8,056 | 8,056 | 8,056 | 0 | 488 | 1,697 | 9,230 |
| 9.3.3 Northwestern Great Plains | 11,147 | 11,147 | 11,147 | 0 | 480 | 1,735 | 5,969 |

The planner's outcome prediction ("forest interiors are far from roads, and lowland cells are
near") holds in this table: the Canadian Rockies (Glacier and the Bob Marshall), the Idaho Batholith
and the North Cascades have road p90s of 9.5 to 15 km; the Puget Lowland, the Willamette Valley and
the Eastern Cascades slopes have road medians under 200 m (run). Road medians are short almost
everywhere because the Forest Service's road network (including 76,111 closed roads in the padded
box) is dense (inferred).

## Which forests lacked trails

Read from the downloaded Forest Service trails file (`ADMIN_ORG` filter, no bbox), 2026-10-17:
Umatilla (0614) 549 trail records, all without a line; Wallowa-Whitman (0616) 936 records, 933
without a line. Nez Perce-Clearwater (0117) has 37 of 1,509 without a line and Malheur (0604) 2 of
214, so both publish trails, contrary to the Forest Service's own data-status layer, which lists
them as "unavailable" (verify report). Masked cells (run): Umatilla 97,018 study cells (89,886 in
T7's table), Wallowa-Whitman 163,489 (128,289 in the table); 218,000 of the table's masked cells are
in the Blue Mountains block (35% of its 614,578) and 175 in the Columbia Plateau.

## Sources kept and dropped (run, `prepare.json`; counts over the box padded by 50 km, per file)

- NTD roads: 2,771,003 segments read over eight state files, 2,770,482 kept; 465 tunnels (class 8)
  and 56 ferry crossings (class 7) dropped. Kept roads come from the Census Bureau, the Forest
  Service and the National Park Service only. Segments near a state line can be counted in two files.
- NTD trails: 81,267 read, 68,966 kept (Forest Service 48,728; BLM 12,582; National Park Service
  6,855; Fish and Wildlife Service 801); 12,301 dropped under the owner's ruling 2: Utah's GIS centre
  8,237; Washington State Parks 2,072; California State Parks 862; California Coastal Commission 485;
  Idaho Parks 401; the Continental Divide Trail Coalition 214; Nevada's conservation department 30.
- Forest Service roads: 168,049, all kept (76,111 at maintenance level 1, closed).
- Forest Service trails: 30,852 with a line in the padded box. BLM trails: 6,188.

## Ten cells by hand

Each cell's centre was re-measured by a separate path (`t7_access_build.py spot`): every line within
about 60 km read straight from the raw source files (no FlatGeobuf, no block search) and measured one
by one with shapely; the nearest line's source named. The cells were chosen before the build (the
list is in the script, committed before it ran). Layer and check agree to within 0.005 m in all 19
comparisons that have a layer value; the twentieth, the Eagle Cap trail, is NaN by the mask, where the
raw sources hold a federal trail 657 m away (run).

| Cell | Centre lon, lat | Road (layer) | Road (check, source) | Trail (layer) | Trail (check, source) | Either | Unpublished |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Portland, OR, downtown | -122.67707, 45.52362 | 17.5 | 17.5 (ntd_oregon) | 11,382.5 | 11,382.5 (ntd_washington) | 17.5 | 0 |
| Eagle Cap Wilderness core (Wallowa-Whitman, masked) | -117.29967, 45.16923 | 10,624.7 | 10,624.7 (ntd_oregon) | NaN | 657.4 (ntd_oregon) | NaN | 1 |
| Frank Church wilderness interior, ID | -115.10165, 45.25015 | 18,033.9 | 18,033.9 (fs_roads) | 909.3 | 909.3 (ntd_idaho) | 909.3 | 0 |
| Olympic NP interior, WA | -123.60061, 47.79966 | 19,865.3 | 19,865.3 (ntd_washington) | 5,722.4 | 5,722.4 (ntd_washington) | 5,722.4 | 0 |
| Bob Marshall Wilderness, MT | -113.1989, 47.6011 | 24,856.5 | 24,856.5 (fs_roads) | 294.6 | 294.6 (fs_trails) | 294.6 | 0 |
| Mount Hood NF slope, OR | -121.79899, 45.30073 | 896.1 | 896.1 (ntd_oregon) | 169.0 | 169.0 (fs_trails) | 169.0 | 0 |
| Salt Lake City, UT | -111.8908, 40.75908 | 22.9 | 22.9 (ntd_utah) | 4,978.3 | 4,978.3 (fs_trails) | 22.9 | 0 |
| Black Rock Desert, NV | -119.10052, 40.89943 | 4,118.6 | 4,118.6 (ntd_nevada) | 11,285.9 | 11,285.9 (ntd_nevada) | 4,118.6 | 0 |
| Klamath Mountains, Trinity Alps, CA | -122.99976, 40.99904 | 9,500.1 | 9,500.1 (fs_roads) | 539.1 | 539.1 (ntd_california) | 539.1 | 0 |
| Malheur NF, Strawberry Mountain, OR | -118.70157, 44.29963 | 2,338.4 | 2,338.4 (ntd_oregon) | 97.9 | 97.9 (fs_trails) | 97.9 | 0 |

What the spot check shares with the build, so cannot test: the source filters (`keep_road_class`,
`keep_trail`) and the reprojection in `read`. Those are covered by the unit tests and by the
counts above, not by this check (inferred).

## Tests first, and revert checks

New tests: `tests/test_t7_access.py` (9: distances on synthetic lines with known answers, the block
search's widening, NaN with no line, cell-centre keying, the combine and mask rule, the federal-trail
filter, the road classes), three in `tests/test_t7_predictors.py` (off by default and unchanged
features; the main and side band names; refusals) and one in `tests/test_pnw.py` (the credit line).
The access tests failed over stubs (NotImplementedError, run); one failed after implementation
because the test's own arithmetic was wrong (it expected 500 m for a point that is 424.3 m from
the second line), and the test was corrected, not the code. `test_ferries_and_tunnels...` was written with its function and
was not seen failing over a stub; it is covered by revert r4. `test_the_main_access_band_is_roads...`
passed over the stub (constants only): **not shown to bite**.

Revert checks (`revert/`; runner `revert/run.sh`): each a one-line edit on its own scratch branch in a
separate worktree, run with that worktree's `src` first on the path (the module path printed), the log
checked for collection or import errors before the results (none in any), the file restored from a
copy saved before the edit (`cmp` equal), the scratch tree clean after, and the forward change
confirmed present (`git status` clean on `t7-part-b`).

| Revert | Edit | Result (JUnit XML) |
| --- | --- | --- |
| r1 | `keep_trail` keeps every source | 1 of 9 failed: `test_only_federal_trail_sources_are_kept` |
| r2 | `combine` no longer masks unpublished cells | 1 of 9 failed: `test_combine_takes_the_nearer_and_masks_unpublished_trail_cells` |
| r3 | `block_distances` never widens its radius | 1 of 9 failed: `test_block_distances_are_exact_when_the_nearest_line_is_far_outside_the_first_radius` (NaN where 1,175 m expected) |
| r4 | no road class left out | 1 of 9 failed: `test_ferries_and_tunnels_are_not_roads_and_every_other_class_is` |
| r5 | access values read at (col, row) | 1 of 8 failed: `test_access_bands_are_off_by_default_and_change_nothing_else` (8 of 10 values mismatched) |
| r6 | cell centres at the corner, not the centre | 1 of 9 failed: `test_cell_centres_are_the_grid_convention` |

## Suite and lint

- `pytest`: 695 passed, 0 failed (run twice: once plain, once under the memory-capped scope; JUnit
  XML read). One earlier run under the scope had 8 failures, all in `test_t6b_host_genera.py` and
  `test_t6b_us_half_runner.py` (a runner stage reporting 0 units done where 1 was expected). Not
  reproduced: those two files pass alone under the scope (20 of 20), the full suite passes twice
  after, and the same two files pass on the base b85bbc66. Cause not determined; not touched.
- `ruff check .` and `ruff format --check .`: clean.

## Calls beyond the dispatch, for the planner

1. `pyogrio` 0.13.0 and `shapely` 2.2.0 added to the pinned dependencies (OGR is needed to read file
   geodatabases; the repository has no vector reader for them).
2. NTD ferries (class 7) and tunnels (class 8) left out of the roads band (521 segments).
3. The layer covers the box's study cells only (codes other than 0 in the 2026-10-17 applicability
   raster); other cells are NaN. The first build run, over every box cell, was stopped after 20
   blocks spent widening searches over open sea, and its partial files deleted.
4. The Forest Service's administrative forest boundaries were fetched (40 MB) for the mask; their
   licence is secondhand (DATA_REGISTER row).
5. The BLM file was fetched twice: the first check compared against the HEAD's answer (a 202 with a
   183-byte JSON status) and failed; the script now checks the GET's length and every zip's CRCs.
   Same sha256 both times. The fetch script was also edited after the NTD and Forest Service files
   were fetched (that fix, and an unused import removed); the committed script is the one that
   fetched BLM and the forest boundaries.
6. `dist_any_m` is NaN where either band is NaN, so it is never the road alone where trails are
   unknown.

## What was not checked

- The data.gov licence pages for the Forest Service products were not re-read (404 at the slugs
  tried); CC BY 4.0 rests on the searches report for roads and trails and on a search summary for the
  forest boundaries.
- The terms of the dropped state and volunteer sources (moot under ruling 2).
- The Canadian border effect: about 84,000 eligible cells lie within about 10 km of 49 N (a lon/lat
  approximation, verify report), where the nearest road may be in Canada and the layer reads too far.
  Not measured further; not fixed (-1168).
- Cells just outside the two masked forests whose nearest real trail lies inside them read too far
  in the trail band; not measured.
- Ground-distance error: grid-plane metres, up to about 6% from ground distance by direction (D149).
