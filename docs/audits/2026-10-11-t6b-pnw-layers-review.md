# Review: T6b's soil and host-tree layers for the PNW box (40 to 49 N, 111 to 125 W), under the standing protocol (D18)

- **Reviewed:** `origin/t6b-continental-layers` at `cfbf50d` (t6b-scanfi-edge merged per Forager
  RECORD -828), plus the runner change the night run actually uses, `origin/t6b-pnw-scanfi` at
  `4ac4cab` (`--tiles`, not merged into t6b-continental-layers at the time of writing).
- **Commissioned by:** Forager RECORD -832 ("Review now, alongside (Recommended)").
- **Rulings read:** D74, D80, D81, D84 to D92, D111 to D120, D122
  (`docs/planning/DECISIONS.md:8-47` at `cfbf50d`). D121 is not on this branch.
- **Data:** read in place on the flash drive,
  `/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b/`. Nothing was
  written to the drive. Reviewer scripts and outputs are in `2026-10-11-t6b-pnw-layers-review/`;
  the scripts are byte-identical to what ran.
- **Reviewer:** a Claude session separate from every T6b builder. Worktree
  `~/Zynergy/forager-forecast-t6b-pnw-review`, branch `t6b-pnw-review`, own `.venv`. I did not
  touch the running `t6b-night` unit, its checkout `~/Zynergy/forager-forecast-scanfi-edge`, or
  any other worktree. CPU: reviewer jobs ran at nice 19 on small windows only.
- **Conventions:** "read" = opened in this session; "observed" = command output in this session;
  "inferred" is marked. Line cites are to `cfbf50d` unless they name another commit.

## Pass 0: pre-registration (committed before any manifest line or tile value was read)

**Box tile list, from the mask only** (`box_tiles.py`, `box_tiles.json`). Study and side rules are
restated in the script from D113, D115 item 1 and D117, not imported. Observed: 296 tree tiles
hold box study cells (273 US only, 20 with both sides, 3 Canada only); 8 soil tiles;
16,571,590 US and 102,543 Canadian study cells in the box. The total, 16,674,133, equals the
figure in `2026-10-09-pnw-monday-completion-report.md` section 5, and the 102,543 equals section
12's, so the two counts agree from independent code. The 8 tree tiles holding Canadian box cells
are exactly the 8 named on the night run's `--tiles` (observed from `ps`, 2026-10-10 20:20 UTC).

**Samples, seed 20261011** (`prereg.py`, `prereg.json`), drawn from the mask alone:
- Hash sample: 6 of the 273 US-only tree tiles, 4 of the 20 US-half tiles, 3 of the 8 soil
  tiles, and every file of the 8 Canadian tiles once they land.
- Spot cells: 3 soil cells, 3 US tree cells and 2 Canadian tree cells, drawn at random from box
  study cells; plus one cell fixed by hand at 47.705 N, 116.79 W (Coeur d'Alene Lake's north
  shore, a guess at a shore cell; whether it is one is read from NALCMS during the recompute).
- Tolerances, fixed now: soil mean and quantiles 0.01 pH, valid fractions 0.005; trees as D115
  item 4 (cover 0.1 points, shares 0.001, valid fraction 0.001, source and flags exact). My
  recompute uses exact polygon clipping, not a point sampler, so the fraction tolerance is tighter
  than the ten-cell rule's 0.02 for soil.
- Manifest checks (no hashing): every box tile has a latest unit line with status ok that names
  files; no failed or deferred line is the latest line of a unit counted done; every file named
  exists.

(Passes 1 to 5 follow.)
