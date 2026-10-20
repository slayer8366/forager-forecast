"""E1: the log of T6's expected outings per T1 unit, refitted per held-out year (plan section 4;
D133 (3)).

For held-out year h: T6's two fits (all fungi, lichens) on the ten other years with the fold's
configuration, combined as T6 combines them (effort.combine, D103, D106). The held-out year's level
is interpolated from its neighbours (effort.interpolated_year_level: T6's interpolated scoring,
T6 completion report :91-92, :145-146), so no held-out outing reaches the held-out units' effort.

Proposed readings (design.PENDING), not rulings:
- M-effort-training: a training unit takes the fold surface at its own year's fitted level.
- M-effort-config: the fold's configuration is the one T6's evaluation chose for that held-out
  year (docs/audits/2026-10-06-t6-fit/{all,cc}_results.json, chosen_per_fold).

A unit whose cell is not in T6's frame has no effort value; the run refuses, naming the count,
and never makes one up (effort.NoEffortValue, D107).

The counts are read from T6's rebuilt counts, read-only, with their sha256 checked against
SHA256SUMS beside them before use (`read_counts`).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np

from forager_forecast import effort as ef
from forager_forecast.cells import Cell, iso_week_of


class CountsChanged(RuntimeError):
    """A counts file's sha256 differs from the one recorded beside it."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_sums(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            out[name.strip().lstrip("*")] = digest
    return out


def read_counts(folder: Path, name: str) -> ef.OutingCounts:
    """One of T6's count files (e.g. all_fungi.npz), after checking its sha256."""
    sums = read_sums(folder / "SHA256SUMS")
    path = folder / name
    if name not in sums:
        raise CountsChanged(f"{name} is not listed in {folder / 'SHA256SUMS'}")
    actual = sha256_file(path)
    if actual != sums[name]:
        raise CountsChanged(f"{name} sha256 {actual} differs from SHA256SUMS {sums[name]}")
    data = np.load(path, allow_pickle=False)
    cells = [
        Cell(int(a), int(b)) for a, b in zip(data["lat_tenths"], data["lon_tenths"], strict=True)
    ]
    entries = zip(
        data["cell"].tolist(),
        data["week"].tolist(),
        data["day"].tolist(),
        data["count"].tolist(),
        strict=True,
    )
    return ef.OutingCounts.from_entries(cells, entries)


def parse_config(text: str) -> ef.Config:
    """'pull=10,smoothing=3' -> Config(10.0, 3), checked against T6's grid."""
    parts = dict(p.split("=") for p in text.split(","))
    config = ef.Config(float(parts["pull"]), int(parts["smoothing"]))
    if config not in ef.configs():
        raise ValueError(f"{text} is not in T6's grid")
    return config


def chosen_per_fold(results_json: Path) -> dict[int, ef.Config]:
    chosen = json.loads(results_json.read_text())["chosen_per_fold"]
    out = {int(y): parse_config(c) for y, c in chosen.items()}
    if sorted(out) != list(ef.YEARS):
        raise ValueError(f"{results_json} has folds {sorted(out)}, expected {list(ef.YEARS)}")
    return out


@dataclass(frozen=True)
class FoldEffort:
    held_out_year: int
    config: ef.Config
    log_effort: np.ndarray  # per unit, every unit (training and held out)
    interpolated_level: float


def fold_surface(
    fungi: ef.OutingCounts, lichen: ef.OutingCounts, held_out: int, config: ef.Config
) -> ef.Surface:
    if fungi.cells != lichen.cells:
        raise ValueError("the lichen counts must use the all-fungi frame")
    train = [y for y in ef.YEARS if y != held_out]
    fungal = ef.fit(fungi, train, config)
    lichen_fit = ef.fit(lichen, train, config)
    return ef.combine(fungal, lichen_fit, fungi, train)


def surface_values(
    surface: ef.Surface,
    counts: ef.OutingCounts,
    cells: Sequence[Cell],
    mondays: Sequence[date],
    year_level: dict[int, float],
) -> np.ndarray:
    """Expected outings per unit (both day-types summed), as effort.EffortSurface.effort, with the
    year level given per ISO year."""
    index = {c: i for i, c in enumerate(counts.cells)}
    absent = sorted({c.id for c in cells if c not in index})
    if absent:
        raise ef.NoEffortValue(
            f"{len(absent)} unit cell(s) are not in T6's frame (first {absent[0]}); "
            "no effort value is made up"
        )
    weekly = float((surface.day_rate * ef.DAYS_PER_TYPE).sum())
    ci = np.array([index[c] for c in cells])
    weeks = [iso_week_of(d) for d in mondays]
    frame = set(ef.frame_weeks())
    outside = [w.id for w in weeks if w not in frame]
    if outside:
        raise ef.NoEffortValue(f"{len(outside)} unit week(s) outside T6's frame ({outside[0]})")
    slot = np.array([ef.season_slot(w) for w in weeks])
    level = np.array([year_level[w.year] for w in weeks])
    band = counts.cell_band[ci]
    return surface.cell_level[ci] * level * surface.season[band, slot] * weekly


def fold_effort(
    fungi: ef.OutingCounts,
    lichen: ef.OutingCounts,
    held_out: int,
    config: ef.Config,
    cells: Sequence[Cell],
    mondays: Sequence[date],
) -> FoldEffort:
    surface = fold_surface(fungi, lichen, held_out, config)
    levels = {y: float(surface.year_level[ef.YEARS.index(y)]) for y in ef.YEARS if y != held_out}
    interpolated = ef.interpolated_year_level(surface.year_level, held_out)
    levels[held_out] = interpolated
    values = surface_values(surface, fungi, cells, mondays, levels)
    if not (np.isfinite(values).all() and (values > 0).all()):
        raise FloatingPointError("an expected outings value is not finite and positive")
    return FoldEffort(held_out, config, np.log(values), interpolated)


def all_folds(
    fungi: ef.OutingCounts,
    lichen: ef.OutingCounts,
    configs: dict[int, ef.Config],
    cells: Sequence[Cell],
    mondays: Sequence[date],
    years: Sequence[int] = ef.YEARS,
) -> dict[int, FoldEffort]:
    return {h: fold_effort(fungi, lichen, h, configs[h], cells, mondays) for h in years}
