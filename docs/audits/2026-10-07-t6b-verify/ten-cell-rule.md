# T6b: the ten cells per layer, fixed by rule before any value is read

Written 2026-10-07 00:45 UTC (2026-10-06 local) by the T6b coder session (D38), branch
`t6b-continental-layers`, base `origin/main` `36cc647`, dispatch
`docs/dispatch/2026-10-06-t6b-continental-layers.md`, Verify item 6.

**State when this was committed:** no T6b data had been fetched or read. Nothing on the flash drive
under `forecast-data/t6b/` existed. No SoilGrids, TreeMap or SCANFI value at any of these cells had
been looked at by this session. The cells below were chosen from place names and coordinates only.
The trial tile (Verify item 3) runs after this commit and does not contain any of these cells
(it straddles 49 N near 114.5 W; the nearest cells below are at 117.2 W, about 200 km west).

## The rule

1. **The same ten points are used for both layers** (soil pH, and host trees).
2. **Each point names the master-grid cell that contains it,** by `grid.cell_for_lonlat`
   (longitude and latitude read as NAD83, ESRI:102008, 250 m, lattice at (0, 0)). The col, row and
   id below were computed from the coordinates only, by that function, at this commit.
3. **No substitution.** A cell that turns out masked, no data, under the 0.5 valid fraction (D74),
   under 10% cover (D89), or "not available" (D85) is kept and checked as that state: the master
   grid must show the state the source and the rules give. No cell is swapped after a value is seen.
4. **The masked cell and the no-data cell** are fixed below by what the rules and published
   descriptions predict, not by any value. If the prediction turns out wrong (for example the lake
   cell has soil), the cell is still checked, and the report says the prediction was wrong.
5. **No "at threshold" exemption.** The T4 review (finding 4) found T4's script exempted cells near
   the 0.5 valid fraction. Here a mismatch is a failure whenever master and source both have a value.
   A cell where one side has a value and the other has none fails too, unless the independent
   recompute puts its valid fraction within 0.001 of 0.5, in which case it is reported as such with
   both fractions and still counted as not passing.

| # | Name | Why | Latitude N | Longitude | col | row | cell id |
|---|---|---|---|---|---|---|---|
| 1 | coast-oregon | Pacific coast range, about 8 km inland | 44.30 | -123.95 | -8267 | 3259 | 2,361,089,973 |
| 2 | mountains-colorado | Rocky Mountains, subalpine | 40.35 | -105.70 | -3097 | 323 | 2,168,681,447 |
| 3 | prairie-kansas | US prairie, cropland | 38.50 | -98.50 | -823 | -697 | 2,101,837,001 |
| 4 | prairie-saskatchewan | Canadian prairie | 51.00 | -106.00 | -2663 | 5329 | 2,496,755,097 |
| 5 | boreal-manitoba | Boreal forest, south of every Arctic line offered | 55.00 | -98.00 | -495 | 7055 | 2,609,872,401 |
| 6 | border-us-selkirks | 49 N, US side (about 5.5 km south) | 48.95 | -117.20 | -5823 | 4880 | 2,467,326,273 |
| 7 | border-ca-selkirks | 49 N, Canadian side (about 5.5 km north) | 49.05 | -117.20 | -5812 | 4926 | 2,470,340,940 |
| 8 | appalachians-smokies | Eastern mountains, broadleaf and conifer | 35.60 | -83.50 | 4279 | -1788 | 2,030,342,327 |
| 9 | masked-mexico-chihuahua | Masked: Mexico (D47), under every Arctic option | 28.00 | -106.00 | -3799 | -5395 | 1,793,945,897 |
| 10 | nodata-lake-michigan | No data predicted for soil (ISRIC masks inland water, T4 verify report section 4.8); for host trees, total cover predicted 0 and every share empty (T5's rule counts a no-data pixel as no crown, so water reads 0% cover and falls under the 10% share threshold) | 43.50 | -87.00 | 2732 | 1783 | 2,264,369,836 |

## What is compared, and against what

**Soil pH (T4's method and tolerance).** For each cell, the independent check samples the cell at
40 × 40 points, takes each point to Homolosine with its own pyproj call, looks it up in the stored
native SoilGrids pixels, and recomputes the 0 to 30 cm blend (weights 5, 10, 15; pH x 10 divided by
10; no-data -32768) itself, importing nothing from `forager_forecast`, as `scripts/t4_ten_cells.py`
does. Compared: mean, Q0.05 (approximate), Q0.95 (approximate), and the three valid fractions.
**Tolerance: 0.01 pH, T4's** (T4 completion report section 6). Valid fraction: 0.02 (the sampler
resolves fractions to 1/1,600; T4 reported Kalaloch at 0.916 against 0.915).

**Host trees (T4's tolerance carried to these units; a reading for the planner).** T4 has no
tolerance for canopy cover or shares. T4's 0.01 pH is one tenth of SoilGrids' own step of 0.1 pH.
The same rule here gives one tenth of each source's own step:
- total canopy cover: **0.1 percentage points** (TreeMap `CANOPYPCT` and SCANFI closure are whole
  percent);
- genus, conifer and broadleaf shares: **0.001** (a share of whole-percent covers; one tenth of 1
  point at 100% cover);
- valid fraction: **0.001**;
- source band and every flag: **exact**.

A point sampler cannot meet 0.001 on 30 m pixels (the T5 review's 50 × 50 sampler agreed to 0.009 in
a share). So the host-tree check is an **exact area-weighted recompute by code that shares nothing
with the pipeline**: it clips each native pixel against the master cell's corner quad (the opposite
direction to `regrid.py`, as the T4 reviewer's check did), reads the stored native windows with its
own code, recomputes plot covers for the plots it touches from the TreeMap tree table, and applies
the published rules (D85, D87 to D92, D74, the 10% threshold of D89) itself. It shares only the
Bechtold 2004 coefficient and diameter tables, which are published constants (as the T5 review's
recompute did). If the planner prefers a looser host-tree tolerance with a sampler, that is a
change to this file made before the run, recorded as such.

**Masked and no-data cells** pass only if the master grid shows the same state: masked cells are no
data in every value band, valid fraction 0, and flag 0; no-data cells match the source's state.

The script that applies this rule is written in the build and committed before it is run on real
output. Its output is committed beside this file.
