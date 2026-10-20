"""T8's fits (plan section 9, item 3; the second point of no return). scripts/t8_fit.py is the
command line; this module prepares the inputs and runs one part at a time, so each heavy part can
be run while t6b-night is paused or finished (plan section 9) and none runs beside another.

`prepare` reads, for one design (design.T1_LISTS):
- T1's units and stored calendar predictions (units.read_t1_units), and refuses unless the count's
  lichen file holds exactly those units in that order;
- the daily weather (weather.read_grids), with each unit's land point, which must be T1's own
  (`land_point` in T1's npz), and W1 to W4 at both timings, never filled;
- the swap tables, checked to reproduce the true weather under the identity mapping;
- E1 per held-out year from T6's counts (effort_term.all_folds), sha256 checked.

The parts (each writes <part>.json and its predictions to the output folder):
- "bar": the main model's C1 to C4 at the headline timing. On the headline design this is T8's
  verdict; with it, the per-year table, the 2015-2023 line, AUC and the reliability table.
- "forecast": the same at the forecast timing, no verdict (design.PENDING M-forecast-bar).
- "alone": each measure alone with its own swaps, no verdict (M-measure-alone).
- "challenger": the gradient-boosted challenger's own C1 to C4, and the better model by Brier.
- "ecoregion": leave-one-ecoregion-out, no verdict (M-ecoregion).
Only "bar" on the headline design carries a verdict (D133 (6)); every other result is labelled
"no verdict".
"""

from __future__ import annotations

import dataclasses
import json
import resource
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from forager_forecast import t1_model as tm
from forager_forecast.t8 import design
from forager_forecast.t8 import ecoregions as eco
from forager_forecast.t8 import effort_term as et
from forager_forecast.t8 import models as md
from forager_forecast.t8 import run as tr
from forager_forecast.t8 import units as tu
from forager_forecast.t8 import weather as tw

PARTS = ("bar", "forecast", "alone", "challenger", "ecoregion")
# D136: the challenger's 199 swaps keep each fold's tuning at the true-weather choice
# (M-challenger-swaps), which favours true weather a little, and the report must say so.
CHALLENGER_C3_LABEL = (
    "slightly generous to true weather: each swap keeps the fold's tuning chosen on true weather "
    "(D136, M-challenger-swaps)"
)
VERDICT = "verdict"

Log = Callable[[str], None]


class InputsDiffer(RuntimeError):
    """An input does not line up with T1's units, or is not what T1 read."""


@dataclass
class Prepared:
    design_name: str
    t1: tu.T1Units
    cells: np.ndarray  # cell id per unit
    lichen_y: np.ndarray
    headline: md.Inputs  # W at the headline timing (gap 1)
    forecast: md.Inputs  # W at the forecast timing (gap 8)
    table_headline: dict[int, np.ndarray]
    table_forecast: dict[int, np.ndarray]
    effort_configs: dict[int, str]
    interpolated_levels: dict[int, float]

    @property
    def is_headline(self) -> bool:
        return self.design_name == design.HEADLINE_LIST


def _quiet(_m: str) -> None:
    return None


def read_lichen(path: Path, t1: tu.T1Units) -> np.ndarray:
    z = np.load(path, allow_pickle=False)
    units = z["unit"].astype(str)
    if units.shape != t1.unit.shape or not np.array_equal(units, t1.unit):
        raise InputsDiffer(f"{path.name} does not hold T1's units in T1's order")
    y = z["lichen_y"].astype(float)
    if not np.isin(y, (0.0, 1.0)).all():
        raise InputsDiffer(f"{path.name} lichen outcomes are not all 0 or 1")
    return y


def weather_inputs(
    grids, t1: tu.T1Units
) -> tuple[np.ndarray, np.ndarray, dict[int, np.ndarray], dict[int, np.ndarray]]:
    """W1 to W4 at both timings and the swap tables, after the identity checks."""
    cells = t1.cells
    points = tw.unit_points(cells, grids)
    kinds = np.array(points.land_kind)
    if not np.array_equal(kinds, t1.land_point):
        bad = int((kinds != t1.land_point).sum())
        raise InputsDiffer(f"{bad} units' land point differs from T1's land_point")
    mondays = t1.mondays
    weeks = t1.iso_weeks
    years = t1.year.tolist()
    x = {}
    tables = {}
    for name, gap in (("headline", design.HEADLINE_END_GAP), ("forecast", design.FORECAST_END_GAP)):
        x[name] = tw.measures_for_units(grids, points, mondays, gap)
        tables[name] = tw.per_source_year(grids, points, years, weeks, gap, design.YEARS)
        identity = tw.swapped_matrix(tables[name], years, {y: y for y in design.YEARS})
        if not np.array_equal(identity, x[name]):
            raise InputsDiffer(f"the {name} swap table does not reproduce the true weather")
    return x["headline"], x["forecast"], tables["headline"], tables["forecast"]


def prepare(
    design_name: str,
    units_npz: Path,
    lichen_npz: Path,
    weather_npz: Path,
    counts_dir: Path,
    track: str,
    t6_results: Path,
    log: Log = _quiet,
) -> Prepared:
    design.require_ruled("fit")
    if design_name not in design.T1_LISTS:
        raise ValueError(f"unknown design {design_name!r}")
    t1 = tu.read_t1_units(units_npz)
    expected = design.T1_LISTS[design_name][1]
    if len(t1) != expected:
        raise tu.UnitsDiffer(f"{units_npz.name} holds {len(t1)} units, expected {expected}")
    lichen_y = read_lichen(lichen_npz, t1)
    log(f"{design_name}: {len(t1)} units, {int(t1.y.sum())} positive")
    grids = tw.read_grids(weather_npz)
    xh, xf, th, tf = weather_inputs(grids, t1)
    del grids
    log("weather: W1 to W4 at both timings, swap tables checked")
    fungi = et.read_counts(counts_dir, f"{track}_fungi.npz")
    lichen_counts = et.read_counts(counts_dir, f"{track}_lichen.npz")
    configs = et.chosen_per_fold(t6_results)
    folds = et.all_folds(fungi, lichen_counts, configs, t1.cells, t1.mondays, design.YEARS)
    log("effort: refitted per held-out year")
    lat = np.array([c.center_latitude for c in t1.cells])
    lon = np.array([c.center_longitude for c in t1.cells])
    log_effort = {h: f.log_effort for h, f in folds.items()}
    base = md.Inputs(t1.y, t1.year, t1.mondays, lat, lon, log_effort, xh)
    return Prepared(
        design_name=design_name,
        t1=t1,
        cells=t1.cell,
        lichen_y=lichen_y,
        headline=base,
        forecast=dataclasses.replace(base, weather=xf),
        table_headline=th,
        table_forecast=tf,
        effort_configs={h: c.id for h, c in configs.items()},
        interpolated_levels={h: f.interpolated_level for h, f in folds.items()},
    )


def bar_json(run: tr.BarRun, label: str) -> dict:
    return {
        "label": label,
        "passed": run.bar.passed,
        "reason": run.bar.reason,
        "conditions": [
            {"name": c.name, "passed": c.passed, "reason": c.reason, "figures": c.figures}
            for c in run.bar.conditions
        ],
        "swap_briers": run.swap_briers.tolist(),
        "chosen": run.chosen,
    }


def run_part(
    part: str,
    prep: Prepared,
    out_dir: Path,
    spec: md.ModelSpec = md.PROPOSED_SPEC,
    fitter: md.Fitter | None = None,
    configs: list[dict] | None = None,
    blocks: np.ndarray | None = None,
    block_effort: np.ndarray | None = None,
    log: Log = _quiet,
) -> dict:
    """Runs one part and writes <design>_<part>.json (and predictions) to out_dir."""
    design.require_ruled("fit")
    if part not in PARTS:
        raise ValueError(f"unknown part {part!r}")
    started = time.monotonic()
    swaps = tw.draw_swaps(design.YEARS, design.N_SWAPS, design.SEED)
    t1p, y, cells = prep.t1.p, prep.headline.y, prep.cells
    result: dict = {"design": prep.design_name, "part": part, "spec": dataclasses.asdict(spec)}
    arrays: dict[str, np.ndarray] = {"unit": prep.t1.unit}
    if part in ("bar", "forecast"):
        inputs, table = (
            (prep.headline, prep.table_headline)
            if part == "bar"
            else (prep.forecast, prep.table_forecast)
        )
        run = tr.additive_bar(inputs, t1p, cells, prep.lichen_y, spec, table, swaps, log)
        label = VERDICT if (part == "bar" and prep.is_headline) else tr.NO_VERDICT
        result["bar"] = bar_json(run, label)
        refs = {"t1_calendar": t1p, "no_weather": run.p_no_weather}
        result["per_year"] = tr.per_year_table(y, inputs.years, run.p_model, refs)
        result["line_2015_2023"] = tr.beside_line(y, inputs.years, run.p_model, refs, cells)
        result["describe"] = {
            "main": tr.describe(run.p_model, y),
            "no_weather": tr.describe(run.p_no_weather, y),
            "t1_calendar": tr.describe(t1p, y),
        }
        arrays |= {"p_main": run.p_model, "p_no_weather": run.p_no_weather,
                   "lichen_p_main": run.lichen_p_weather,
                   "lichen_p_no_weather": run.lichen_p_no_weather}  # fmt: skip
    elif part == "alone":
        p0 = md.loyo_additive(prep.headline, spec, False)
        result["measures"] = [
            tr.measure_alone(prep.headline, spec, p0, cells, prep.table_headline, swaps, j, log)
            for j in range(len(design.MEASURES))
        ]
        result["label"] = tr.NO_VERDICT
    elif part == "challenger":
        if fitter is None or configs is None:
            raise ValueError("the challenger needs T1's configurations and a fitter")
        run = tr.challenger_bar(
            prep.headline, t1p, cells, prep.lichen_y, configs, fitter,
            prep.table_headline, swaps, log,
        )  # fmt: skip
        main = out_dir / f"{prep.design_name}_bar.npz"
        if not main.exists():
            raise FileNotFoundError(f"run the bar part first: {main} is the main model's")
        p_main = np.load(main)["p_main"]
        briers = {"main": tm.brier(p_main, y), "challenger": tm.brier(run.p_model, y)}
        result["challenger"] = bar_json(run, tr.NO_VERDICT)
        result["challenger"]["note"] = "passes only if it clears C1 to C4 itself (D133 (6))"
        for condition in result["challenger"]["conditions"]:
            if condition["name"] == "C3":
                condition["label"] = CHALLENGER_C3_LABEL
        result["better_by_brier"] = {"briers": briers, "better": min(briers, key=briers.get)}
        arrays |= {"p_challenger": run.p_model, "p_challenger_no_weather": run.p_no_weather}
    else:  # ecoregion
        if blocks is None or block_effort is None:
            raise ValueError("the ecoregion part needs each unit's block and its effort")
        result["ecoregion"] = tr.ecoregion_report(prep.headline, spec, blocks, block_effort, cells)
        arrays |= {"block": blocks}
    result["effort_configs"] = prep.effort_configs
    result["interpolated_levels"] = prep.interpolated_levels
    result["seconds"] = round(time.monotonic() - started, 1)
    result["peak_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / f"{prep.design_name}_{part}"
    np.savez_compressed(f"{stem}.npz", **arrays)
    Path(f"{stem}.json").write_text(json.dumps(result, indent=2, default=float) + "\n")
    return result


def unit_blocks(
    prep: Prepared, cec_zip: Path, cec_sha256: str, scratch: Path
) -> tuple[np.ndarray, int]:
    """Each unit's CEC level III block (by its cell's centre), and the centres claimed twice."""
    shp = eco.extract_level3(cec_zip, cec_sha256, scratch)
    polygons = eco.read_level3(shp)
    distinct = sorted(set(prep.cells.tolist()))
    codes, shared = eco.assign([tu.parse_cell(c) for c in distinct], polygons)
    by_cell = dict(zip(distinct, codes, strict=True))
    return np.array([by_cell[c] for c in prep.cells]), shared
