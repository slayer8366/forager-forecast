"""Revert checks for the T6b host-genera build, under Forager CLAUDE.md's revert-runner rules.

For each check: save a copy of the file, make a one-line edit that undoes one behaviour, run the
named tests with a fresh JUnit XML, refuse to read results if the run shows a collection, import
or syntax error (or the XML is missing), compare the failing tests with the predicted set,
restore the file from the saved copy (never from git), and confirm the restored file is byte for
byte the saved copy and the committed version. Writes revert_checks.out.json beside this file.

Run from the repository root:
    systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0 \
        nice -n 10 .venv/bin/python docs/audits/2026-10-15-t6b-host-genera-build/revert_checks.py
"""

import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
WORK = REPO / ".pytest-tmp" / "revert"
T = "tests/test_t6b_host_genera.py::"
HG = "tests/test_t6b_host_genera.py"

CHECKS = [
    {
        "name": "r1-genus-list",
        "file": "src/forager_forecast/t6b_hosts.py",
        "old": "T6B_BANDS = (*T5_BANDS, *TIER_A_GENERA, *TIER_B_GENERA, ECM_HOSTS)",
        "new": "T6B_BANDS = T5_BANDS",
        "tests": [HG],
        "expect": {
            "test_the_plot_table_carries_every_new_genus_and_the_total_without_moving_t5s_columns",
            "test_a_tree_tile_has_the_new_bands_canada_flags_them_not_available",
            "test_f1_a_tile_built_with_the_old_genus_list_is_rebuilt_not_counted_done",
            "test_an_old_layout_us_half_is_rebuilt_as_a_new_file_and_the_old_one_kept",
            "test_f2_the_plot_table_is_rebuilt_when_the_genus_list_changes",
        },
    },
    {
        "name": "r2-ecm-total",
        "file": "src/forager_forecast/crown_cover.py",
        "old": "        crown[name] = sum(crown[g] for g in members)",
        "new": "        crown[name] = 0.0",
        "tests": [HG],
        "expect": {
            "test_the_plot_table_carries_every_new_genus_and_the_total_without_moving_t5s_columns",
            "test_a_tree_tile_has_the_new_bands_canada_flags_them_not_available",
        },
    },
    {
        "name": "r3-f1-done-needs-layout",
        "file": "src/forager_forecast/t6b_run.py",
        "old": 'if band_layout is not None and entry.get("band_layout") != band_layout:',
        "new": "if False:",
        "tests": [HG],
        "expect": {
            "test_f1_a_tile_built_with_the_old_genus_list_is_rebuilt_not_counted_done",
            "test_the_trees_only_supersede_keeps_the_old_tile_and_leaves_soil_scanfi_and_manifest",
            "test_an_old_layout_us_half_is_rebuilt_as_a_new_file_and_the_old_one_kept",
            "test_a_stale_whole_tile_is_moved_aside_without_its_current_us_half",
        },
    },
    {
        "name": "r4-f2-plots-rebuilt-on-layout",
        "file": "scripts/t6b_run.py",
        "old": 'and old.get("band_layout") == BAND_LAYOUT',
        "new": "and True",
        "tests": [HG],
        "expect": {"test_f2_the_plot_table_is_rebuilt_when_the_genus_list_changes"},
    },
    {
        "name": "r5-plot-table-refusal",
        "file": "src/forager_forecast/t6b_layers.py",
        "old": 'if layout != BAND_LAYOUT or tuple(z["bands"].tolist()) != BANDS:',
        "new": "if False:",
        "tests": [HG],
        "expect": {"test_a_plot_table_of_another_band_layout_is_refused"},
    },
    {
        "name": "r6-supersede-moves",
        "file": "scripts/t6b_run.py",
        "old": "    if layout == BAND_LAYOUT:\n        return {}",
        "new": "    if True:\n        return {}",
        "tests": [HG],
        "expect": {
            "test_the_trees_only_supersede_keeps_the_old_tile_and_leaves_soil_scanfi_and_manifest",
            "test_an_old_layout_us_half_is_rebuilt_as_a_new_file_and_the_old_one_kept",
            "test_a_stale_whole_tile_is_moved_aside_without_its_current_us_half",
        },
    },
    {
        "name": "r7-supersede-per-group",
        "file": "scripts/t6b_run.py",
        "old": "before_tree_unit(lambda k: [_whole_paths(k), _us_half_paths(k)], dest)",
        "new": "before_tree_unit(lambda k: [[*_whole_paths(k), *_us_half_paths(k)]], dest)",
        "tests": [HG],
        "expect": {"test_a_stale_whole_tile_is_moved_aside_without_its_current_us_half"},
    },
    {
        "name": "r8-free-space",
        "file": "scripts/t6b_run.py",
        "old": "require_free_space(T6B, tree_tile_bytes() + FREE_MARGIN)",
        "new": "require_free_space(T6B, 0)",
        "tests": [HG],
        "expect": {
            "test_a_tree_tile_is_not_started_without_free_space[trees]",
            "test_a_tree_tile_is_not_started_without_free_space[trees-us-half]",
        },
    },
    {
        "name": "r9-box",
        "file": "scripts/t6b_run.py",
        "old": "        units = [u for u in units if u in box_tiles]\n",
        "new": "        units = list(units)\n",
        "tests": [HG],
        "expect": {"test_the_box_option_runs_only_the_tiles_with_a_study_cell_in_the_box"},
    },
    {
        # A guard, not a fix: it passes before and after the build by design. Changing T5's list
        # must fail it; other tests may fail too (T6b's list starts from T5's), so only
        # membership of the guard among the failures is required here.
        "name": "r10-t5-guard",
        "file": "src/forager_forecast/crown_cover.py",
        "old": '"Pinus", "Quercus")\nBANDS',
        "new": '"Pinus", "Quercus", "Betula")\nBANDS',
        "tests": [HG, "tests/test_t5_layer.py"],
        "expect_includes": {"test_t5s_genus_list_and_its_cover_split_are_unchanged"},
    },
]

ERROR_MARKS = ("ERROR collecting", "ImportError", "SyntaxError", "ModuleNotFoundError",
               "IndentationError", "NameError")  # fmt: skip


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def committed_sha(rel: str) -> str:
    blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=REPO, capture_output=True,
                          check=True).stdout  # fmt: skip
    return hashlib.sha256(blob).hexdigest()


def run(check: dict) -> dict:
    path = REPO / check["file"]
    saved = WORK / f"{check['name']}.saved"
    WORK.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, saved)
    saved_sha = sha(saved)
    text = path.read_text()
    if text.count(check["old"]) != 1:
        return {"name": check["name"], "status": "anchor not found exactly once; not run"}
    xml = WORK / f"{check['name']}.xml"
    if xml.exists():
        xml.unlink()
    try:
        path.write_text(text.replace(check["old"], check["new"]))
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             f"--basetemp={WORK / check['name']}", f"--junitxml={xml}", *check["tests"]],
            cwd=REPO, capture_output=True, text=True,
        )  # fmt: skip
    finally:
        shutil.copy2(saved, path)  # restore from the saved copy, never from git
    out = proc.stdout + proc.stderr
    (WORK / f"{check['name']}.log").write_text(out)
    restored = sha(path) == saved_sha == committed_sha(check["file"])
    result = {"name": check["name"], "file": check["file"], "edit": [check["old"], check["new"]],
              "forward_change_restored": restored,
              "tail": out.strip().splitlines()[-1:]}  # fmt: skip
    marks = [m for m in ERROR_MARKS if m in out]
    if not xml.exists() or marks:
        result["status"] = f"REFUSED: build or collection error {marks}, results not read"
        return result
    root = ET.parse(xml).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if int(suite.get("errors", 0)):
        result["status"] = "REFUSED: errors in the run, results not read"
        return result
    failed = set()
    messages = {}
    for case in suite.iter("testcase"):
        bad = case.find("failure")
        if bad is not None:
            failed.add(case.get("name"))
            messages[case.get("name")] = (bad.get("message") or "")[:300]
    result["tests_run"] = int(suite.get("tests", 0))
    result["failed"] = sorted(failed)
    result["messages"] = messages
    if "expect" in check:
        ok = failed == check["expect"]
        result["predicted"] = sorted(check["expect"])
    else:
        ok = check["expect_includes"] <= failed
        result["predicted_among"] = sorted(check["expect_includes"])
    result["status"] = "bites as predicted" if ok and restored else "MISMATCH"
    return result


def main() -> None:
    if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "src", "scripts", "tests"],
                      cwd=REPO).returncode != 0:  # fmt: skip
        sys.exit("uncommitted changes in src, scripts or tests: commit the forward change first")
    results = [run(c) for c in CHECKS]
    (OUT / "revert_checks.out.json").write_text(json.dumps(results, indent=1) + "\n")
    for r in results:
        print(r["name"], r["status"], r.get("failed"))
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "src", "scripts", "tests"],
                           cwd=REPO).returncode == 0  # fmt: skip
    print("working tree equals HEAD after all checks:", clean)


if __name__ == "__main__":
    main()
