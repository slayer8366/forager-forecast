# Review: T6b host genera (branch `t6b-host-genera`), under the standing protocol (D18)

- **Reviewed:** `origin/t6b-host-genera`. The dispatch named head `f874616`; the worktree was cut
  at `b0a0e88`, two commits later. Those two commits (`25cf772`, `b0a0e88`) are the continental
  section's own evidence commits (the night unit now runs from a checkout of this branch, Forager
  RECORD -1047) and touch only `docs/audits/2026-10-07-t6b-run/` (observed,
  `git diff f874616..b0a0e88 --stat`: 3 files, 10 insertions). Code reviewed is `8793bce`'s, unchanged
  since. Diff base: main `a79d667`.
- **Commissioned by:** the Forager planner under the owner's "Continue building the PNW with
  whatever else needs to be done" (RECORD -1049, -1050). D18 for the 13 new bands was open (T7
  verify report V6, `origin/t7-pnw-verify`).
- **Read:** the dispatch (`docs/dispatch/2026-10-15-t6b-host-genera-build.md`), the build report and
  its evidence folder, the verify report (`origin/t6b-host-genera-verify`), the T7 verify report V4
  to V6 (`origin/t7-pnw-verify`), the 2026-10-11 T6b PNW layers review, DECISIONS D18, D85, D89,
  D115, D116, D119, D121 and the proposed D127, START_HERE, RECORD -1029 to -1050.
- **Reviewer:** a Claude session separate from the builder, worktree
  `~/Zynergy/forager-forecast-host-genera-review`. Nothing was written on the drive; the running
  `t6b-night` unit, its PAUSE file and its checkout were not touched. No GBIF, climate or
  Open-Meteo request; no fit; no merge. Data reads at nice 19 under memory caps.
- **Flags:** READ = opened in this session, cited by file:line or URL; OBSERVED = command output in
  this session, file named; INFERRED = my reasoning; COULD NOT DETERMINE is said where it applies;
  UNVERIFIED = from memory.
- **Evidence:** `2026-10-15-t6b-host-genera-review/`. The scripts are saved as `.py.txt`,
  byte-identical to what ran, so the repository's lint does not run on them; to re-run one, copy it
  to `.py` in the same folder and run it from the repository root with the worktree's `.venv`.

## Verdict

**Holds with items.** The code does what the dispatch and the owner's rulings ask. T5 is untouched.
F1 and F2 are fixed. The supersede moves only tree outputs and keeps them. The free-space stop and
`--box` work. On the drive, all 296 PNW box tiles carry the new layout. The 13 new bands are
consistent with each other and with the reviewed bands. Ten cells recomputed independently from
the source rasters agree with the tiles to 2.6e-7 on every share. Every tile-edge window agrees
exactly: 29 windows, 117,110 cells, 0 differences (item 6).

Nothing found blocks T7 from **reading** these bands for the PNW. Two kinds of item still stand:

- **Blocking for the D40 merge:** item 2. Lint fails at the branch head, so the CI run on a pull
  request would be red.
- **Owner decisions before the fit uses particular bands** (RECORD -1030's point of no return 2):
  - `ecm_hosts` and tier B rest on proposals (items 11 and 12).
  - The Canadian Larix flag rests on a reading that no ruling covers (item 10).

## Items

1. **The code holds against the dispatch (not blocking).** READ, with tests re-run.
   - **The T6b-only genus list.** `src/forager_forecast/t6b_hosts.py:32-53` puts
     T5's eight bands first in T5's order, then tier A, tier B and `ecm_hosts`. `plot_cover` gains
     two defaulted arguments (`crown_cover.py:230-276`). With the defaults it computes exactly
     what it did before: the accumulator keys and `by_band` order are T5's.
   - **A tree counts in its genus band and in conifer or broadleaf, as before**
     (`crown_cover.py:268-270`). So conifer and broadleaf are unchanged by the new bands. The
     build report's real-data table comparison and T7 V4's bit-identity of the 19 shared bands
     both agree with this.
   - **The total** is the sum of its members' crown area (`crown_cover.py:274`). The members must
     be bands, or the call raises ValueError.
   - **F1.** `done_units` takes the layout (`src/forager_forecast/t6b_run.py:61`). The tree stage,
     the US-half stage, `us_half_done` and `_first_pending` pass it.
   - **F2.**
     - `stage_plots` rebuilds on a layout change and moves the old table aside
       (`scripts/t6b_run.py:159`).
     - `load_plot_table` refuses another layout, and also refuses a table with no layout
       (`t6b_layers.py:327`).
     - `fill_canadian_cells` refuses a US half of another layout (`t6b_layers.py:842`).
   - **The supersede.** `move_aside_stale` and `before_tree_unit` (`scripts/t6b_run.py:271`,
     `:291`):
     - Only the unit's own tree files are moved, each group judged by its own value file.
     - Soil, SCANFI layer tiles and the manifest are never in the lists.
   - **Free space.** `require_free_space(T6B, tree_tile_bytes() + FREE_MARGIN)` runs before each
     unit.
   - **`--box`.** `box_tile_keys` and `parse_box` (`:512`, `:528`) use the 2026-10-11 review's
     cell-centre rule. The option is refused together with `--tiles` or `scanfi-layers` (`:607`).
   - **T5 untouched.** `git diff a79d667..HEAD` lists no change to `t5_layer.py`,
     `scripts/t5_build.py` or `tests/test_t5_layer.py` (OBSERVED).
   - **Suite (OBSERVED, this session).** `uv sync --locked --all-groups`, then pytest at nice 10
     under a 5G cap with basetemp `.pytest-tmp/suite`: **604 passed**, 0 failed, 0 errors, 0
     skipped, 271 s. That equals the build report's 604.

2. **Lint fails at the branch head (blocking for the D40 merge; not for T7).** OBSERVED:
   - `ruff check .` gives 2 E501 errors and `ruff format --check .` would reformat 1 file. All of it
     is in `docs/audits/2026-10-15-t6b-host-genera-build/plot_table_real.py`, which entered with
     `5a3cc7c`, after the build commit `8793bce` the report's ruff run describes.
   - The build report's section 7 ("all checks passed", "294 files already formatted") is
     therefore true of `8793bce`, not of the branch.
   - CI runs `ruff check .` and `ruff format --check .` on every pull request
     (`.github/workflows/ci.yml:45-48`), so a merge PR would go red.
   - Options for the planner (none chosen here):
     - Rename it `.py.txt`, as the 2026-10-11 review did with its scripts.
     - Add it to `pyproject.toml`'s `exclude` as D124 did for two evidence scripts.
     - Reformat it. That makes the committed file differ from what ran, so it would need saying.

3. **The two-worker path of the new hook is untested, but has run correctly on real data (not
   blocking).**
   - My own revert R4 removes `check_before` from the two-worker path
     (`src/forager_forecast/t6b_run.py:303`). With that edit, 56 of 56 tests pass across
     `test_t6b_host_genera.py`, `test_t6b_run.py`, `test_t6b_us_half_runner.py` and
     `test_t6b_layers.py` (OBSERVED, `revert_review.out.json`). Nothing guards that path; the build
     report says so (section 9).
   - The first PNW section ran with two workers (RECORD -1039, -1041).
   - The manifest holds 296 `before_unit` lines that moved 606 files: 15 lines from that
     two-worker section (`superseded/20261015T055455Z-trees`, 44 files), 268 from the one-worker
     section and 13 from the US-half stage. Every moved file exists where its line says and
     hashes to the recorded sha256. No line stopped a section (OBSERVED,
     `supersede_check.out.json`).
   - The superseded folders hold only `tiles/trees`, `tiles/trees_us_half` and the plot table
     (and the 2026-10-07 folder from before this branch).
   - Recommended, not required: a two-worker test before any two-worker tree section.
     RECORD -1041 already runs trees with one worker for memory.

4. **The new bands on all 296 box tiles are consistent (not blocking).** OBSERVED,
   `box_new_bands.out.json`: 283 whole files and 13 US halves, all tagged
   `t6b-bands-f4e9b848ba51`, none missing.
   - **US side** (16,571,590 study cells, 6,991,082 with shares):
     - Every new share band is defined on exactly the cells where `share_Pseudotsuga` is: 0
       differ.
     - Every new flag equals Pseudotsuga's flag: 0 differ.
     - No share lies outside [0, 1].
     - `share_ecm_hosts` equals the sum of the 18 genus shares within 7.8e-8 (0 cells off by more
       than 1e-5). The 18 genus shares sum to at most 1.00000005, and conifer plus broadleaf is
       within 3e-8 of 1.
   - **Canadian side** (102,543 box study cells): all 13 new bands are NaN with flag 3 on every
     cell (0 exceptions).
   - **Could this fail?** The definedness, flag and range checks have no positive control here; a
     corrupt band would show as a count above 0. The ecm check compares two separately stored
     bands.

5. **Ten cells recomputed independently: 10 of 10 agree (not blocking).**
   - **The recompute.** OBSERVED, `recompute_new.out.json`. The code is the 2026-10-11 review's
     independent implementation (its geometry, clipping, side, water and crown cover kept
     unchanged), extended to the 18 genera written out by hand and to the total. It imports only
     the published Bechtold tables and T5's class lists from the package.
   - **The sample.** It was drawn by `box_new_bands.py`, seed 20261015, under a rule written in
     that script's docstring before I read any new-band value:
     - one cell for each tier A genus, among cells where that genus's stored share is at least
       0.05;
     - two cells with total cover at least 10%;
     - one cell in a US-half file.
   - **Results.**
     - Largest share or valid-fraction difference: 2.6e-7 (tolerance 0.001, D115 item 4).
     - Largest cover difference: 1.9e-5 points (tolerance 0.1).
     - Every flag is 1.
   - **The sample is informative.** Seven cells carry their genus at 7.5% to 45% (Larix 0.075,
     Betula 0.079, Populus 0.113, Alnus 0.453, Lithocarpus 0.333, Chrysolepis 0.121, Arbutus
     0.174). One cell has 12 NALCMS water pixels. One is a D119 US half.
   - **Where this could mislead.** Seven of the ten cells were selected on a stored non-zero
     value. That shows stored non-zero values are right, not that stored zeros are. The two
     cover-selected cells (stored Alnus 0.453 and Larix 0.101 among their shares) partly cover
     that.
   - **Not tested on a real cell:** tier B, which is zero across the box.

6. **The tile-edge check holds for the 24-band layout (not blocking).** OBSERVED,
   `edges_new.out.json`.
   - **The windows.** All 32 distinct fixed points of `scripts/pnw_checks.py` (16 tree corners and 17
     border corners, one shared) were re-run with the pipeline's own entry points into a scratch folder on
     `/mnt/work`. Each was compared with the stored tiles on all 24 value bands and 22 flag bands,
     NaN for NaN.
   - **Results:** **29 windows computed, 117,110 cells compared, 0 band-cells differ on any of the 46 bands.**
     Of the other three, one window has no study cell and two have Canadian cells only. 28 windows
     went through `tree_tile` and 1 through `tree_tile_us_half`, which left out 1,674 Canadian
     cells. The compared cells include 47,932 with a new tier A share above 0, so the new bands
     were exercised, not only zeros. Peak memory 326 MB. The pnw-monday report's figure after D120 was
     117,760 cells on 29 windows (as the 2026-10-11 review quotes it). Why the counts differ by 650
     was not traced.
   - **What this check can show.** It tests that cutting the box into tiles changes no value
     (D115 item 5), not correctness, since it shares every input and line of code with the run
     (as the 2026-10-11 review said).
   - **S3 in my script.** A window with Canadian cells is recomputed as a US half and compared on
     its non-Canadian cells only. Canadian cells across a tile edge stay unchecked (S3, item 13).

7. **The 49 N seam cannot test the new bands, by construction (not blocking).** They have no
   value on the Canadian side (item 4), so a border step has nothing to step to. The seam
   verdicts for the old bands carry over (T7 verify V6, read; the shared bands are bit-identical
   by V4). Nothing more can be done until a Canadian source supplies these genera
   (RECORD -1033 item 2, -1036).

8. **Genus shares are plausible by ecoregion, but TreeMap puts small shares well outside native
   ranges (not blocking; a note for T7).** OBSERVED, `box_new_bands.out.json` `level3` and
   `range_check.out.json`. Figures are the mean share over cells with shares, and the fraction of
   those cells above 0.
   - **Larix** is highest in:
     - Columbia Mountains/Northern Rockies (0.073; above 0 on 97%);
     - Canadian Rockies (US part, 0.060);
     - Blue Mountains (0.031);
     - North Cascades (0.026).

     It is near 0 in Coastal Range, Klamath, Willamette and Puget Lowland. By longitude: 0.035
     east of 120 W, 0.009 from 122 to 120 W, 0.00015 west of 122 W.
   - **Alnus** is highest in Puget Lowland (0.258), Coastal Range (0.197) and Willamette (0.184),
     and is 0.000 east of 120 W.
   - **Lithocarpus** is 0.085 in Klamath Mountains and 0.045 in Coastal Range. **Arbutus** is 0.078
     in Klamath. **Chrysolepis** is small everywhere (at most 0.008, Klamath).
   - **Populus** is highest in Colorado Plateaus (0.534, a few cells), Wasatch and Uinta (0.401),
     Snake River Plain (0.281) and Wyoming Basin (0.186).
   - **ecm_hosts** is lowest in Northern and Central Basin and Range (0.461, 0.524) and Wyoming
     Basin (0.522), and in Willamette (0.598) and Puget Lowland (0.619).
   - **Betula** is small throughout (at most 0.005).
   - INFERRED: each pattern matches the general picture: western larch east of the Cascades and
     in the northern Rockies, red alder in the western lowlands, tanoak, madrone and chinquapin in
     SW Oregon, aspen in the interior mountains and basins, and juniper-dominated basins and
     cedar- and maple-rich lowlands lowering the host total. These range statements are
     UNVERIFIED general knowledge, except tanoak's, below.
   - **Out of range.**
     - The USDA silvics entry for tanoak (https://research.fs.usda.gov/silvics/tanoak, read
       through a search summary, not opened) gives its northernmost record as a disjunct stand
       just north of the Umpqua River in SW Oregon, and its general Coast Range limit as the
       Coquille drainage, further south.
     - Yet `share_Lithocarpus` is above 0 on 17,859 cells from 45 to 49 N, as far as Washington,
       and on 28% of the Willamette Valley's cells with shares.
     - Likewise Larix is above 0 on 33,516 cells from 40 to 43 N and on 36,882 cells west of
       122 W.
     - The mean share in each of those bands rounds to 0.000.
     - INFERRED cause: TreeMap gives each 30 m pixel a whole FIA plot's tree list by imputation,
       so a donor plot from inside a genus's range can be placed outside it. The code passes this
       through correctly; it is a property of the source.
   - **Where this could mislead.** A T7 term that reads a share as presence (share > 0) would
     treat these cells as hosted. A term using the share's size is barely affected.
   - **What I compared, and its limits.**
     - I compared the stored tiles, by CEC level III ecoregion (burned by cell centre with the
       mask's own `_burn`) and by latitude and longitude band, against general knowledge.
     - I did not use plot coordinates. TreeMap's plot table carries none, and the code uses the
       plot table only through the raster's plot IDs, as I did here.
     - The comparison is qualitative: no independent map of genus cover was read.

9. **Tier B is zero across the PNW box (not blocking; for T7).** Fagus, Carya, Tilia, Ostrya and
   Carpinus are above 0 on no box cell (OBSERVED; agrees with T7 V5). In the pilot they are
   constant 0 where defined, so a D121 held-out comparison cannot evaluate them there. INFERRED:
   leave them out of the PNW fit and state it.

10. **Larix is flagged not available in Canada (not blocking for the PNW; the owner rules before
    the Canadian tree tiles go continent-wide).**
    - **Why.** READ: every band outside `SCANFI_BAND_CLASSES` (`t5_layer.py:105-109`: Pseudotsuga,
      conifer, broadleaf) gets flag 3 in Canada (`t6b_layers.py:706`). Larix is not mapped to
      SCANFI's `tamarack` class, so it falls to flag 3 by that default, not by any line written
      for it.
    - **Which ruling covers it?**
      - RECORD -1033 item 2 covers "the genera SCANFI folds into broadleaf". Larix is a conifer,
        so that item does not cover it.
      - D85 covers genera "SCANFI cannot supply", naming Tsuga, Quercus "and the pines it does not
        map".
      - D89 (1) rules Pinus, Picea and Abies wholly not available rather than "filled with
        SCANFI's partial sums".
      - Treating Larix like D89 (1)'s three is a consistent reading of that reasoning. Tamarack is
        *Larix laricina* per the v1 dataset page, cited by the verify report; not re-read here.
        On that reading tamarack is a partial sum for Larix wherever western or subalpine larch
        grows.
      - But it is a reading by analogy, not a ruling, and RECORD -1050 already found "-1032's
        'Larix partial in Canada'" contradicted by the code.
    - **In the box it changes nothing measurable.** SCANFI's tamarack layer is 0 on all 96,577
      Canadian box cells with shares (OBSERVED, `scanfi_box.out.json`). Those cells are on southern
      Vancouver Island and the Gulf Islands, where no larch is expected (UNVERIFIED general
      knowledge).
    - **Continent-wide it matters.** INFERRED: tamarack would supply the dominant boreal larch
      across most of Canada. Western and subalpine larch (SE British Columbia, SW Alberta) would
      be missing or misplaced. SCANFI v2's class membership is still not published in its readme
      (verify report section 3; COULD NOT DETERMINE here).
    - **Options for the owner:**
      - (a) keep flag 3, as D89 (1);
      - (b) fill Larix from tamarack and flag it partial where western larch can occur;
      - (c) take Larix from the second Canadian source (RECORD -1036: a "Lari" genus layer exists
        there).

      Recommended: (a) for now, written as a decision row, then revisited with (c) for the
      continental run.

11. **The `ecm_hosts` membership: the 18 genera hold against the one source read (not blocking for
    building; the owner rules before the fit uses `ecm_hosts`).** READ: Brundrett, "Mycorrhizal
    Associations: Ectomycorrhizas", https://mycorrhizas.info/ecm.html (2008, read through a
    summarising fetch).
    - **Named there as forming ectomycorrhizas:**
      - Pinaceae: Abies, Larix, Picea, Pinus, Pseudotsuga, Tsuga;
      - Fagaceae: Castanea, Castanopsis, Fagus, Lithocarpus, Quercus;
      - Betulaceae: Alnus, Betula, Carpinus, Corylus, Ostrya;
      - Juglandaceae: Carya;
      - Salicaceae: Populus, Salix, "VAM also";
      - Tiliaceae: Tilia;
      - Ericaceae, arbutoid: Arbutus among others.
    - **Dual ECM and arbuscular, by name:** Alnus, Populus, Salix.
    - **Chrysolepis is not named there.** That Chrysolepis was split from Castanopsis is UNVERIFIED
      memory. A thesis title read in a search result, "Comparing Ectomycorrhizal Communities of
      Understory Giant Chinquapin (Chrysolepis chrysophylla) and Overstory Pinaceae Trees in a
      Mixed Conifer Forest in Central Oregon" (Longway 2015), implies it is ectomycorrhizal; the
      thesis was not opened.
    - **Arbutus.** Molina and Trappe 1982 (New Phytologist 90:495-509) is cited by later work for
      Arbutus menziesii forming arbutoid mycorrhizas with ectomycorrhizal fungi such as
      Cenococcum, Laccaria and Pisolithus. This is read only through a search summary of
      citations; the paper was not opened.
    - **Judgement calls.**
      - Arbutus: arbutoid mycorrhizas are formed by ectomycorrhizal fungi, so including it serves
        a total meant as "trees these fungi can partner" (INFERRED).
      - Populus and Alnus: dual. The source says the balance "varies with soil moisture".
      - Leaving any of the three out changes only the total, not its genus band, and changes the
        layout hash (rebuild).
    - **Not checked:** FungalRoot's Table S2 (licence unreadable, RECORD -1036). Brundrett's page
      is from 2008 and is family-level in places.
    - **Recommendation:** accept the 18 as proposed, with Arbutus, Populus and Alnus named as
      partial or dual in the decision row. No source read argues against any member.
    - **Also note for the owner:** in the box `ecm_hosts` is above 0 on 99.1% of US cells with
      shares (T7 V5), and its block means run from 0.46 to 0.99 (item 8). So it mostly separates
      juniper and cedar or maple stands from the rest.

12. **The proposed D127 is accurate as written (not blocking; the owner's).**
    - **Its claims hold.** OBSERVED: none of the five tier B genera has a Table 3 species of its
      own (`TABLE_3_GENUS`), so each takes quaking aspen's width. Their FIA codes in the tree table
      are 391, 400 to 407 and more, 531, 701 and 950 to 953 (`genus_strings.out.json`), all at
      least 300, so FIA's code classes them broadleaf. The live-tree and plot counts match my count
      of the tree table: rows and live trees of 5 in and up equal the build report's for every
      genus.
    - **The number is free.** D127 is used on no other `origin/*` branch (D125 and D126 are on
      `t7-mycorrhizal-plan` and `t7-pnw-verify`).
    - **The decision does not move the PNW pilot.** In the box, tier B is zero (item 9), so D127
      matters for the continental run, not the pilot. Recommendation: accept, or defer to the
      continental run; either way it changes no PNW value.

13. **S2 and S3 (V6: still open) do not affect the new bands (not blocking).**
    - **S2.** `layers_ready` still trusts file existence (`scripts/t6b_run.py:423-426`, and inline
      in `tree_unit`).
      - The new bands take no SCANFI value: flag 3 in Canada (item 4). So S2 can touch only the
        old bands' Canadian values.
      - On today's data the gap is closed in fact, though not in code. All 110 SCANFI layer files
        behind the 10 whole tiles with Canadian cells have an ok manifest line and hash to it
        (OBSERVED, `scanfi_box.out.json`).
      - It matters again when the continental Canadian tree tiles are built. The fix recommended
        on 2026-10-11 still applies.
    - **S3.** `scripts/pnw_checks.py` is unchanged. My edge script works around it by excluding
      Canadian cells. The new bands are constant (NaN, flag 3) on Canadian cells, so a Canadian
      cross-edge check could not tell them apart anyway.

14. **The free-space margin is right, but the build report did not cover memory (not blocking;
    note).** The first PNW section was killed for memory at two workers on 24-band tiles
    (RECORD -1041), and the rest-of-US estimate moved to about 2 to 3 days at one worker.
    INFERRED: any continental tree section needs one worker or a memory measurement first. No
    code change is implied.

15. **Small notes (not blocking).**
    - **Genus names.**
      - Tanoak is `Lithocarpus` in the tree table (9,999 rows; `Notholithocarpus` 0).
      - `Castanopsis` has 0 rows, so chinquapin is not split across two names (OBSERVED,
        `genus_strings.out.json`).
      - `Notholithocarpus` is in `BROADLEAF_GENERA` (`crown_cover.py:150`). If a later TreeMap
        renames tanoak, its trees would silently count toward broadleaf only, not the tanoak band
        or the total. Nothing guards that.
    - **Branch head moves.** The runner pushes evidence commits to this branch while the night
      unit runs from its checkout. A D40 merge should name the head it merges.
    - **Unit counts.** "283 trees units" in the build report's section 8 came out as 13 plus 270
      across two sections (RECORD -1047). That matches.

## Revert checks re-run by the reviewer

Runner: `revert_review.py.txt`, written by me. Its rules:
- Copy the file aside, make the one-line edit, run the named tests with a fresh JUnit XML.
- Refuse to read the results on any collection, import or syntax error, a missing XML, or errors
  counted in the XML.
- Restore from the saved copy, never from git.
- Confirm the restored file hashes to the copy and the forward change's anchor text is back.

Output: `revert_review.out.json`. HEAD was `b0a0e88`, and the tree equalled HEAD afterwards
(OBSERVED). No run was refused.

| Check | Edit | Failed | Each message names this edit's effect |
|---|---|---|---|
| R1 (coder's r3) | `done_units` ignores the layout | the 4 predicted, of 12 | "the old-layout tile was counted done (F1)"; "the old tile was not kept in a superseded folder"; "the old-layout US half was counted done (F1)"; the stale-whole test's unit count |
| R2 (coder's r4) | `stage_plots` ignores the layout | the 1 predicted | "the old table was reused (F2)", (4, 10) against (4, 23) |
| R3 (coder's r8) | free space needed set to 0 | both free-space cases | the unit ran (`units_ok` 1, asserted 0) |
| R4 (mine) | two-worker path skips `before_unit` | none, of 56 (predicted none) | shows the gap in item 3 |

R1 to R3 fail for the coder's stated reasons. Each failure is one only that edit could cause: the
F1 messages appear only under R1 and the F2 message only under R2.

## What I could not determine

- FungalRoot's genus table (licence unreadable). Brundrett 2009's own tables. The Longway thesis.
  Molina and Trappe 1982 itself. The mycorrhizal statuses rest on one web page read through a
  summarising fetch, plus search summaries.
- SCANFI v2's class membership for larch species (item 10).
- The real-world distribution of the genera, beyond tanoak's range statement. The plausibility
  check in item 8 is against general knowledge.
- Canadian cells across tile edges (S3), and any seam for the new bands (item 7).
- Tier B on a real cell (zero in the box).
- Whether the out-of-range shares (item 8) come from TreeMap's imputation or from something
  else. The cause is INFERRED; TreeMap's methods were not read.
- Anything outside the PNW box: the rest-of-US rebuild is not authorised (RECORD -1048), and
  continental tiles of the new layout do not exist yet.
