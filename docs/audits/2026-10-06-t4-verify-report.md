# T4 master grid: verify-first report

Answers the "Verify first, report by message" section of `docs/dispatch/2026-10-06-t4-master-grid.md`.
Written 2026-10-06 (UTC) by the coder session on the credentials machine (D38), on branch
`t4-master-grid` at `d1c0cce`, worktree `~/Zynergy/forager-forecast-t4`. **Nothing is built and no
SoilGrids data has been fetched.** Two of the dispatch's stops are met (section 9): depth and
statistic are decided by no row, and "western Washington" has no definition that avoids a choice.
No GBIF, Climate Data Store or Open-Meteo request. No secret appears here.

Where this report says "read", the page or file was opened in this session. "Observed" means a
command ran and its output is quoted. "Inferred" is marked as such. Web pages were fetched with
`curl` on 2026-10-06 and reduced to text in `/tmp/claude-1000/t4/` (not committed); every quote below
is copied from that text.

## 1. Base

- `git fetch origin`; `origin/main` = `ad64fefaa5c0`. Unmoved.
- `origin/t4-master-grid` = `HEAD` = `d1c0cce`, one commit over main (the dispatch).
- Suite before any change (observed): `213 passed`, from **117 test functions**
  (`git grep -c '^def test_' -- tests`, summed; no indented test defs). `ruff check` clean,
  `ruff format --check`: "133 files already formatted".

## 2. Cites

| Dispatch cite | Status |
|---|---|
| TASKS.md T4 block "about :49-53" | Confirmed, lines 49 to 53, wording as quoted |
| T3 is done (TASKS.md, T3 row) | Confirmed, TASKS.md:13. T3's review is filed (`docs/audits/2026-09-18-t3-review.md`), so D18's "prerequisite's review is filed" holds |
| D8 | Confirmed, DECISIONS.md:67 |
| D6 | Confirmed, DECISIONS.md:69 |
| SPEC "static habitat layers on a 250 m equal-area grid", about :15 | Confirmed, SPEC.md:15-16 (sentence wraps) |
| SPEC "Tiles stop at zoom 9 ... 216 m per pixel", about :48 | Confirmed, SPEC.md:48. Arithmetic re-derived: 2πa/256/2^9 = 305.748 m at the equator, × cos 45° = 216.2 m |
| R8 and D12, about SPEC :78 | Confirmed, R8 at SPEC.md:78-80; D12 at DECISIONS.md:63 |
| D58 | Confirmed, DECISIONS.md:17, three terms as quoted |
| DATA_REGISTER SoilGrids row | Confirmed, DATA_REGISTER.md:15: "Soil pH, carbon, texture, nitrogen, with 90% intervals", Global, 250 m, CC BY 4.0, Verified. Re-checked at source today: "The SoilGrids maps are publicly available under the CC-BY 4.0 License" (docs.isric.org/globaldata/soilgrids/) |
| D52 (request stored beside the data) | Confirmed, DECISIONS.md:23. It is written for climate pulls; applied here by analogy as the dispatch says |
| D18, D38, D40, D41, D36 | Confirmed at DECISIONS.md:57, :37, :35, :34, :39 |
| `pyproject.toml:11-13`, rasterio bundles GDAL 3.12.4, bindings not installed | Confirmed (the comment runs 10-13). Observed: `rasterio 1.5.1`, `__gdal_version__` `3.12.4`; no `osgeo` in the venv |
| "CLAUDE.md in the Forager repo applies here as well" | Noted; the dispatch's own statement, not a row |

One finding, not a cite: the whole of `data/` is gitignored (`.gitignore:6`, observed with
`git check-ignore -v data/t4/x.tif data/t4/request.json`). So "the request stored beside the data"
would not be committed. Proposal in section 4.7.

## 3. The master grid (the main decision; proposal)

- **Lattice origin: the projection's own false origin, (0, 0) in ESRI:102008.** Cell edges sit at
  integer multiples of 250 m on both axes. Reason: it needs no extent to be chosen, so it cannot
  change when a later layer widens the area, and every layer snaps by `floor(coord / 250)`. ESRI:102008
  has false easting and northing 0 (DATA_REGISTER.md:26), so (0, 0) is lon -96, lat 40.
- **Cell index: `col = floor(x / 250)`, `row = floor(y / 250)`**, both signed integers, row
  increasing northward. A cell covers `[col*250, (col+1)*250) × [row*250, (row+1)*250)`. A point on
  an edge goes to the cell east or north of it, the same direction as D63's tie rule (toward +∞).
- **Cell id: one unsigned 32-bit integer, `((row + 32768) << 16) | (col + 32768)`**, valid for
  |x| and |y| under 8,192 km. Observed extremes in ESRI:102008: Kure (Hawaii) x -6,847 km, Attu
  -5,001 km, Panama-Colombia y -3,447 km, Cape Columbia y 4,451 km, east Greenland 2,630 / 5,473 km.
  All inside. Outside the range the id function raises, it never wraps. Alternative: keep `(col,
  row)` as the key and no scalar id (simpler, but a table join then needs two columns).
- **Extent rule for any raster on the grid:** its bounds snap outward to the 250 m lattice
  (`floor` the minimum, `ceil` the maximum); pixel rows run north to south as rasters do, and
  `row = top_row - 1 - raster_row` converts. No continental extent is fixed by T4; T10 fixes one when
  it needs a nightly frame, and the ids do not depend on it.
- **Datum step, to keep ids stable across runs (proposal, implementer-level):** ESRI:102008 is NAD83,
  sources are WGS84. Observed: PROJ 9.8.1 offers several NAD83-to-WGS84 operations, some needing
  grids that are unavailable offline. The code pins one, the null "NAD83 to WGS 84 (1)" (EPSG:1188),
  with `PROJ_NETWORK=OFF`, so a run with network grids cannot assign a different cell. The shift it
  ignores is metres against 250 m cells. pyproj and rasterio both carry PROJ 9.8.1 and EPSG v12.029
  (observed in each `proj.db`).

## 4. SoilGrids choices

### 4.1 Access route (proposal: WebDAV VRT read through GDAL `/vsicurl/`, native projection)

- ISRIC lists three routes (read, docs.isric.org/globaldata/soilgrids/ and `SoilGrids_faqs_02.html`):
  WMS "for visualisation", WCS "best way to obtain a subset of a map and use SoilGrids as input to
  other modelling pipelines", WebDAV "download the complete global map(s) in VRT format". The REST
  API is paused ("we ... have decided to temporarily pause the service").
- Proposal: open `https://files.isric.org/soilgrids/latest/data/phh2o/<layer>.vrt` through
  `/vsicurl/` and read only the window over the extent, in the native Homolosine grid. Reasons:
  GDAL reads the published GeoTIFF tiles themselves, so the stored subset is the product's own
  pixels with no server-side resampling; ISRIC publishes `checksum.sha256.txt` in that folder
  (5,797 bytes, observed in the listing) to check against; and the subset is then warped exactly
  once, Homolosine to ESRI:102008, as the dispatch requires. The WCS is ISRIC's stated route for
  subsets and is the alternative; asked in the native CRS (EPSG:152160) it should also return
  unresampled pixels, but that is inferred, not read.
- Native projection, read: "the Homolosine projection ... ESRI:54052 ... applied to the WGS84 datum",
  pseudo-code EPSG:152160, `+proj=igh +datum=WGS84 +no_defs +towgs84=0,0,0`.
- Version: `latest` is a rolling release ("SoilGrids works on a 'rolling release' system"). The pH
  files are dated 2020 (folder listing: tile folders 2020-04-07, `phh2o_0-5cm_mean.vrt` last-modified
  2020-06-02, ETag `"10771316263-1591112287-3524139"`, observed by HEAD). The stored request records
  each VRT's ETag and last-modified, and the sha256 of every file written, so a later change at ISRIC
  is detectable.

### 4.2 Depth: **STOP, undecided by any row**

Searched SPEC.md, RESEARCH_LOG.md, EVIDENCE.md, IDEAS.md, DECISIONS.md and DATA_REGISTER.md for
pH, soil, depth, acid and SoilGrids: no row chooses a depth (the only soil-pH mentions are the
register rows for SoilGrids and POLARIS). The options, for the owner:

- **A. 0-5 cm** alone. The surface layer, one fetch per statistic.
- **B. 0-30 cm, thickness-weighted** from 0-5, 5-15 and 15-30 (weights 5, 10, 15 over 30). The
  conventional "topsoil" figure; three fetches per statistic. A weighted mean of quantiles is not a
  quantile, so under B the Q0.05 and Q0.95 bands cannot be carried exactly (only as a bound).
- **C. 5-15 cm** alone, a single layer that sits in the upper root zone.

No source in this repository argues for any of them for chanterelle or Laetiporus habitat; whether
one does in the literature was not searched (that is a modelling question, outside this dispatch).

### 4.3 Statistic: **STOP for the bands, proposal for the central value**

ISRIC, read: "The 'mean' and 'median (0.5 quantile)' may both be used as predictions"; "The mean
represents the 'expected value' and provides an unbiased prediction"; Q0.05 and Q0.95 "present the
lower and upper boundaries of a 90% prediction interval". Proposal: **mean** as the value (the
unbiased one; for pH the two should be close, inferred). Whether Q0.05 and Q0.95 are carried onto
the master grid is a scope and cost question (two more fetches per depth, and under depth option B
not exact), so it goes to the owner with the depth. If carried, they live on the master grid only
and the archive holds the central value.

### 4.4 Units

Read (`SoilGrids_faqs_01.html`): "phh2o pH water pH x 10 10 -", that is mapped units pH × 10,
conversion factor 10. Proposal: the division happens once, in the ingest function, when the native
subset is read; the master grid stores pH as Float32 with NaN for no data. The archive encodes
`round(pH × 10)` as an unsigned byte (pH 0 to 14 is 0 to 140) with an alpha band for no data, and
the scale (0.1) is written into its metadata.

### 4.5 Resampling (proposal)

- **Homolosine to ESRI:102008: `average`** (GDAL's area-weighted mean of the source pixels a target
  cell overlaps). Both grids are equal-area and 250 m, so this is a conservative regrid: each master
  cell gets the area-weighted mean of the up-to-four native cells it covers. Bilinear would weight by
  distance to pixel centres instead and smooth slightly; nearest would shift values by up to about
  177 m.
- **ESRI:102008 to EPSG:3857 at zoom 9: `nearest`, then `average` for the overview zooms.** Zoom 9 is
  about 208 m per pixel at 47 N (observed arithmetic), so this step upsamples by about 1.2. Nearest
  keeps every archive pixel equal to the master cell under its centre, so a value read from a tile is
  the model's value and the ten-cell check can be exact at this step. This argues against the
  dispatch's default of bilinear; the smoothing a viewer wants belongs to the client (MapLibre's
  raster resampling), and the warp is display-only (D8). If the planner prefers bilinear here, the
  ten-cell tolerance has to widen to the interpolation, and that is said in the report.

### 4.6 The ten-cell check (proposal, before any value is seen)

Ten cells fixed now by rule: eight at the centres of a 4 × 2 lattice over the extent (spread,
deterministic), one coastal (Kalaloch, 47.604 N 124.374 W, at the beach edge), one high (Paradise on
Mount Rainier, 46.786 N 121.736 W, about 1,650 m). A cell that turns out to be no data in the source
is kept and checks that no data stays transparent. The check reads the stored native subset with
its own code (pyproj point transform and pixel arithmetic, no GDAL warp), computes the area-weighted
value independently, and compares: master grid vs that value within 1 in pH × 10 (one rounding step);
archive pixel vs master cell exactly. Its output is committed.

### 4.7 Where the request is stored (proposal)

The request JSON (VRT URLs, window in native pixel coordinates, ETags, time of the request, account
"anonymous", sha256 of each file written) goes beside the data in `data/t4/`, which is ignored, and
an identical copy is committed under `docs/pulls/`, as the GBIF and grid-positions requests are. The
attribution text is recorded verbatim from ISRIC's FAQ ("Please cite as follows"): "Poggio, L., de
Sousa, L. M., Batjes, N. H., Heuvelink, G. B. M., Kempen, B., Ribeiro, E., and Rossiter, D.: SoilGrids
2.0: producing soil information for the globe with quantified spatial uncertainty, SOIL, 7, 217–240,
2021", plus the licence line quoted in section 2.

### 4.8 Observation, not a gate

ISRIC's soil mask removes "Urban (code 190), inland water (code 210), glacier (code 220) and bare
surface (code 200)" from the 2015 ESA land cover. So the Seattle-Tacoma urban area, lakes and the
glaciers of Rainier, Baker and the Olympics will be no data on this layer (inferred from the mask
description; seen only after the fetch).

## 5. "Western Washington": **STOP, no definition without a choice**

Nothing in the repository defines it (searched `docs`, `src`, `tests`, `scripts`). Two state rules
do, read today, and both are drainage-divide polygons that need a boundary file this repository does
not have:

- WAC 222-16-010 (forest practices): "'Western Washington' means the geographic area of Washington
  west of the Cascade crest and the drainages defined in Eastern Washington", with Eastern Washington
  running from the crest to Mt. Adams and then along the White Salmon / Lewis and Little White Salmon
  / Wind divides.
- WAC 220-200-020 (fish and wildlife): "All lands lying west of the Cascade Crest Trail and west of
  and including the Big White Salmon River in Klickitat County."

Options:

- **A. T1's PNW box cut to Washington's latitudes, as a rectangle in code:** 45.5 to 49.0 N, 125.0 to
  121.0 W. T1's box is `src/forager_forecast/t1_design.py:35` (42.0 to 49.5 N, 125.0 to 121.0 W).
  No new download; it reuses an extent the records already use. It includes the strip of northern Oregon
  between 45.5 N and the Columbia (which runs near 46.2 N in the far west, inferred from the map, not
  measured) and the southern tip of Vancouver Island, and 121 W
  sits near, not on, the crest. Grid area about 390 × 476 km in ESRI:102008 (observed).
- **B. One of the WAC polygons,** which needs a boundary dataset fetched (a second download, with
  its own licence row).
- **C. Washington's 19 counties west of the crest,** which needs county boundaries (also a download).

Recommendation: A, because T4's purpose is to prove the grid and the pipeline end to end, and the
extent of this one demonstration layer is not inherited by anything (the lattice in section 3 is).

## 6. Tooling

- Observed: the rasterio wheel's GDAL has **no PMTiles driver** (`env.drivers()` has no `PMTiles`
  key). GDAL's own page, read: PMTiles "Added in version 3.8", vector read and write only, raster no.
  It has `MBTiles` with raster creation (GDAL MBTiles page, read: `TILE_FORMAT=PNG`, `RESAMPLING`,
  power-of-two overviews through `BuildOverviews`).
- Route: write a zoom-9 MBTiles through rasterio, then convert with the **`pmtiles` package from
  PyPI, version 3.8.1** (Protomaps, BSD-3-Clause, pure Python, no dependencies; wheel sha256
  `718561bb21f8c7dd5464fdcc3b9ad0e7b1c917be60ddfdf9a5ab56b8c67f7bde`, observed). Its
  `pmtiles.convert.mbtiles_to_pmtiles` converts and `pmtiles.reader.Reader` reads the header, which
  stands in for the viewer's `show`. Pinned exactly in `pyproject.toml` and locked by uv when the
  build starts; not added yet. The Go `pmtiles` CLI is not installed and is not proposed (a system
  binary). pmtiles.io is a browser page; the build can say the archive's header is what that page
  reads, but no session here can open it.
- **Probe, synthetic data only, observed** (`docs/audits/2026-10-06-t4-verify/probe_mbtiles.py.txt`,
  run from `/tmp/claude-1000/t4/probe/`, pmtiles installed only in a throwaway environment): a
  512 × 512 grey+alpha byte raster aligned to zoom 9 wrote as `minzoom 8, maxzoom 9`, 4 tiles at z9
  and 1 at z8; the tile PNG colour type is 4 (grey+alpha); reopened, every value under alpha 255
  round-trips exactly; converted to PMTiles, the header reads `min_zoom 8, max_zoom 9, tile_type PNG`.
  So the route writes a raster PMTiles with exact byte values, and max zoom is set by the
  resolution, not by guesswork.

## 7. Size

- Disk free: 5.6 GB of 67 GB (observed, `df -h ~`).
- Fetch (inferred from the extent): option A covers about 390 × 374 km in Homolosine, about 2.3
  million native pixels, about 4.7 MB per layer as raw int16. GDAL reads whole source blocks, so
  transfer per layer is estimated at 5 to 15 MB plus the 3.5 MB VRT (observed `content-length:
  3524139`). One depth, mean only: about 10 to 20 MB. Mean plus both bands: about 30 to 55 MB. Depth
  option B triples either.
- Stored: native subsets a few MB each as compressed GeoTIFF; master grid about 3 million cells,
  about 12 MB as Float32; the archive, about 6 × 9 tiles at zoom 9 plus overviews, estimated under
  5 MB. All under `data/t4/`, ignored.

## 8. What was not verified

- That the WCS in the native CRS returns unresampled pixels (inferred).
- SoilGrids' no-data value, block size and exact pixel origin: these are in the VRT, which was not
  read because reading it is the first step of the fetch.
- The fetch and archive sizes: estimates until the fetch.
- Whether pmtiles.io opens the archive: no browser in this session.

## 9. Stops

1. **Depth** (section 4.2): no row decides; options A, B, C.
2. **Bands** (section 4.3): whether Q0.05 and Q0.95 are carried; tied to the depth answer.
3. **Extent** (section 5): no definition without a choice; options A, B, C, recommendation A.

Also for the planner, not stops: the grid proposal (section 3), the access route (4.1), nearest at
the Mercator step against the dispatch's default (4.5), the ten-cell rule (4.6), the committed copy
of the request (4.7), and the `pmtiles==3.8.1` dependency (6).
