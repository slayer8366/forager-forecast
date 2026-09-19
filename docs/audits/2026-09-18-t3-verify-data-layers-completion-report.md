# T3 completion report: the from-memory data layers, verified

**Date:** 2026-09-18
**Type:** completion report for docs/dispatch/2026-09-18-t3-verify-data-layers.md.
**Base:** main f96d557, on branch t3-verify-data-layers. Web sources opened 2026-09-18 from
this machine; commands run in this worktree with the locked uv environment (pyproj 3.8.0,
rasterio 1.5.1).
**Supersedes:** none.

Every claim below names a URL opened today, a file and line, or a command whose output is
quoted, or is marked inferred. Flags: verified means the source was opened today; abstract only
means only an abstract or catalogue record was readable; from memory means unchecked.

---

## The short version

All 17 "To verify" items in RESEARCH_LOG.md and every register row with a Memory flag or a
"Not checked" cell were taken to a primary source or logged as a dead end. Twelve items are
ticked. Five stay unticked, each with its dead end logged: POLARIS and BIGMAP have no licence
statement anywhere at their source; no open North American fungal survey with true absences was
found; no North American equivalent of ForestTemp exists; and Tsunoda et al. 2025 is located
but its abstract is behind a 403.

Nothing that was remembered turned out wrong in a way that changes the plan. Two corrections
of substance: BIGMAP covers the coterminous US only, so Alaska has no host-tree layer from it;
and NBAC's 10 ha minimum was removed in 2016, so it carries small fires. ESRI:102008 is accepted
by both PROJ and GDAL as installed, with the parameters quoted below. Open-Meteo's terms say
the free tier is non-commercial in plain words and the pricing page ticks commercial use only
on paid plans; that is an owner item under D22, and no layer was ruled in or out here.

## What was checked

### Confirmed as remembered

Each line: the register or log claim, then the source opened.

- **MTBS is 30 m from 1984, CONUS, Alaska, Hawaii, Puerto Rico; fires of 1,000 acres or more
  in the West and 500 or more in the East.** https://www.mtbs.gov/project-overview and
  https://www.mtbs.gov/faqs. Verified. Latency, not previously recorded: "releases new
  geospatial fire data approximately each quarter" (faqs).
- **NBAC is Canada's annual burned-area composite.** Metadata PDF
  NBAC_1972to2025_20260513_shp_metadata.pdf from https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/,
  read from /tmp and not committed. Verified. Vector polygons, 1972 to 2025, "no access and
  use limitations for this item", update frequency "as needed".
- **NALCMS is 30 m North American land cover.** https://www.cec.org/north-american-environmental-atlas/land-cover-30m-2020/
  and the 2015 page. Verified. 19 classes; epochs 2010, 2015, 2020 and two change layers.
- **USGS 3DEP is bare-earth terrain for the US.** https://www.usgs.gov/3d-elevation-program/about-3dep-products-services.
  Verified. Seamless 1/3 arc-second over the 48 states, Alaska, Hawaii and territories;
  1 arc-second CONUS and Alaska; 1 m where lidar exists; "free of charge and without use
  restrictions".
- **POLARIS is probabilistic 30 m soil for the US.** http://hydrology.cee.duke.edu/POLARIS/PROPERTIES/v1.0/Readme.
  Verified for resolution and variables: 1 arc-second, CONUS, 13 variables including pH and
  organic matter, six depths, mean, mode, p5, p50, p95.
- **CEC ecoregions come in levels I to III as polygons.** https://www.cec.org/north-american-environmental-atlas/terrestrial-ecoregions-level-iii/
  and its metadata.zip. Verified. 15, 50 and 182 regions; ed. 2.0, 2021; CC BY 4.0.
- **ESRI:102008 is North America Albers equal-area.** PROJ's own database through pyproj and
  GDAL through rasterio, command and output under Evidence. Verified.
- **BIGMAP is 30 m.** https://data.fs.usda.gov/geodata/rastergateway/bigmap/index.php:
  "327 individual tree species at a 30 meter pixel spatial resolution". Verified.
- **SCANFI version 2 exists.** https://open.canada.ca/data/en/dataset/07653869-f303-46c2-a04e-9ab479b73cbf
  and its readme. Verified. Published 2026-01-01, 30 m, 1985 to 2025 in five-year steps, OGL
  Canada; species layers are now crown closure percent per species.
- **Open-Meteo's archive serves ERA5-Land at 0.1 degree with a 5-day delay.**
  https://open-meteo.com/en/docs/historical-weather-api. Verified. Also: the default "Best
  Match combines IFS HRES, ERA5 and ERA5-Land", which agrees with D19.
- **Open-Meteo soil variables cover North America.** 16 requests under models=era5_seamless,
  counts under Evidence. Verified.
- **The Saskatchewan chanterelle result.** Ivanochko, Svendsen, Hrycan and Tanino 2021,
  Canadian Journal of Plant Science 101(6):853-870, doi 10.1139/cjps-2021-0136. Abstract only
  (Crossref and Semantic Scholar records; publisher page 403). The abstract matches
  EVIDENCE.md line 40: GDD base 5 C, minimum 500 plus or minus 70, with 50 to 100 mm of soil
  moisture or rain, 6 to 13 weeks before first appearance, from buyer purchase data.
- **CaPA HRDPA licence "to confirm".** https://open.canada.ca/data/en/dataset/eff69d42-ce81-4672-867f-cc3baaf4157a.
  Verified: Open Government Licence - Canada.
- **MRMS access path.** https://mrms.ncep.noaa.gov/2D/ (GRIB2, rolling) and
  https://registry.opendata.aws/noaa-mrms-pds/ (S3, NODD, "open to the public and can be used
  as desired"). Verified.
- **SSURGO is finer soil for the US.** https://catalog.data.gov/dataset/soil-survey-geographic-database-ssurgo.
  Verified from the catalogue record: annual updates, US public domain. The NRCS page timed
  out twice, so the record is the catalogue's, not NRCS's own page.
- **iNaturalist does not auto-obscure any target group.** Taxa API, every active species of
  Cantharellus (165), Craterellus (84), Laetiporus (18), Morchella (80), Boletus (131) and
  Tricholoma (306): no conservation status with a geoprivacy of obscured or private, at any
  place. Verified. So obscured target records are user-chosen, which bears on I3 in IDEAS.md.
- **Buntgen et al. 2012 windows.** Open-access PDF at
  https://www.dora.lib4ri.ch/wsl/dload/wsl:3966/PDF/view. Verified. Figure 3: June-July
  counts against June precipitation, August-September counts against August precipitation,
  October-November counts against September precipitation; week of appearance against August
  maximum temperature. These are correlation maps over 1975 to 2006, not a fitted forecast
  model, which is consistent with D4.
- **Radar coverage gaps in the mountain West.** NOAA 2019, "Study: Gaps in NEXRAD Radar
  Coverage", https://repository.library.noaa.gov/view/noaa/25911/noaa_25911_DS1.pdf. Verified.
  Figure B.1 maps coverage at 4, 6 and 10 kft AGL: "most of the radar coverage gaps are in the
  intermountain western US"; Appendix K: "both central and coastal Oregon have limited to no
  radar coverage below 10,000 ft AGL".

### Corrected (old value, new value, source)

- **BIGMAP coverage.** Old: "US" (DATA_REGISTER.md, BIGMAP row, Coverage). New: coterminous
  United States only; no Alaska. Source: the BIGMAP page quoted above.
- **NBAC minimum fire size.** Old: not recorded, and the dispatch's memory grouped NBAC with
  MTBS's size thresholds. New: the 10 ha minimum filter for agency burns was removed in 2016
  (metadata lineage, "removed the 10 ha minimum size filter for agency burns"), so NBAC has no
  size floor from that year. Source: the NBAC metadata PDF.
- **POLARIS resolution wording.** Old: "Not checked". New: 1 arc-second, which is "about 30
  meters", not exactly 30 m; the tiles are 1x1 degree GeoTIFFs. Source: the POLARIS Readme.
- **Open-Meteo licence wording.** Old: "Free tier is non-commercial. Terms to confirm". New,
  confirmed and sharpened: "You may only use the free API services for non-commercial
  purposes", with "apps that have subscriptions or display advertisements" named as
  commercial; data under CC BY 4.0. Source: https://open-meteo.com/en/terms.
- **SCANFI species layer meaning.** Old (register, Latency cell): "A version 2 exists". New:
  in v2 the species layers are crown closure percent per species, not a share of total
  closure, and the readme says the product is "optimized for regional to national-scale
  analyses, not local plot-level validation". Source: the v2 readme.

### Could not be verified (with what was tried)

- **POLARIS licence.** Tried: the Duke landing page (404, certificate error), the data server
  and Readme (no licence text), the WRR 2019 paper (closed access, OpenAlex license field
  empty). Nothing names a licence. Left unticked.
- **BIGMAP licence.** Tried: the BIGMAP page (only the USDA FS Enterprise Data Disclaimer,
  which disclaims warranty and says nothing about reuse), the 2018 file directory (403 to
  this client). Left unticked.
- **MTBS licence by name.** The site says "freely available to the public" and names no
  licence. The USGS copyright page says "USGS-authored or produced data and information are
  considered to be in the U.S. Public Domain". MTBS is a USGS and USFS program, so this is
  inferred, not stated by MTBS itself. Ticked for the five facts, licence marked as inferred.
- **NBAC licence by name.** Metadata says "no access and use limitations"; the datamart page
  that would carry the licence needs JavaScript and returned only an app shell to curl and to
  WebFetch. Ticked with that caveat.
- **Tsunoda et al. 2025 window lengths.** Tried: three searches, Crossref (no abstract),
  OpenAlex (closed, no abstract), the DOI resolver (leads to a ScienceDirect page that returns
  403), the author's researchmap profile (title only). Located as Fungal Ecology 75:101415,
  doi 10.1016/j.funeco.2025.101415. Window lengths still unknown. Left unticked.
- **Structured fungal surveys with true absences in North America.** Tried: two searches,
  FunDiS (occurrence only), Ratz et al. 2026 Molecular Ecology (31 plots, no absences
  recorded, data on iNaturalist and Zenodo), PNW-GTR-576 and Dunham et al. 2006 (Oregon
  chanterelle plots with counts every two weeks, 1986 to 1997, published as papers, no
  dataset). Left unticked.
- **A North American ForestTemp.** Tried: two searches. Nearest product is Lembrechts et al.
  2022 global soil bioclimatic layers at about 1 km, CC BY 4.0 on Zenodo record 7134169; that
  is soil temperature, not under-canopy air. Left unticked.
- **A Cascades-specific radar blockage evaluation.** The NOAA 2019 study covers CONUS and
  names Oregon; McRoberts and Nielsen-Gammon 2017 (J. Atmos. Oceanic Technol. 34:1407) detect
  blockage from climatology but apply it to the central and eastern US only; Kucera et al.
  2005 (doi 10.1016/j.cageo.2005.06.024) was found by title and not opened. Ticked on the
  strength of the NOAA coverage map, with this gap stated.
- **Open-Meteo prices.** The pricing page prints tiers and limits but no prices; they appear
  only in checkout. Not pursued.
- **gSSURGO raster resolution.** Not opened. SSURGO's own record was enough for the row.

## What landed

| Commit | Change |
|---|---|
| 9f63927 | RESEARCH_LOG.md: 21 dated rows inserted under the log header, 12 items ticked, 5 left unticked with a note; DATA_REGISTER.md: verified values appended inside 31 cells across 12 rows, nothing overwritten |
| the commit that adds this file | This report |
| the commit after it | One row in docs/audits/README.md, one session log row in START_HERE.md, T3 status cell in TASKS.md |

The last two hashes are in the hand-back message, since a file cannot quote the commit that
adds it.

Append-only check on the register, run before committing: every changed row still has seven
cells, and every changed cell begins with its previous text. The script and its output:

```
register rows changed: 12 | cells changed: 31 | cells that are not a prefix-preserving append: 0
log: old rows 11 all still present: True | new rows 21
```

A first pass of the register edit failed this check: appending to the last column had moved
the row's closing pipe into the middle of the row on nine rows. The check caught it, the file
was restored from HEAD and the edit redone; the numbers above are from the second pass.

## Evidence

### ESRI:102008 through PROJ (pyproj) and GDAL (rasterio)

Command:

```
uv run python -c "from pyproj import CRS; c=CRS.from_user_input('ESRI:102008'); print(c.to_wkt(pretty=True)); print(c.to_proj4()); print(c.to_authority())"
```

Output, with the USAGE block's state list elided:

```
pyproj 3.8.0 PROJ 9.8.1
PROJCRS["North_America_Albers_Equal_Area_Conic",
    BASEGEOGCRS["NAD83",
        DATUM["North American Datum 1983",
            ELLIPSOID["GRS 1980",6378137,298.257222101,
                LENGTHUNIT["metre",1]]],
        PRIMEM["Greenwich",0,
            ANGLEUNIT["degree",0.0174532925199433]],
        ID["EPSG",4269]],
    CONVERSION["North_America_Albers_Equal_Area_Conic",
        METHOD["Albers Equal Area",
            ID["EPSG",9822]],
        PARAMETER["Latitude of false origin",40, ... ID["EPSG",8821]],
        PARAMETER["Longitude of false origin",-96, ... ID["EPSG",8822]],
        PARAMETER["Latitude of 1st standard parallel",20, ... ID["EPSG",8823]],
        PARAMETER["Latitude of 2nd standard parallel",60, ... ID["EPSG",8824]],
        PARAMETER["Easting at false origin",0, LENGTHUNIT["metre",1], ID["EPSG",8826]],
        PARAMETER["Northing at false origin",0, LENGTHUNIT["metre",1], ID["EPSG",8827]]],
    CS[Cartesian,2],
        AXIS["(E)",east, ORDER[1], LENGTHUNIT["metre",1]],
        AXIS["(N)",north, ORDER[2], LENGTHUNIT["metre",1]],
    USAGE[
        SCOPE["Not known."],
        AREA["North America - onshore and offshore: Canada - ...; United States (USA) - ..."],
        BBOX[23.81,-172.54,86.46,-47.74]],
    ID["ESRI",102008]]
PROJ4: +proj=aea +lat_0=40 +lon_0=-96 +lat_1=20 +lat_2=60 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs +type=crs
authority: ('ESRI', '102008')
```

Through rasterio:

```
uv run python -c "import rasterio; from rasterio.crs import CRS; c=CRS.from_user_input('ESRI:102008'); print(rasterio.__gdal_version__); print(c.to_proj4()); print(c.to_authority()); print(c.is_projected, c.linear_units)"
```

```
rasterio 1.5.1 GDAL 3.12.4
to_proj4: +proj=aea +lat_0=40 +lon_0=-96 +lat_1=20 +lat_2=60 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs=True
to_authority: ('ESRI', '102008')
is_projected: True linear_units: metre
```

Answer to dispatch item 5: both installed libraries accept the code, so no substitute
definition string is needed. The parameters, from PROJ's database (which carries Esri's
definition under the ESRI authority): Albers Equal Area, latitude of origin 40, central
meridian -96, standard parallels 20 and 60, false easting and northing 0, datum NAD83 on the
GRS 1980 ellipsoid, units metres. The PROJ string above is the equivalent if a tool ever
lacks the ESRI table. pyproj printed its standard warning that a PROJ string loses
information relative to WKT; the WKT is the definition to store.

Esri's own page for the code was not opened; PROJ's database entry is the definition
that the pipeline will actually use, and the dispatch accepts either.

### Open-Meteo, models=era5_seamless, soil variables across North America

Request shape, one per point, 2024-09-01 to 2024-09-10, timezone UTC:

```
https://archive-api.open-meteo.com/v1/archive?latitude=LAT&longitude=LON&start_date=2024-09-01&end_date=2024-09-10&daily=temperature_2m_mean,precipitation_sum&hourly=soil_temperature_0_to_7cm,soil_moisture_0_to_7cm&models=era5_seamless&timezone=UTC
```

Counts are non-null over returned, then the soil moisture range in m3/m3:

```
Fairbanks_AK     elev=155.0  temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.348..0.376
Anchorage_AK     elev=28.0   temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.325..0.371
Whitehorse_YT    elev=773.0  temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.447..0.502
Yellowknife_NT   elev=200.0  temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.201..0.319
Churchill_MB     elev=0.0    temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.232..0.290
Iqaluit_NU       elev=0.0    temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.221..0.244
Victoria_BC      elev=0.0    temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.139..0.206
CentralBC        elev=716.0  temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.240..0.345
NW_Ontario       elev=461.0  temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.181..0.304
Montreal_QC      elev=175.0  temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.363..0.423
Halifax_NS       elev=41.0   temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.149..0.268
Denver_CO        elev=1596.0 temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.119..0.135
Austin_TX        elev=189.0  temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.272..0.520
Miami_FL         elev=6.0    temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.181..0.358
MexicoCity_MX    elev=2230.0 temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.383..0.430
Honolulu_HI      elev=0.0    temp 10/10 precip 10/10 soilT 240/240 soilM 240/240 soilM 0.135..0.212
```

Observed, not verified against another source: the host returned an empty body or the text
"Unexpected error while streaming data: timeoutReached" on the first attempt for seven of the
points and Yellowknife needed four attempts; each eventually succeeded. Three coastal points
report grid elevation 0.0, which suggests the 0.1 degree cell chosen is partly sea; the soil
values there are still populated. Whether those values are land values is not something this
check can tell, and T1 or T4 should look at the land-sea mask before using coastal cells. The
Fairbanks and Whitehorse soil moisture values (0.35 to 0.50) are plausible for September but
were not compared with any station.

Scope of this check: 16 points, one 10-day window in September 2024. It shows the variables
are served, not that they are complete over 1950 to 2025. T0b's section 5 already showed
era5_seamless and era5_land agree on temperature and soil at one point (T0b report, "Evidence").

### Open-Meteo terms, verbatim from https://open-meteo.com/en/terms

> Non-Commercial Use. By using the Free API for non-commercial use you agree to following
> terms: Less than 10'000 API calls per day, 5'000 per hour and 600 per minute. You may only
> use the free API services for non-commercial purposes. You accept to the CC-BY 4.0 licence,
> as specified in the licence conditions. [...] the following examples are considered
> commercial use: Operating websites or apps that have subscriptions or display
> advertisements. Integrating our service into commercial products or promotional activities.
> Conducting undisclosed research at commercial entities.

From https://open-meteo.com/en/pricing: "Commercial use" is a cross for Free / Open-Access and
a tick for API Standard, Professional and Enterprise; "The free API is for non-commercial use,
rate-limited to 10,000 calls/day, and carries no uptime guarantee. The customer API runs on
dedicated servers, has no daily rate limit, and includes a commercial use licence." Prices are
not printed on the page.

### iNaturalist taxon geoprivacy, taxa API, 2026-09-18

```
Cantharellus  genus 47348  species returned 165 of 165  species with an obscuring status: 0
Craterellus   genus 48611  species returned 84 of 84    species with an obscuring status: 0
Laetiporus    genus 48431  species returned 18 of 18    species with an obscuring status: 0
Morchella     genus 56830  species returned 80 of 80    species with an obscuring status: 0
Boletus       genus 48703  species returned 131 of 131  species with an obscuring status: 0
Tricholoma    genus 62484  species returned 306 of 306  species with an obscuring status: 0 (two pages)
```

Genus-level conservation_statuses were also empty for all six. This is the taxa endpoint's
view of statuses, which includes place-specific statuses; it is not a check of individual
observations. Counts used the API for spot checks only, which SPEC.md Constraints allows.

## Conventions line

Followed: append beside, never overwrite (register cells and log rows, checked by the
append-only script above); newest first in the log; the three flags on every fact; no em
dashes (grep count 0 on both files and this report); "sighting chance" only, and the phrase
the reviewer searches for appears nowhere in the three changed files (grep count 0); no bulk
data, nothing over 1 MB (the NBAC and radar PDFs were read from /tmp and not committed);
report shape from the T0b completion report. Not followed: none known.

## Decisions taken here, and what was rejected

- **Ticking rule.** An item is ticked only when every fact it names was read at a primary
  source today. POLARIS and BIGMAP stay unticked because their licence is not stated at
  source, even though resolution and variables are verified. Rejected: ticking on the strength
  of the resolution alone, which would hide the licence gap.
- **Government catalogue records as primary for SSURGO.** The NRCS page timed out twice, so
  the data.gov record, which NRCS publishes, was used and the substitution is stated in the
  cell. Rejected: leaving the row secondhand for a page that would not load.
- **Crossref and Semantic Scholar records for the Saskatchewan paper.** The publisher page
  returns 403. The abstract is identical in both records and matches the EVIDENCE.md row, so
  it is recorded as abstract only. Rejected: quoting the search engine's summary.
- **Points, not a grid, for the Open-Meteo check.** 16 points chosen to include Alaska, the
  three northern territories, Hudson Bay, both coasts, the interior, Mexico City and Hawaii.
  Rejected: running the script's section 5, which tests one point and the model comparison T0b
  already reported.
- **PDFs read in /tmp.** Both NOAA PDFs and the NBAC metadata are over 1 MB and were not
  copied into the tree. The text extracted was read, not just the abstract, where the finding
  depends on a figure or appendix.
- **No new register rows and no removals**, per the dispatch. The Lembrechts soil temperature
  product and the NOAA radar study are in the log only.

## Deviations from the dispatch

- None on scope. One from the launching message, which is not the dispatch: it suggested
  running the verify script's section 5; direct requests were used instead, as described above,
  because section 5 tests one point and by-model agreement rather than continental coverage.
- The dispatch's "State this was written against" says "six rows are flagged Memory". The
  register at f96d557 has six Memory rows (MTBS and NBAC, NALCMS, USGS 3DEP, POLARIS, CEC
  ecoregions, ESRI:102008) and five more rows with a "Not checked" or "To confirm" cell (MRMS,
  CaPA, BIGMAP, SSURGO, and the Open-Meteo licence). All eleven were handled, plus SCANFI's
  version 2 note. The premise held.

## Owner items

- **Open-Meteo free tier is non-commercial by its terms**, quoted above. If the tool is
  commercial, training and serving on the free archive endpoint is outside those terms and a
  paid plan (customer-api.open-meteo.com, unlimited daily calls) is the path the vendor names.
  The archive data itself is CC BY 4.0. D22 leaves this open; nothing was ruled in or out.
- **POLARIS has no licence at source.** If it is wanted for T4 or later, someone has to ask
  the Chaney lab or drop it in favour of SoilGrids (CC BY 4.0) and SSURGO (public domain).
- **BIGMAP has no licence at source.** A US federal product, so public domain is the likely
  answer, but the page does not say so. Same choice as POLARIS.
- **BIGMAP stops at the coterminous US.** Alaska has no host-tree layer in the register.
  SPEC.md already masks the Arctic; whether Alaska outside the Arctic is masked too is a
  question T5 will hit.
- **Lembrechts et al. 2022 soil temperature layers** are CC BY 4.0 and global at 1 km. Whether
  a soil-temperature offset is worth a register row, given ERA5-Land already carries soil
  temperature, is a modelling question for T8, not decided here.

## Not checked

- Esri's own web page for 102008; PROJ's table was taken as the definition.
- Open-Meteo prices, which are only shown in checkout.
- The MRMS specification slides linked in the register (ROC 2016 PDF); only the access path
  and licence were new today.
- gSSURGO raster resolution and the NRCS page itself.
- Whether the era5_seamless soil values at coastal cells with elevation 0.0 are land values.
- Any time span for the soil variables beyond the ten September 2024 days requested.
- The Kucera et al. 2005 beam-blockage paper, found by title only.
- Tsunoda et al. 2025 beyond its bibliographic record.
- Whether iNaturalist applies geoprivacy through a route other than conservation statuses on
  the taxa endpoint; the help article describes only that route.
- The three PDFs read from /tmp were deleted with the temporary directory; nothing from them
  is in the tree except the quotations above.
