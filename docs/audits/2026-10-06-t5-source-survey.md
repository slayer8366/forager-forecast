# T5 Part 1: source survey for US host-tree layers, against BIGMAP and SCANFI at the seam

Written 2026-10-06 (UTC) by the T5 coder session (writer, D38) on branch `t5-host-trees`, worktree
`~/Zynergy/forager-forecast-t5`, against `origin/t5-host-trees` at `62a0e4d` (the dispatch commit,
whose parent is main `ad64fef`; main is now `614b262` and was not merged in). Dispatch:
`docs/dispatch/2026-10-06-t5-host-trees.md`, Part 1. Started on the planner's word after T4's review
was filed (`origin/t4-review` at `fe87ec3`), relaying the owner: "Start it after T4 review is filed"
(Forager RECORD -585).

What this is: a reading of producers' pages, licence texts, metadata records, readme files and
ArcGIS service metadata. Nothing was downloaded that holds data: no raster, tile, zip or CSV body was
fetched. File sizes come from directory listings, catalogue pages and HTTP HEAD responses. No code in
`src/` or `tests/`. One local calculation (the D82 rectangle's area, with pyproj, shown in section 6)
was run and is not committed. Page copies used for the quotes were kept in the session scratchpad,
not in the repository.

Context the reader needs: forager-forecast is public with no licence chosen (D22, D62), and Forager is
not sold (D61). Licence terms below are quoted as stated. Where this report says what a term means
for this project, that is marked as a reading for the owner, not a ruling. Anything inferred is
marked inferred.

## 1. Result in one paragraph

Two findings change the picture the dispatch was written on. **First, BIGMAP itself carries a
licence statement, just not on the page T3 read.** The USDA Forest Service's own image-service item
for BIGMAP on the federal Interdepartmental Imagery Publication Platform reads "As a work of the
United States Government, these data are within the public domain of the United States.
Additionally, the U.S. Forest Service waives copyright and related rights in the work worldwide
through the CC0". The raster gateway page that D31 was based on still states no licence. Whether a
statement on a second official channel clears BIGMAP under D31 is a licence reading for the owner.
**Second, the Forest Service Research Data Archive**, which publishes TreeMap and the 2013
species basal-area maps, says that its datasets are "released under the Creative Commons CC-BY license
structure", under a data use agreement. Every US candidate with species detail is CONUS only, apart
from a 240 m Alaska basal-area set whose download page states no licence. On the Canadian side, SCANFI
cannot supply hemlock (*Tsuga*) or oak (*Quercus*) on its own, and it supplies pines (*Pinus*) only in
part. The recommendation is TreeMap 2023 for the US side, with genus share of the cell's total as the
common variable. BIGMAP via the CC0 statement is the alternative if the owner reads that statement as
clearing it. Seven items need the owner (section 8).

## 2. Candidates table

The D82 rectangle (45.5 to 49.0 N, 121 to 125 W) covers about 117,776 km², which is about 131 million
30 m pixels or about 1.88 million 250 m cells. In ESRI:102008 its bounding box is about 390 x 476 km,
which is about 206 million 30 m pixels (section 6). The sizes are for what the producer serves. Wherever the
only route is a whole-CONUS file, the size given is for that whole file.

| Candidate | Licence or terms, as quoted at source | Coverage (Alaska?) | Resolution, year | Variable | Species or genus | Access, and size for D82 |
| --- | --- | --- | --- | --- | --- | --- |
| **TreeMap 2023 CONUS** (RDS-2026-0038). TreeMap 2022 (RDS-2025-0032), 2020 (RDS-2025-0031) and 2016 (RDS-2021-0074) are the same series | Catalogue and metadata Use_Constraints: "These data were collected using funding from the U.S. Government and can be used without additional permissions or fees." Archive Conditions of Use: "Formally, Archive-published datasets are released under the Creative Commons CC-BY license structure." Data Use Agreement: citation "in the metadata of any derived data products", and "The Data User agrees to not re-distribute a modified version of the data publication and represent it as the original data publication." No CC version is named | CONUS only; metadata extent "Forested areas in the conterminous United States". **No Alaska** | 30 m, circa 2023 (2022, 2020 and 2016 also published) | A raster of imputed FIA plot identifiers plus a tree table (species, diameter, height, crown ratio, trees per acre, live or dead). Per-species quantities are not served as layers. They are computed by joining the tree table (inferred route) | Every FIA tree species on the imputed plots (inferred from "a list of tree attributes for all imputed FIA plots"). Includes *Pseudotsuga*, *Tsuga*, *Quercus* and *Pinus* wherever FIA plots carry them | One zip of the whole publication, `RDS-2026-0038.zip`, **4.87 GB**, with no subset option. The 2022 zip is 4.5 GB. The raster gateway serves 21 per-attribute rasters (basal area, forest type and others), none of them per species |
| **BIGMAP 2018** (the blocked baseline) | Gateway page (`data.fs.usda.gov/.../bigmap/index.php`): no licence. Only the Enterprise Data Disclaimer, which ends "FS published data is intended for viewing and analysis only." **IIPP image-service item** `USFS_FIA_BIGMAP_AboveGroundBiomass`, licenseInfo: "As a work of the United States Government, these data are within the public domain of the United States. Additionally, the U.S. Forest Service waives copyright and related rights in the work worldwide through the CC0". accessInformation: "USDA Forest Service, Forest Inventory and Analysis (FIA)" | CONUS only, **no Alaska** | 30 m. Landsat 8, 2014 to 2018 | Aboveground biomass, tons per acre, per species | 327 species plus a total. Includes Douglas-fir (SPCD 202), western and mountain hemlock (263, 264), Oregon white oak (815) and the western pines | Gateway: one CONUS zip per species, e.g. Douglas-fir **3.74 GB** (HEAD). IIPP: `exportImage` with a raster function per species, 30 m F32, `maxImageWidth`/`Height` 100000. For D82, about 0.5 to 0.8 GB uncompressed per layer (inferred from pixel count x 4 bytes) |
| **LEMMA GNN** (Oregon State University and USFS PNW Research Station), series GNN.2023.1 | **Not stated.** No licence, terms or copyright text on the LEMMA home, data, species, structure or about pages, or on the download site | Washington, Oregon and California. **No Alaska** | 30 m. Model years 1986 to 2021; the open download offers 2017 and 2021 | Basal area per species (`*_BA`), plus total canopy cover (`CANCOV`) and conifer and hardwood canopy cover | About 95 species. Includes `PSME_BA`, `TSHE_BA`, `TSME_BA`, `QUGA4_BA` (*Quercus garryana*) and the western pines | A request form (name, organisation, email); a link is emailed. Presets include "Washington" and "221: Washington Coast and Cascades". Up to 5.0 GB per request. The per-layer size for D82 is not shown before a request is submitted |
| **FIADB plot data** (FIA DataMart) | DataMart product page: **not stated.** FIA Spatial Data Services page: "public databases that can be downloaded and used by anyone." Coordinates: "the plot coordinate data are slightly altered (fuzzed) and some of the plot data are exchanged (swapped)", within half a mile and up to 1 mile, with 0 to 25 percent swapped. No text found that allows or forbids gridding the public data | All states, **including Alaska** | Plots, not a grid. Locations are fuzzed by up to 1 mile | A tree list per plot (species, diameter, trees per acre, biomass columns) | All FIA species | Per-state CSVs, by HEAD: `WA_TREE.csv` 334 MB, `WA_PLOT.csv` 5.4 MB, `WA_COND.csv` 11 MB, `AK_TREE.csv` 127 MB. The Oregon files were not checked |
| **Live tree species basal area, 2000 to 2009** (Wilson et al. 2013, RDS-2013-0013; BIGMAP's 250 m predecessor) | RDS: "can be used without additional permissions or fees", plus the Archive's CC-BY text above. The IIPP item `USFS_EDW_FIA_ForestAtlas_TreeSpecies_107`, which describes this dataset: "the U.S. Forest Service waives copyright and related rights in the work worldwide through the CC0" | CONUS, **no Alaska** | 250 m. MODIS, plots from 2000 to 2009 | Basal area per species | Per species. The count was not read; tags include Douglas fir, western hemlock and white oak | `RDS-2013-0013_RasterMaps_s10-s350.zip` **819 MB** (whole CONUS), plus a 30 MB data zip |
| **Individual Tree Species Parameter maps (ITSP)**, FHAAST / NIDRM | ITSP page: **not stated.** The IIPP item `USFS_EDW_FHP_TreeSpeciesMetrics_BasalArea` (30 m) adds: "The U.S. Forest Service waives copyright and related rights in the work worldwide through the CC0". The **Alaska** geodatabase on the ITSP page carries no statement on that page. Its embedded metadata was not read, since that needs the download | CONUS. **Alaska as a separate download** (`AK_by_spp_n_Totals.gdb.zip`). The 30 m IIPP service's extent reaches about 171 W to 70 N, which takes in Alaska's longitudes. Whether that service holds Alaska pixels was not determined | IIPP 30 m: "circa 2002". Downloads: 240 m, "circa 2011" (Alaska white spruce layer metadata) | Basal area and stand density index per species. Alaska also has "% of Total Basal Area" for spruces | 264 species in the atlas; the 30 m service lists 341 functions, including Douglas fir, western and mountain hemlock, Oregon white oak and `hemlock_spp` / `oak_spp` | CONUS basal-area geodatabase **553 MB**; Alaska **135 MB** (HEAD). IIPP `exportImage` 30 m U16, about 0.26 to 0.4 GB uncompressed per layer for D82 (inferred) |
| **ABoVE plant-functional-type top cover** (ORNL DAAC 2032) | Landing page: "This dataset is openly shared, without restriction, in accordance with the EOSDIS Data Use and Citation Guidance." | **Alaska and Yukon only**; no CONUS | 30 m, every five years from 1985 to 2020 | Top cover percent | **Conifer trees and broadleaf trees only**, with no genus | The whole dataset is 96.159 GB. Not relevant to D82 |
| **FIA forest type groups, Alaska** (IIPP `..._ForestTypeGroups_109_AK`) | The IIPP item: "the U.S. Forest Service waives copyright and related rights in the work worldwide through the CC0" | Alaska | MODIS 2002 to 2003. The resolution was not read. "should not be displayed at scales smaller than 1:2,000,000" | Six forest type groups (classes, not shares) | Groups, not genera | Not relevant to D82 |
| **LANDFIRE EVT** | **Not stated** on the EVT page (`landfire.gov/vegetation/evt`). The FAQ URL returned 404 | CONUS and Alaska (LF 2024, 2025 listed) | 30 m | Existing vegetation type, as classes | Classes, not genus shares | Not pursued: a class map gives no genus fraction |

Read times (UTC, 2026-10-06), with each URL:

- TreeMap 2023: https://www.fs.usda.gov/rds/archive/catalog/RDS-2026-0038 at 10:52:40, its metadata
  https://www.fs.usda.gov/rds/archive/products/RDS-2026-0038/_metadata_RDS-2026-0038.html at 10:53:21,
  and the file index at 10:53:23. TreeMap 2022: https://www.fs.usda.gov/rds/archive/catalog/RDS-2025-0032 at 10:51:53.
  Gateway: https://data.fs.usda.gov/geodata/rastergateway/treemap/ at 10:52:28.
- Archive terms: https://www.fs.usda.gov/rds/archive/dataUseInfo at 11:01:08, and
  https://www.fs.usda.gov/rds/archive/datauseinfo/open at 11:01:53.
- BIGMAP gateway: https://data.fs.usda.gov/geodata/rastergateway/bigmap/index.php at 10:52:30. The
  Douglas-fir zip HEAD was at about 10:54. BIGMAP IIPP item:
  https://imagery.geoplatform.gov/iipp/rest/services/Vegetation/USFS_FIA_BIGMAP_AboveGroundBiomass/ImageServer/info/iteminfo?f=pjson
  at 10:57:08, and the service root (`...ImageServer?f=pjson`) at 10:57:58.
- LEMMA: https://lemma.forestry.oregonstate.edu/data at 10:52:30, `/data/species-maps` and
  `/data/structure-maps` at 10:55:26, https://lemmadownload.forestry.oregonstate.edu at 10:55:27, and
  `/about` at 10:55:38.
- FIA: https://research.fs.usda.gov/programs/fia/sds at 10:54:57, and
  https://research.fs.usda.gov/products/dataandtools/fia-datamart at 10:54:59. The DOI
  https://doi.org/10.2737/RDS-2001-FIADB redirects to the DataMart's JavaScript app (10:54:37). The
  CSV HEADs were at about 10:55.
- Wilson 2013: https://www.fs.usda.gov/rds/archive/catalog/RDS-2013-0013 at 10:56:17. Its IIPP item
  `.../USFS_EDW_FIA_ForestAtlas_TreeSpecies_107/ImageServer/info/iteminfo?f=pjson` at 10:56:11.
- ITSP: https://fs.usda.gov/science-technology/data-tools-products/fhp-mapping-reporting/individual-tree-species-parameter-maps
  at 10:58:17. IIPP item `.../USFS_EDW_FHP_TreeSpeciesMetrics_BasalArea/ImageServer/info/iteminfo?f=pjson`
  at 10:58:45, and its service root at 10:59:00. The Alaska spruce layer
  https://apps.fs.usda.gov/dmsm/rest/services/FHAS_Host/Spruce/MapServer/30?f=pjson at 10:58:36. The
  zip HEADs were at about 10:58.
- ABoVE: https://daac.ornl.gov/cgi-bin/dsviewer.pl?ds_id=2032 at 10:59:52.
- Alaska forest type groups: `.../USFS_EDW_FIA_ForestAtlas_ForestTypeGroups_109_AK/ImageServer/info/iteminfo?f=pjson`
  at 10:58:50.
- LANDFIRE: https://landfire.gov/vegetation/evt at 11:00:41.

Dead ends: the data.gov API and page for "forest-health-protection-tree-species-metrics-basal-area"
returned 404 (10:58). `apps.fs.usda.gov/fsgisx01/.../RDW_FHP_TreeSpeciesMetrics` returned 403, with
"The service being requested has been migrated to IIPP" (10:58:37). One fetch of the ABoVE user guide
URL came back as a PDF with no licence text. No Alaska tree-species product at genus level was found
other than ITSP Alaska and FIADB plots.

**A correction to an earlier record, appended here and not edited there.** The 2026-09-18 RESEARCH_LOG
row on BIGMAP says "The 2018 file directory returns 403 to this client." On 2026-10-06 a HEAD request
for one 2018 species zip returned 200, with a Content-Length of 3,741,609,821. The register row and
the log row stand as written.

## 3. Against BIGMAP

| Candidate | Gains over BIGMAP | Losses against BIGMAP |
| --- | --- | --- |
| TreeMap 2023 | A stated use permission and Archive terms at source. Newer (circa 2023 against 2014 to 2018, and closer to SCANFI's 2020 and 2025 steps). A tree list allows any variable: basal area, stems, crown measures (inferred), and biomass through FIADB | Each pixel takes a whole imputed plot, so species composition at 30 m is lumpy. It should smooth at 250 m, where a cell averages about 69 pixels (inferred). No per-species layers, so a join step is needed. Whole-CONUS download only (4.87 GB) |
| LEMMA GNN | Basal area per species directly. Regional models tuned for the Pacific Northwest. Years to 2021 | **Licence not stated**, the same state as BIGMAP under D31. WA, OR and CA only. Access by personal request form |
| FIADB plots | Stated "used by anyone". Covers Alaska. The ground truth that BIGMAP, TreeMap and LEMMA are all built on | Not a grid. Fuzzing up to 1 mile and 0 to 25 percent swapping make 250 m placement impossible from public coordinates (inferred from the stated fuzz distance) |
| Wilson 2013 (250 m) | Archive terms and a CC0 statement on its IIPP item. Already at the grid's 250 m | Old (2000 to 2009, MODIS). Basal area, not biomass. CONUS only |
| ITSP | CC0 statement on its 30 m IIPP item. An Alaska set exists | Old (circa 2002 at 30 m; circa 2011 at 240 m). The Alaska set's licence is not stated on its page |
| BIGMAP via IIPP (if the owner reads the CC0 statement as clearing it) | No other dataset to set it against: 327 species as continuous predictions at 30 m, with server-side subsetting to D82 | CONUS only. Biomass, a different measure from SCANFI's crown closure (section 5) |

## 4. Against SCANFI at the seam: genera

**The host claims were checked against the repository.** EVIDENCE.md states no host trees for
*Cantharellus* or *Laetiporus*. Its fruiting-records table (`EVIDENCE.md:10-24`) and published-findings
table (`EVIDENCE.md:37-46`) are about timing, not hosts. The one host statement in the planning record
is in RESEARCH_LOG (`RESEARCH_LOG.md:41`, the 2026-09-18 row on the Saskatchewan chanterelle source): "jack pine stands,
Boreal Plain Ecozone". The dispatch's lists (Douglas-fir, hemlock and oak for *Cantharellus*; oak,
conifers and others for *Laetiporus*) are therefore **dispatch premises, unverified in this
repository**. The table below takes the dispatch's genera plus *Pinus* from the log, as given, and
answers only whether each side can supply them.

SCANFI v2's species layers, from the readme
(`https://ftp.maps.canada.ca/pub/nrcan_rncan/Forests_Foret/SCANFI/v2/_SCANFI_v2_read_me.txt`, read
11:00:09) are balsam fir, black spruce, broadleaf, Douglas-fir, jack pine, lodgepole pine, other
coniferous, ponderosa pine, tamarack, and white and red pine, each as "the actual crown closure (%)
for each species", plus total crown closure and aboveground biomass. Licence, from the dataset page
(https://open.canada.ca/data/en/dataset/07653869-f303-46c2-a04e-9ab479b73cbf, read 11:02:35):
"Open Government Licence - Canada".

| Genus | Named for | US side (any species-level candidate) | SCANFI | Both? |
| --- | --- | --- | --- | --- |
| *Pseudotsuga* | *Cantharellus* (dispatch) | Yes (Douglas-fir) | Yes, "Douglas-fir crown closure". Douglas-fir is the only *Pseudotsuga* in Canada (inferred, general knowledge), so the species layer is the genus | **Yes** |
| *Tsuga* | *Cantharellus* (dispatch) | Yes (western and mountain hemlock) | **No.** It falls inside "other coniferous" (inferred: the readme lists no hemlock and does not define that class's membership) | **No** |
| *Quercus* | *Cantharellus*, *Laetiporus* (dispatch) | Yes (Oregon white oak and others) | **No.** It falls inside the single "broadleaf" class (inferred, as above) | **No** |
| *Pinus* | *Cantharellus* (RESEARCH_LOG: jack pine) | Yes | **Partly:** jack, lodgepole, ponderosa, and white and red pine. Western white pine, whitebark and limber pine are not listed and presumably sit in "other coniferous" (inferred) | Partly. At the BC and WA seam, lodgepole and ponderosa are in both, and western white pine is in the US only (inferred) |
| All conifers, all broadleaf | Fallback for any host list | Yes, by summing species | Yes, by summing the conifer classes, and the broadleaf class | **Yes**, but coarse |

## 5. The variable both sides can be converted to

What each side measures: SCANFI, crown closure percent per species class, with total crown closure.
BIGMAP, biomass. TreeMap, a tree list (so basal area, biomass through FIADB, or crown measures,
computed). LEMMA, Wilson 2013 and ITSP, basal area.

**Proposal: genus fraction = the genus's share of the cell's total**, a number from 0 to 1, with a
source flag. Each side keeps the measure it has. Canada: the sum of the genus's crown closure divided
by total crown closure (`att_closure`). US: the sum of the genus's basal area divided by total live
basal area, from TreeMap's tree table. That basal area is BA = 0.005454 x DBH² x trees per acre, in
ft²/acre per tree, which is the standard FIA expression (inferred: it is not quoted from a TreeMap
page). Both are then regridded to the 250 m master grid.

Why not convert SCANFI to biomass to match BIGMAP: the SCANFI readme's own route is "Species-level
aboveground biomass can still be approximated by scaling pixel-level biomass by the relative species
crown closure." Under that route, a species' share of biomass equals its share of crown closure
exactly, because the total biomass cancels (derived from the readme's sentence). Converting SCANFI to
biomass therefore changes no fraction, and gives no common ground beyond what crown closure already
gives.

What stays unharmonised: a crown-closure share and a basal-area or biomass share differ for the
same stand. Large-stemmed Douglas-fir carries more basal area per unit of crown than broadleaf
species (inferred, not measured here). That difference is part of what the Part 2 transects will
measure at the border. An alternative that matches SCANFI's measure on the US side is crown-cover
share from TreeMap's tree list through crown-width equations. TreeMap's producer already computes
plot cover this way ("We calculated plot-level tree cover and height using the StrClass keyword in
the Forest Vegetation Simulator", TreeMap 2023 metadata, Process_Description). Doing it per species is
the same calculation on a subset (inferred). It costs more code and equations per species, so it is
offered as an owner choice and not as the default.

## 6. Arithmetic behind the sizes

The calculation was run in this worktree with `uv run --frozen python` and pyproj; nothing was written
to the repository. Geodesic area of the D82 rectangle on WGS84: 117,776 km². At 30 m that is 130.9
million pixels, 523 MB as float32 and 262 MB as uint16, uncompressed. At 250 m it is 1,884,424 cells.
The ESRI:102008 bounding box of the rectangle's edges is 390 x 476 km, which is 206.3 million 30 m
pixels. A served export in that projection is between the two pixel counts, depending on the request
CRS (inferred).

## 7. Recommendation

**Primary: TreeMap 2023** for the US side, built as basal-area genus share and paired with SCANFI's
crown-closure genus share for 2020 or 2025 (the step that matches TreeMap's year is the owner's pick
or Part 2's proposal). Reasons:

1. It has a use statement at source ("can be used without additional permissions or fees") and the
   Archive's CC-BY text. D31's blocking test is "licence not stated at source", which this does not
   meet (whether the Archive's terms suit a public repository and the app is the owner's reading,
   item 2 below).
2. It is the newest US source (circa 2023).
3. The tree list keeps the variable choice open: basal area now, and crown cover later if the
   transects show the measure difference matters.
4. The tree list supplies every genus the dispatch names on the US side.

**Alternative: BIGMAP via the IIPP item**, if the owner reads its CC0 statement as clearing BIGMAP. It
is technically the strongest US layer (per-species continuous predictions at 30 m, with server-side
subsetting), but it measures biomass and is 2014 to 2018.

**Not recommended:** LEMMA (licence not stated, which leaves it in the same blocked state as BIGMAP
was). FIADB plots on their own (no 250 m placement). Wilson 2013 and ITSP for the main layer (both a
decade or more older). ABoVE, forest type groups and LANDFIRE (no genus shares).

Neither choice fixes the seam for *Tsuga* and *Quercus*: SCANFI cannot supply them (section 4).

## 8. For the owner to decide

1. **BIGMAP's licence reading.** The USDA FS's IIPP item for BIGMAP states public domain plus a CC0
   waiver. The raster gateway page states none, and its disclaimer ends "FS published data is
   intended for viewing and analysis only." Does a statement on the producer's image-service item
   clear BIGMAP under D31? If yes, BIGMAP becomes a candidate again and D31's blocked state for it
   needs a new row (it is not edited here, per D41).
2. **The Archive's terms for TreeMap.** "Creative Commons CC-BY license structure" with no version
   named, attribution in derived products' metadata, and no redistribution of a modified copy
   represented as the original. How these sit with a public repository that has no licence (D22,
   D62) and an app that is not sold (D61) is the owner's reading. This report does not judge it.
3. **Which US source**: TreeMap 2023 (recommended) or BIGMAP via IIPP (if item 1 is yes).
4. **Genera SCANFI cannot supply.** *Tsuga* and *Quercus* have no class of their own in SCANFI, and
   *Pinus* is partial. Options: (a) model those hosts at conifer and broadleaf level on both sides;
   (b) keep the genus on the US side and set it to missing, with the source flag, on the Canadian
   side; (c) look for a BC provincial layer, which is a new survey with its own licence check. The
   dispatch's host lists also need a source, since EVIDENCE.md has none.
5. **The common variable.** Genus share of the total, with crown closure in Canada and basal area in
   the US (proposed). Or crown-cover share on both sides, which needs TreeMap per-species crown
   computation and is more work.
6. **Alaska.** No cleared genus-level layer covers it. ITSP Alaska (240 m, circa 2011) is the only
   species-level grid found, and its page states no licence. Keep Alaska masked (D31 as it stands),
   or ask the Forest Service about ITSP Alaska's terms (a person-only item).
7. **LEMMA**, if wanted for comparison: its licence is not stated, so it would need the producer
   asked (a person-only item) and a request form under the owner's name.

## 9. Not done or not verified

- No data was opened, so no candidate's values, coverage at the seam, or no-data handling was
  checked.
- TreeMap's tree-table columns are taken from the RDS abstract and file index, not from the CSV.
  The `_variable_descriptions.csv` sits inside the 4.87 GB zip and was not read.
- The ITSP Alaska geodatabase's embedded licence metadata, the LEMMA download sizes, and the
  resolution of the Alaska forest type groups were not read.
- The Google Earth Engine copies of TreeMap were not checked for their own terms.
- The FIADB user guide was not searched for a use statement.
- Host-tree evidence for *Cantharellus* and *Laetiporus* was not researched. Only the repository was
  checked, as the dispatch asked.
- The inferred items are marked where they appear: species membership of SCANFI's "other coniferous"
  and "broadleaf", Douglas-fir as the only Canadian *Pseudotsuga*, per-pixel lumpiness in TreeMap,
  export sizes, the basal-area formula, and per-species crown cover from FVS.
