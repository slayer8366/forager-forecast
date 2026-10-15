"""scripts/pnw_t1_compare.py computes D33 (2)'s headline: one Brier skill pooled over every held-out
unit of all folds, not an average of per-fold skills, and refuses runs that hold different units.
Added by the D18 reviewer (docs/audits/2026-10-10-pnw-pilot-t1-review.md). Synthetic numbers
only."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

SCRIPT = Path(__file__).parents[1] / "scripts/pnw_t1_compare.py"


def compare_module():
    spec = importlib.util.spec_from_file_location("pnw_t1_compare", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_run(fits: Path, model: str, unit, cell, year, y, p, partial=False):
    np.savez_compressed(fits / f"t_{model}.npz", unit=unit, cell=cell, year=year, y=y, p=p)
    (fits / f"t_{model}.json").write_text(json.dumps({"partial": partial, "top_features": {}}))


def fixture(fits: Path, partial_full=False):
    # A large fold where the full model is slightly better and a small fold where it is much
    # worse: the pooled skill and the mean of the two fold skills then differ in sign.
    rng = np.random.default_rng(20260918)
    n_big, n_small = 400, 20
    year = np.array([2024] * n_big + [2016] * n_small)
    y = (rng.random(n_big + n_small) < 0.2).astype(float)
    y[n_big] = 1.0
    cal = np.full(n_big + n_small, 0.2)
    full = cal.copy()
    full[:n_big] = np.where(y[:n_big] == 1, 0.3, 0.15)
    full[n_big:] = np.where(y[n_big:] == 1, 0.01, 0.6)
    cell = np.array([f"c{i % 37}" for i in range(n_big + n_small)])
    unit = np.array([f"{c}@{i}" for i, c in enumerate(cell)])
    write_run(fits, "calendar", unit, cell, year, y, cal)
    write_run(fits, "full", unit, cell, year, y, full, partial=partial_full)
    return y, cal, full, year


def test_headline_is_pooled_over_all_held_out_units_not_a_mean_of_folds(tmp_path):
    y, cal, full, year = fixture(tmp_path)
    compare_module().main(tmp_path, "t")
    out = json.loads((tmp_path / "t_comparison.json").read_text())
    pooled = 1 - np.mean((full - y) ** 2) / np.mean((cal - y) ** 2)
    per_fold = [
        1 - np.mean((full[m] - y[m]) ** 2) / np.mean((cal[m] - y[m]) ** 2)
        for m in (year == 2016, year == 2024)
    ]
    assert abs(pooled - np.mean(per_fold)) > 0.05, "fixture must separate the two readings"
    assert out["skill"] == pytest.approx(pooled, rel=1e-12)
    assert out["units"] == len(y)
    assert [f["year"] for f in out["folds"]] == [2016, 2024]
    assert [f["informative"] for f in out["folds"]] == [False, True]
    assert out["label"] == "T1 result"


def test_a_partial_run_labels_the_comparison_partial(tmp_path):
    fixture(tmp_path, partial_full=True)
    compare_module().main(tmp_path, "t")
    out = json.loads((tmp_path / "t_comparison.json").read_text())
    assert out["label"] == "PARTIAL: not the T1 result"


def test_runs_on_different_units_are_refused(tmp_path):
    fixture(tmp_path)
    z = dict(np.load(tmp_path / "t_full.npz"))
    z["unit"] = z["unit"][::-1]
    np.savez_compressed(tmp_path / "t_full.npz", **z)
    with pytest.raises(SystemExit, match="do not hold the same units"):
        compare_module().main(tmp_path, "t")
