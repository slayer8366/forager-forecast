# The PNW for Monday: completion report

Written 2026-10-09 (UTC) by the PNW coder session, branch `t6b-pnw-monday`, base
`origin/t6b-continental-layers` at `c2b0769`. Dispatch: Forager RECORD -772
(`prompts/preserved/2026-10-09-04.md`), with the owner's additions -773 and -775 to -777 and the
planner's calls of -774. Evidence: `docs/audits/2026-10-09-pnw-monday/`.

**In short:**
- **Built and run:** D119's US-half path; a PNW mosaic; four labelled images; four PMTiles
  archives; a browsable page on the site's preview; the checks; the briefing. Housekeeping done.
- **Stopped, as ruled:** 3 of the 20 PNW border tiles hit an existing T6b guard. The planner chose
  to leave them uncomputed for now; option (a) waits for the owner.
- **Checks:** tile edges agree exactly (29 tree windows, 10 soil windows). The two fixed check
  cells in the box match. The seam check gives no verdict, Canadian side pending.

## 1. What landed

forager-forecast, `t6b-pnw-monday`:

| Commit | What |
|---|---|
| `07b8daa` | D119. `tree_tile` split into its parts with no change of output; `tree_tile_us_half`, `fill_canadian_cells`, stage `trees-us-half`; percent byte encoding; D119 row |
| `dbc00be` | Revert checks, 9 of 9 bite |
| `d42a63f` | Check rules, committed before any PNW value was read |
| `640f697` | Render (`pnw.py`, `scripts/pnw_build.py`) and checks (`scripts/pnw_checks.py`) |
| `ee0c1fc` | TASKS.md and START_HERE corrected against origin/main 36cc647 |
| `8653ad7` and the next | The runner's own commits for step 1 (evidence under `2026-10-09-pnw-monday/run/`) |
| this commit | `--pause-file`, the not-computed style, check outputs, step logs, briefing, this report |

zynergy-site, `forager-forecast-pnw` from origin/main 89593b1 (`e126901` to `7dde25e`):
- the page `Forager/forecast/`, with `app.js`;
- the data: four PMTiles and the boundary lines;
- `vendor/` with MapLibre GL JS 6.13.0 and PMTiles 4.5.0;
- `_redirects` (301 from lowercase);
- a byte-range handler in `functions/_middleware.js`;
- README rows.

No PR, no merge (D40).

## 2. D119 and its tests

- **The decision (D119, owner):** "Compute the US half now".
- **What the code does:**
  - A border tile's US cells go to `tiles/trees_us_half/`. Its Canadian study cells carry flag 4,
    "pending".
  - Its manifest line says "US cells done; Canadian cells pending SCANFI (D119)".
  - Later, the trees stage fills only the Canadian cells. It copies every other cell from the
    US-half file, which is never rewritten.
- **Tests,** on T6b's synthetic world, through the real entry points:
  - the US half equals the whole tile on every cell outside Canada;
  - one tile against sixteen smaller tiles is equal bit for bit;
  - filling gives exactly the whole tile, and the US-half file hashes the same afterwards;
  - a non-US-half file is refused;
  - through `scripts/t6b_run.py`: the tile waits, then its US half runs, then the fill runs;
    a whole tile is never offered to the US-half stage again.
- **Refactor guard:** synthetic outputs of both SCANFI routes over five tiles were saved before the
  split and compared after. Equal.
- **Reverts:** 9 checks, 9 bite, each with a message specific to its edit (`revert_results.json`).
  Restores come from saved copies, and every file was confirmed equal to its pre-edit hash.
- **Suite:** 460 before, 473 after, under a 2 GB cap. Ruff clean.

## 3. The heavy steps (planner's go after T6b paused at 03:44:52 PDT)

Each step ran under `MemoryMax=5G MemorySwapMax=0` at nice 10, one at a time. Peak is the scope's
cgroup `memory.peak`; disk is the data drive's free space before and after. Logs are in `steps/`.

| Step | Time | Peak | Data drive used | Result |
|---|---|---|---|---|
| 1, trees-us-half, 20 tiles | 25 s | 1,348 MiB | 0 | **Stopped** on tile 3: "the TreeMap raster does not cover the US side of this tile" (section 4). No file written |
| 1b, the other 17 tiles | 686 s | 2,484 MiB | 11 MiB | 17 ok, 0 deferred |
| 2, mosaic | 135 s | 2,198 MiB | 482 MiB | Soil and trees mosaics |
| 3, lines | 49 s | 561 MiB | 0.4 MB | 1,902 lines |
| 3, images | 58 s | 1,467 MiB | 8 MiB | 4 SVGs |
| 3, PMTiles, four runs | 21 to 50 s | 1,581 to 2,203 MiB | 46 MiB | 8.8, 18.3, 15.2 and 7.6 MB |
| 4, tree edges | 175 s | 477 MiB | 1 MiB | 29 agree exactly |
| 5, soil edges | 1,449 s | 143 MiB | 1 MiB | 10 agree exactly; 11 SoilGrids fetches |
| 6, ten cells | 17 s | 202 MiB | 0 | 2 of 2 match |
| 7, seam | 5 s | 1,201 MiB | 0 | No verdict |

- **Largest peak:** 2.48 GB, in step 1b.
- **Data drive:** 3.96 GB free before, 3.38 GB after the steps, 3.2 GB after the browser
  screenshots.
- **Root disk:** about 2.45 GB to 2.3 GB free. The site branch adds 50 MB.
- **Last heavy step ended** 04:34:43 PDT. The planner was told.

## 4. The stop: three border tiles

The tiles are 256_-31_20, 256_-30_20 and 256_-29_20. All three hit
`t6b_layers._treemap_part`'s guard at line 397. That is T6b's code; this session did not change it.

**What the read-only diagnosis found** (`diag` in the planner message):
- Bad pixels: 235, 4,956 and 7,721 TreeMap pixels.
- Where: on BC coasts at 48.68 to 49.16 N, 122.9 to 125.0 W.
- Every one is side NONE. Its cell lies in no CEC political polygon, but NALCMS calls it land.
- D115's pixel rule lets a NONE pixel count for either side, and these lie outside TreeMap's raster.

**Rulings:**
- **The planner ruled (b):** leave the three tiles uncomputed. They are drawn "not computed yet",
  dark grey, in the images and on the page.
- **Pending with the owner:** (a), "a NONE pixel outside TreeMap's raster is no data for the US
  side". That is my recommendation, the narrowest change.

**Size:** the three tiles hold 25,760 US study cells in the box, 0.16% of the box's US cells.
1,720, 829 and 23,211 by tile; the last is around Bellingham.

**If (a) is chosen:** the re-run is the three US halves (about 2 minutes, 2 workers) plus the
mosaic, images and three tree PMTiles. That is about 6 minutes of compute from the timings above.
Then copy and deploy, about 15 minutes in all, plus a new D row.

**Beyond D119:** T6b's own whole-tile run of these tiles will hit the same guard later.

## 5. Checks

The rules are in `check-rules.md`, committed at `d42a63f` before any value was read.

| Check | Sample | Against | Result |
|---|---|---|---|
| Tree tile edges | 32 windows of 64 x 64 cells at fixed corners; 29 computed, 113,664 cells compared, 107,416 of them with a cover value. Excluded: 2 windows with Canadian cells only, 1 with no study cell, 5,120 cells inside the held-back tiles | 16,674,133 study cells in the box | Exact on every band and flag |
| Soil tile edges | 11 windows; 10 computed, 40,960 cells. 1 window off the coast has no study cell | same | Exact |
| Ten cells | 2 of the rule's 10: coast-oregon (tile 256_-33_12, whole) and border-us-selkirks (256_-23_19, a US half, so D119 on real data) | the other 8 lie outside the box | Soil: mean, Q0.05 and Q0.95 match. Trees: valid fraction, cover, 8 shares, source and 8 flags all within tolerance |
| 49 N seam | T5's 25 transects, 80 samples a side | — | No verdict: 0 transects with a border step, the Canadian side pending |

- **The ten-cell checker's controls:** positive (agrees with the pipeline on 12 synthetic US
  cells) and negative (a doubled canopy table fails), `tests/test_pnw_checks.py`.
- **What the seam check does show:**
  - Of 2,000 US-side samples, 1,443 have a value.
  - All 557 empty ones lie in the held-back tile 256_-29_20, west of 122.16 W
    (`seam-us-missing.out.txt`).
  - Within-US step medians: cover 9.29 points, Douglas-fir share 0.042.

## 6. Outputs and how to open them

**Images,** labelled SVGs that open in any web browser:
- `/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/pnw/images/`
- files `pnw-soil-ph.svg`, `pnw-tree-cover.svg`, `pnw-douglas-fir.svg`, `pnw-hemlock.svg`
- each carries the label, the sources and the data licence.

**PMTiles,** zoom 5 to 9:
- the same drive under `forecast-data/pnw/pmtiles/`
- also opens at pmtiles.io, in grey.

**Mosaics:** `forecast-data/pnw/mosaic/`.

**The page:** https://forager-forecast-pnw.zynergy-site.pages.dev/Forager/forecast/ (preview).
Production needs the owner's merge.

**Checked on the preview,** by headers, bodies and a headless Firefox through geckodriver
(`browser_check.py.txt`, `.out.json`; screenshots in `forecast-data/pnw/preview-check/`):
- the page loads;
- the lowercase paths 301 to `/Forager/forecast/`, and `/forager` is unchanged;
- the worker `vendor/maplibre-gl-worker.mjs` loads under the unchanged CSP: 1 worker, 0 map errors;
- all four layers draw;
- a real pointer tap at 45 N, 122 W read "Hemlock: 25.5%", and the mosaic holds 25.52 at that
  point;
- Range requests:
  - `0-126`, `1000000-1000999`, `15219000-` and `-5` return 206;
  - their bytes equal the local file's (sha256);
  - an out-of-range request returns 416.

**The Range handler** wasn't planned. The asset server answered Range with 200 and the whole file,
and inside a Function it gave no Content-Length. So the middleware reads the archive and cuts the
range, for `/Forager/forecast/data/*.pmtiles` only.

## 7. Confirmed vs inferred

**Confirmed by running or reading:**
- every count above;
- the guard's cause on the three tiles, per pixel;
- the preview's behaviour;
- the vendor tarballs' sha512 against the npm registry.

**Inferred:**
- that the asset server, not the middleware, dropped Range. The middleware passed the request
  through unchanged, and an untouched asset like `app.js` also returned 200;
- that reading the whole archive per range request is cheap enough for a test area. Not load-tested.

## 8. Could not determine

- Whether Cloudflare would cache the 206 responses; not measured.
- How the page behaves on a phone. Only desktop headless Firefox was used.
- No independent review (D18).

## 9. Premises that were wrong

- **23 tiles.** The dispatch's 23 tiles touching Canada is 20 with both sides. Three hold Canadian
  cells only. Continent-wide there are 92 mixed tiles.
- **The seam check** cannot be run as a verdict until Canadian cells exist.
- **Range and the asset server.** The assumption that Pages answers Range on static assets did not
  hold behind this site's Function.
- **Tiles finished overnight.** "The PNW US tree tiles finish in tonight's section" held for the
  273 US-only tiles. Three of the border tiles cannot run under the current rules.

## 10. Decided beyond scope (each said here)

**Code and site changes:**
- **`--pause-file`.** T6b's PAUSE file was set by the planner, and the runner honours it, so step
  1's first start did nothing. I added an option rather than touch that file.
- **The middleware Range handler** on the site.
- **The page:** a `[hidden]` CSS fix, and `window.pnwErrors` kept for checks.

**Choices of mine:**
- **What the page shows:** Douglas-fir and hemlock as the two host layers, with total cover for
  context. Reasons are in the briefing.
- **How the other 72 mixed tiles get their US halves:** the `trees-us-half` stage is in the
  runner's default stages on this branch. A T6b section started from this branch picks them up
  automatically. Sections run from the c2b0769 checkout do not; they need this branch merged into
  `t6b-continental-layers`, or one run of `--stages trees-us-half`.

**A slip:** commit `b1c6177` on the site branch cites "RECORD -778" for the planner's (b). That
number was not read anywhere; it is a guess. The ruling's real record ID is not known to this
session. Pushed, so not amended.

## 11. Not done

- An independent review.
- The owner's word on (a).
- Merges: both branches.
- Phone check of the page.

## 12. Appended 2026-10-09 12:48 UTC: D120 and the re-run (supersedes the held-back state above)

Sections 1 to 11 stand as written. Where they describe the three held-back tiles, this section
supersedes them.

**The ruling.** The owner chose (a), Forager RECORD -784, verbatim "1 yes". Filed as **D120**: a
pixel in no country polygon (side NONE) that lies outside TreeMap's raster is no data for the US
side. A US-side pixel outside the raster is still refused.

**The change** (`t6b_layers._treemap_part`) is one condition on the guard, plus a comment. The
`blank` mask already held every pixel outside the raster. `RULINGS` was left unchanged, so no
other tile's tags differ.

**Tests and reverts:**
- **The new test** (parametrised, `test_a_no_country_pixel_outside_treemap_...`): a TreeMap raster
  cut short, with the cut-off strip set to side NONE, gives no data there and values east of it.
  The same strip set to side US is still refused.
  - Seen red before the change, for the right reason: the guard's message.
- **Revert runner:** 11 checks, 11 bite (`revert_results_2.json`). Two are for D120: removing the
  condition refuses NONE pixels again; dropping the US refusal fails the US case.
- **Suite:** 473 to 475 passed.
- **Commit:** `d5c338b`.

**The re-run** (T6b paused, unit inactive since 05:22:38 PDT; same caps):

| Step | Time | Peak |
|---|---|---|
| US halves of 256_-31_20, -30_20, -29_20 | 161 s | 2,343 MiB |
| Mosaic, images, 3 tree PMTiles (first pass) | 321 s | 2,177 MiB |
| Mosaic, images, 3 tree PMTiles (second pass, below) | 354 s | 2,246 MiB |
| Tree edges | 176 s | 725 MiB |
| Seam | 7 s | 1,231 MiB |

- **Last heavy step ended** about 05:45:25 PDT. The planner was told.
- **Disk:** the data drive ended at 3.2 GB free and the root disk at 2.1 GB.

**A labelling error found and fixed.** The first pass showed 14,683 cells in the box still "not
computed yet". They are the Canadian cells of three tiles holding Canadian cells only:
256_-30_21, 256_-31_21, 256_-32_20 (section 9). Such a tile has no file until SCANFI is in.
- They were never held back. They are Canadian cells pending, like a US half's.
- `scripts/pnw_build.py` now marks them pending.
- The first version of this report and of the images had counted them in the 119,935
  "not computed" cells: 94,175 Canadian (14,683 of them in these Canada-only tiles) and 25,760 US.
- The US figure in section 4 (25,760) stands.

**Now, in the box:**
- Every US study cell has its tile: 0 cells "not computed yet".
- 102,543 Canadian cells are pending.
- Tree cover is defined in 16,377,178 cells, shares in 6,991,082.
- The earlier figures are kept as `*-v1.json`.

**Checks re-run:**
- **Tree edges:** 29 of 32 windows agree exactly, 117,760 cells compared (113,664 before). The
  1,024 cells still excluded are in the Canada-only tiles.
- **Seam:** still no verdict, Canada pending. All 2,000 US-side samples now carry a valid fraction
  and source (1,443 before). 1,974 have a cover value; the other 26 are under half valid, such as
  water. Within-US median steps: cover 8.03 points, Douglas-fir share 0.041.
- **Soil edges and ten cells:** not re-run; neither reads the changed tiles.

**On the preview** (site `01b3cde`; `browser_check_d120.out.json`; screenshots in
`forecast-data/pnw/preview-check-d120/`):
- 0 map errors.
- The worker loads from the site, and all four layers draw.
- A real pointer tap at 48.775 N, 122.273 W, inside 256_-29_20 (a D120 tile), read "Hemlock:
  29.5% of the canopy". The mosaic holds 29.47 there.
- A Range request on the new tree-cover archive returns 206, and its bytes equal the local
  file's.
- The page's "held back" legend key is removed; the colour stays in `app.js` for any later case.

**Also from the first run, and wrong:** section 10 of this report said T6b's own whole-tile run
would hit the same guard. Under D120 it no longer does, for these pixels.

## 13. Appended 2026-10-09 16:53 UTC: the D18 review's items (Forager RECORD -786) and the static-tile site

Sections 1 to 12 stand as written; where they describe the site's PMTiles archives and the
byte-range handler, this section supersedes them.

**F1 (blocking): a Canada-only tile could get a US-half line with no files.** That line counted
as done, and once SCANFI was in the trees stage would have tried to fill a file that does not
exist, ending the section. The reviewer reproduced it. Fixed twice:
- `stage_trees_us_half` offers only tiles with both US and Canadian study cells
  (`has_us_cells`, read from the mask);
- `us_half_done` requires a line that names its files.

Tests (red first, for the reviewer's reason):
- the stage offers no Canada-only tile;
- an "ok" line with no files is not a done US half;
- through the runner, a Canada-only tile waits, gets no US half, and becomes a whole tile by
  `tree_tile` once its layers exist.

Reverts: `revert_results_3.json`, 13 of 13 bite. Each guard alone bites its own test. With both
reverted together the runner test fails with the reviewer's error, a missing US-half file
(checked by hand, restored from a saved copy, hash confirmed). Suite 475 to 480.

**F2 to F5:**
- F2 and F3: the briefing gives 850 of the 2,015 US-only tree tiles at 28bbf09, plus 20 of the 92
  straddling tiles. It says Douglas-fir showed no step across 49 N, as did the conifer and
  broadleaf totals. The box's list now includes northern Nevada and northwestern Utah.
- F4: a START_HERE row records D120.
- F5: the site's new tiles are nearest at every zoom (`tiles.tile_values`), so a sentinel is
  never blended. The PMTiles archives on the drive keep their averaged overviews below zoom 9 and
  are no longer used by the site; read them at zoom 9 only.

**The site, the owner's choice "A: Pre-cut tiles, go live" (RECORD -786).**
- **Tiles:** static grey+alpha PNGs, `Forager/forecast/data/<layer>/{z}/{x}/{y}.png`, zooms 5 to 9,
  570 per layer, 2,280 in all, 55 MB. The site now holds 2,304 files; the largest is 1.08 MB.
  - The tiles were cut on the laptop under a 2 GB cap, peak 0.67 GB, so T6b kept running.
  - Every tile meeting the bounds is written, 64 of them empty, because a missing path here
    answers with the home page.
- **Dropped:** `pmtiles.js`.
- **Middleware:** byte-identical to origin/main again (`git diff` empty).
- **New files:** `_routes.json` keeps the Function off the tiles; `_headers` gives them
  `Cache-Control: public, max-age=3600, stale-while-revalidate=86400`.
- **README:** the handler rationale is replaced by the static-tile description.
- **Copy (S5):** the page text "per forager group" now reads "per mushroom group", and the "held
  back" text is gone.

**Checked on the preview** (`browser_check_static.out.json`; deployment f77ebe9b, site commit
8423138; screenshots in `forecast-data/pnw/preview-check-static/`):
- **Tiles:** four tiles across layers and zooms are byte-identical to the local files. They answer
  200 `image/png` with the cache header above and without the middleware's CSP header, so the
  Function did not handle them.
- **Rendering:** in headless Firefox, all four layers drew at zooms 6, 8 and 10 with 0 map errors.
  The worker loaded from the site, and 245 data requests were made, all `.png`, none to PMTiles.
- **Two real pointer taps on the hemlock layer:**
  - At 45.0 N, 122.0 W the readout was 21.0% (grey 42).
  - In D120 tile 256_-29_20 the readout was 30.5% (grey 61).
  - In each case the grey byte equals the expected one. That is floor(2v + 0.5) of the master cell
    under the centre of the zoom-9 pixel the tap fell in: 20.80 and 30.35.
- **A correction to my earlier tap check.** I compared the readout with the cell at the rounded
  coordinates the readout prints. That cell can be a neighbour. The exact comparison above
  replaces it (the page now keeps `window.pnwLastTap` for checks).
- **Not yet propagated:** on the branch alias the removed `vendor/pmtiles.js` still answered 200
  at the time of checking, while the deployment's own URL answered with the home page (removed).
  Likely the edge still holds the old file; not confirmed.
