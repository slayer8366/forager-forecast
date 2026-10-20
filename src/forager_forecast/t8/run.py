"""T8's evaluation as functions of arrays: the headline bar, the challenger, and every item
reported beside with no verdict (plan section 7). scripts/t8_fit.py reads the files and calls these.

Only the main model on the headline units and timing decides (D133 (6)); the challenger passes only
if it clears C1 to C4 itself; everything else is labelled "no verdict".
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

from forager_forecast import t1_model as tm
from forager_forecast.t8 import bar as tb
from forager_forecast.t8 import models as md
from forager_forecast.t8 import weather as tw
from forager_forecast.t8.design import (
    BESIDE_LINE_YEARS,
    MEASURES,
    MIN_POSITIVES_INFORMATIVE,
)

NO_VERDICT = "no verdict"

Log = Callable[[str], None]


def _quiet(_m: str) -> None:
    return None


@dataclass
class BarRun:
    """One model family's predictions and its bar."""

    p_model: np.ndarray
    p_no_weather: np.ndarray
    swap_briers: np.ndarray
    lichen_p_weather: np.ndarray
    lichen_p_no_weather: np.ndarray
    bar: tb.BarResult
    chosen: dict = dataclasses.field(default_factory=dict)


def with_outcome(inputs: md.Inputs, y: np.ndarray) -> md.Inputs:
    return dataclasses.replace(inputs, y=np.asarray(y, dtype=np.float64))


def additive_bar(
    inputs: md.Inputs,
    t1_p: np.ndarray,
    cells: np.ndarray,
    lichen_y: np.ndarray,
    spec: md.ModelSpec,
    table: dict[int, np.ndarray],
    swaps: Sequence[dict[int, int]],
    log: Log = _quiet,
) -> BarRun:
    """The main model's bar: C1 to C4 (table: weather per source year, for the swaps)."""
    p = md.loyo_additive(inputs, spec, True)
    p0 = md.loyo_additive(inputs, spec, False)
    log(f"main {tm.brier(p, inputs.y):.6f}, no-weather {tm.brier(p0, inputs.y):.6f}")
    briers = np.empty(len(swaps))
    for k, s in enumerate(swaps):
        w = tw.swapped_matrix(table, inputs.years, s)
        briers[k] = tm.brier(md.loyo_additive(inputs, spec, True, weather=w), inputs.y)
        if (k + 1) % 20 == 0:
            log(f"swap {k + 1} of {len(swaps)}")
    lichen = with_outcome(inputs, lichen_y)
    lp = md.loyo_additive(lichen, spec, True)
    lp0 = md.loyo_additive(lichen, spec, False)
    result = tb.evaluate_bar(inputs.y, p, t1_p, p0, cells, briers, lichen_y, lp, lp0)
    return BarRun(p, p0, briers, lp, lp0, result)


def challenger_bar(
    inputs: md.Inputs,
    t1_p: np.ndarray,
    cells: np.ndarray,
    lichen_y: np.ndarray,
    configs: Sequence[dict],
    fitter: md.Fitter,
    table: dict[int, np.ndarray],
    swaps: Sequence[dict[int, int]],
    log: Log = _quiet,
) -> BarRun:
    """The challenger's own C1 to C4. Its swaps reuse each fold's true-weather choice
    (design.PENDING M-challenger-swaps)."""
    p, chosen = md.loyo_challenger(inputs, True, configs, fitter)
    p0, chosen0 = md.loyo_challenger(inputs, False, configs, fitter)
    log(f"challenger {tm.brier(p, inputs.y):.6f}, twin {tm.brier(p0, inputs.y):.6f}")
    briers = np.empty(len(swaps))
    for k, s in enumerate(swaps):
        w = tw.swapped_matrix(table, inputs.years, s)
        ps, _ = md.loyo_challenger(inputs, True, configs, fitter, weather=w, fixed_choice=chosen)
        briers[k] = tm.brier(ps, inputs.y)
        if (k + 1) % 20 == 0:
            log(f"challenger swap {k + 1} of {len(swaps)}")
    lichen = with_outcome(inputs, lichen_y)
    lp, lchosen = md.loyo_challenger(lichen, True, configs, fitter)
    lp0, lchosen0 = md.loyo_challenger(lichen, False, configs, fitter)
    result = tb.evaluate_bar(inputs.y, p, t1_p, p0, cells, briers, lichen_y, lp, lp0)
    return BarRun(
        p, p0, briers, lp, lp0, result,
        {"weather": chosen, "no_weather": chosen0, "lichen_weather": lchosen,
         "lichen_no_weather": lchosen0},
    )  # fmt: skip


def measure_alone(
    inputs: md.Inputs,
    spec: md.ModelSpec,
    p_no_weather: np.ndarray,
    cells: np.ndarray,
    table: dict[int, np.ndarray],
    swaps: Sequence[dict[int, int]],
    j: int,
    log: Log = _quiet,
) -> dict:
    """The no-weather model plus measure j alone, its skill over no-weather and its own swaps
    (design.PENDING M-measure-alone). No verdict."""
    one = dataclasses.replace(inputs, weather=inputs.weather[:, [j]])
    p = md.loyo_additive(one, spec, True)
    observed = tm.brier(p, inputs.y)
    briers = np.empty(len(swaps))
    for k, s in enumerate(swaps):
        w = tw.swapped_matrix(table, inputs.years, s)[:, [j]]
        briers[k] = tm.brier(md.loyo_additive(one, spec, True, weather=w), inputs.y)
    log(f"{MEASURES[j].name} alone done")
    return {
        "measure": MEASURES[j].name,
        "label": NO_VERDICT,
        **tb.skill_interval(p, p_no_weather, inputs.y, cells),
        **tb.swap_test(observed, briers),
    }


def per_year_table(
    y: np.ndarray, years: np.ndarray, p_model: np.ndarray, references: dict[str, np.ndarray]
) -> list[dict]:
    rows = []
    for h in sorted(set(years.tolist())):
        held = years == h
        row = {
            "year": int(h),
            "units": int(held.sum()),
            "positives": int(y[held].sum()),
            "informative": int(y[held].sum()) >= MIN_POSITIVES_INFORMATIVE,
            "brier_model": tm.brier(p_model[held], y[held]),
            "label": NO_VERDICT,
        }
        for name, ref in references.items():
            row[f"brier_{name}"] = tm.brier(ref[held], y[held])
            row[f"skill_vs_{name}"] = tm.brier_skill(p_model[held], ref[held], y[held])
        rows.append(row)
    return rows


def beside_line(
    y: np.ndarray,
    years: np.ndarray,
    p_model: np.ndarray,
    references: dict[str, np.ndarray],
    cells: np.ndarray,
    line_years: Sequence[int] = BESIDE_LINE_YEARS,
) -> dict:
    """The 2015-2023 line: pooled skill over those years' units only, with its interval."""
    keep = np.isin(years, list(line_years))
    return {
        "years": [int(min(line_years)), int(max(line_years))],
        "label": NO_VERDICT,
        **{
            name: tb.skill_interval(p_model[keep], ref[keep], y[keep], cells[keep])
            for name, ref in references.items()
        },
    }


def describe(p: np.ndarray, y: np.ndarray) -> dict:
    """AUC and the reliability table, as T1 reported them."""
    return {
        "brier": tm.brier(p, y),
        "auc": tm.auc(p, y),
        "reliability": tm.reliability_by_decile(p, y),
    }


def ecoregion_report(
    inputs: md.Inputs,
    spec: md.ModelSpec,
    blocks: np.ndarray,
    log_effort: np.ndarray,
    cells: np.ndarray,
) -> dict:
    """Leave-one-ecoregion-out, main against no-weather, per block and pooled. No verdict."""
    p = md.leave_one_block_out_additive(inputs, spec, True, blocks, log_effort)
    p0 = md.leave_one_block_out_additive(inputs, spec, False, blocks, log_effort)
    rows = []
    for b in sorted(set(blocks.tolist())):
        held = blocks == b
        positives = int(inputs.y[held].sum())
        rows.append(
            {
                "block": str(b),
                "units": int(held.sum()),
                "positives": positives,
                "informative": positives >= MIN_POSITIVES_INFORMATIVE,
                "skill_vs_no_weather": tm.brier_skill(p[held], p0[held], inputs.y[held]),
            }
        )
    return {
        "label": NO_VERDICT,
        "pooled": tb.skill_interval(p, p0, inputs.y, cells),
        "blocks": rows,
    }
