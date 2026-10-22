"""T8's bar (plan section 7; D133 (5)), fixed before any result, as one function.

T8 passes only if all four hold for the main model, on the headline units and timing:

- C1: Brier skill against T1's stored calendar predictions, on the same units, with its 95%
  interval wholly above zero.
- C2: the same against the no-weather model (calendar, place, effort).
- C3: p <= 0.05 over the 199 whole-year weather swaps: p = (1 + swaps whose pooled Brier is at or
  below the model's) / (1 + 199). A tie counts against the model. So the model must beat all but
  9 of the swaps.
- C4, the turnout guard: the weather model's Brier skill over the no-weather model for lichen
  reports (D103) must NOT be wholly above zero (its interval's lower end at or below zero).

Every interval is from 1,000 resamples of cells, seed 20260918, pooled over all held-out units
(t1_model.clustered_bootstrap_skill, T1's own bootstrap). "Wholly above zero" is the lower end of
the 95% percentile interval strictly above zero.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from forager_forecast import t1_model as tm
from forager_forecast.t8.design import (
    BOOTSTRAP_RESAMPLES,
    C3_ALPHA,
    N_SWAPS,
    SEED,
)


@dataclass(frozen=True)
class Condition:
    name: str
    passed: bool
    reason: str
    figures: dict


@dataclass(frozen=True)
class BarResult:
    passed: bool
    conditions: tuple[Condition, ...]

    @property
    def reason(self) -> str:
        failing = [c for c in self.conditions if not c.passed]
        if not failing:
            return "all four conditions hold"
        return "; ".join(f"{c.name} fails: {c.reason}" for c in failing)


def _check(name: str, values: np.ndarray, n: int) -> np.ndarray:
    a = np.asarray(values, dtype=np.float64)
    if a.shape != (n,):
        raise ValueError(f"{name} has length {a.shape}, expected ({n},)")
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{name} holds a value that is not finite")
    return a


def skill_interval(
    model: np.ndarray,
    reference: np.ndarray,
    outcomes: np.ndarray,
    cells: np.ndarray,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = SEED,
) -> dict:
    """Pooled Brier skill and its cell-clustered 95% interval."""
    low, high, _ = tm.clustered_bootstrap_skill(model, reference, outcomes, cells, resamples, seed)
    return {
        "skill": tm.brier_skill(model, reference, outcomes),
        "low": low,
        "high": high,
        "resamples": resamples,
        "seed": seed,
        "units": int(len(outcomes)),
        "positives": int(outcomes.sum()),
    }


def swap_test(observed_brier: float, swap_briers: np.ndarray) -> dict:
    """C3's p: swaps scoring at or below the model's Brier count against it."""
    swaps = np.asarray(swap_briers, dtype=np.float64)
    if swaps.shape != (N_SWAPS,):
        raise ValueError(f"C3 needs exactly {N_SWAPS} swaps, got {swaps.shape}")
    if not np.all(np.isfinite(swaps)):
        raise ValueError("swap_briers holds a value that is not finite")
    at_or_above = int(np.sum(swaps <= observed_brier))
    return {
        "observed_brier": observed_brier,
        "swaps": N_SWAPS,
        "swaps_at_or_above": at_or_above,
        "p": (1 + at_or_above) / (1 + N_SWAPS),
    }


def evaluate_bar(
    y: np.ndarray,
    p_model: np.ndarray,
    p_calendar: np.ndarray,
    p_no_weather: np.ndarray,
    cells: np.ndarray,
    swap_briers: np.ndarray,
    lichen_y: np.ndarray,
    lichen_p_weather: np.ndarray,
    lichen_p_no_weather: np.ndarray,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = SEED,
) -> BarResult:
    """Pass or fail, and why. All arrays are over the same held-out units, in the same order."""
    n = len(y)
    y = _check("y", y, n)
    p_model = _check("p_model", p_model, n)
    p_calendar = _check("p_calendar", p_calendar, n)
    p_no_weather = _check("p_no_weather", p_no_weather, n)
    lichen_y = _check("lichen_y", lichen_y, n)
    lichen_p_weather = _check("lichen_p_weather", lichen_p_weather, n)
    lichen_p_no_weather = _check("lichen_p_no_weather", lichen_p_no_weather, n)
    cells = np.asarray(cells)
    if cells.shape != (n,):
        raise ValueError(f"cells has length {cells.shape}, expected ({n},)")

    c1 = skill_interval(p_model, p_calendar, y, cells, resamples, seed)
    c2 = skill_interval(p_model, p_no_weather, y, cells, resamples, seed)
    c3 = swap_test(tm.brier(p_model, y), swap_briers)
    c4 = skill_interval(lichen_p_weather, lichen_p_no_weather, lichen_y, cells, resamples, seed)

    def interval(f: dict) -> str:
        return f"skill {f['skill']:+.5f} [{f['low']:+.5f}, {f['high']:+.5f}]"

    conditions = (
        Condition(
            "C1",
            c1["low"] > 0.0,
            f"against T1's stored calendar, {interval(c1)}; needs the interval wholly above zero",
            c1,
        ),
        Condition(
            "C2",
            c2["low"] > 0.0,
            f"against the no-weather model, {interval(c2)}; needs the interval wholly above zero",
            c2,
        ),
        Condition(
            "C3",
            c3["p"] <= C3_ALPHA,
            f"{c3['swaps_at_or_above']} of {N_SWAPS} swaps at or above the model, p = "
            f"{c3['p']:.3f}; needs p <= {C3_ALPHA}",
            c3,
        ),
        Condition(
            "C4",
            not c4["low"] > 0.0,
            f"lichen reports, weather against no-weather, {interval(c4)}; needs the interval "
            "not wholly above zero",
            c4,
        ),
    )
    return BarResult(all(c.passed for c in conditions), conditions)
