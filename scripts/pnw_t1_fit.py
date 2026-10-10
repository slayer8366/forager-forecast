"""T1's fit on the PNW box (T1 dispatch; D13, D31, D33; D122).

Run:  uv run python scripts/pnw_t1_fit.py --records <records dir> --list t1_1000m
          --design primary|secondary --model calendar|full [--weather <daily npz>]
          [--years 2019,2020,...] --out <dir> [--threads 4]

Primary design (D13): unit = 0.1° cell x ISO week; eligible = at least one survivor of the list in
it; positive = at least one Cantharellus survivor (`cell_weeks.label_cell_weeks`). Only ISO weeks
wholly inside 2015-01-01 to 2025-12-31 are units (2015-W02 to 2025-W52, as T6 framed its weeks,
D101), so no unit is part-filtered by the year step. The fold year is the ISO year.

Secondary design (D13, for comparison only): each Cantharellus survivor is a presence at its own
date; 12 random-date pseudo-absences per record at the same coordinates (dispatch), dates uniform
over 2015-01-01 to 2025-12-31, seed 20260918. Fold year = calendar year of the date.

Calendar model: doy_sin, doy_cos, latitude, longitude (weather_windows.calendar_place_features at
the cell centre, scored date = Monday of the week, or the record date). Full model: those plus the
32 weather windows (weather_windows.window_features).

Writes predictions (npz), fold table and summary (json) to --out. A run on a subset of years
(--years) is labelled partial in its summary and is never the T1 result.
"""

import argparse
import csv
import json
import os
import resource
import sys
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np

from forager_forecast import t1_model as tm
from forager_forecast.cell_weeks import CellWeek, label_cell_weeks
from forager_forecast.cells import cell_for
from forager_forecast.records.occurrence import Record
from forager_forecast.t1_design import (
    CANTHARELLUS_GENUS_KEY,
    RANDOM_DATE_PSEUDO_ABSENCES_PER_RECORD,
)
from forager_forecast.weather_windows import calendar_place_features

FIRST_DAY = date(2015, 1, 1)
LAST_DAY = date(2025, 12, 31)
MODELS_DIR = Path.home() / "Zynergy/forecast-data-pnw-pilot/models"
GRID_FILE = Path(__file__).parents[1] / "docs/audits/2026-10-10-pnw-pilot-t1/tuning_grid.json"


def log(msg: str) -> None:
    print(f"{datetime.now(UTC).isoformat(timespec='seconds')} {msg}", flush=True)


def read_records(path: Path) -> list[Record]:
    out = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            out.append(
                Record(
                    gbif_id=int(row["gbif_id"]),
                    taxon_key=int(row["taxon_key"]),
                    genus_key=int(row["genus_key"]) if row["genus_key"] else None,
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    event_date=date.fromisoformat(row["event_date"]),
                    event_time=None,
                    coordinate_uncertainty_m=None,
                    license=row["license"],
                )
            )
    return out


def week_inside(unit: CellWeek) -> bool:
    monday = unit.week.monday()
    return monday >= FIRST_DAY and monday + timedelta(days=6) <= LAST_DAY


def primary_units(records: list[Record]):
    labelled = [r for r in label_cell_weeks(records, CANTHARELLUS_GENUS_KEY) if week_inside(r.unit)]
    rows = []
    for r in labelled:
        rows.append(
            {
                "cell": r.unit.cell,
                "scored": r.unit.week.monday(),
                "year": r.unit.week.year,
                "y": 1.0 if r.positive else 0.0,
                "lat": r.unit.cell.center_latitude,
                "lon": r.unit.cell.center_longitude,
            }
        )
    return rows


def secondary_units(records: list[Record]):
    rng = np.random.default_rng(tm.SEED)
    span = (LAST_DAY - FIRST_DAY).days + 1
    rows = []
    for r in sorted(
        (r for r in records if r.genus_key == CANTHARELLUS_GENUS_KEY), key=lambda r: r.gbif_id
    ):
        cell = cell_for(r.latitude, r.longitude)
        base = {"cell": cell, "lat": cell.center_latitude, "lon": cell.center_longitude}
        rows.append({**base, "scored": r.event_date, "year": r.event_date.year, "y": 1.0})
        for offset in rng.integers(0, span, size=RANDOM_DATE_PSEUDO_ABSENCES_PER_RECORD):
            d = FIRST_DAY + timedelta(days=int(offset))
            rows.append({**base, "scored": d, "year": d.year, "y": 0.0})
    return rows


def calendar_matrix(rows) -> tuple[np.ndarray, list[str]]:
    names = ["doy_sin", "doy_cos", "latitude", "longitude"]
    x = np.array(
        [list(calendar_place_features(r["scored"], r["lat"], r["lon"]).values()) for r in rows]
    )
    return x, names


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", type=Path, required=True)
    ap.add_argument("--list", default="t1_1000m")
    ap.add_argument("--design", choices=["primary", "secondary"], required=True)
    ap.add_argument("--model", choices=["calendar", "full"], required=True)
    ap.add_argument("--weather", type=Path)
    ap.add_argument("--years", default="")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument(
        "--final-only",
        action="store_true",
        help="skip the evaluation; only fit and save the all-years model for scoring",
    )
    ap.add_argument("--models", type=Path, default=MODELS_DIR)
    args = ap.parse_args()
    started = time.monotonic()
    commit, dirty = code_state()
    if dirty:
        raise SystemExit(
            f"tracked files are uncommitted; commit before fitting (review S2):\n{dirty}"
        )

    committed = json.loads(GRID_FILE.read_text())
    configs = tm.tuning_configurations()
    if committed["configurations"] != configs:
        raise SystemExit("the committed tuning grid differs from tuning_configurations()")

    records = read_records(args.records / f"{args.list}.csv")
    rows = primary_units(records) if args.design == "primary" else secondary_units(records)
    years_all = sorted({r["year"] for r in rows})
    partial = bool(args.years)
    if partial:
        keep = {int(y) for y in args.years.split(",")}
        rows = [r for r in rows if r["year"] in keep]
    log(f"{len(rows)} units, {int(sum(r['y'] for r in rows))} positive, years {years_all}")

    # Review B3: weather that is missing is counted and its units dropped, never passed to the
    # model as NaN. The calendar model is given the same --weather so that both models are fitted
    # and scored on the same units. Sea points (no ERA5-Land value at the cell) are dropped and
    # counted. A window reaching a month not yet pulled is allowed only in a run labelled partial.
    weather_drops: dict = {}
    if args.weather:
        from pnw_weather import weather_matrix, weather_status  # noqa: PLC0415

        wx, wnames, kind = weather_matrix(args.weather, rows)
        status = weather_status(args.weather, rows, wx, kind)
        nan_by_feature = {n: int(np.isnan(wx[:, j]).sum()) for j, n in enumerate(wnames)}
        by_reason_year: dict[str, dict[str, int]] = {}
        for r, st in zip(rows, status, strict=True):
            if st != "ok":
                by_reason_year.setdefault(st, {})
                y_key = str(r["year"])
                by_reason_year[st][y_key] = by_reason_year[st].get(y_key, 0) + 1
        dropped_cells = sorted(
            {r["cell"].id for r, st in zip(rows, status, strict=True) if st == "sea"}
        )
        kept_kind = [k for k, st in zip(kind, status, strict=True) if st == "ok"]
        weather_drops = {
            "units_before": len(rows),
            "kept_land_point_own": kept_kind.count("own"),
            "kept_land_point_neighbour_RECORD_822": kept_kind.count("neighbour"),
            "kept_neighbour_positives": int(
                sum(
                    r["y"]
                    for r, k, st in zip(rows, kind, status, strict=True)
                    if st == "ok" and k == "neighbour"
                )
            ),
            "neighbour_cells": sorted(
                {
                    r["cell"].id
                    for r, k, st in zip(rows, kind, status, strict=True)
                    if st == "ok" and k == "neighbour"
                }
            ),
            "dropped_by_reason_and_year": by_reason_year,
            "dropped_positives": int(
                sum(r["y"] for r, st in zip(rows, status, strict=True) if st != "ok")
            ),
            "sea_cells": dropped_cells,
            "nan_units_by_feature": nan_by_feature,
        }
        if "missing_days" in by_reason_year and not partial:
            raise SystemExit(
                f"weather missing for {sum(by_reason_year['missing_days'].values())} units "
                "(months not pulled); a run over all years refuses them (review B3)"
            )
        keep_mask = np.array([st == "ok" for st in status])
        rows = [r for r, k in zip(rows, keep_mask, strict=True) if k]
        wx = wx[keep_mask]
        for r, k in zip(rows, kept_kind, strict=True):
            r["land_point"] = k
        weather_drops["copernicus_sources"] = copernicus_sources(args.weather)
        log(f"weather: kept {len(rows)}, dropped {weather_drops['dropped_by_reason_and_year']}")
    x, names = calendar_matrix(rows)
    if args.model == "full":
        if not args.weather:
            raise SystemExit("--model full needs --weather")
        x = np.hstack([x, wx])
        names = names + wnames
    y = np.array([r["y"] for r in rows])
    years = np.array([r["year"] for r in rows])
    cells = np.array([r["cell"].id for r in rows])

    def fitter(config, train_x, train_y, test_x):
        return tm.fit_predict(config, train_x, train_y, test_x, args.threads)

    tag = f"{args.design}_{args.list}_{args.model}"
    if not partial:
        save_final_model(configs, x, y, years, names, fitter, args, tag)
    if args.final_only:
        return 0

    predictions, folds = tm.leave_one_year_out(configs, x, y, years, fitter, log)

    args.out.mkdir(parents=True, exist_ok=True)
    unit_ids = np.array([f"{r['cell'].id}@{r['scored'].isoformat()}" for r in rows])
    np.savez_compressed(
        args.out / f"{tag}.npz",
        unit=unit_ids,
        cell=cells,
        year=years,
        y=y,
        p=predictions,
        land_point=np.array([r.get("land_point", "") for r in rows]),
    )
    importance = {}
    if args.model == "full":
        importance = top_features(configs, folds, x, y, years, names, args.threads)
    summary = {
        "tag": tag,
        "partial": partial,
        "years_present": years_all,
        "years_fitted": sorted(set(years.tolist())),
        "label": (
            "PARTIAL: a fit on a subset of years, not the T1 result" if partial else "all years"
        ),
        "units": len(rows),
        "positives": int(y.sum()),
        "features": names,
        "brier": tm.brier(predictions, y),
        "auc": tm.auc(predictions, y),
        "reliability": tm.reliability_by_decile(predictions, y),
        "folds": [
            {
                "year": f.year,
                "units": f.units,
                "positives": f.positives,
                "informative": f.informative,
                "chosen": f.chosen,
                "brier": tm.brier(predictions[years == f.year], y[years == f.year]),
            }
            for f in folds
        ],
        "inner_scores": {str(f.year): f.inner_scores for f in folds},
        "top_features": importance,
        "seed": tm.SEED,
        "commit": commit,
        "weather_npz": str(args.weather) if args.weather else None,
        "weather_units_dropped": weather_drops,
        "threads": args.threads,
        "seconds": round(time.monotonic() - started, 1),
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "written_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "pid": os.getpid(),
    }
    (args.out / f"{tag}.json").write_text(json.dumps(summary, indent=2) + "\n")
    log(
        f"done {tag}: brier {summary['brier']:.5f} auc {summary['auc']:.4f}"
        f" in {summary['seconds']} s"
    )
    return 0


def save_final_model(configs, x, y, years, names, fitter, args, tag) -> None:
    """The model the map scores with: one fit on every year, with the configuration the same
    inner leave-one-year-out rule picks over all years (tm.inner_choice). Not an evaluation
    result; it never feeds the headline, which comes only from held-out predictions."""
    import subprocess  # noqa: PLC0415

    import lightgbm as lgb  # noqa: PLC0415

    best, scores = tm.inner_choice(configs, x, y, years, fitter)
    params = {
        "objective": "binary",
        "verbose": -1,
        "seed": tm.SEED,
        "deterministic": True,
        "force_row_wise": True,
        "num_threads": args.threads,
        "bagging_seed": tm.SEED,
        "feature_fraction_seed": tm.SEED,
        **{k: v for k, v in best.items() if k not in ("id", "num_boost_round")},
    }
    booster = lgb.train(params, lgb.Dataset(x, y), num_boost_round=best["num_boost_round"])
    out = args.models / tag
    out.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(out / "model.txt"))
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path(__file__).parent,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path(__file__).parent,
    ).stdout.strip()
    meta = {
        "tag": tag,
        "purpose": "scoring for the prototype map (Forager RECORD -814); NOT an evaluation result",
        "feature_names": names,
        "chosen_config": best,
        "inner_scores_all_years": scores,
        "years": sorted(set(years.tolist())),
        "units": int(len(y)),
        "positives": int(y.sum()),
        "weather_npz": str(args.weather) if args.weather else None,
        "copernicus_sources": copernicus_sources(args.weather) if args.weather else [],
        "commit": commit,
        "working_tree_dirty": bool(dirty),
        "written_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "label": "unvalidated pilot, unreviewed; sighting chance (D12)",
    }
    (out / "model.json").write_text(json.dumps(meta, indent=2) + "\n")
    log(f"final model saved to {out} ({best['id']})")


def copernicus_sources(weather: Path | None) -> list[str]:
    """The store products this weather file was built from, from its build summary
    (`<npz>.summary.json`, written by pnw_weather.py): era5_daily_sum (ERA5 single-levels daily
    statistics, rain), era5_land_daily (ERA5-Land daily statistics), era5_land_hourly (hourly
    ERA5-Land aggregated to the UTC day). Only those actually read. Refuses without the summary."""
    if weather is None:
        return []
    summary_path = Path(str(weather) + ".summary.json")
    if not summary_path.exists():
        raise SystemExit(f"no build summary beside {weather}; rebuild with scripts/pnw_weather.py")
    summary = json.loads(summary_path.read_text())
    out = []
    if summary["files"].get("precip", 0):
        out.append("era5_daily_sum")
    routes = set(summary.get("land_route_by_month", {}).values())
    if "derived daily statistics" in routes:
        out.append("era5_land_daily")
    if any(r.startswith("hourly") for r in routes):
        out.append("era5_land_hourly")
    return out


def code_state() -> tuple[str, str]:
    import subprocess  # noqa: PLC0415

    here = Path(__file__).parent
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=here
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        capture_output=True,
        text=True,
        check=True,
        cwd=here,
    ).stdout.strip()
    return commit, dirty


def top_features(configs, folds, x, y, years, names, threads) -> dict[str, float]:
    """Gain importance, summed over the outer folds' final models (each with its chosen config)."""
    import lightgbm as lgb  # noqa: PLC0415

    by_id = {c["id"]: c for c in configs}
    total = np.zeros(len(names))
    for f in folds:
        c = by_id[f.chosen]
        train = years != f.year
        params = {
            "objective": "binary",
            "verbose": -1,
            "seed": tm.SEED,
            "deterministic": True,
            "force_row_wise": True,
            "num_threads": threads,
            "bagging_seed": tm.SEED,
            "feature_fraction_seed": tm.SEED,
            **{k: v for k, v in c.items() if k not in ("id", "num_boost_round")},
        }
        booster = lgb.train(
            params, lgb.Dataset(x[train], y[train]), num_boost_round=c["num_boost_round"]
        )
        total += booster.feature_importance(importance_type="gain")
    order = np.argsort(-total)[:10]
    return {names[i]: float(total[i]) for i in order}


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main())
