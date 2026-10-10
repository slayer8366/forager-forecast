"""T1's headline: Brier skill of the full model against the calendar baseline (D33 (2)).

Run:  uv run python scripts/pnw_t1_compare.py <fits dir> <tag prefix, e.g. primary_t1_1000m>

Reads <prefix>_calendar.npz and <prefix>_full.npz. Both must hold the same units in the same order
(checked). Pooled skill over every held-out unit of all folds, 95% interval from 1,000 resamples of
cells (seed 20260918), a per-fold table with folds under 30 positives marked uninformative, and the
verdict under D33 (5): if the interval includes zero, "not shown".
"""

import json
import sys
from pathlib import Path

import numpy as np

from forager_forecast import t1_model as tm


def main(fits: Path, prefix: str) -> int:
    cal = np.load(fits / f"{prefix}_calendar.npz")
    full = np.load(fits / f"{prefix}_full.npz")
    if not np.array_equal(cal["unit"], full["unit"]) or not np.array_equal(cal["y"], full["y"]):
        raise SystemExit("the two runs do not hold the same units")
    cal_meta = json.loads((fits / f"{prefix}_calendar.json").read_text())
    full_meta = json.loads((fits / f"{prefix}_full.json").read_text())
    y, pc, pf, years, cells = cal["y"], cal["p"], full["p"], cal["year"], cal["cell"]
    skill = tm.brier_skill(pf, pc, y)
    low, high, _ = tm.clustered_bootstrap_skill(pf, pc, y, cells)
    folds = []
    for yr in sorted(set(years.tolist())):
        m = years == yr
        pos = int(y[m].sum())
        folds.append(
            {
                "year": yr,
                "units": int(m.sum()),
                "positives": pos,
                "informative": pos >= tm.MIN_POSITIVES_INFORMATIVE,
                "brier_calendar": tm.brier(pc[m], y[m]),
                "brier_full": tm.brier(pf[m], y[m]),
                "skill": tm.brier_skill(pf[m], pc[m], y[m]),
            }
        )
    partial = cal_meta["partial"] or full_meta["partial"]
    result = {
        "prefix": prefix,
        "label": "PARTIAL: not the T1 result" if partial else "T1 result",
        "years": sorted(set(years.tolist())),
        "units": int(len(y)),
        "positives": int(y.sum()),
        "cells": int(len(set(cells.tolist()))),
        "brier_calendar": tm.brier(pc, y),
        "brier_full": tm.brier(pf, y),
        "skill": skill,
        "interval_95": [low, high],
        "verdict": "weather adds skill" if low > 0 else ("not shown" if high >= 0 else "worse"),
        "auc_calendar": tm.auc(pc, y),
        "auc_full": tm.auc(pf, y),
        "reliability_full": tm.reliability_by_decile(pf, y),
        "reliability_calendar": tm.reliability_by_decile(pc, y),
        "top_features_full": full_meta["top_features"],
        "folds": folds,
    }
    (fits / f"{prefix}_comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if "reliability" not in k}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), sys.argv[2]))
