"""Revert checks for the T8b step 1 tests that guard a D159 rule (committed exactly as it ran).

Each check copies src/ and tests/ from the worktree into its own fresh scratch folder, makes one
edit there (the edit must match exactly once), and runs the named test files against the copy
(PYTHONPATH puts the copy's src first; the log prints which forager_forecast was imported). The
worktree is never edited, so nothing needs restoring from git; its files' sha256 are taken before
and after every check and must not change. A run whose log shows a collection, import or syntax
error is refused as evidence, and the expected failing test must be among the failures.

Run: python -I revert_checks.py <worktree> <scratch> <venv python>
"""

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

CHECKS = [
    ("R1-tree-clamp", "src/forager_forecast/t8b/models.py",
     "fold_w = cl.clamp_to_training(w, ~held) if use_weather else None",
     "fold_w = w if use_weather else None",
     ["tests/test_t8b_models.py"],
     ["test_the_held_out_year_reaches_the_trees_clamped_to_its_folds_training_range"]),
    ("R2-readable-clamp", "src/forager_forecast/t8b/models.py",
     "fold_w = cl.clamp_to_training(w, train)",
     "fold_w = w",
     ["tests/test_t8b_models.py"],
     ["test_the_readable_model_does_not_extrapolate_past_a_folds_training_range"]),
    ("R3-clamp-function", "src/forager_forecast/t8b/clamp.py",
     "return np.clip(np.asarray(weather, dtype=np.float64), low, high)",
     "return np.asarray(weather, dtype=np.float64).copy()",
     ["tests/test_t8b_models.py"],
     ["test_values_outside_the_range_take_its_nearest_end_and_inside_stay_as_they_are",
      "test_clamp_to_training_clamps_held_out_rows_to_the_training_range"]),
    ("R4-window-day-before", "src/forager_forecast/t8b/daymet.py",
     "last_day = monday - timedelta(days=gap)",
     "last_day = monday - timedelta(days=gap - 1)",
     ["tests/test_t8b_daymet.py"],
     ["test_the_window_ends_the_day_before_the_week"]),
    ("R5-leap-daymet-days", "src/forager_forecast/t8b/daymet.py",
     "dropped = set(dropped_days(first, last))",
     "dropped = set()",
     ["tests/test_t8b_daymet.py"],
     ["test_a_window_over_a_dropped_31_december_counts_w_daymet_days"]),
    ("R6-m5-depression", "src/forager_forecast/t8b/era5land.py",
     "DailyGrid(t2m.start, t2m.index, t2m.values - d2m.values)",
     "DailyGrid(t2m.start, t2m.index, t2m.values)",
     ["tests/test_t8b_era5land.py"],
     ["test_daily_statistics_give_layer_2_and_the_dewpoint_depression"]),
    ("R7-m3-window", "src/forager_forecast/t8b/design.py",
     'Measure("M3", "soil_moisture_l2", "mean", 14)',
     'Measure("M3", "soil_moisture_l2", "mean", 7)',
     ["tests/test_t8b_design.py", "tests/test_t8b_measures.py"],
     ["test_the_five_measures_are_d159s_and_nothing_else",
      "test_the_measures_are_d159s_windows_ending_the_day_before_the_week"]),
    ("R8-swaps-hold-tuning", "src/forager_forecast/t8b/bar_run.py",
     "ps, _ = bm.loyo_trees(inputs, True, configs, fitter, weather=w, fixed_choice=chosen)\n"
     "        briers[k] = tm.brier(ps, inputs.y)\n        if",
     "ps, _ = bm.loyo_trees(inputs, True, configs, fitter, weather=w)\n"
     "        briers[k] = tm.brier(ps, inputs.y)\n        if",
     ["tests/test_t8b_bar.py"],
     ["test_tuning_runs_once_per_fold_and_the_199_swaps_reuse_it"]),
    ("R9-frozen-checksum", "src/forager_forecast/t8b/frozen.py",
     "if got != expected_sha256:",
     "if False:",
     ["tests/test_t8b_frozen_c5.py"],
     ["test_a_different_checksum_or_an_edited_file_is_refused"]),
    ("R10-c5-weeks", "src/forager_forecast/t8b/c5.py",
     "if not np.isin(u.iso_week, design.C5_WEEKS).all():",
     "if False:",
     ["tests/test_t8b_frozen_c5.py"],
     ["test_c5_refuses_a_unit_outside_2026_weeks_27_to_52"]),
    ("R11-c5-after", "src/forager_forecast/t8b/c5.py",
     "day = design.C5_DOWNLOAD_AFTER + timedelta(days=1)",
     "day = design.C5_DOWNLOAD_AFTER",
     ["tests/test_t8b_frozen_c5.py"],
     ["test_the_download_must_be_taken_after_15_february_2027"]),
    ("R12-c5-ruled", "src/forager_forecast/t8b/c5.py",
     '    design.require_ruled("c5")\n',
     "",
     ["tests/test_t8b_frozen_c5.py"],
     ["test_c5_refuses_while_its_readings_are_open"]),
    ("R13-jump-third", "src/forager_forecast/t8b/jump_reporting.py",
     "return abs(s1 / s0 - 1) > MOVE",
     "return abs(s1 / s0 - 1) >= MOVE",
     ["tests/test_t8b_jump.py"],
     ["test_a_share_moves_when_it_changes_by_more_than_a_third_of_itself"]),
    ("R14-jump-fungi", "src/forager_forecast/t8b/jump_reporting.py",
     "if ch and not fu:",
     "if ch:",
     ["tests/test_t8b_jump.py"],
     ["test_a_move_shared_by_all_fungi_stays_undetermined"]),
    ("R15-never-filled", "src/forager_forecast/t8b/measures.py",
     "    if bad.any():\n        by =",
     "    if False:\n        by =",
     ["tests/test_t8b_measures.py"],
     ["test_a_unit_with_a_missing_window_is_refused_and_counted"]),
    ("R16-partial-pixel", "src/forager_forecast/t8b/daymet.py",
     "        if partial.any():\n",
     "        if False:\n",
     ["tests/test_t8b_daymet.py"],
     ["test_a_pixel_missing_on_some_days_but_not_all_is_refused"]),
]  # fmt: skip

BAD_LOG = re.compile(
    r"ERROR collecting|ImportError|SyntaxError|ModuleNotFoundError|IndentationError"
)


def tree_hashes(root: Path) -> dict[str, str]:
    out = {}
    for sub in ("src", "tests"):
        for p in sorted((root / sub).rglob("*.py")):
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main() -> int:
    worktree, scratch, python = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    scratch.mkdir(parents=True, exist_ok=True)
    before = tree_hashes(worktree)
    failures = 0
    for name, rel, old, new, tests, expected in CHECKS:
        copy = scratch / name
        if copy.exists():
            shutil.rmtree(copy)
        for sub in ("src", "tests"):
            shutil.copytree(worktree / sub, copy / sub)
        shutil.copy2(worktree / "pyproject.toml", copy / "pyproject.toml")
        target = copy / rel
        text = target.read_text()
        if text.count(old) != 1:
            print(f"{name}: REFUSED, the edit matches {text.count(old)} times")
            failures += 1
            continue
        target.write_text(text.replace(old, new))
        probe = "import forager_forecast, sys; print('imported', forager_forecast.__file__)"
        env = {"PYTHONPATH": str(copy / "src"), "PATH": "/usr/bin:/bin"}
        imp = subprocess.run([python, "-c", probe], capture_output=True, text=True, env=env)
        run = subprocess.run(
            [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf", *tests],
            cwd=copy, capture_output=True, text=True, env=env,
        )  # fmt: skip
        log = imp.stdout + imp.stderr + run.stdout + run.stderr
        (scratch / f"{name}.log").write_text(log)
        imported_copy = f"imported {copy / 'src'}" in log
        failed = sorted(set(re.findall(r"^FAILED [^:]+::(\w+)", run.stdout, flags=re.M)))
        tally = run.stdout.strip().splitlines()[-1] if run.stdout.strip() else "(no output)"
        if BAD_LOG.search(log) or not imported_copy:
            print(f"{name}: REFUSED as evidence (build log error or wrong import): {tally}")
            failures += 1
            continue
        missing = [t for t in expected if t not in failed]
        verdict = "bites" if not missing and run.returncode != 0 else "DOES NOT BITE"
        if missing or run.returncode == 0:
            failures += 1
        print(f"{name}: {verdict}; {tally}; failed: {', '.join(failed) or 'none'}")
        for line in run.stdout.splitlines():
            if line.startswith("E ") and len(line) < 220:
                print(f"    {line}")
                break
    after = tree_hashes(worktree)
    print("worktree unchanged:", before == after, f"({len(after)} files hashed)")
    return 1 if failures or before != after else 0


if __name__ == "__main__":
    raise SystemExit(main())
