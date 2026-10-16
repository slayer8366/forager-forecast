"""T7 item 8: background drawn inside the effort frame (P3 as ruled, D133).

Background cells come at random, without replacement, from the eligible cells (P4) whose weather
cell is in T6's effort frame (D101), seed 20260918 (D31), drawn once; every fold uses the same
draw. Its total weight equals the presences' total weight (P3 point 4). Fewer eligible cells than
asked for is refused, not quietly made up.
"""

from __future__ import annotations

import hashlib

import numpy as np

SEED = 20260918
BACKGROUND_SIZE = 500_000


class NotEnoughBackground(ValueError):
    pass


def in_frame(weather_keys: np.ndarray, frame_keys: np.ndarray) -> np.ndarray:
    return np.isin(np.asarray(weather_keys), np.asarray(frame_keys))


def draw_background(candidates: np.ndarray, n: int = BACKGROUND_SIZE, seed: int = SEED):
    """Sorted uint32 cell ids drawn from the distinct candidate ids."""
    pool = np.unique(np.asarray(candidates, dtype=np.uint32))
    if n > len(pool):
        raise NotEnoughBackground(f"{n} background cells asked for, {len(pool)} eligible")
    picks = np.random.default_rng(seed).choice(len(pool), size=n, replace=False)
    return np.sort(pool[picks])


def cell_list_sha256(cell_ids: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(cell_ids, dtype="<u4").tobytes()).hexdigest()


def background_weights(n_background: int, presence_total_weight: float) -> np.ndarray:
    return np.full(n_background, presence_total_weight / n_background)
