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

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.windows import Window

from forager_forecast.grid import CELL_SIZE_M, GRID_CRS, GridWindow
from forager_forecast.t5_layer import SCANFI_CITATION
from forager_forecast.t7.predictors import CODE_LEGEND, CODE_OUTSIDE

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
TEST_SCRATCH = ".pytest-tmp"

DEFAULT_OUTPUT_ROOT = Path("/mnt/work/Zynergy/forecast-data/t7")
FLASH_DRIVE_ROOT = Path("/run/media")
HABITAT_FILE = "relative_habitat_pnw.tif"
MASK_FILE = "applicability_pnw.tif"
HABITAT_LABEL = (
    "Relative habitat for mycorrhizal mushrooms as a group: the model's raw score with search "
    "effort held at one value. It ranks places within this map only. Not a forecast. Not shown "
    "to anyone (M8)."
)
HABITAT_DESCRIPTION = "relative habitat, raw score at the held effort"
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
    lowered = str(text).lower()
    for word in FORBIDDEN_WORDS:
        if word in lowered:
            raise OutputRefused(f"output wording carries {word!r}: {text!r}")


def _within(path: Path, root: Path) -> bool:
    """True if ``path`` is ``root`` or under it, compared by file identity where both exist (so a
    bind mount of the same folder under two names is caught)."""
    path = Path(os.path.abspath(path))
    for candidate in (path, *path.parents):
        if candidate == root:
            return True
        if candidate.exists() and root.exists() and os.path.samefile(candidate, root):
            return True
    return False


def check_output_dir(path: Path) -> Path:
    path = Path(path)
    if _within(path, FLASH_DRIVE_ROOT):
        raise OutputRefused(f"{path}: the flash drive is the live run's; T7 writes to /mnt/work")
    if _within(path, REPOSITORY_ROOT) and not _within(path, REPOSITORY_ROOT / TEST_SCRATCH):
        raise OutputRefused(f"{path}: inside the repository; bulk outputs stay out of git")
    return path


class HabitatWriter:
    """Writes the habitat raster and the code mask over ``window``, one tile at a time."""

    def __init__(self, out_dir: Path, window: GridWindow, tags: dict) -> None:
        for k, v in tags.items():
            if k != "attribution":  # citations are quoted as their sources write them
                check_wording(f"{k} {v}")
        check_wording(CODE_LEGEND)
        check_wording(HABITAT_DESCRIPTION)
        self.out_dir = check_output_dir(Path(out_dir))
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.window = window
        base = {
            "driver": "GTiff", "width": window.width, "height": window.height, "count": 1,
            "crs": GRID_CRS, "compress": "deflate", "tiled": True,
            "transform": from_origin(window.left, window.top, CELL_SIZE_M, CELL_SIZE_M),
        }  # fmt: skip
        self._habitat = rasterio.open(self._partial(HABITAT_FILE), "w", dtype="float32",
                                      nodata=float("nan"), **base)  # fmt: skip
        self._mask = rasterio.open(self._partial(MASK_FILE), "w", dtype="uint8", nodata=None,
                                   **base)  # fmt: skip
        self._habitat.write(np.full((window.height, window.width), np.nan, "float32"), 1)
        self._mask.write(np.full((window.height, window.width), CODE_OUTSIDE, "uint8"), 1)
        self._habitat.set_band_description(1, HABITAT_DESCRIPTION)
        self._mask.set_band_description(1, CODE_LEGEND)
        self._habitat.update_tags(**tags)
        self._mask.update_tags(**tags)

    def _partial(self, name: str) -> Path:
        return self.out_dir / f"{name}.partial"

    def write(self, tile_window: GridWindow, scores: np.ndarray, codes: np.ndarray) -> None:
        col = (tile_window.left - self.window.left) // CELL_SIZE_M
        row = (self.window.top - tile_window.top) // CELL_SIZE_M
        win = Window(col, row, tile_window.width, tile_window.height)
        if (
            col < 0
            or row < 0
            or col + win.width > self.window.width
            or (row + win.height > self.window.height)
        ):
            raise ValueError(f"tile window {tile_window} is not inside the output window")
        self._habitat.write(np.asarray(scores, dtype="float32"), 1, window=win)
        self._mask.write(np.asarray(codes, dtype="uint8"), 1, window=win)

    def close(self) -> dict[str, str]:
        self._habitat.close()
        self._mask.close()
        digests = {}
        for name in (HABITAT_FILE, MASK_FILE):
            self._partial(name).rename(self.out_dir / name)
            digests[name] = _sha256(self.out_dir / name)
        return digests


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(path: Path, manifest: dict) -> str:
    missing = [k for k in REQUIRED_MANIFEST_KEYS if k not in manifest]
    if missing:
        raise OutputRefused(f"manifest lacks {missing}")
    for label in manifest.get("labels", []):
        check_wording(label)
    path = Path(path)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8")  # fmt: skip
    return _sha256(path)


def attribution(tree_tags: set[str], soil_tags: set[str], canadian_values_read: bool,
                extra: list[str]) -> list[str]:  # fmt: skip
    out: list[str] = []
    for tag in sorted(tree_tags):
        for item in (part.strip() for part in tag.split(" | ")):
            if not item or item in out:
                continue
            if item.startswith(SCANFI_CITATION) and not canadian_values_read:
                continue
            out.append(item)
    for item in [*sorted(soil_tags), *extra]:
        if item and item not in out:
            out.append(item)
    return out
