"""T7 items 12 and 13: the raster, mask and manifest writers, and attribution from tile tags.

Outputs go under ``DEFAULT_OUTPUT_ROOT`` on /mnt/work (P9; T7 verify V13), never on the flash
drive, which is the live continental run's, and never inside this repository (bulk data stays out
of git), except its git-ignored test scratch folder ``.pytest-tmp``. Each raster is written as
``<name>.partial`` and renamed when whole.

- ``relative_habitat_pnw.tif``: float32, the full model's raw score at the held effort (P6), NaN
  where masked. A raw score ranks places within this map only; it is never a percent (D12, R8).
- ``applicability_pnw.tif``: uint8, the codes of ``t7/predictors.CODE_LEGEND``.
- ``manifest.json``: refused unless it names every input and setting P9 lists.

Every label and tag written is checked for wording no 250 m output may carry: a percent, "sighting
chance" or "probability", D58's terms, or edibility words (R8, ``SPEC.md:25``).

Attribution (item 13; T7 verify V14 found the PNW render's list omits SCANFI) is built from the
tiles' own ``attribution`` tags and filtered to what the output read: SCANFI is named only if a
Canadian cell's value was read, which under D136 none is.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from forager_forecast.grid import GridWindow

_STUB = "T7 build: not written yet (tests first)"

DEFAULT_OUTPUT_ROOT = Path("/mnt/work/Zynergy/forecast-data/t7")
FLASH_DRIVE_ROOT = Path("/run/media")
HABITAT_FILE = "relative_habitat_pnw.tif"
MASK_FILE = "applicability_pnw.tif"
HABITAT_LABEL = (
    "Relative habitat for mycorrhizal mushrooms as a group: the model's raw score with search "
    "effort held at one value. It ranks places within this map only. Not a forecast. Not shown "
    "to anyone (M8)."
)
REQUIRED_MANIFEST_KEYS = (
    "inputs", "code_commit", "seed", "membership", "background", "tuning_grid_sha256",
    "chosen_configurations", "share_floor", "held_effort", "aoa", "licence_track",
    "attribution", "codes", "level3_codes",
)  # fmt: skip
FORBIDDEN_WORDS = (
    "%", "percent", "sighting chance", "probability", "chance of finding", "fruiting",
    "edible", "edibility", "safe to eat",
)  # fmt: skip


class OutputRefused(ValueError):
    pass


def check_wording(text: str) -> None:
    raise NotImplementedError(_STUB)


def check_output_dir(path: Path) -> Path:
    raise NotImplementedError(_STUB)


class HabitatWriter:
    """Writes the habitat raster and the code mask over ``window``, one tile at a time."""

    def __init__(self, out_dir: Path, window: GridWindow, tags: dict) -> None:
        raise NotImplementedError(_STUB)

    def write(self, tile_window: GridWindow, scores: np.ndarray, codes: np.ndarray) -> None:
        raise NotImplementedError(_STUB)

    def close(self) -> dict[str, str]:
        raise NotImplementedError(_STUB)


def write_manifest(path: Path, manifest: dict) -> str:
    raise NotImplementedError(_STUB)


def attribution(tree_tags: set[str], soil_tags: set[str], canadian_values_read: bool,
                extra: list[str]) -> list[str]:  # fmt: skip
    raise NotImplementedError(_STUB)
