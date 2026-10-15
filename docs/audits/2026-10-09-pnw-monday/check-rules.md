# PNW for Monday: the checks, fixed by rule before any value is read

Written 2026-10-09 (UTC) by the PNW coder session, branch `t6b-pnw-monday` at `dbc00be`, before any
soil or host-tree value in the Pacific Northwest was read by this session, and before any
US-half tile existed. Dispatch: Forager RECORD -772 (`prompts/preserved/2026-10-09-04.md`), with
the planner's calls of RECORD -774. The geometry below was computed from coordinates, the master
grid and the T6b mask alone (`border.json`, `geometry.out.txt` beside this file).

## The PNW

- **The box:** 40 to 49 N, 111 to 125 W, edges inclusive (`t4_layer.LonLatBox`), longitude and
  latitude read as NAD83 as everywhere on the master grid. A cell is in the PNW when its centre is
  in the box. Clipping at 49 N is the box's north edge.
- **Its master-grid window** (`t4_layer.master_window`): left -2,295,000, bottom 95,000, right
  -1,033,000, top 1,367,250 (5,048 x 5,089 cells). Cells of the window outside the box are not
  shown and not counted.
- **The PNW total** a sample is reported against: study cells (D111, D113, D117) whose centre is in
  the box, per layer, counted from the mosaic.

## 1. Tile-edge agreement (TASKS.md T6b Verify, first item)

"The same cells computed inside one tile and across a tile edge agree exactly." Each window below
is recomputed as one pseudo-tile of 64 x 64 cells centred on a point where tiles meet, by the same
entry point the run used (`soil_tile`, `tree_tile`, or `tree_tile_us_half` for a window holding
Canadian cells), into a scratch folder, and compared cell by cell with the stored tiles: every
value band and every flag, exact equality, NaN equal to NaN. Any difference fails the check. Cells
pending on both sides (Canadian cells of US-half tiles) are compared as pending.

- **Trees, lattice corners:** every corner of the 1,024-cell lattice (super-window corners, four
  256-cell tree tiles meet at each) whose point lies in the box: 16 corners,
  (col, row) in cell units: (-8192, 2048), (-8192, 3072), (-8192, 4096), (-7168, 1024),
  (-7168, 2048), (-7168, 3072), (-7168, 4096), (-7168, 5120), (-6144, 1024), (-6144, 2048),
  (-6144, 3072), (-6144, 4096), (-5120, 1024), (-5120, 2048), (-5120, 3072), (-5120, 4096).
- **Trees, border corners (D119):** every 256-lattice corner in the box at which at least two of
  the four tiles meeting there are PNW US-half tiles: 17 corners, (-7936, 5120), (-7680, 4864),
  (-7680, 5120), (-7680, 5376), (-7424, 5120), (-7168, 5120), (-6912, 5120), (-6656, 4864),
  (-6400, 4864), (-6144, 4864), (-5888, 4864), (-5632, 4608), (-5376, 4608), (-5120, 4608),
  (-4864, 4608), (-4608, 4608), (-4352, 4608). (-7168, 5120) is in both lists, so 32 tree windows.
- **Soil:** every corner of the 2,048-cell soil lattice in the box (4: (-8192, 2048),
  (-8192, 4096), (-6144, 2048), (-6144, 4096)) and every midpoint of a soil-tile edge in the box
  (7: (-7168, 2048), (-8192, 3072), (-7168, 4096), (-6144, 1024), (-5120, 2048), (-6144, 3072),
  (-5120, 4096)): 11 windows. Each needs its own small SoilGrids fetch, recorded beside the result.
- A window corner is in cell units: cell (col, row) has its lower-left corner at
  (250 col, 250 row) m.

## 2. The fixed ten cells (docs/audits/2026-10-07-t6b-verify/ten-cell-rule.md)

The rule and its tolerances stand unchanged. Of its ten cells, two have their centre in the box:
**coast-oregon** (44.30 N, 123.95 W) and **border-us-selkirks** (48.95 N, 117.20 W).
border-ca-selkirks (49.05 N) is north of the clip; the other seven are outside the box. So this
check runs on **2 of the 10 cells**, both on the US side, for soil and for host trees, and says
nothing about the other eight. border-us-selkirks lies in tree tile 256_-23_19, one of the 20
US-half tiles, so it checks the D119 path on real data.

- Soil: the rule's independent 40 x 40 point sampler against the stored native SoilGrids windows,
  tolerance 0.01 pH, valid fraction 0.02.
- Host trees: the rule's exact area-weighted recompute by code that imports nothing from the
  pipeline except the published Bechtold 2004 tables and T5's genus lists, tolerances cover 0.1
  points, shares 0.001, valid fraction 0.001, source and flags exact.

## 3. The 49 N seam (T5's transects, `seam.run_transects`)

Run as written (25 meridians from 121.0 W westward, 80 samples a side) on the PNW tree mosaic,
bands `total_cover_pct`, `share_Pseudotsuga`, `share_conifer`, `share_broadleaf`. **It cannot give
a verdict now**: the border step is Canada minus US, and the Canadian cells are pending SCANFI
(D118, D119), so every border step is empty. Reported as "no verdict, Canadian side pending", with
what it does show: how many US samples next to 49 N have a value, and the within-US step
statistics. It is not a pass (planner, RECORD -774).

## What fails, and what happens then

A failure on real data is reported as it stands and the check is not adjusted (dispatch, Stops).
