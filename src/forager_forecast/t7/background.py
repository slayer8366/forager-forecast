"""T7 item 8: background drawn inside the effort frame (P3 as ruled, D133).

Background cells come at random, without replacement, from the eligible cells (P4) whose weather
cell is in T6's effort frame (D101), seed 20260918 (D31), drawn once; every fold uses the same
draw. Its total weight equals the presences' total weight (P3 point 4). Fewer eligible cells than
asked for is refused, not quietly made up.
"""

from __future__ import annotations

import numpy as np

_STUB = "T7 build: not written yet (tests first)"

SEED = 20260918
BACKGROUND_SIZE = 500_000


class NotEnoughBackground(ValueError):
    pass


def in_frame(weather_keys: np.ndarray, frame_keys: np.ndarray) -> np.ndarray:
    raise NotImplementedError(_STUB)


def draw_background(candidates: np.ndarray, n: int = BACKGROUND_SIZE, seed: int = SEED):
    """Sorted uint32 cell ids drawn from the distinct candidate ids."""
    raise NotImplementedError(_STUB)


def cell_list_sha256(cell_ids: np.ndarray) -> str:
    raise NotImplementedError(_STUB)


def background_weights(n_background: int, presence_total_weight: float) -> np.ndarray:
    raise NotImplementedError(_STUB)
