# T5 Part 2: verify-first report (strip, transect plan, crown-cover formula, host-genus sources)

Written 2026-10-06 (UTC) by the T5 coder session on `t5-host-trees`, after merging main `74c7f3b`
(merge commit `cf4d2ae`) and filing Amendment 1 with D83 to D87 (`f1ea5e6`). It answers Amendment 1's
"verify first and report the strip width and transect plan, the crown formula and the host-genus
source", and is written before any T5 code exists. Section 6 lists the readings that are the
builder's own and could be overturned.

## 1. Base and data, checked

- Base: `origin/main` was `74c7f3b` when it was merged. `grid.py` and `regrid.py` are T4's as
  merged: the lattice on ESRI:102008's false origin, 250 m, with the uint32 cell id, and the exact
  area-weighted regrid, which returns `(values, valid_fraction)`.
- The full suite after the merge and before any T5 code: **275 passed** (`uv run --frozen pytest`,
  `__pycache__` cleared, `PYTHONDONTWRITEBYTECODE=1`).
- Flash drive: mounted at `/run/media/zynergy-labs/2ebd084f-.../forecast-data/t5/`, ext4, read-write.
  `data/t5` in this worktree is a symlink to it, and `data/` is gitignored.
- TreeMap 2023: downloaded from the Archive's link (a usfs-public.box.com static URL) between
  11:15:12 and 11:21:54 UTC. Its sha256 is
  `348264eb608cd55cf49cacec0fa354d03e3f6963d7895582502315629e66abb7`, which equals the catalogue's
  checksum. The zip holds the raster (`TreeMap2023_CONUS.tif`, int32, 30 m, EPSG:5070, LZW,
  striped, nodata -2147483648), its `.vat.dbf`, the data dictionary, the tree table and
  `_variable_descriptions.csv`. The raster was extracted on the flash drive only. The tree table is
  streamed from the zip and never extracted.
- The tree table's columns, from `_variable_descriptions.csv`: `TM_ID` (equal to the raster value),
  `PLT_CN`, `STATUSCD` (1 live), `TPA_UNADJ`, `SPCD`, `COMMON_NAME`, `SCIENTIFIC_NAME`,
  `SPECIES_SYMBOL`, `DIA` (in), `HT`, `ACTUALHT`, `CR` (compacted crown ratio), `SUBP`, `TREE`,
  `AGENTCD`.
- SCANFI v2: tiled 256 x 256, deflate, uint8, nodata 255, NAD83 Canada Lambert, 30 m (header read
  over HTTP). A window read through `/vsicurl/` fetches only the tiles it needs. Nothing from SCANFI
  has been fetched yet.

## 2. The crown-cover formula (D87), proposed with its sources

Per live tree with DBH of at least 5.0 in (`STATUSCD` = 1, `DIA` >= 5.0):

1. **Largest crown width.** LCW (ft) = b0 + b1·D + b2·D², from **Bechtold 2004**, Equation 3, with
   the Table 3 coefficients. Bechtold, W.A. 2004. Largest-crown-width prediction models for 53 species
   in the western United States. *West. J. Appl. For.* 19(4):245-251,
   https://research.fs.usda.gov/download/treesearch/7732.pdf (read 11:15:40 UTC). The paper's own
   words: "The mean crown diameters of stand-grown trees 5.0-in. dbh and larger were modeled". Table 3
   is the paper's "Simpler models, based solely on stem diameter". I chose Equation 3 over the fuller
   Equation 6 because Equation 6 also needs stand basal area and Hopkins index for each plot. The
   tree table can supply basal area, but it gives no plot location for the Hopkins index (TreeMap
   plots carry no coordinates).
2. **Crown area** a = π (LCW/2)², in ft², the circle formula **Crookston and Stage 1999** use ("the
   crown area of a tree is computed using the formula for a circle as a function of crown radius").
   Crookston, N.L. and Stage, A.R. 1999. *Percent canopy cover and stand structure statistics from
   the Forest Vegetation Simulator.* RMRS-GTR-24, https://www.fs.usda.gov/rm/pubs/rmrs_gtr024.pdf
   (read 11:15:42 UTC). This is the method TreeMap's own metadata names for its plot cover ("We
   calculated plot-level tree cover ... using the StrClass keyword in the Forest Vegetation
   Simulator", citing Crookston and Stage 1999).
3. **Plot cover without overlap**, C′ = 100 Σ pᵢaᵢ / 43560, where pᵢ is `TPA_UNADJ` (their
   equation 1). **With overlap**, C = 100 [1 − exp(−0.01 C′)] (their equation 2, "for randomly
   located" trees).
4. **Genus share in a plot**, s_g = Σ_{i∈g} pᵢaᵢ / Σ_i pᵢaᵢ. **Genus cover**, C_g = C · s_g. Equation 2
   has no species term. Splitting the overlap-corrected cover pro rata by crown area is my reading
   of the random-placement assumption, and is **inferred**, not stated by Crookston and Stage. With
   it, the genus covers sum to C, as SCANFI v2's species crown closures sum to its total ("A pixel
   with 100% crown closure composed of 60% black spruce and 40% balsam fir has 60% black spruce and
   40% balsam fir crown closure", SCANFI v2 readme).
5. **On the master grid**: each TreeMap pixel takes its plot's C_g and C. Both are regridded with
   `area_weighted_regrid`, and the 250 m genus share is regridded C_g divided by regridded C. SCANFI
   takes the same route, with its class crown closures and their sum.

**Species with no Bechtold 2004 coefficients.** In the strip's TreeMap plots these carry **7.14% of
basal area**, pixel-weighted (probe in section 5). The main ones are Oregon ash 4.08%, Alaska
yellow-cedar 1.77% and black cottonwood 0.98%. The rule, stated before any value is seen:
1. a species in Table 3 uses its own coefficients;
2. otherwise the same-genus Table 3 species with the most observations in Bechtold's Table 1,
   excluding the woodland species, whose D is root-collar diameter;
3. otherwise the class default: the softwood or hardwood Table 3 species with the most observations
   (Douglas-fir, n = 4,088; quaking aspen, n = 1,383).

Every surrogate is counted in the build record. The build also reruns the shares with every
surrogate crown width scaled by 0.7 and by 1.3, and reports how much the shares move. That way the
effect of the rule is measured, not argued.

**Trees under 5.0 in** are outside Bechtold's fitted range and are left out. They carry 5.82% of the
strip's live basal area (probe). SCANFI's crown closure has no stated diameter limit, so this is a
known difference between the two sides and is recorded as such.

Defensible? Every step has a published source, and the one inferred step (pro-rata overlap, step 4)
cancels in the shares except through the per-pixel weighting by C. I do not judge this to be a stop.

## 3. Host-genus sources (D85)

EVIDENCE.md has none (survey section 4). The sources found:

- ***Cantharellus*, Pacific Northwest.** Pilz, D., Norvell, L., Danell, E. and Molina, R. 2003.
  *Ecology and management of commercially harvested chanterelle mushrooms.* PNW-GTR-576,
  https://www.fs.usda.gov/pnw/pubs/gtr576.pdf (read 11:16:35 UTC). p. 19 (PDF page 25): "In the
  Pacific Northwest, chanterelles generally associate with Douglas-fir, hemlock, spruce, fir, and
  pine". The same page has "In eastern North America and southern California, chanterelles associate
  with oak, beech, birch, and various conifers". The Pacific golden chanterelle (PDF page 39 area)
  occurs "under hemlock, Douglas-fir, and spruce". **Host genera for the PNW: *Pseudotsuga*,
  *Tsuga*, *Picea*, *Abies*, *Pinus*.** *Quercus* is a host in California and the East, not the PNW.
  This corrects the dispatch's line, which put oak among the PNW chanterelle hosts.
- ***Laetiporus*, western North America.** Burdsall, H.H. Jr. and Banik, M.T. 2001. The genus
  *Laetiporus* in North America. *Harvard Papers in Botany* 6(1):43-55, Forest Products Laboratory
  copy https://www.fpl.fs.usda.gov/documnts/pdf2001/burds01a.pdf (read 11:17:07 UTC), PDF page 6:
  "*Laetiporus conifericola* occurs on mature and over mature living and dead conifers in western
  North America from California to Alaska", and "The only other species of *Laetiporus* in the West
  is *L. gilbertsonii*, which is found only on hardwoods, mainly *Quercus* and *Eucalyptus* spp."
  **Hosts: conifers (all), and *Quercus*.**

Both are primary sources: a Forest Service synthesis, and the taxonomic paper that described the
western species. Neither is a habitat model. They name hosts, and say nothing about how strongly
each host predicts fruiting.

**Bands carried (D85):** genus shares for *Pseudotsuga*, *Tsuga*, *Picea*, *Abies*, *Pinus* and
*Quercus*, plus the conifer and broadleaf totals.

What SCANFI can supply:
- *Pseudotsuga* (Douglas-fir, the only Canadian *Pseudotsuga*; inferred, general knowledge);
- conifer and broadleaf totals (sums of its classes).

**Not available on the Canadian side**, flagged:
- *Tsuga* and *Quercus*, which have no class of their own;
- *Picea*, *Abies* and *Pinus*. SCANFI maps only some of their species (black spruce; balsam fir;
  jack, lodgepole, ponderosa, and white and red pine). The others fall in "other coniferous"
  (inferred), so a sum of the mapped species would be a partial genus. I read the owner's "the
  missing Pinus" as making the whole genus not available on the Canadian side, and apply the same
  reading to *Picea* and *Abies*, which the owner's answer did not name (section 6).

## 4. The strip and the transect plan (stated before any value is read)

- **Border**: the 49th parallel. Within D82 the land boundary runs along 49° N from Semiahmoo Bay
  (about 122.76 W, inferred from the coastline) to 121.0 W (D82's east edge). West of that the
  boundary is in water, and Point Roberts (west of 122.95 W) is left out. Country side for a cell is
  decided by its centre: latitude of at least 49.0 is Canada (SCANFI), below it is the US
  (TreeMap). The surveyed boundary monuments depart from the parallel by up to a few hundred metres
  (inferred, not checked). Cells that straddle the line take their own country's native pixels, and
  D74's 0.5 valid-fraction rule applies.
- **Strip**: 48.70 to 49.30 N (about 33 km each side), 122.80 to 120.95 W. That is the D82
  rectangle's land border plus a margin, extended north into British Columbia, "beside" D82 as the
  dispatch allows. About 137 km by 67 km, or about 147,000 master cells (inferred from area).
- **Transects**: 25 meridians, from 121.000 W westward every 5 km of ground distance at 49° N
  (0.06844° of longitude), the last at 122.643 W. Along each, 80 sample points per side at 125 m +
  250 m·j (j = 0 to 79) north and south of 49° N, to 20 km, placed with a WGS84 geodesic. Each point
  reads the master cell that holds it.
- **Windows**: four consecutive points make a 1 km window, 20 per side. A window with any point
  missing is missing.
- **Border step** per transect and variable: Δb = W0(north) − W0(south), Canada minus US.
- **Within-country steps**: Δw = W_k − W_{k+1}, k = 0 to 18, on each side separately, measured the
  same way.
- **Verdict per variable**:
  - B = median over transects of |Δb|. V_US and V_CA = medians over transects and k of |Δw|.
  - The step is "larger than the variation inside each country" if B > max(V_US, V_CA). Then it is
    written up as a known artifact with B, V_US, V_CA and the ratio.
  - Also reported: the 95th percentiles of |Δw|, and the mean signed Δb with a 95% bootstrap
    interval over transects (10,000 resamples, seed 20260918, D31).
- **Variables tested**: *Pseudotsuga* share, conifer share, broadleaf share, total crown cover (%).
  *Tsuga*, *Picea*, *Abies*, *Pinus* and *Quercus* cannot be tested, being not available on the
  Canadian side (D85), and are reported as untestable.
- **A share is defined** only where the cell's regridded total crown cover is at least 10%. LEMMA's
  forest definition is "areas currently or with the potential to support at least 10% tree cover"
  (lemma.forestry.oregonstate.edu/data/species-maps, read 10:55:26 UTC). The cell must also pass
  D74's valid fraction of at least 0.5.
- **SCANFI year: 2025**, the step nearest TreeMap's circa 2023 (2 years against 3 for 2020).

## 5. Probe

`2026-10-06-t5-verify/treemap_strip_probe.py.txt`, with its output beside it. On the strip's US side
(48.70 to 49.00 N), the TreeMap window has 10,776,740 pixels, 4,524,208 of them forest. They hold
1,396 distinct plots, and every one has tree rows (49,723 live trees). Basal area by species,
pixel-weighted (the top six): Pacific silver fir 27.9%, western hemlock 25.2%, Douglas-fir 10.0%,
mountain hemlock 9.5%, western redcedar 5.8%, red alder 4.9%. Trace shares of Californian species
appear (blue oak 0.007%, for example). That is TreeMap's imputation, not an error in the probe. The
probe ranks species by basal area only to size the coefficient gap. Basal area is not the variable
(D87).

## 6. Readings that are mine, and could be overturned

1. I read "the missing Pinus" as making *Pinus* not available on the Canadian side. I extended the
   same reading to *Picea* and *Abies*, which became host genera only through section 3's source.
2. The surrogate rule for species with no coefficients, and leaving out trees under 5.0 in.
3. The 10% cover threshold, the strip and transect geometry, and the verdict statistic.
4. SCANFI 2025 rather than 2020.

None of these is a stop under Amendment 1. I am going ahead with the build as written.

## 7. Appended 2026-10-06, before any real value was read: two corrections to section 4

Section 4 is left as written above. These notes supersede the parts they name.

1. **Westmost transect.** Section 4 says the last meridian is at 122.643 W, 0.06844° apart. Those
   figures used a spherical Earth. On the WGS84 parallel radius at 49° N, 5 km is 0.06833°, which
   puts the last meridian at **122.640 W** (`seam.transect_longitudes`, which
   `tests/test_seam.py` checks against geodesic distance).
2. **Verdict rule.** Section 4's rule was B > max(V_US, V_CA), using the medians of |within
   steps|. While writing its test I found that this rule fires about half the time when there is
   no step: B and V are then medians of draws from the same distribution. It is replaced by a null
   built from the within-country steps themselves:
   - for each side, draw one |within step| per transect at random, take the median over
     transects, and repeat 10,000 times (seed 20260918);
   - the threshold is the 95th percentile of those medians, on the side whose threshold is larger;
   - B above the threshold is a step larger than the variation inside each country.

   A test (`test_with_no_step_the_verdict_fires_about_one_time_in_twenty_or_less`) checks that the
   rule fires on at most 8% of no-step draws. V_US, V_CA, the 95th percentiles and the bootstrap
   interval are still reported, as section 4 promised. No real transect value had been computed
   when this change was made: the master raster did not exist yet.

## 8. Appended 2026-10-06, after the T5 review (F5): page numbers in section 3

Section 3 is left as written above. In section 3 the Pilz et al. 2003 PDF page numbers are wrong;
the printed page, 19, is right. I re-checked them on the copy read at 11:16:35 UTC (sha256
`250a2951…9123`) with `pdftotext`, one page at a time:

| Quote | Section 3 says | Correct PDF page |
| --- | --- | --- |
| "In the Pacific Northwest, chanterelles generally associate with Douglas-fir, hemlock, spruce, fir, and pine" (printed p. 19) | PDF page 25 | **PDF page 24** |
| The Pacific golden chanterelle, "under hemlock, Douglas-fir, and spruce" | "PDF page 39 area" | **PDF page 38** |

- **Where the errors came from.** Page 25 holds the next sentence, "Chanterelles have a very broad
  host range", which is where my first search landed. Page 39 holds the white chanterelle's
  "mycorrhizal with Douglas-fir and hemlocks".
- **The review agrees.** Its pages (24 and 38) match this copy.
