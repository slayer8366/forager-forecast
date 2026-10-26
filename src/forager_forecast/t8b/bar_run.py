"""T8b's bar on the main tree model (plan section 7; D159 (4), (6)).

C1 to C4 are T8's own function (t8/bar.py `evaluate_bar`), unchanged: every interval from 1,000
resamples of cells, seed 20260918, C3 over 199 whole-year swaps with p = (1 + swaps at or below
the model's Brier) / 200. This module only supplies the tree model's predictions, in the shape
T8's challenger_bar did (t8/run.py), with the clamp (clamp.py) applied in every fold:

1. the main model, each fold tuned by T1's inner leave-one-year-out on true weather;
2. the no-weather twin, tuned on its own;
3. 199 swaps, each refitted with every fold's configuration held at the one chosen in 1
   (D159 (4): "tuned once per fold ... and held fixed for the 199 shuffles");
4. the lichen outcome's weather and no-weather models (C4), each tuned as 1 and 2.

`measure_shuffle` is the per-measure shuffle reported beside with no verdict (PENDING
B-measure-shuffle, proposed): only one measure's column takes the swapped year's values.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np

from forager_forecast import t1_model as tm
from forager_forecast.t8 import bar as tb
from forager_forecast.t8 import models as md
from forager_forecast.t8 import run as tr
from forager_forecast.t8 import weather as tw
from forager_forecast.t8b import design
from forager_forecast.t8b import models as bm
from forager_forecast.t8b.design import MEASURES

Log = Callable[[str], None]


def _quiet(_m: str) -> None:
    return None


def tree_bar(
    inputs: md.Inputs,
    t1_p: np.ndarray,
    cells: np.ndarray,
    lichen_y: np.ndarray,
    configs: Sequence[dict],
    fitter: md.Fitter,
    table: dict[int, np.ndarray],
    swaps: Sequence[dict[int, int]],
    log: Log | None = None,
) -> tr.BarRun:
    """The main tree model's C1 to C4 (table: M1 to M5 per source year, for the swaps)."""
    design.require_ruled("fit")
    log = log or _quiet
    p, chosen = bm.loyo_trees(inputs, True, configs, fitter)
    p0, chosen0 = bm.loyo_trees(inputs, False, configs, fitter)
    log(f"trees {tm.brier(p, inputs.y):.6f}, no-weather {tm.brier(p0, inputs.y):.6f}")
    briers = np.empty(len(swaps))
    for k, s in enumerate(swaps):
        w = tw.swapped_matrix(table, inputs.years, s)
        ps, _ = bm.loyo_trees(inputs, True, configs, fitter, weather=w, fixed_choice=chosen)
        briers[k] = tm.brier(ps, inputs.y)
        if (k + 1) % 20 == 0:
            log(f"swap {k + 1} of {len(swaps)}")
    lichen = tr.with_outcome(inputs, lichen_y)
    lp, lchosen = bm.loyo_trees(lichen, True, configs, fitter)
    lp0, lchosen0 = bm.loyo_trees(lichen, False, configs, fitter)
    result = tb.evaluate_bar(inputs.y, p, t1_p, p0, cells, briers, lichen_y, lp, lp0)
    return tr.BarRun(
        p, p0, briers, lp, lp0, result,
        {"weather": chosen, "no_weather": chosen0, "lichen_weather": lchosen,
         "lichen_no_weather": lchosen0},
    )  # fmt: skip


def measure_shuffle(
    inputs: md.Inputs,
    configs: Sequence[dict],
    fitter: md.Fitter,
    chosen: dict[int, str],
    p_no_weather: np.ndarray,
    cells: np.ndarray,
    table: dict[int, np.ndarray],
    swaps: Sequence[dict[int, int]],
    j: int,
) -> dict:
    """Measure j's own shuffle: the main model with only column j swapped, tuning fixed at the
    true-weather choice. Its skill over no-weather and its p. No verdict."""
    design.require_ruled("fit")
    p, _ = bm.loyo_trees(inputs, True, configs, fitter, fixed_choice=chosen)
    observed = tm.brier(p, inputs.y)
    briers = np.empty(len(swaps))
    for k, s in enumerate(swaps):
        w = inputs.weather.copy()
        w[:, j] = tw.swapped_matrix(table, inputs.years, s)[:, j]
        ps, _ = bm.loyo_trees(inputs, True, configs, fitter, weather=w, fixed_choice=chosen)
        briers[k] = tm.brier(ps, inputs.y)
    return {
        "measure": MEASURES[j].name,
        "label": tr.NO_VERDICT,
        **tb.skill_interval(p, p_no_weather, inputs.y, cells),
        **tb.swap_test(observed, briers),
    }
