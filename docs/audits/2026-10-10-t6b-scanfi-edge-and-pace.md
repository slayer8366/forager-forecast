# T6b SCANFI: edge tiles, the pace, the compressed manifest (2026-10-10)

Dispatch: the Forager planner, relaying Forager RECORD -802, -803, -805 (and -806, -807 as scope
additions, measure only). Base: origin/t6b-continental-layers at 63dc6e4. Branch t6b-scanfi-edge.
Measurements are in `2026-10-10-t6b-scanfi-edge-and-pace/` (scripts as `.py.txt`, outputs as
`.out.txt`). Nothing on the flash drive was written; all scratch output went to
/mnt/work/scanfi-edge-scratch.

## 1. Edge tiles (D122)

Counted read-only over all 2,043 Canadian tree tiles against balsamFir.tif's grid
(178,400 x 119,100 px, 30 m; `count_edge.out.txt`):

- 10 tiles reach past the raster: 256_-36_28 to 256_-36_32 (west), 256_46_22 to 256_46_24
  (east), 256_15_4 and 256_16_4 (south). 20,026,729 of their 62,305,556 native pixels are past it.
- Their 193,470 Canadian study cells: 0 have any part of their area past the edge.
  10,454 study cells that do are on the US side, where SCANFI is not read.

So blanking changes no Canadian value in the current mask; it lets the 10 tiles finish. Built
test-first (`test_a_tile_past_the_scanfi_edge_is_blank_there_and_read_where_scanfi_covers`, red
with the run's own message "tile 16_-443_326 reaches past the SCANFI raster"). The runner now
records a unit's non-network error as `failed` and carries on. Reverts, each restored from a saved
copy, logs checked for compile and import errors first, forward change confirmed afterwards:
blank count and no-crown value both bite on the edge revert; the runner revert fails exactly the
three tests that cover it.

Read but not changed: the ruling's offer said "the same rule as SCANFI's own no-data", and the run
reads SCANFI's no-data (255) as no crown (0), not blank (T5). The title says blank, and blank was
built. With 0 Canadian cells touched the two readings give the same values today.

## 2. The pace (measured, nothing built)

One unit alone (256_-35_32, 5G cap, nice 10): 35.4 s wall, 35.2 s CPU, 5.2 MB read from disk,
RSS 606 MB. Four more in two concurrent pairs, as the run does: 44 to 70 s wall each, CPU equal to
wall, 2.8 to 18 MB from disk, RSS 503 to 602 MB. Another session's model fit (about 4 cores) ran
during the pairs, so their times are inflated. The run's own mean was 37.7 s.

| Phase | Share of a unit |
| --- | --- |
| regrid (`area_weighted_regrid_from_origin`) | 86 to 92% (30 to 63 s) |
| pixel lon/lat + side + NALCMS water | 11 to 14% (4.0 to 6.6 s) |
| SCANFI read from the flash drive | under 0.3 s |
| mask read, write, hash | under 0.4 s |

It is CPU-bound with no I/O wait (vmstat: wa 0). Inside the regrid, the cost is the cell-by-pixel
overlap geometry, not the values: one call on 11 bands cost the same CPU as on 1 band (13.2 s
against 10.4 to 13.4 s on a 64-row strip, `bench_bands.out.txt`). Two real layers regridded
together came out bit-identical to each alone (`bench_identical.out.txt`). Across the 11 layers of
one tile, the geometry, side and water are recomputed 11 times.

Remaining: 22,473 - 709 = 21,764 units, at 18.8 s wall each now.

| Option | Estimated hours | What changes |
| --- | --- | --- |
| A. As is | about 114 h (4.7 days) + about 1 h of downloads | nothing |
| B. More workers (4 or 6) | 40 to 75 h, unverified | the `--workers` flag only; D115 item 2 says two |
| C. Side and water once per tile | about 100 h | a per-tile cache; saves 11 to 14% |
| D. All 11 layers of a tile in one pass | about 11 to 12 h with 2 workers, about 8 h with 3 (memory unverified, estimated 1.3 to 1.6 GB a worker) | a unit becomes a tile, not a layer and tile; all 11 whole layers on disk together (19.0 GB; the drive would keep about 6 GB free, or /mnt/work); replaces D118's "one at a time, then deleted"; per-layer output unchanged |
| D + B | under 8 h, unverified | both |

A faster overlap kernel (compiled or a weight matrix kept per tile) was not measured and is not
estimated.

## 3. The compressed manifest (Forager RECORD -803)

`copy_manifest_evidence` writes `manifest.jsonl.gz`; the test drives the real hook (the plain copy
is refused, the gzipped copy passes and decompresses to the same bytes). In the run checkout, the
three staged files were committed by hand as 7f7cb49 with the manifest gzipped (304,165 bytes from
1,708,991).

Not solved by it: each SCANFI unit line adds about 56 bytes gzipped. The gzipped manifest passes
1 MiB after about 13,250 more SCANFI units (about 60% of the stage) and ends near 1.5 MB, so the
hook will refuse again partway through under option A, B or C. Option D writes about a tenth as
many lines.

## 4. PNW pilot (Forager RECORD -806, -807; measured, nothing built)

`count_pnw.out.txt`: 53 Canadian tiles meet the PNW window; 8 hold Canadian study cells inside the
box (256_-31_21, 256_-30_21, 256_-32_20, 256_-31_20, 256_-30_20, 256_-29_20, 256_-31_19,
256_-30_19), 102,543 cells, matching the briefing. None is an edge tile, and none has a SCANFI
layer done yet.

- Time: 88 units, about 28 min at the current pace (about 3 min under option D), plus downloading
  the 5 layers not on the drive: 9.02 GB (otherConiferous 2.58, ponderosaPine 0.08, tamarack 1.87,
  whiteRedPine 0.28, att_closure 4.20; HEAD requests 2026-10-10), 0.5 to 1.8 h at the rates measured
  on 2026-10-06.
- Running them first needs a new tile filter for the scanfi-layers stage. `--tree-groups` and
  `--us-half-tiles` apply to other stages. Note: `run_section` cleans up a layer group once every
  unit *in the list it was given* is done, so a filtered run would delete each whole layer file
  after the 8 tiles. A filtered run must skip cleanup, or the continent downloads 19 GB again.
- The trees stage then fills those tiles with no change: it offers a Canadian tile once all 11 npz
  files exist, and fills a tile with a US half by `fill_canadian_cells`.

## Found along the way

- `scanfi_balsamFir_256_38_33.npz` is on the drive with no manifest line. It was in the other
  worker when the run raised. It is not counted as done, so the next section redoes it and
  overwrites it by rename. Nothing is lost.
- A worker killed by the memory cap still ends a section. Only errors inside the unit are caught.
