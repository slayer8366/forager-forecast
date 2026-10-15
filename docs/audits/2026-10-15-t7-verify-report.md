# T7 verify report: the PNW habitat map for mycorrhizal mushrooms as a group

Written 2026-10-15 (about 19:00 to 20:00 UTC) by a verify coder session on the Forager planner's
dispatch, on the owner's go (Forager RECORD -1049; the owner, verbatim: "Continue building the
PNW with whatever else needs to be done"). Task: the "Verify before building, report by message"
section of `docs/dispatch/2026-10-15-t7-mycorrhizal-habitat.md` (the plan), with the planner's
binding scope changes: **V9 and V17 held** (no presence or observation of the target group or the
comparison read, counted, tabulated or plotted in any form), the box's tree layers read as the
24-band tiles written by unmerged branch `t6b-host-genera`, the live continental run's drive
folder read only, no GBIF, climate or Open-Meteo request, no fit, no merge.

**Base.** Branch `t7-pnw-verify`, cut from `origin/t7-mycorrhizal-plan` `c11b4b6` (forecast main
`a79d667` plus the plan, D125, D126 and a closeout note). `origin/main` is still `a79d667` after
`git fetch origin` at about 19:05 UTC. Code read on `t6b-host-genera` at `b0a0e88` (its tip at
fetch). Forager RECORD read at `records-after-173` `8580f835` (entries -806, -913, -914, -1021,
-1023, -1027 to -1036, -1039, -1041, -1047, -1049).

**What ran.** Six read-only scripts, committed with their outputs under
`2026-10-15-t7-verify/`, each under `systemd-run --user --scope -q -p MemoryMax=5G -p
MemorySwapMax=0` and `nice -n 10` (the small ones under nice only). Peak RSS 0.35 GB, longest
1 min 44 s. They read T6b's mask, tiles, flags and manifest, the level III shapefile, and the
cell keys (not the values) of T6's stored effort surface. Nothing was written under the drive's
`t6b/` folder; no PAUSE file was touched; `t6b-night` was active throughout. The D26 zip was
hashed and its `meta.xml` and header line read; **no record row was read.** No test suite was run
(no code changed).

Evidence flags: **READ** (a file, record or page says so, cited), **OBSERVED** (a command or
script here produced it, output committed), **INFERRED**, **COULD NOT DETERMINE**.

## Answers

### V1. Base: holds

- OBSERVED: `origin/main` = `a79d667` (unchanged since the plan was written); `HEAD` =
  `c11b4b6` = `origin/t7-mycorrhizal-plan`.
- OBSERVED (`git merge-base --is-ancestor <c> HEAD`): ancestors of the base are the nine tips
  RECORD -1021 names (`8586b8a`, `37691c6`, `b91599f`, `3c39d66`, `c313f5c`, `c2154af`,
  `72fd2c2`, `31f956c`, `f7c8648`) and the plan's six (`cfbf50d`, `aec605d`, `a8f85b9`,
  `dd28648`, `9e24e67`, `04f0302`). So the base holds T6b's code, D121 (`DECISIONS.md:13`) and
  D123 (`:11`). Main has not moved.
- **But the base does not hold the code that wrote the box's current tree tiles.** Those are on
  unmerged `origin/t6b-host-genera` (merge-base with main `a79d667`; RECORD -1039, -1047). Main's
  `TREE_BANDS` (`src/forager_forecast/t6b_layers.py:97`) is the 11-band layout. See "Premises that
  were wrong" 1 and the D18 point under V6.

### V2. Decision rows: holds, with line drift

- READ: on this base D122 is the SCANFI edge ruling at `DECISIONS.md:12` and D123 the pilot
  ruling at `:11` (the plan's `:10` and `:9` are main's numbering; D125 and D126 at `:9` and `:8`
  pushed them down two lines). D125 and D126 are on the base as filed (`:9`, `:8`).
- OBSERVED (every `origin/*` branch's `docs/planning/DECISIONS.md`): rows above D124 exist only
  as D125 and D126 on `t7-mycorrhizal-plan` and **D127 on `t6b-host-genera`** (proposed there,
  amending D116 for tier B hosts, RECORD -1039). No branch holds a different D125 or D126. This
  verify writes no decision row. **The next free number for T7's rows is D128**, unless D127 is
  renumbered at its merge.

### V3. The pilot ruling reaches this T7: yes (READ), not a stop

- D123 (`DECISIONS.md:11`): "the first model is a Pacific Northwest pilot, fitted on the PNW and
  not on continental layers. D100's clause 'so the model is fitted on continental layers, not the
  test areas T4 and T5 built' is changed for this first fit only. D100's continental fit stays the
  target and follows the pilot." RECORD -806: "Order: T1 ... first; the PNW box's Canadian SCANFI
  tiles ahead of the continent; then T7 to T9 on the PNW."
- Both were written while the target was chanterelles. Neither names a group: D123's object is
  "the first model", and the clause it changes is D100's line in T7's own "Also depends on"
  (`TASKS.md:82`). So on their words they cover whatever T7 fits first (INFERRED reading).
- The direct cover is later and from the owner: RECORD -1027 (after -913's change of target):
  "forager-forecast's T7, T8 and T9 are built and fitted on the PNW first, as a pilot of the whole
  pipeline, before any continental fit (D100's target stands, after the pilot, as D123 already put
  it)". -1027 is not yet a forecast decision row; M6's row is a natural place to cite it.

### V4. The box's tiles: holds (OBSERVED, `box_layers.out.json`)

- 296 tree tiles hold box study cells: 283 whole tiles (`tiles/trees/`) and 13 US-half files
  (`tiles/trees_us_half/`, D119). Every one has a latest manifest line with status `ok`, band
  layout `t6b-bands-f4e9b848ba51` in both the line and the file's tag, 24 value bands, and both
  files hashing to the line. Box study cells: 16,571,590 US and 102,543 Canadian (the mosaic
  summary's counts, re-derived).
- The 8 Canadian tiles (256_-29_20, -30_19, -30_20, -30_21, -31_19, -31_20, -31_21, -32_20):
  each a whole file and flags, line ok, hashes match, current layout; their lines record
  `scanfi_route: "whole layers (D118)"` (e.g. 256_-30_20, finished 2026-10-14T22:56 -07:00).
- **No box study cell carries 4 "pending"**: 0 in the `source` band, 0 in any flag band. The 13
  US halves' pending cells all lie outside the box.
- **The 24-band tiles keep the reviewed values** (`old_vs_new_tiles.out.json`): for all 283 whole
  tiles, the old 11-band file kept under `superseded/20261015T055455Z-trees/` or
  `superseded/20261015T133145Z-trees/` equals the new file on all 19 shared bands (11 value, 8
  flag), NaN for NaN, over the whole tile: 0 cells differ in any tile. The 13 rebuilt US halves
  likewise (26 files, `old_vs_new_us_halves.out.json`); the 7 old border halves are replaced by
  whole tiles (RECORD -1047). Positive control: the same comparison between two different tiles
  reports 60,268 differing cells (`old_vs_new_control.out.txt`).

### V5. Every tree band, both sides (OBSERVED, `box_layers.out.json`)

Cells in the box's study area with a defined value, by side:

| Band | US | Canada |
|---|---|---|
| total_cover_pct | 16,377,178 | 100,427 |
| any genus share, conifer, broadleaf (all 21 share bands alike on the US side) | 6,991,082 | see below |
| share_Pseudotsuga, share_conifer, share_broadleaf | 6,991,082 | 96,577 |
| the other 18 share bands | 6,991,082 | 0 (flag 3 on all 102,543) |

- **The mosaic's gap is the Canadian side, exactly.** 7,087,659 (Pseudotsuga) = 6,991,082 US +
  96,577 Canada; 6,991,082 (Tsuga) = US only. On the US side every share band is defined on the
  same cells (canopy cover at least 10% and valid, D89 (3)); 9,580,508 US box study cells (57.8%)
  carry flag 0 on every share band (under 10% canopy or under half valid).
- **Not available on the Canadian side (flag 3, D85, D89 (1), and the new bands):** Tsuga, Picea,
  Abies, Pinus, Quercus, Larix, Betula, Populus, Alnus, Lithocarpus, Chrysolepis, Arbutus, Fagus,
  Carya, Tilia, Ostrya, Carpinus, and ecm_hosts. Only Pseudotsuga, conifer and broadleaf come from
  SCANFI (`SCANFI_BAND_CLASSES`, `t5_layer.py:105-109` on `t6b-host-genera`; the fill rule at
  `t6b_layers.py` `_tree_bands`, flags at the `FLAG_NOT_AVAILABLE` branch). READ: SCANFI's ten
  classes include `tamarack`, `jackPine`, `lodgepolePine`, `ponderosaPine`, `whiteRedPine`
  (`t5_layer.py:101-104`), none mapped to Larix or Pinus (D89 (1) rules the pines out; Larix is
  simply not mapped). RECORD -1032 called Larix "partial" in Canada; the code gives it nothing.
- **Cells with a share above 0, US side** (layer values only): Pseudotsuga 6,267,639; Pinus
  6,183,427; Abies 5,711,561; Picea 3,534,331; Tsuga 2,897,773; Larix 2,380,921; Populus
  2,185,945; Alnus 1,782,928; Quercus 1,777,611; Chrysolepis 1,031,070; Arbutus 924,294; Betula
  655,702; Lithocarpus 642,443; ecm_hosts 6,930,807. **Tier B (Fagus, Carya, Tilia, Ostrya,
  Carpinus): 0 cells above 0 anywhere in the box**, so in the pilot those five bands are constant
  0 where defined (INFERRED: they carry no information for a PNW fit).
- ecm_hosts is above 0 on 99.1% of US cells with shares (6,930,807 of 6,991,082). INFERRED: in
  this box it is close to "canopy that is not juniper, cedar or other non-host conifer", so it may
  say little beyond the conifer share; the members are a proposal (`t6b_hosts.py:37-38`, "all
  eighteen genus bands"), not a ruling.

### V6. The T6b review's open items

- **S2 not fixed on any branch** (READ). `layers_ready` still asks only that the eleven npz files
  exist: main `scripts/t6b_run.py:322-325`, `t6b-host-genera` `:423-426`; a whole tile's line
  still records only `us_cells_from` and its own two files (`fill_canadian_cells`,
  `t6b_layers.py` on `t6b-host-genera`, the `us_cells_from` and `files` fields). No branch
  changes `layers_ready` (searched every `origin/*`).
- **S3 not fixed** (READ). `scripts/pnw_checks.py` last changed in `2cba4a7` (main); no
  `origin/*` branch has a later commit to it.
- **Seam verdicts after the re-run hold as the plan states** (READ, `seam-after-10-tiles/
  seam.out.json`): each band ran on 25 transects; total_cover_pct "artifact", 23 with a border
  step; share_Pseudotsuga, share_conifer and share_broadleaf "no step", 7 each. Because the
  24-band tiles equal the old ones on these bands (V4), the verdicts carry over to the current
  tiles (OBSERVED). **No seam or edge check exists for the 13 new bands**; in Canada they have no
  value at all, so a 49 N seam cannot test them as written (INFERRED).
- **D18 for the new bands is not met.** No review of `t6b-host-genera` is filed (no review branch
  on origin; the build report is the builder's own). The 2026-10-11 review covered the 19 bands
  shared with the old layout, which are bit-identical (V4); the 12 genus bands and ecm_hosts are
  unreviewed, and D127 (tier B as hosts) is proposed, not filed. Plan deviation 6 says D18 is
  "Now met for the box's layers"; that holds for the old bands only.
- How T7 handles the total-cover artifact is P4's to propose, not this verify's. Options seen
  (none chosen): leave total cover out and use shares only; use it with the artifact stated; or
  enter it only through D121's held-out comparison.

### V7. Soil in the box: holds (OBSERVED, `box_layers.out.json` "soil")

- 8 soil tiles (2048 cells) hold box study cells (a ninth, 2048_-5_2, meets the window with none).
  All exist; each file hashes to its manifest line. Two lines (2048_-4_2, 2048_-3_2, written
  2026-10-07) predate the manifest's `status` field and carry none; their hashes match.
- 16,248,227 of 16,674,133 box study cells have `ph_mean_0_30cm`, as the mosaic summary reads.
  Every one has `valid_fraction_mean` at least 0.5, and no cell with a mean has a valid fraction
  under 0.5; each tile's `min_valid_fraction` tag reads 0.5. So the bands are as D74 rules (0.5,
  `t4_layer.py:82` per D74's row).

### V8. NALCMS: holds

- OBSERVED: no master-grid NALCMS layer on the drive or `/mnt/work` (`find -iname '*nalcms*'`
  finds only the source raster, its sidecars and request records); `t6b/tiles/` holds soil, trees
  and trees_us_half only.
- READ: water (18) and unmapped (0, 127) are no data in the tree layer: `t6b_layers.py:91-92`
  and `:367` (main); the tile tags say so (`"water"` tag, `_tree_tags` on `t6b-host-genera`).
  Class 19 "Snow and Ice" is not blanked (D112 names 18 and unmapped only).
- READ: the study area is `t6b/mask.tif` (version "D111 D113 D117" in `mask.json`), read through
  `t6b_mask.read_mask` and `cells_in_study` (`t6b_mask.py:194`, `:224`). Under A4 nothing is
  built.

### V9. Presences: HELD (planner's scope; M1 not cleared, RECORD -1036; RECORD -1030 point 1)

Nothing read. The plan's (a) to (e) are untouched.

### V10. Effort frame (OBSERVED, `box_cells.out.json`, `frame_in_lattice.out.txt`)

- The box's 0.1° lattice has 12,831 centres (91 x 141); **12,150 weather cells hold at least one
  box study cell** (12,037 with US cells, 114 with Canadian).
- T6's frame has 43,035 cells (`all/cell_level.csv`, cell keys only; the ten stored files hash to
  `docs/audits/2026-10-06-t6-fit/stored_surface_sha256.txt`). 4,190 frame cells lie in the box's
  lattice; 4,185 of them hold box study cells.
- **7,965 of the 12,150 weather cells are outside the frame, holding 11,145,103 of the 16,674,133
  box study cells (66.8%)**: US 7,951 cells and 11,129,409 study cells; Canada 14 and 15,694.
  `effort()` raises `NoEffortValue` for every one (`effort.py:620-621`).
- What it means (INFERRED, for P3 and P6, nothing chosen): the frame is "every cell with an
  outing" (D101), so a cell outside it had no all-fungi outing in 2015 to 2025; effort there is
  not unknown in the counts, but D107 forbids the function from inventing a value. (1) A
  background drawn at random from the study area lands two times in three where `effort()`
  refuses, so the covariate route needs a rule for those cells, which D107 does not give. (2) A
  target-group background drawn from T6's outings sits inside the frame by construction, and
  then covers a third of the box's cells. (3) Holding effort constant for prediction (P6) needs
  no per-cell effort, so prediction itself is not blocked. A rule for out-of-frame cells is a new
  rule and goes to the owner.

### V11. Cell keying across scales (OBSERVED, `box_cells.out.json` "keying", `keying_fixture.out.txt`)

- A master cell's centre is put to longitude and latitude by `Transformer.from_crs(GRID_CRS,
  GEOGRAPHIC_CRS)` (`t6b_mask.cell_lonlat`, `t6b_mask.py:206-211`; `GRID_CRS` "ESRI:102008",
  `GEOGRAPHIC_CRS` "EPSG:4269", `grid.py:29`, `:33`), then `cells.cell_for` (decimal nearest,
  ties toward +infinity on the decimal value, `cells.py:68-87`; D46, D63, D64).
- Over all 16,674,133 box study cells, none lies within 1e-9 of a tenth's half-way point on
  either axis, so no tie arises from the master grid in this box. On 18,924 sampled cells (64 per
  tile, seed 20260918) the decimal `cell_for` and a float `floor(10x + 0.5)` agree on every one.
  Fixture: a 3 x 3 window at 45.5 N, 122.5 W maps to `455_-1225`; the tie (47.05, -123.05) goes to
  `471_-1230` and (45.25, -122.45) to `453_-1224`, as D63 and D64 say.
- **No production code maps a master-grid cell to a weather cell today** (READ: `git grep` of
  `cell_for(` finds only record paths: `cell_weeks.py:38`, `effort.py:156`,
  `records/filters.py:114`, `:120`, `records/t1_record.py:106`). T7 needs that path as new code,
  with a test.
- Datum (INFERRED, not measured): the master grid's geographic CRS is NAD83 (EPSG:4269), GBIF's
  coordinates are WGS84; PROJ's default NAD83 to WGS84 step without a grid is the identity, so the
  two agree to within about a metre or two at most, far inside a 0.1° cell. The T4 report already
  lists the datum pin as not checked.

### V12. Ecoregion assignment (READ and OBSERVED)

- The file: `t6b/sources/terr_ecoregions_v2_level_iii_shapefile/NA_TerrEcoregions_III/data/
  NA_Terrestrial_Ecoregions_v2_level3.shp` (`scripts/t6b_run.py:69-71`), 2,905 polygons, fields
  LEVEL1 to LEVEL3 with English, Spanish and French names (UTF-8, per its `.cpg`).
- Licence as stated at source, in the metadata shipped with the data
  (`NA_Terrestrial_Ecoregions_v2_level3.shp.xml`): "This material is licensed under CC BY 4.0,
  allowing non-exclusive rights to distribute, remix, adapt, and build upon the material in any
  medium or format, including for commercial purposes, so long as attribution is given to the
  creator." Citation (`HowToCite_ComoCitar_CommentCiter.txt`): CEC 2021, "North American
  Environmental Atlas - Terrestrial Ecoregions: Level III", Ed. 2.0. DATA_REGISTER's row
  (`DATA_REGISTER.md:25`) agrees.
- **The mask stores no level III code.** Its band 2 holds only none, Arctic, or other
  (`t6b_mask.py:111-114`). So T7 must burn level III itself. Done here by cell centre with the
  mask's own `_burn` (GDAL's default rule, `t6b_mask.py:130-151`), the D117 route: every one of
  the 16,674,133 box study cells falls in a level III polygon (0 in none), which agrees with the
  mask.
- At the master grid the box holds **25 level III blocks under 5 level I**, as the plan's 0.1°
  count found. Per block (study cells; cells with shares, that is canopy at least 10%):
  Northern Basin and Range 2,243,189 (165,910); Central Basin and Range 1,847,039 (98,539);
  Middle Rockies 1,428,904 (641,567); Columbia Plateau 1,330,083 (51,703); Columbia
  Mountains/Northern Rockies 1,311,221 (1,069,982); Blue Mountains 1,134,602 (614,710); Idaho
  Batholith 964,521 (623,506); Cascades 937,675 (832,956); Snake River Plain 857,980 (12,182);
  Eastern Cascades Slopes and Foothills 852,142 (491,454); Coastal Range 751,751 (698,432);
  Klamath Mountains 675,557 (556,207); North Cascades 486,255 (392,324); NW Glaciated Plains
  444,773 (8,107); Strait of Georgia/Puget Lowland 337,609, of them 66,806 Canadian (235,712);
  Canadian Rockies 302,132 (230,095); Willamette Valley 238,153 (95,182); Wasatch and Uinta
  Mountains 229,582 (151,004); Central California Foothills and Coastal Mountains 90,151
  (41,755); Wyoming Basin 64,966 (4,276); NW Great Plains 54,435 (11,154); Sierra Nevada 46,334
  (24,897); Coastal Western Hemlock-Sitka Spruce Forests 35,737, all Canadian (35,171); Central
  California Valley 8,510 (394); Colorado Plateaus 832 (440). Level I: Northwestern Forested
  Mountains 8,368,925; North American Deserts 6,344,089 (5.2% with shares); Marine West Coast
  Forests 1,363,250; Great Plains 499,208; Mediterranean California 98,661.
- For P7 (INFERRED): seven blocks have under 8% of their cells with shares: Snake River Plain
  1.4%, NW Glaciated Plains 1.8%, Columbia Plateau 3.9%, Central California Valley 4.6%, Central
  Basin and Range 5.3%, Wyoming Basin 6.6%, Northern Basin and Range 7.4%. The two Basin and
  Range blocks are the largest in the box. That is the "deserts flatter the score" risk the plan
  names, in numbers. The next is NW Great Plains at 20.5%; 17 blocks are at 40% or more.

### V13. Size and memory (OBSERVED where stated; estimates INFERRED)

- OBSERVED: one streaming pass over all 296 box tree tiles, reading every value and flag band,
  with the mask and box test per tile: 1 min 40 s, peak RSS 0.35 GB (`box_layers.log`). The
  same with the level III burn and weather keys: 1 min 43 s, 0.31 GB (`box_cells.log`).
- INFERRED: the window over the box is 5,048 x 5,089 = 25.7 million cells, 16.67 million in the
  study area. A predictor table of D121's lean set (21 share bands, total cover, soil pH, its
  valid fraction, an effort term: about 25 columns) for every study cell is 16.67 M x 25 x 4 B =
  1.7 GB in float32, 3.3 GB in float64, before the model's own copies. With t6b-night holding its
  own 5 GB scope on an 11 GB laptop (about 5 GB available at 19:40 UTC, `free -g`), **prediction
  must stream by tile** (65,536 cells a tile, about 6.5 MB of predictors). A background sample of
  10^5 to 10^6 points at 25 float64 columns is 20 to 200 MB. No trial window was fitted (no fit
  allowed), so model memory is not measured.
- Outputs (INFERRED): a float32 relative-habitat raster and a uint8 mask over the window, about
  100 MB and 26 MB uncompressed. The drive has 5.7 GB free and is the live run's; `/mnt/work` has
  21 GB (`df -h`, 19:2x UTC). They belong on `/mnt/work`.
- Continental scale (INFERRED): D117's row puts the first mask at 241,229,862 study cells, about
  14.5 times the box, so a continental predict pass is about 14 to 15 times the box's by cell
  count.

### V14. Licences of what the output reads (READ)

| Source | Read for | Licence as stated, where |
|---|---|---|
| TreeMap 2023 CONUS (Zimmer et al. 2026) | US host trees, cover | Archive-published "under the Creative Commons CC-BY license structure" (no version), data use agreement on derived products; `DATA_REGISTER.md:27` |
| SCANFI v2 (Guindon et al. 2026) | Canadian Pseudotsuga, conifer, broadleaf, cover | Open Government Licence - Canada; `DATA_REGISTER.md:14`, `t5_layer.py:100` |
| NALCMS 2020 30 m, Ed. 2.0 | water and unmapped as no data | CC BY 4.0; `DATA_REGISTER.md:30` (D112) |
| CEC Political Boundaries 2021, Ed. 3.0 | study area, side | CC BY 4.0; `DATA_REGISTER.md:29` (D113) |
| CEC Terrestrial Ecoregions level III, Ed. 2.0 | study area (D117), validation blocks (D125) | CC BY 4.0; shipped metadata (V12), `DATA_REGISTER.md:25` |
| SoilGrids 2.0 | soil pH | CC BY 4.0; `DATA_REGISTER.md:15`, `soilgrids.py:42-46` |
| GBIF download 0012112-260928105237408 (DOI 10.15468/dl.8jxmeb) | presences (held), effort | download licence CC BY-NC 4.0, per-record licences filed (D29); `docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json:18`; D61 rules its use |
| T6 effort surface | effort | derived from the same download (D107) |
| Membership list (M1) | which genera count | **not chosen**; RECORD -1036: no licence found at source for either fungal-lifestyle list checked; V17 held |

Finding: the PNW render's tree attribution, `pnw.py:46-53` `SOURCES["trees"]`, names TreeMap,
NALCMS and the CEC files but **not SCANFI**, though the box now has 102,543 SCANFI cells. The
tiles' own `attribution` tag names all three sources (`_tree_tags`, `t6b_layers.py` on
`t6b-host-genera`). T7's attribution should be built from the tile tags or this list fixed.

### V15. Prior art

See the section "V15: prior art" below.

### V16. Genus names to keys, offline: holds for the columns; the count HELD

- OBSERVED (the zip's `meta.xml` and `occurrence.txt`'s header line only, no row): the D26
  download carries `genus` (header column 166), `genusKey` (205), `family` (162), `familyKey`
  (201), `order` (160), `orderKey` (199), `taxonRank` (173), `acceptedTaxonKey` (195),
  `acceptedScientificName` (209), and `genericName`. So a list of genus names can be joined to
  records offline, without GBIF's matching API.
- READ: the loader reads `acceptedTaxonKey` and `genusKey` only (`records/occurrence.py:52-65`),
  so T7 needs `genus` (or a name-to-key table) added to what it reads.
- OBSERVED: zip sha256 `c0d5f6a1...b26c`, equal to `docs/pulls/gbif-fungi-us-canada-2015-2025.
  doi.json:11`.
- **The count "records with a family but no genus, by family" is not done.** It is a count of
  records of candidate member families, which the planner's hold on V9 covers ("in any form").

### V17. The membership source: HELD (planner's scope; RECORD -1036)

## V15: prior art

PLACEHOLDER

## Confirmed vs inferred

Confirmed (OBSERVED or READ, cited above): V1, V2, V4, V5, V7, V8, V10, V11's arithmetic and
fixture, V12, V14's table, V16's columns, S2 and S3 open, D26 and T6 hashes. Inferred: V3's
reading of D123 as group-neutral; the meaning of the out-of-frame cells; ecm_hosts and tier B
carrying little in this box; all memory and size estimates in V13; the datum note.

## Could not determine

- Model memory and time for a fit or a predict (no fit allowed).
- Whether the 12 new genus bands and ecm_hosts are right on the ground: no ten-cell recompute,
  edge or seam check exists for them, and no review (D18).
- Why `tamarack` is not used for Larix in Canada (no record says; INFERRED a choice under D89
  (1)'s logic, never ruled for Larix).
- Anything about the target group's or the comparison's records (held).

## Premises that were wrong

1. **The base holds what T7 reads** (plan V1, "Inputs" table, `TREE_BANDS` at
   `t6b_layers.py:97`): the box's tree tiles are now the 24-band layout from unmerged
   `t6b-host-genera`; main's code describes 11 bands. A T7 cut from main reads them by band name
   but cannot name the new bands from its own code.
2. **D18 "Now met for the box's layers"** (plan deviation 6): met for the 19 bands shared with
   the reviewed layout (bit-identical, V4), not for the 13 new ones.
3. **M7** (plan `:469-475`, recommended (a)): overtaken; the owner chose to add the genera now
   (RECORD -1029, -1033) and they are built (-1039, -1047). The plan's "have no band of their
   own" (`:81-83`) no longer holds for the box.
4. **"Tsuga, Quercus, Pinus, Picea and Abies are not available" in Canada** (V5): true but now
   incomplete; 18 share bands are not available there, including every new genus and ecm_hosts.
5. **The planner's "24 bands (T5's 8 plus 12 new host genera and share_ecm_hosts)"**: 8 + 12 + 1
   = 21 share bands; the 24 are those plus total_cover_pct, valid_fraction and source.
6. Line numbers: D122 and D123 at `DECISIONS.md:12`, `:11` on this base (plan `:10`, `:9`); D121
   at `:13` (plan `:11`); D18 at `:108` (plan `:106`); `crown_cover.py` HOST_GENERA at `:156`,
   BANDS at `:157` (plan `:155-156`). All from the plan's own two inserted rows or off by one.
7. Not a plan premise but a planner's: RECORD -1032's "Larix partial" in Canada; the code flags
   Larix not available on every Canadian cell.

## Decided beyond scope

- Burned level III by cell centre over the box (V12) and computed weather keys for every box
  study cell (V10, V11) in throwaway scripts, to answer the counts; this is not T7's code and
  sets no rule.
- Compared old and new tree tiles (V4, V6), beyond the plan's list, because the box's tiles had
  been rewritten since the review the plan relies on.
- Counted cells with a share above 0 per band (V5), layer values only, to see which new bands
  carry anything in the box.
- Held V16's family-only count under the V9 hold.

## What affects the open decisions and proposals

- **M1 / M2 (held):** V16 confirms names, families and orders are in the download, so any list
  type works offline; nothing else learned, by design.
- **M4 / P1:** nothing read.
- **M6:** cite RECORD -1027 with -913 in the row; the habitat map is now on bands from an
  unmerged, unreviewed branch, which the row or a merge should settle first.
- **M7 (ruled):** tier B is all zero in the box (drop or ignore for the pilot); every new band is
  missing in Canada (102,543 cells, 0.6% of the box, all in the two Marine West Coast blocks);
  ecm_hosts is near-ubiquitous where canopy is at least 10%.
- **M8 / P10:** the deserts: 7 of 25 blocks have under 8% of cells with canopy at least 10%,
  the two largest among them; P7's forested-block score is needed, and its cut can be fixed
  from these layer counts before any presence is read.
- **P3 / P6:** two thirds of the box is outside the effort frame; a rule for it, or a
  target-group background, is needed before any background is drawn.
- **P4:** total cover's artifact stands; 57.8% of US box cells have no share at all, so how an
  undefined share enters (missing, 0, or masked) decides most of the map.
- **P9:** outputs on `/mnt/work`, streamed by tile; attribution from the tile tags (SCANFI
  included).
- **D18 / D40:** a review of `t6b-host-genera` and its merge (with D127) come before a T7 build
  that uses the new bands, or T7 states it builds on an unreviewed branch.
