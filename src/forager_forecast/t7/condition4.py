"""P10b condition 4 as ruled (D145; Forager RECORD -1187): the map ranking independent presences,
the herbarium specimens of the re-fit's Phase 1, above background.

The owner's rulings, verbatim (-1187):
- "Average over its area (Recommended)": each specimen's score is the map's mean over its stated
  uncertainty circle (``circle_mean``: the cells whose centres lie within the radius of the
  record's point, its own cell always included, masked cells left out, never filled). Background
  points are scored the same way, at the same radii.
- "Matched to road distance (Recommended)": the background is drawn to match the specimens'
  road-distance mix (``matched_background``): for each specimen, ``BACKGROUND_PER_SPECIMEN``
  scorable cells in the same road-distance band (``ROAD_BANDS_M``, by the road band at the
  specimen's own cell), each carrying that specimen's radius.
- "Whole box, interior beside (Recommended)": the whole box's kept specimens on scorable cells
  carry the verdict; the interior sub-box is reported beside it, with no verdict.

The figure is the AUC of specimens against background minus 0.5, unweighted, with its 95% interval
from resampling whole level III blocks (each row in its own cell's block), seed 20260918
(``metrics.auc_above_half``). The band edges, the ten background points per specimen and the
block resampling are the coder's calls, reported for the planner, not rulings.

A specimen is scorable when its own cell has a map value: an eligible cell (P4 code 1) inside the
area of applicability. Background is drawn from the same scorable cells.
"""

from __future__ import annotations

import math

import numpy as np

from forager_forecast.grid import CELL_SIZE_M
from forager_forecast.t7 import metrics as mt

ROAD_BANDS_M = (0.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2000.0, 5000.0, np.inf)
BACKGROUND_PER_SPECIMEN = 10
SEED = 20260918
_OFFSET = 1 << 15


def road_band(dist_m) -> np.ndarray:
    """The index of each distance's band in ``ROAD_BANDS_M`` (lower edges inclusive)."""
    d = np.asarray(dist_m, dtype=np.float64)
    if not np.isfinite(d).all():
        raise ValueError("a road distance is undefined")
    return np.searchsorted(np.asarray(ROAD_BANDS_M[1:-1]), d, side="right")


def cell_centres(cell_id) -> tuple[np.ndarray, np.ndarray]:
    """Grid-plane centres of packed master-grid cell ids (``grid.GridCell.id``)."""
    ids = np.asarray(cell_id, dtype=np.int64)
    col = (ids & 0xFFFF) - _OFFSET
    row = (ids >> 16) - _OFFSET
    return (col + 0.5) * CELL_SIZE_M, (row + 0.5) * CELL_SIZE_M


def circle_mean(raster, window, x: float, y: float, radius_m: float) -> float:
    """The mean of ``raster`` (over ``window``, row 0 at the top) over the cells whose centres lie
    within ``radius_m`` of (x, y), the point's own cell always included; NaN cells left out. NaN
    when no included cell has a value."""
    r0 = math.floor((window.top - y) / CELL_SIZE_M)
    c0 = math.floor((x - window.left) / CELL_SIZE_M)
    k = math.ceil(radius_m / CELL_SIZE_M) + 1
    rows = np.arange(max(r0 - k, 0), min(r0 + k + 1, raster.shape[0]))
    cols = np.arange(max(c0 - k, 0), min(c0 + k + 1, raster.shape[1]))
    rr, cc = np.meshgrid(rows, cols, indexing="ij")
    cx = window.left + (cc + 0.5) * CELL_SIZE_M
    cy = window.top - (rr + 0.5) * CELL_SIZE_M
    take = (cx - x) ** 2 + (cy - y) ** 2 <= radius_m**2
    take |= (rr == r0) & (cc == c0)
    values = np.asarray(raster[rr[take], cc[take]], dtype=np.float64)
    values = values[np.isfinite(values)]
    return float(values.mean()) if len(values) else float("nan")


def matched_background(specimen_bands, specimen_radii, pool_cells, pool_bands,
                       per_specimen: int = BACKGROUND_PER_SPECIMEN, seed: int = SEED):  # fmt: skip
    """For each specimen, ``per_specimen`` pool cells in its road band, drawn without replacement
    within the band (one generator, bands in ascending order), each carrying that specimen's
    radius. Refuses a band whose pool is too small."""
    bands = np.asarray(specimen_bands)
    radii = np.asarray(specimen_radii, dtype=np.float64)
    pool_cells = np.asarray(pool_cells)
    pool_bands = np.asarray(pool_bands)
    rng = np.random.default_rng(seed)
    cells, out_radii = [], []
    for b in np.unique(bands):
        which = np.nonzero(bands == b)[0]
        need = per_specimen * len(which)
        candidates = pool_cells[pool_bands == b]
        if len(candidates) < need:
            raise ValueError(f"road band {b}: {len(candidates)} pool cells, {need} needed")
        cells.append(rng.choice(candidates, size=need, replace=False))
        out_radii.append(np.repeat(radii[which], per_specimen))
    return np.concatenate(cells), np.concatenate(out_radii)


def _count(values) -> dict:
    u, n = np.unique(np.asarray(values), return_counts=True)
    return {int(a): int(b) for a, b in zip(u, n, strict=True)}


def _one_set(raster, window, sx, sy, s_radius, s_band, s_block, cell_id, access, level3, pool,
             pool_band, per_specimen, seed, resamples) -> dict:  # fmt: skip
    s_scores = np.array([circle_mean(raster, window, x, y, r)
                         for x, y, r in zip(sx, sy, s_radius, strict=True)])  # fmt: skip
    b_cells, b_radius = matched_background(s_band, s_radius, pool, pool_band, per_specimen, seed)
    bx, by = cell_centres(b_cells)
    b_scores = np.array([circle_mean(raster, window, x, y, r)
                         for x, y, r in zip(bx, by, b_radius, strict=True)])  # fmt: skip
    b_pos = np.searchsorted(cell_id, b_cells)
    scores = np.concatenate([s_scores, b_scores])
    if not np.isfinite(scores).all():
        raise RuntimeError("a scorable point has no map value in its circle")
    y = np.concatenate([np.ones(len(s_scores)), np.zeros(len(b_scores))])
    blocks = np.concatenate([s_block, level3[b_pos]])
    s_bands = _count(s_band)
    return {
        "specimens_scored": int(len(s_scores)),
        "background": int(len(b_scores)),
        "difference": mt.auc_above_half(scores, y, blocks, resamples, seed),
        "specimen_road_bands": s_bands,
        "specimen_road_bands_times_per_specimen": {k: v * per_specimen for k, v in s_bands.items()},
        "background_road_bands": _count(road_band(access[b_pos])),
        "specimen_score_median": float(np.median(s_scores)),
        "background_score_median": float(np.median(b_scores)),
    }


def score_condition_4(raster, window, spec_x, spec_y, spec_cell, spec_radius, spec_interior,
                      cell_id, access, level3, scorable,
                      per_specimen: int = BACKGROUND_PER_SPECIMEN, seed: int = SEED,
                      resamples: int = 1000) -> dict:  # fmt: skip
    """Condition 4 over the whole box (the verdict's figure) and the interior sub-box (beside, no
    verdict). ``cell_id`` sorted, with ``access`` (the road band), ``level3`` and ``scorable``
    aligned to it; specimens given by their point (grid metres), own cell, radius and interior
    flag."""
    cell_id = np.asarray(cell_id)
    access = np.asarray(access, dtype=np.float64)
    level3 = np.asarray(level3)
    scorable = np.asarray(scorable, dtype=bool)
    spec_cell = np.asarray(spec_cell)
    spec_x, spec_y = np.asarray(spec_x), np.asarray(spec_y)
    spec_radius = np.asarray(spec_radius, dtype=np.float64)
    pos = np.clip(np.searchsorted(cell_id, spec_cell), 0, len(cell_id) - 1)
    ok = (cell_id[pos] == spec_cell) & scorable[pos]
    pool = cell_id[scorable]
    pool_band = road_band(access[scorable])
    result = {}
    sets = (("whole_box", ok), ("interior_no_verdict", ok & np.asarray(spec_interior, bool)))
    for name, keep in sets:
        result[name] = _one_set(raster, window, spec_x[keep], spec_y[keep], spec_radius[keep],
                                road_band(access[pos[keep]]), level3[pos[keep]], cell_id, access,
                                level3, pool, pool_band, per_specimen, seed,
                                resamples)  # fmt: skip
    result["whole_box"] = {"specimens_in": int(len(spec_cell)),
                           "specimens_not_scorable": int((~ok).sum()),
                           **result["whole_box"]}  # fmt: skip
    return result
