# T6b host genera for the mycorrhizal map: build report

Written 2026-10-15 (about 05:50 UTC) on branch `t6b-host-genera`. Base: forecast `origin/main` at
`a79d667`, checked equal to the remote with `git fetch` before work began, plus the dispatch commit
`1d45987`. Dispatch: `docs/dispatch/2026-10-15-t6b-host-genera-build.md` (Forager RECORD -1037, the
owner's go "1 to 3 yes"; rulings RECORD -1033, "All recommended", provisional until review).

Nothing ran on the drive. No T6b stage was run, nothing was written under `forecast-data/t6b`, the
PAUSE file was not touched. Reads only: the tree table and VAT under `forecast-data/t5/treemap2023`,
the run's `tiles_trees.json`, `mask.tif`, `plots.npz`, and a listing of `scanfi_layers/`. The night
run (`t6b-night`, stages `scanfi-layers,trees`) was live throughout.

Flags: **observed** = run or read by me today, file named; **INFERRED** = my reasoning, not measured.

## 1. Commits

| Commit | What |
| --- | --- |
| `37a7729` | Tests first: `tests/test_t6b_host_genera.py`, ten failing on `a79d667`, one guard passing; output `2026-10-15-t6b-host-genera-build/failing-first.txt` |
| `8793bce` | The build: `src/forager_forecast/t6b_hosts.py` (new), `crown_cover.py`, `t6b_layers.py`, `t6b_run.py`, `scripts/t6b_run.py`; one more test (section 3, last row) |
| `5a3cc7c` | Revert checks and read-only measurements in `2026-10-15-t6b-host-genera-build/` |
| this commit | This report, its index row, proposed row D127, a session-log row |

## 2. What was built

- **The T6b genus list** (`src/forager_forecast/t6b_hosts.py`), separate from T5's. Bands, in
  order: T5's eight (`Pseudotsuga`, `Tsuga`, `Picea`, `Abies`, `Pinus`, `Quercus`, `conifer`,
  `broadleaf`) unchanged and first; tier A `Larix`, `Betula`, `Populus`, `Alnus`, `Lithocarpus`,
  `Chrysolepis`, `Arbutus`; tier B `Fagus`, `Carya`, `Tilia`, `Ostrya`, `Carpinus`; then
  `ecm_hosts`. 21 bands, 24 value bands per tile with total cover, valid fraction and source.
  - **Tanoak and chinquapin: two bands (proposed and built).** Each band keeps one meaning, a
    genus; chinquapin is small (158 plots) but the fit under D121 decides whether it earns a place.
    Joining them is a one-line change to `TIER_A_GENERA` if the owner prefers one band.
  - **Tanoak's band is `Lithocarpus`, not `Notholithocarpus`** (a dispatch premise corrected, not a
    design change): the tree table holds 9,999 tanoak rows under `Lithocarpus` and none under
    `Notholithocarpus` (observed, section 6).
  - **Carried through** the plot table (`build_plot_table`, `t6b_layers.py`), the share and flag
    bands (`_tree_bands`), the US halves (`tree_tile_us_half`) and the Canadian fill
    (`fill_canadian_cells`, `_ca_parts`). Canada flags every new genus and `ecm_hosts` 3, "not
    available", by the existing rule for any band outside `SCANFI_BAND_CLASSES` (RECORD -1033 item
    2); no second Canadian source added.
  - `crown_cover.plot_cover` gained two keyword arguments, a genus list and totals; their defaults
    are T5's, so T5's calls are unchanged. Aspen's crown width serves genera with no Table 3
    species of their own, by the existing D89 (2) rule (no code change was needed for that).
- **The total band `ecm_hosts`**: the summed cover of an explicit member list
  (`ECM_HOST_MEMBERS`), as a share of canopy like any genus band. Proposed membership in section 5.
- **F1 fix.** Every tree tile, US half and their manifest lines carry `band_layout`, a hash of the
  band names and the total's members (today `t6b-bands-f4e9b848ba51`). `done_units`
  (`src/forager_forecast/t6b_run.py`) takes the layout; the tree and US-half stages, `us_half_done`
  and `_first_pending` pass it, so a tile of an older layout is rebuilt, not skipped. The fill also
  refuses a US half of another layout.
- **F2 fix.** `stage_plots` rebuilds when `plots.json` names another `band_layout`, not only another
  rulings string; the old `plots.npz` and `plots.json` are moved to
  `superseded/<UTC stamp>-plots/`. The table now records `bands` and `band_layout`, and
  `load_plot_table` refuses a table of any other layout. `PLOT_TABLE_RULINGS` is unchanged on
  purpose (section 7).
- **Trees-only supersede, per unit.** Just before a tree or US-half unit starts, files of that
  unit whose value file carries another layout (or none) are moved to
  `superseded/<UTC stamp>-trees/tiles/trees/` or `.../tiles/trees_us_half/`, kept, never deleted,
  and the move is written to the manifest (`kind: before_unit`, `superseded` with each file's
  sha256). Whole tile and US half are judged separately. Soil, SCANFI layer tiles and the
  manifest are never moved. A tile is absent from `tiles/trees` only while its replacement is being
  computed. Old US halves are rebuilt as new files the same way (D119's "kept, never rewritten" is
  met by moving the old file aside, not rewriting it).
- **Free-space check before each tree or US-half unit**: the section stops before the unit unless
  `forecast-data/t6b` has `tree_tile_bytes() + FREE_MARGIN` free (every band uncompressed, 7,667,712
  bytes at 256-cell tiles, plus the SCANFI stage's 2 GB margin), and says so in the manifest and
  the section summary.
- **`--box S,N,W,E`**, beside `--tiles`: the trees and trees-us-half stages offer only tiles holding
  a study cell whose centre lies in the box, edges inclusive (the PNW review's rule). Refused with
  `--tiles` or with the scanfi-layers stage. `--tiles` was left as it is: it accepts only tiles
  with Canadian cells.
- A generic `before_unit` hook in `run_section` carries the last two.

## 3. Failing first, then the fix

All ten new tests failed on `a79d667` for their stated reason (observed,
`2026-10-15-t6b-host-genera-build/failing-first.txt`, 10 failed, 1 passed):

| Test | Failure on `a79d667` |
| --- | --- |
| plot table carries every new genus and the total, T5's columns unmoved | "the plot table does not record its band list" |
| a tree tile has the new bands; Canada flags them not available | "the tile lacks the new bands" |
| a plot table of another band layout is refused | DID NOT RAISE ValueError |
| F1: an old-layout tile is rebuilt, not counted done | "the old-layout tile was counted done (F1)" |
| trees-only supersede keeps the old tile, leaves soil, SCANFI and manifest | "the old tile was not kept in a superseded folder" |
| an old-layout US half is rebuilt as a new file, old kept | "the old-layout US half was counted done (F1)" |
| F2: the plot table is rebuilt when the genus list changes | "the old table was reused (F2)", (4, 10) against (4, 23) |
| no tree tile starts without free space (trees, trees-us-half) | the tile ran, `units_ok` 1 |
| `--box` runs only the tiles with a study cell in the box | argparse: unrecognized arguments `--box` |
| T5's list and split unchanged (guard) | passes before and after by design; its evidence is revert r10 |

One test was added with the fix, not before it: a stale whole tile is moved aside without its
current US half. It covers a bug I found in my own first version (moving a current US half with a
stale whole tile); its evidence is revert r7, which restores that version and fails it.

## 4. Revert checks

Runner: `2026-10-15-t6b-host-genera-build/revert_checks.py`; results `revert_checks.out.json`. Per
the Forager CLAUDE.md rules: each file saved to a copy before editing and restored from that copy,
never from git; each run's output checked for collection, import and syntax errors before the JUnit
XML was read (none found, no check refused); each restored file confirmed byte-identical to the
saved copy and to `HEAD`; the working tree equal to `HEAD` afterwards (observed: `True`).

| Check | One-line revert | Failed (predicted set matched exactly) |
| --- | --- | --- |
| r1 | `T6B_BANDS = T5_BANDS` | plot table, tile bands, F1, US half, F2 (all "13 more items", or the 10-column table) |
| r2 | the total summed as 0.0 | plot table, tile (total not the sum of its genera) |
| r3 | `done_units` ignores the layout | F1, supersede, US half, stale-whole |
| r4 | `stage_plots` ignores the layout | F2 only |
| r5 | `load_plot_table` accepts any layout | the refusal test only |
| r6 | the supersede never moves a file | supersede, US half, stale-whole (nothing kept) |
| r7 | whole tile and US half judged as one group | stale-whole only (`KeyError: 'tile_state'`: the US half was moved, so no fill) |
| r8 | free space needed set to 0 | both free-space tests |
| r9 | `--box` filter removed from the trees stage | box test only (six tiles ran, not one) |
| r10 | `"Betula"` added to T5's `HOST_GENERA` | the T5 guard, among 7 (also T5's own `test_the_strip_is_the_planned_one` and five layout tests, each naming the extra Betula band) |

Each failure message names something only its own edit could cause.

## 5. Proposals for the owner's review

**Total-band membership (`ecm_hosts`), proposed: all eighteen genus bands.** *Pseudotsuga*,
*Tsuga*, *Picea*, *Abies*, *Pinus*, *Quercus*, *Larix*, *Betula*, *Populus*, *Alnus*,
*Lithocarpus*, *Chrysolepis*, *Arbutus*, *Fagus*, *Carya*, *Tilia*, *Ostrya*, *Carpinus*. Not in it:
every other genus, so Cupressaceae and yew in `conifer`, and maples, ash and elm in `broadleaf`.
Two judgement calls: *Arbutus* forms arbutoid mycorrhizas with ectomycorrhizal fungi, and *Populus*
is both ecto- and arbuscular mycorrhizal; both are in the list as proposed. Every status is from
memory: FungalRoot's genus table was not opened, and its licence is unreadable (RECORD -1036). The
list is one constant, so a member can be dropped without changing any genus band, though the layout
hash changes and tiles are rebuilt.

**D116 row, proposed as D127** (added at the top of `docs/planning/DECISIONS.md`, marked
"Proposed, for the owner's review; not in force until accepted"; D116's row not edited): for T6b
only, *Fagus*, *Carya*, *Tilia*, *Ostrya* and *Carpinus* each count as a host band of their own and
toward `ecm_hosts`; every other D116 clause stands for them (broadleaf by FIA code, aspen's crown
width under D89 (2), still counted in `unlisted_genus_trees`); T5 unchanged. Rejected: adding them
to T5's broadleaf list, leaving tier B out, one band for *Ostrya* and *Carpinus*. **D127, not D125:**
D125 and D126 are already used on the unmerged branch `t7-mycorrhizal-plan` (observed), so the
number must be checked again at merge time.

## 6. Premises re-checked

- Base `a79d667` equals `origin/main` (observed, `git rev-parse` after fetch).
- `HOST_GENERA` and `BANDS` at `crown_cover.py:156-157` on `a79d667`, F1 at `t6b_run.py:61-72`, F2
  at `scripts/t6b_run.py:143-150`, `supersede()` moving soil, manifest and `scanfi_layers`, no
  free-space check in `stage_trees`: all as the verify report says (read, and F1, F2 and the
  free-space gap shown by failing tests).
- **Every genus has data in the US tree table** (stop condition), counted today from the drive's
  `RDS-2026-0038.zip` member, read only. Rows, live trees of 5 in and up, plots: *Larix* 22,619,
  15,688, 2,603; *Betula* 62,000, 43,298, 9,124; *Populus* 89,567, 58,209, 6,570; *Alnus* 3,583,
  2,990, 418; *Lithocarpus* 9,999, 7,581, 449 (*Notholithocarpus* 0); *Chrysolepis* 1,162, 785,
  158; *Arbutus* 4,924, 3,724, 603; *Fagus* 35,942, 22,002, 5,136; *Carya* 42,625, 33,089, 9,622;
  *Tilia* 10,789, 9,240, 2,562; *Ostrya* 11,128, 4,190, 2,006; *Carpinus* 6,720, 2,015, 903. The
  live-tree and plot counts equal the verify report's where it gives them.
- **No existing plot-table column changes meaning** (stop condition), checked on real data: the
  new table built from the real tree table into a temporary folder (`plot_table_real.py`, 25.7 s,
  693 MB peak, 65,814 plots, 23 columns, 12,638,298 bytes) has its total, T5's eight columns and
  CANOPYPCT bit-identical to the run's own `plots.npz` on the drive (`plot_table_compare.out.json`).
  Each new genus column is non-zero on exactly the plot counts above; `ecm_hosts` on 59,908 plots.
- **T5's outputs unchanged** (stop condition): `t5_layer.py`, `scripts/t5_build.py` and every T5
  test are untouched (`git diff a79d667 --stat`); T5's tests pass unchanged; `plot_cover`'s
  defaults are T5's list.
- No premise in the verify report was wrong in a way that changes the design. Two differences,
  neither a stop: the tanoak genus string (above), and the PNW tile count (section 8: 296 tiles by
  the box-centre rule against the report's "about 344", which counted the PNW window's rectangle).

## 7. Suite and ruff

- Baseline on `a79d667` before any change: 592 passed (observed).
- After the build: **604 passed**, 0 failed (592 plus the 12 new), 236.8 s, under the 5 GB cap at
  nice 10, basetemp under `.pytest-tmp/` (not committed).
- `ruff check .`: all checks passed. `ruff format --check .`: 294 files already formatted.

## 8. The PNW run (for the planner to schedule; not run)

Pause the night section first (its PAUSE file), so only one writer touches the manifest. Then, from
a checkout of `t6b-host-genera` with its `.venv` (the runner commits and pushes its evidence to the
branch of the checkout it runs in):

```
systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0 \
    nice -n 10 .venv/bin/python scripts/t6b_run.py --until 07:00 \
    --stages plots,trees,trees-us-half --workers 2 --box 40,49,-125,-111 \
    --pause-file /run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b/PAUSE-pnw
```

- **Box**: 40 to 49 N, 125 to 111 W, the pilot map's `PNW_BOX` (`src/forager_forecast/pnw.py:30`)
  and the PNW review's box. D123's weather box reaches 49.5 N; `--box 40,49.5,-125,-111` adds only
  14 Canada-only tiles, all still waiting for their SCANFI layers, so it runs the same units.
- **Expected units** (observed, read-only `pnw_units.py` on the drive's mask and listing): 296 tree
  tiles, the same 296 the PNW review listed with its own code: **283 trees units** (273 US-only, 7
  border tiles whose SCANFI layers are ready, computed whole, 3 Canada-only with layers ready) and
  **13 trees-us-half units** (border tiles still waiting for SCANFI). Plus the plot table, rebuilt
  once (about 26 s, measured on the same data).
- **Time** (INFERRED): at the run's measured 36.6 s of wall time per tile at two workers (verify
  report section 5), 296 units take about 3.0 h; with 21 split layers regridded instead of 9, up
  to about 5 h. One night section, if started by about 01:00 for a 07:00 stop; otherwise it
  resumes the next night.
- **Space** (INFERRED from the verify report's 52 kB per band per tile): new tiles at most about
  1.3 MB each with flags, about 0.4 GB for 296; the plot table 12.6 MB. Old files are moved on the
  same drive, so the move frees nothing and costs nothing. Free at 05:48 UTC: 6,345,211,904 bytes
  (observed). The run stops itself under about 2.01 GB free.
- **Afterwards**: the moved-aside old tiles stay under `t6b/superseded/<stamp>-trees/` until the
  owner's word (RECORD -1033 item 5). The PNW mosaic and images (`scripts/pnw_build.py`) still show
  only their four named layers; they read bands by name and are unaffected.

## 9. What is untested, and what to watch

- **No tile was computed on real data.** The new bands, the Canadian "not available" flags, the
  total and the supersede were exercised on T6b's synthetic world only. The real plot table was
  built (temporary folder), but no real tile. Per-tile time and file size with 24 bands are
  INFERRED.
- **The two-worker path of `before_unit`** (`run_section` with `workers > 1`) is not exercised by a
  test; every new test runs one worker. The code path is the same call before `pool.submit`.
- **The old code still running on the drive.** The night unit runs a different checkout. Read from
  the code, INFERRED, not run: (a) it reads the rebuilt `plots.npz` correctly, since T5's columns
  and CANOPYPCT keep their positions (shown identical above) and the old code reads columns 1 to 8
  and the last; (b) it will not rebuild the table, since `PLOT_TABLE_RULINGS` was kept unchanged for
  this reason; (c) it counts new-layout tiles as done, which is right; (d) if it reaches a border
  tile whose US half is new-layout, its fill refuses the band names and records a failed unit.
  The night unit should move to this code before any tree tile, as the planner planned.
- **Moving the night run to this code starts the continental rebuild by itself.** Every US tile of
  the old layout is no longer done, so an unfiltered trees stage supersedes and rebuilds each one,
  one unit at a time (about 2,000 tiles, three to five nights by the verify report). That is the
  owner's order (PNW first, then the rest of the US), but it begins as soon as an unfiltered
  section runs the new code; no separate step is needed or offered.
- **Statuses and licences**: every mycorrhizal status is from memory (section 5).
- **T7 reading the bands**: not built here (D121, RECORD -1033 item 3).
- **The superseded folder** is never emptied by code; removing old tiles is the owner's word.
