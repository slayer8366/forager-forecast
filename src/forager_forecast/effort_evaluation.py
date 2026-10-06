"""T6's evaluation, as fixed before any fit (D104, D105; docs/audits/2026-10-06-t6-proposal.md).

Leave one year out over 2015 to 2025. Inside each outer fold the configuration is chosen from the
20 in the grid by an inner leave-one-year-out over that fold's ten training years, by pooled
Poisson deviance of the effort surface (the lichen-season surface, which is the one the pass is
judged on, D104). Scored on the held-out year: every frame cell x week x day-type, zeros included,
each model given the year's own total. A fit on training years minus {h, j} serves both fold h's
inner year j and fold j's inner year h, so each pair is fitted once.

The surface stored for T7 is fitted on all eleven years with the configuration whose pooled
leave-one-year-out deviance over all eleven years is lowest (ties to the grid's first).
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np

from forager_forecast import effort as ef

LADDER: tuple[tuple[str, frozenset[str]], ...] = (
    ("+ cell", frozenset({"cell"})),
    ("+ year", frozenset({"cell", "year"})),
    ("+ season", frozenset({"cell", "year", "season"})),
    ("+ day-type (all-fungi fit)", ef.TERMS_FULL),
)
CONSTANT = "constant"
EFFORT = "effort surface (lichen season)"


def _effort_surface(fungi, lichen, config, train):
    fungal = ef.fit(fungi, train, config)
    lichen_fit = ef.fit(lichen, train, config)
    return fungal, lichen_fit, ef.combine(fungal, lichen_fit, fungi, train)


@dataclass
class Evaluation:
    chosen: dict[int, ef.Config] = field(default_factory=dict)
    inner: dict[ef.Config, dict[tuple[int, int], float]] = field(default_factory=dict)
    per_cell: dict[str, np.ndarray] = field(default_factory=dict)  # model -> summed over folds
    per_cell_interpolated: dict[str, np.ndarray] = field(default_factory=dict)
    per_fold: dict[int, dict[str, float]] = field(default_factory=dict)
    per_fold_interpolated: dict[int, dict[str, float]] = field(default_factory=dict)
    held_out_outings: dict[int, float] = field(default_factory=dict)
    outer_by_config: dict[ef.Config, float] = field(default_factory=dict)
    final_config: ef.Config | None = None


def evaluate(
    fungi: ef.OutingCounts,
    lichen: ef.OutingCounts,
    grid: Sequence[ef.Config] = ef.configs(),
    years: Sequence[int] = ef.YEARS,
    log: Callable[[str], None] = lambda _line: None,
) -> Evaluation:
    if fungi.cells != lichen.cells:
        raise ValueError("the lichen counts must use the all-fungi frame")
    result = Evaluation()
    # Inner tuning: one fit per pair of left-out years and configuration.
    for config in grid:
        scores: dict[tuple[int, int], float] = {}
        for h, j in itertools.combinations(years, 2):
            train = [y for y in years if y not in (h, j)]
            _f, _l, surface = _effort_surface(fungi, lichen, config, train)
            scores[(h, j)] = float(ef.surface_deviance(surface, fungi, j).sum())
            scores[(j, h)] = float(ef.surface_deviance(surface, fungi, h).sum())
        result.inner[config] = scores
        log(f"inner tuning done for {config.id}")
    for h in years:
        totals = {
            config: sum(result.inner[config][(h, j)] for j in years if j != h) for config in grid
        }
        best = min(totals.values())
        result.chosen[h] = next(c for c in grid if totals[c] == best)
    # Outer folds with each fold's chosen configuration: the ladder and the effort surface.
    names = [CONSTANT, *(name for name, _ in LADDER), EFFORT]
    result.per_cell = {name: np.zeros(fungi.n_cells) for name in names}
    result.per_cell_interpolated = {
        name: np.zeros(fungi.n_cells) for name in (CONSTANT, LADDER[-1][0], EFFORT)
    }
    for h in years:
        config = result.chosen[h]
        train = [y for y in years if y != h]
        fold: dict[str, np.ndarray] = {CONSTANT: ef.constant_deviance(fungi, h)}
        full = None
        for name, terms in LADDER:
            surface = ef.fit(fungi, train, config, terms=terms)
            fold[name] = ef.surface_deviance(surface, fungi, h)
            if terms == ef.TERMS_FULL:
                full = surface
        lichen_fit = ef.fit(lichen, train, config)
        effort_surface = ef.combine(full, lichen_fit, fungi, train)
        fold[EFFORT] = ef.surface_deviance(effort_surface, fungi, h)
        interpolated = {
            CONSTANT: ef.constant_deviance(fungi, h, ef.interpolated_total(fungi, h, train)),
            LADDER[-1][0]: ef.surface_deviance(full, fungi, h, given_total=False),
            EFFORT: ef.surface_deviance(effort_surface, fungi, h, given_total=False),
        }
        for name, values in fold.items():
            result.per_cell[name] += values
        for name, values in interpolated.items():
            result.per_cell_interpolated[name] += values
        result.per_fold[h] = {name: float(v.sum()) for name, v in fold.items()}
        result.per_fold_interpolated[h] = {name: float(v.sum()) for name, v in interpolated.items()}
        result.held_out_outings[h] = fungi.total(h)
        log(f"outer fold {h} done with {config.id}")
    # The stored surface's configuration: plain leave-one-year-out over all eleven years.
    for config in grid:
        total = 0.0
        for h in years:
            train = [y for y in years if y != h]
            _f, _l, surface = _effort_surface(fungi, lichen, config, train)
            total += float(ef.surface_deviance(surface, fungi, h).sum())
        result.outer_by_config[config] = total
    best = min(result.outer_by_config.values())
    result.final_config = next(c for c in grid if result.outer_by_config[c] == best)
    log(f"final configuration {result.final_config.id}")
    return result


def difference_interval(
    model: np.ndarray, comparison: np.ndarray, resamples: int = ef.BOOTSTRAP_RESAMPLES
) -> tuple[float, tuple[float, float]]:
    """Pooled model minus comparison deviance, and its 95% interval from the cell-clustered
    bootstrap (seed 20260918)."""
    difference = model - comparison
    draws = [float(w @ difference) for w in ef.cluster_weights(len(difference), resamples, ef.SEED)]
    return float(difference.sum()), ef.percentile_interval(draws)


def weekend_ratio_interval(
    fungi: ef.OutingCounts, config: ef.Config, resamples: int = ef.BOOTSTRAP_RESAMPLES
) -> tuple[float, tuple[float, float]]:
    """The all-years all-fungi fit's weekend-to-weekday ratio, and its 95% interval from refits
    on cell-clustered resamples (seed 20260918)."""
    point = ef.fit(fungi, ef.YEARS, config).weekend_ratio
    draws = [
        ef.fit(fungi, ef.YEARS, config, cell_weights=w).weekend_ratio
        for w in ef.cluster_weights(fungi.n_cells, resamples, ef.SEED)
    ]
    return point, ef.percentile_interval(draws)


def raw_weekend_ratios(counts: ef.OutingCounts) -> dict[str, dict]:
    """Observed outings per weekend day over outings per weekday day, no model: by year, by
    band, and overall. Shown beside the test, with no verdict (D105)."""

    def ratio(mask: np.ndarray) -> float | None:
        weekend = counts.count[mask & (counts.day == ef.WEEKEND)].sum()
        weekday = counts.count[mask & (counts.day == ef.WEEKDAY)].sum()
        if weekday == 0:
            return None
        return float((weekend / 2.0) / (weekday / 5.0))

    everything = np.ones(len(counts.count), dtype=bool)
    by_year = {str(y): ratio(counts.entry_year == i) for i, y in enumerate(ef.YEARS)}
    entry_band = counts.cell_band[counts.cell]
    by_band = {str(b): ratio(entry_band == i) for i, b in enumerate(counts.band_ids)}
    return {"overall": ratio(everything), "by_year": by_year, "by_band": by_band}
