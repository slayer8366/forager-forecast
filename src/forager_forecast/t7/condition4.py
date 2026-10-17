"""P10b condition 4 as ruled (Forager RECORD -1187)."""

from __future__ import annotations

import numpy as np

ROAD_BANDS_M = (0.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2000.0, 5000.0, np.inf)
BACKGROUND_PER_SPECIMEN = 10
SEED = 20260918


def road_band(dist_m) -> np.ndarray:
    raise NotImplementedError


def circle_mean(raster, window, x: float, y: float, radius_m: float) -> float:
    raise NotImplementedError


def matched_background(specimen_bands, specimen_radii, pool_cells, pool_bands,
                       per_specimen: int = BACKGROUND_PER_SPECIMEN, seed: int = SEED):  # fmt: skip
    raise NotImplementedError


def score_condition_4(raster, window, spec_x, spec_y, spec_cell, spec_radius, spec_interior,
                      cell_id, access, level3, scorable,
                      per_specimen: int = BACKGROUND_PER_SPECIMEN, seed: int = SEED,
                      resamples: int = 1000) -> dict:  # fmt: skip
    raise NotImplementedError
