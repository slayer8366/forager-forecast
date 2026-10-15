# T6b host genera for the mycorrhizal group: verify-first report (M7)

Written 2026-10-15 04:37 UTC on branch `t6b-host-genera-verify`, from forecast main `a79d667`
(verified equal to `origin/main` at that time). Dispatched by the Forager planner after the
owner's ruling on T7's M7 (Forager RECORD -1029), verbatim: "M7 let's add them now, it's not a
huge task now, but it will be later." This is the verify step only. Nothing was built, no code
changed, nothing fitted, no data downloaded. The T6b run (user unit `t6b-night`) was live
throughout; its drive folder was only listed and its manifest read.

Flags: **read** = opened and quoted here with file:line or URL; **measured** = counted by me
today from a file named here; **INFERRED** = my reasoning from read material; **UNVERIFIED** =
from memory, not checked against a source.

Small reads made, none in the T6b folder's working files: the TreeMap 2023 tree table (25 MB
compressed, read once, at nice 19, to count live trees per genus; below), the SCANFI v2 readme
(5,697 bytes), two Open Government portal pages, and the FungalRoot paper's open copy (PDF, read
for its methods text and supplement names only).

## 1. What the tree layers carry today, and why

**One genus list for both sides.** `HOST_GENERA = ("Pseudotsuga", "Tsuga", "Picea", "Abies",
"Pinus", "Quercus")` and `BANDS = (*HOST_GENERA, "conifer", "broadleaf")`
(`src/forager_forecast/crown_cover.py:156-157`, read). Every tree output takes its bands from
`BANDS`: the T6b value file's `TREE_BANDS` (`src/forager_forecast/t6b_layers.py:97`), its flag
file (`t6b_layers.py:673-685`), and T5's strip layer (`src/forager_forecast/t5_layer.py:36`).

(Citation note: the T7 plan on `origin/t7-mycorrhizal-plan` cites these as
`crown_cover.py:155-156` "on main"; on `a79d667` they are lines 156 and 157. Off by one.)

**US side (TreeMap 2023, FIA tree lists, D84, D87).** A genus's canopy cover is computed from each
plot's tree list (Bechtold 2004 crown widths, Crookston and Stage 1999 overlap,
`crown_cover.py:1-21`), and a tree whose genus is in `crown` (that is, in `BANDS`) adds to its own
band (`crown_cover.py:258`, in `plot_cover`; read). Any genus can be a band on
this side: the tree table carries `SCIENTIFIC_NAME` and `SPCD` for every tree
(`t6b_layers.py:269-276`). Trees under 5 in d.b.h. carry no crown (`crown_cover.py:27`).

**Canadian side (SCANFI v2 2025, D85, D89).** SCANFI has ten fixed classes
(`t5_layer.py:101-104`). The only genus band it fills is *Pseudotsuga* from `douglasFir`, plus the
conifer and broadleaf totals (`SCANFI_BAND_CLASSES`, `t5_layer.py:105-109`). Every other band is
flagged 3, "not available in SCANFI (D85)" (`t5_layer.py:110`, `t6b_layers.py:675-683`).
D89 (1) made *Pinus*, *Picea* and *Abies* wholly not available rather than filled with SCANFI's
partial species sums (`docs/planning/DECISIONS.md:40`, read).

**How they were chosen: for chanterelles (and the chicken-of-the-woods control).** T5 verify
report section 3 (`docs/audits/2026-10-06-t5-verify-report.md:86-125`, read):
Pilz et al. 2003 (PNW-GTR-576) for *Cantharellus* in the PNW, "Douglas-fir, hemlock, spruce, fir,
and pine", gave the five conifer genera; Burdsall and Banik 2001 for *Laetiporus* gave *Quercus*
(*L. gilbertsonii* "found only on hardwoods, mainly *Quercus* and *Eucalyptus*"). *Laetiporus*
is a wood-decay fungus, not mycorrhizal (UNVERIFIED as a citation here, general mycology), so the
one broadleaf band was chosen for the control, not for a mycorrhizal partner, though oak is also
a major ectomycorrhizal host (section 2).

## 2. Hosts the mycorrhizal group needs that are missing: a proposal, not a decision

**Which source should decide it.** The authoritative compiled source found is FungalRoot:
Soudzilovskaia, N.A. et al. 2020, *New Phytologist* 227(3):955-966, doi 10.1111/nph.16569. Read
in its open copy (Leiden repository, PDF sha256 `cd5718db...283363`): "we provide a recommended
list of genus-level plant mycorrhizal associations", published as "Table S2 Recommended
mycorrhizal status for plant genera"; its authors warn it was assigned "at 67% level of
consistency" and "should, as such, never be used to detect misdiagnoses. Rather they should be
used in ecological analyses in cases where more detailed information is not available". It
cites Tedersoo 2017 (Biogeography of mycorrhizal symbiosis, Springer, 469-531) for ectomycorrhizal
plant genera. **I did not open Table S2.** Every genus status below is therefore from memory
(UNVERIFIED) until checked against Table S2, and Table S2's licence must be read before it is
used or copied (the PDF's own repository licence line is "Article 25fa Copyright Act/Law
(Amendment Taverne)", which covers the article copy, not the supplement).

**Ectomycorrhizal (ECM) tree genera, the main case.** Counts are live trees of 5 in and up in
TreeMap 2023's CONUS tree table, and the plots holding them (**measured** today from
`.../forecast-data/t5/treemap2023/RDS-2026-0038.zip`, member
`Data/TreeMap2023_CONUS_Tree_Table.csv`). "PNW box" means 40 to 49.5 N, 111 to 125 W; whether a
genus occurs there is UNVERIFIED (general knowledge; no per-box count was made, which would need a
raster read).

| Genus | Status (UNVERIFIED, check Table S2) | In PNW box? (UNVERIFIED) | TreeMap live trees, plots | Already a band? |
| --- | --- | --- | --- | --- |
| *Pseudotsuga*, *Tsuga*, *Picea*, *Abies*, *Pinus* | ECM (Pinaceae) | yes | 89,333 / 46,898 / 69,536 / 138,116 / 445,515 trees | yes |
| *Quercus* | ECM (Fagaceae) | yes, S Oregon and N California oaks, Oregon white oak | 194,793 trees, 24,570 plots | yes |
| ***Larix*** | ECM (Pinaceae); host-specific *Suillus* partners (UNVERIFIED) | yes: western larch, subalpine larch in E WA, N ID, NE OR, W MT, SE BC | 15,688 trees, 2,603 plots (tamarack 8,211, western larch 7,063, subalpine larch 231) | **no** |
| ***Betula*** | ECM (Betulaceae) | yes but minor: paper and water birch, interior | 43,298 trees, 9,124 plots (mostly eastern: yellow, paper, sweet birch) | **no** |
| ***Populus*** | ECM and AM (Salicaceae) | yes: quaking aspen, black cottonwood | 58,209 trees, 6,570 plots (aspen 45,779) | **no** |
| ***Alnus*** | ECM, with a narrow alder-specific fungal set (UNVERIFIED) | yes: red alder west of the Cascades is abundant (UNVERIFIED) | 2,990 trees, 418 plots (red alder 2,907) | **no** |
| ***Lithocarpus*** (tanoak; *Notholithocarpus* in current names) | ECM (Fagaceae) | yes: SW Oregon, N California | 7,581 trees, 449 plots | **no** |
| ***Chrysolepis*** (chinquapin) | ECM (Fagaceae) | yes: SW Oregon, N California, W Cascades | 785 trees, 158 plots | **no** |
| ***Arbutus*** (madrone) | arbutoid mycorrhiza formed by ECM fungi (UNVERIFIED) | yes | 3,724 trees, 603 plots | **no** |
| *Salix* | ECM and AM | yes, but mostly shrubs | 1,486 trees | no |
| *Cercocarpus* | reported ECM (UNVERIFIED, weakest claim here) | yes, dry interior | 4,953 trees | no |
| *Fagus* | ECM (Fagaceae) | no (eastern) | 22,002 trees, 5,136 plots | no; **unlisted genus, D116** |
| *Carya* | ECM (Juglandaceae; *Juglans* is AM) | no | 33,089 trees, 9,622 plots | no; unlisted, D116 |
| *Tilia* | ECM | no | 9,240 trees | no; unlisted, D116 |
| *Ostrya*, *Carpinus* | ECM (Betulaceae) | no | 4,190 / 2,015 trees | no; unlisted, D116 |
| *Castanea* | ECM (Fagaceae) | no | 19 trees | no; unlisted, D116 |
| *Eucalyptus* | ECM (Myrtaceae) | planted only | 2 trees | no |

**Proposed list, two tiers (the owner chooses).**
- **Tier A, the PNW pilot's hosts:** *Larix*, *Betula*, *Populus*, *Alnus*, plus one Fagaceae
  band for tanoak and chinquapin together or two bands (*Lithocarpus*, *Chrysolepis*), and
  *Arbutus*. That is six or seven new bands. Reason: each is a recognised ECM host
  (UNVERIFIED until Table S2) present in the box, and each has a usable count in TreeMap.
- **Tier B, continental:** add *Fagus*, *Carya*, *Tilia*, and *Ostrya* with *Carpinus*
  (one band or two). Not needed for the PNW pilot. These five are D116 "unlisted" genera today
  (`docs/audits/2026-10-07-t6b-run/genus_classes.out.txt`, read), which section 6 turns into an
  owner decision.
- **Not proposed as bands:** *Salix* (mostly shrubs, which FIA does not tally), *Cercocarpus*
  (status uncertain), *Castanea* (19 trees), *Eucalyptus*.

**Other (non-ECM) cases, for the owner's awareness.**
- **Shrub hosts are invisible to this source.** Manzanita (*Arctostaphylos*), hazel (*Corylus*),
  shrub willows and *Dryas* do not appear in TreeMap's tree table at all (no rows for
  *Arctostaphylos* or *Corylus*, measured), and trees under 5 in carry no crown
  (`crown_cover.py:27`). No tree layer can supply them. A stated gap.
- **The conifer total is not an ECM total.** Cupressaceae and yew (*Thuja*, *Calocedrus*,
  *Juniperus*, *Chamaecyparis*, *Sequoia*, *Taxus*) are arbuscular mycorrhizal (UNVERIFIED), yet
  count in `conifer`. Western redcedar is common in the PNW (8,265 trees CONUS-wide, measured).
  Likewise `broadleaf` mixes ECM (oak, birch, aspen) with AM genera (maples, ash, elm). An optional
  **"ECM host" total band** (sum of the ECM genera's cover, as a share) would give the model the
  group's own quantity. It is computable on the US side only; in Canada, `otherConiferous` mixes
  hemlock and spruce (ECM) with redcedar (AM) and `broadleaf` mixes birch and aspen with maple, so
  the total is not available there. Offered as an option, not recommended or rejected here.
- **Ericoid and orchid mycorrhizas** do not form the mushrooms this map is about (UNVERIFIED);
  not proposed.

## 3. Availability per side, and options where a side lacks a genus

**US side: every Tier A and Tier B genus is in the data the code already reads**, with FIA codes
(measured above). Crown widths: *Larix* (73), *Populus* (746, 749), *Alnus* (351, 352),
*Lithocarpus* (631) and *Arbutus* (361) have Bechtold Table 3 coefficients
(`crown_cover.py:47`, `:71-77`); tamarack (71) takes western larch by D89 (2); *Betula*,
*Chrysolepis*, *Fagus*, *Carya*, *Tilia*, *Ostrya*, *Carpinus* have no same-genus Table 3 species
and take the broadleaf default, quaking aspen (`crown_cover.py:154`, `:181-188`). So a birch or
beech band would rest entirely on surrogate widths (INFERRED from the rule; the counts already
record surrogates, `plots.json` "surrogate_trees": 1,074,858, read).

**Canadian side: SCANFI v2 offers exactly ten species-class layers plus totals.** From the v2
readme (`https://ftp.maps.canada.ca/pub/nrcan_rncan/Forests_Foret/SCANFI/v2/_SCANFI_v2_read_me.txt`,
fetched 2026-10-15 04:33:39 UTC, 5,697 bytes, sha256 `996f671e...6f11c5`): balsam fir, black spruce,
broadleaf ("Broadleaf species crown closure"), Douglas-fir, jack pine, lodgepole pine, other
coniferous ("Other coniferous species crown closure"), ponderosa pine, tamarack ("Tamarack crown
closure"), white and red pine; plus total crown closure, biomass, height, NFI land cover, age.
The v2 readme defines no class membership. The v1 dataset page
(https://open.canada.ca/data/en/dataset/18e6a919-53fd-41ce-b4e2-44a9707c52dc, read through a
summarising fetch 2026-10-15) gives Latin names: "Tamarack tree cover in percentage (*Larix
laricina*)", balsam fir *Abies balsamea*, black spruce *Picea mariana*, white and red pine
*Pinus strobus* and *P. resinosa*; broadleaf and other coniferous carry no species list. The v2
page (dataset 07653869-...) names no species membership (read through a summarising fetch).

| Genus | SCANFI v2 | Reading |
| --- | --- | --- |
| *Larix* | **Partial**: `tamarack` = *L. laricina* (v1 page). Western and subalpine larch, the only larches in SE British Columbia inside the PNW box, are presumably in `otherConiferous` (INFERRED) | Under D89 (1)'s reasoning a partial genus is "not available". Inside the PNW box SCANFI's tamarack layer would be close to zero where western larch grows (INFERRED) |
| *Betula*, *Populus*, *Alnus*, *Quercus*, *Arbutus*, Fagaceae, Tier B | **Folded into `broadleaf`** | Not available |
| *Tsuga* | Folded into `otherConiferous` (D85, unchanged) | Not available |

**Options where Canada lacks a genus (owner decides):**
1. **Flag "not available" in Canada, as D85 does today.** The code does this automatically for any
   new band not in `SCANFI_BAND_CLASSES` (`t5_layer.py:110`). Zero new source, zero licence work.
   In the PNW box the Canadian cells are 102,543 of 16,674,133 study cells (measured in
   `docs/audits/2026-10-09-pnw-monday/mosaic.json`, read), about 0.6%.
2. **A combined class:** carry a "broadleaf ECM proxy" in Canada from `broadleaf`. Not
   recommended by me: it would mix maple with birch and break the meaning of a genus band
   (INFERRED).
3. **A second Canadian source.** "Maps of Canada's forest attributes for 2001 and 2011"
   (Beaudoin et al., Natural Resources Canada; https://open.canada.ca/data/en/dataset/ec9e2659-1c29-4ddb-87a2-6aced147a990,
   read through a summarising fetch 2026-10-15): licence shown as "Open Government Licence -
   Canada", 250 m on the MODIS grid, 78 "tree species/genus composition layers", genera including
   *Betula*, *Larix*, *Populus*, *Tsuga*, *Alnus*, *Quercus*, *Fagus*, *Carya*. Before it could be
   used: re-read the licence on the dataset page itself (not a summary), read what the
   composition variable is (percent of what: volume, basal area or crown, UNVERIFIED, I believe
   volume), note its vintage (2011, against TreeMap 2023 and SCANFI 2025) and grid (250 m MODIS
   sinusoidal, a regrid with its own error), check file sizes against the drive, and decide how a
   2011 volume share and a 2025 crown-closure total combine. It was never surveyed in T5
   (`docs/audits/2026-10-06-t5-source-survey.md` section 2 lists no Canadian alternative; D85's
   rejected alternative was "Surveying British Columbia provincial layers (a new licence check)").
   British Columbia's own forest inventory is another candidate, not opened (UNVERIFIED).
4. **State the gap** and restrict any host-genus model term to US cells.

## 4. What changes in code

**Where the genus list lives.** `crown_cover.HOST_GENERA` and `BANDS` (`crown_cover.py:156-157`).
Everything else derives from it: `plot_cover`'s accumulator (`crown_cover.py:235`, `dict.fromkeys(BANDS, 0.0)`);
the plot table's columns, `2 + len(BANDS)` (`t6b_layers.py:280-291`); the US split per band
(`t6b_layers.py:421-425`); the share and flag bands (`t6b_layers.py:673-685`);
`SCANFI_NOT_AVAILABLE` (`t5_layer.py:110`).

**Design point for the owner or the coder.** `HOST_GENERA` is shared with T5, a merged and reviewed
product (`t5_layer.py:36`). Editing it in place changes T5's outputs and tests
(`tests/test_t5_layer.py`, which also asserts on specific bands, e.g. `:260`). A T6b-only genus
list, passed to `plot_cover`, leaves T5 alone and follows the repository practice of a new path
rather than a conditional in working code (INFERRED; a coder's choice within scope, flagged).

**Outputs that gain bands.** Each new genus adds `share_<Genus>` to `trees_<tile>.tif` and
`flag_<Genus>` to `trees_flags_<tile>.tif`, the same for the US-half files. `plots.npz` gains one
column per genus. SCANFI per-layer files (`scanfi_layers/scanfi_<class>_<tile>.npz`) are per
SCANFI class and do **not** depend on the genus list (`t6b_layers.py:567-611`, read): they stay
valid unless option 3 adds a new Canadian source, which would be new layer units. Soil tiles are
untouched. `scripts/pnw_build.py:80-81` reads bands by name and would keep working but show no new
band until its `TREE_BANDS` and `LAYERS` are extended (read; `scripts/pnw_checks.py:561` likewise).

**Do existing outputs stay valid?** No. Every finished tree tile (2,025), every US-half file (92)
and `plots.npz` lack the new bands and must be recomputed. The new genus shares are independent of
the old bands (each share is the genus's regridded cover over the same regridded tree-list total,
`t6b_layers.py:674`), so an **additive** design, a separate `trees_hosts2_<tile>.tif` holding only
new bands, is possible and would leave the 2,025 old files valid. It still needs a full US pass:
the per-tile TreeMap read, side and water masks and the regrid of the tree-list total are redone
(INFERRED from `_treemap_part`, `t6b_layers.py:380-429`). Owner or planner choice: one tile format
with all bands (simpler for T7 to read) against an additive file (keeps reviewed files).

**Resume and manifest: two findings to fix in the build, not now.**
- **F1 (bug if the list changes in place): finished tiles would be skipped silently.** A tree unit
  is named by its tile key only (`scripts/t6b_run.py:349`, units are keys) and counts as done when
  its last manifest line is ok and its files still hash (`src/forager_forecast/t6b_run.py:61-72`).
  Nothing records the genus list. Change `BANDS` and rerun: all 2,025 done tiles are skipped as
  done, and only the 2,033 Canadian tiles are built with the new bands, giving a continent of two
  band layouts with no error. The build must make the genus list part of what "done" means (a
  version in the unit name, the manifest line and the file tags, checked by `done_units`), or move
  the old tree outputs aside first.
- **F2: the plot table would be reused unless its ruling string changes.** `stage_plots` rebuilds
  only when `plots.json`'s `rulings` differs from `PLOT_TABLE_RULINGS = "D87 to D91, D116"`
  (`scripts/t6b_run.py:90`, `:143-150`). A new genus list with the old string keeps the
  ten-column table. It would then fail loudly, but by accident: with eight bands plus two new ones,
  `rows[:, k]` would read the CANOPYPCT column as a genus at `k = 9` and raise IndexError at
  `k = 10` (`t6b_layers.py:422-425`, INFERRED). A single new band would read CANOPYPCT as that
  genus without any error (INFERRED). The table needs a versioned rebuild check.
- **`supersede()` is too wide for this.** It exists to move outputs aside, never deleting
  (`scripts/t6b_run.py:112-121`), but moves the whole `tiles` folder (soil included), the manifest
  and `scanfi_layers`. Used for a genus change it would force 89 soil tiles (8.18 h summed,
  measured) and every SCANFI layer tile to be redone, neither of which depends on genera. A
  trees-only supersede is needed.
- **The US-half path fails loudly, as it should.** `fill_canadian_cells` refuses a US-half file
  whose band names differ from a fresh tree tile's (`t6b_layers.py:822-823`). So old US halves
  cannot be merged with new Canadian cells; they would be recorded as failed units each night
  until the halves are rebuilt. Rebuild them too.

## 5. Rerun cost (from the manifest's own timings)

Read from `.../forecast-data/t6b/manifest.jsonl` (1,780,630 bytes, 2026-10-14 21:31 local) and
`tiles_trees.json`: 4,058 tree tiles, 2,043 with Canadian cells. Done: 2,025 whole tiles
(2,015 US-only plus 10 PNW Canadian tiles), 92 US halves. Plot table built once in 18.1 s; mask
440.6 s.

**Timings (measured).** Tree-stage section wall times sum to 74,021 s for 2,025 tiles at two
workers, 36.6 s per tile of wall time (sections 3,904 + 1,713 + 21,580 + 2,767 + 15,468 + 15,275
+ 13,289 + 25 s). Per-tile worker time: median 71.8 s, max 175.9 s. US halves: 3,417 s of section
wall time for 92.

**Recompute if the change lands before the Canadian tree tiles (the planner's plan, RECORD -1029):**

| Work | Units | Wall time at 2 workers, today's bands | With new bands (INFERRED) |
| --- | --- | --- | --- |
| Plot table | 1 | 18 s | about the same |
| US-only tiles | 2,015 | 20.5 h | 20.5 to about 33 h |
| PNW Canadian whole tiles | 10 | 0.1 h | same order |
| US halves | 92 | 0.95 h | 0.95 to about 1.5 h |
| **Total rerun** | | **about 21.5 h** | **about 21.5 to 35 h**, three to five nights at the 21:00 to 07:00 window |
| PNW box only (if the owner wants the pilot first) | about 344 (314 whole and 20 US-half tiles over the PNW window, `mosaic.json`, plus the 10 Canadian) | about 3.5 h | 3.5 to 6 h, one night |

The upper bound assumes cost grows with the number of regridded split layers (9 today, up to 16
with seven new genera, `t6b_layers.py:421-428`). How much of a tile's time is the regrid and how
much the TreeMap read and masks was not measured; the range is a guess at both ends. The 2,033
Canadian tiles are not a rerun: they have not been built and would be built once, with the new
bands, at their own cost.

**When the Canadian tree tiles start (INFERRED).** The running section does `scanfi-layers` first:
896 of 22,473 layer tiles were on the drive at 21:31 local (2,043 tiles x 11 layers), median
about 40 to 50 s of worker time each (measured, per layer), so about 120 h of wall time remain at
two workers before any Canadian tree tile is ready. The genus change has time to be built before
that, which fits RECORD -1029's plan to pause the run before its tree tiles.

**Flash-drive space (measured now, INFERRED forward).** Free 6,386,176,000 bytes (`df`, 2026-10-15).
Existing tree value files 1,170,406,305 bytes for 2,025 tiles (578 kB each, 11 bands), flag files
21,201,051 bytes, US halves 43,811,345 bytes. Adding six or seven float32 bands adds roughly 52 kB
per band per tile (the mean per band today; rare genera are mostly no-data and compress better, so
this is likely an upper bound): a redone tile about 0.9 MB. Redoing 2,025 tiles: about 1.8 GB new;
if the old files are moved aside and kept (as `supersede` does), the old 1.2 GB stays. The 2,033
Canadian tiles, needed anyway: about 1.8 GB. The running SCANFI stage adds about 2.0 GB more of
layer tiles (90 kB each, measured on 896) but deletes each whole SCANFI layer when its tiles are
done (`scripts/t6b_run.py:301-305`), and those total 18,780,034,255 bytes. So space is tight only
until the first whole layers are deleted; the free-space check before each download guards the
SCANFI stage, but the tree stage has no such check (INFERRED from `stage_trees`,
`scripts/t6b_run.py:328-350`). Moving the old tree tiles off the drive, or deleting them, is an
owner decision (the project's rule is to keep superseded outputs).

## 6. Decisions this touches (for the owner; none resolved here)

1. **Which genera.** Tier A only (PNW pilot), Tier A plus Tier B (continental), and whether an
   "ECM host" total band is added. Table S2 of FungalRoot (licence to be read first) or another
   cited source checks each genus before the list is fixed.
2. **D121 and the new bands.** D121 sets the first models' inputs as "host trees (T5/T6b genus
   fractions with the conifer and broadleaf totals)" and says "Any further input (terrain,
   SSURGO, POLARIS, burn perimeters or others) enters only if a model with it beats the same model
   without it on held-out years" (`DECISIONS.md:11`, read). Two readings: (a) new genus fractions
   are part of the named "host trees" input, so they enter the lean start; (b) they are further
   inputs and must beat held-out. On either reading D121 governs what the **model** uses, not what
   a **layer** carries, so building the bands does not by itself conflict with D121 (INFERRED).
   RECORD -1029 chose option (b) of M7 over option (a), which was the "beat held-out" route; whether
   that also settles how the new bands enter the T7 fit is not stated in -1029. Owner's word needed.
3. **D116.** "Such a tree counts toward the conifer or broadleaf total only, never as a host"
   (`DECISIONS.md:16`). *Fagus*, *Carya*, *Tilia*, *Ostrya*, *Carpinus*, *Castanea* are among those
   unlisted genera, so Tier B needs them added to T5's broadleaf list (FIA's code agrees: all are
   300 and over) or D116 amended. Tier A does not touch D116: its genera are already listed
   (`crown_cover.py:142-151`).
4. **D85 and D89 (1) for Canada.** New genera fall to "not available" in Canada under D85; *Larix*
   is partial (tamarack only) and falls under D89 (1)'s reasoning. Options 1 to 4 in section 3.
   A second Canadian source (option 3) reopens D85's rejected alternative and needs a licence
   reading at source and a vintage and measure decision.
5. **D87 and D89 (2), surrogate widths.** Birch, chinquapin and every Tier B genus would take the
   quaking-aspen crown width. Accept as D89 (2) already provides, or ask for species coefficients
   from another source.
6. **D115 item 2 and D119.** The plot table "computed once" is recomputed, and the US-half files,
   which D119 says are "kept, never rewritten", must be rebuilt (new files, the old kept aside) for
   the Canadian merge to work.
7. **T5's product.** Whether the genus list changes for T5 too or only for T6b (section 4).
8. **Order.** PNW box first (one night) or the whole US redo (three to five nights) before the
   Canadian tree tiles; and whether old tree outputs stay on the drive.

## 7. What I could not determine

- The mycorrhizal status of each genus from FungalRoot's Table S2 itself (not opened), and Table
  S2's licence. Every status in section 2 is UNVERIFIED.
- Which genera actually occur in the PNW box, and their cover there. That needs a TreeMap raster
  read over the box; not done (no heavy work during the run).
- SCANFI's class membership for `otherConiferous` and `broadleaf`, and whether v2's `tamarack` is
  still *L. laricina* only (only v1's page names it).
- The kNN 2011 maps' variable, file sizes and licence text on the page itself (read only through a
  summarising fetch).
- How a tile's time splits between reads, masks and regrid, so the time range in section 5 is wide.
- Whether *Laetiporus* was meant as the only reason for the *Quercus* band (the T5 report gives both
  sources; I read it as the control's).

## Sources read

- Code at `a79d667`: `src/forager_forecast/crown_cover.py`, `t5_layer.py`, `t6b_layers.py`,
  `t6b_run.py`; `scripts/t6b_run.py`, `scripts/pnw_build.py`; tests by grep.
- `docs/planning/DECISIONS.md` rows D83 to D92, D100, D111 to D124; `START_HERE.md`.
- `docs/audits/2026-10-06-t5-verify-report.md` sections 3 and 8; `2026-10-06-t5-source-survey.md`
  sections 2 and 4; `2026-10-07-t6b-run/genus_classes.out.txt`; `2026-10-09-pnw-monday/mosaic.json`.
- `origin/t7-mycorrhizal-plan:docs/dispatch/2026-10-15-t7-mycorrhizal-habitat.md` (M7, the inputs
  section, the citation corrections).
- Forager RECORD 2026-09-28-1023 to -1030 (read-only copy at
  `~/.cache/forager-wt/records/RECORD.md`).
- Drive, read only: `forecast-data/t6b/manifest.jsonl`, `plots.json`, `mask.json`,
  `tiles_trees.json`, directory sizes; `forecast-data/t5/treemap2023/RDS-2026-0038.zip` tree table.
- Web: SCANFI v2 readme; open.canada.ca pages for SCANFI v1, SCANFI v2 and the 2001/2011 forest
  attribute maps; Soudzilovskaia et al. 2020 open copy (Leiden repository).
