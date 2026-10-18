# ruff: noqa: E501
"""Revert checks for the T7 re-fit's condition 4 tests (Forager RECORD -1187) (dispatch 2026-10-17-T7R).

Each revert is ONE edit, made in its own scratch worktree on its own local branch cut from the
commit under test. The runner, per CLAUDE.md:
- saves a copy of the file before editing and restores from that copy, never from git;
- reads the compile and import log before any result, and refuses to cite results if it shows an
  error, or if the code imported is not the scratch tree's;
- reads the JUnit XML, and lists each failing test with its message;
- after restoring, confirms the file equals the saved copy and the forward change is present.

Usage: python revert_checks.py <repo> <commit> <scratch root> <out file>
"""

import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TEST = "tests/test_t7_condition4.py"
MODEL = "src/forager_forecast/t7/model.py"
METRICS = "src/forager_forecast/t7/metrics.py"
SPEC = "src/forager_forecast/t7/specimens.py"
FIT = "scripts/t7_fit.py"

C4 = "src/forager_forecast/t7/condition4.py"

# (id, file, forward text, reverted text, what the revert undoes)
REVERTS = [
    (
        "c1",
        C4,
        "    take = (cx - x) ** 2 + (cy - y) ** 2 <= radius_m**2",
        "    take = np.zeros_like(rr, dtype=bool)",
        "the circle ignored: own cell only",
    ),
    (
        "c2",
        C4,
        "    take |= (rr == r0) & (cc == c0)",
        "    take = take",
        "the point's own cell no longer always included",
    ),
    (
        "c3",
        C4,
        "    values = values[np.isfinite(values)]",
        "    values = values",
        "masked cells no longer left out of the mean",
    ),
    (
        "c4",
        C4,
        "        candidates = pool_cells[pool_bands == b]",
        "        candidates = pool_cells",
        "background no longer matched to the road band",
    ),
    (
        "c5",
        C4,
        "        out_radii.append(np.repeat(radii[which], per_specimen))",
        "        out_radii.append(np.repeat(np.full(len(which), radii.mean()), per_specimen))",
        "background no longer carrying its specimen's radius",
    ),
    (
        "c6",
        METRICS,
        "    return clustered_auc_difference(s, np.zeros(len(s)), outcomes, np.ones(len(s)), clusters,",
        "    return clustered_auc_difference(s, np.zeros(len(s)), outcomes, np.ones(len(s)), np.arange(len(s)),",
        "condition 4's interval resampling rows, not blocks",
    ),
    (
        "c7",
        C4,
        '    sets = (("whole_box", ok), ("interior_no_verdict", ok & np.asarray(spec_interior, bool)))',
        '    sets = (("whole_box", ok), ("interior_no_verdict", ok))',
        "the interior set no longer the interior specimens",
    ),
    (
        "c8",
        FIT,
        "                host_specific_contrast=condition_3, independent_data=condition_4)  # fmt: skip",
        "                host_specific_contrast=condition_3, independent_data=None)  # fmt: skip",
        "P10b no longer taking condition 4",
    ),
    (
        "c9",
        C4,
        "    ok = (cell_id[pos] == spec_cell) & scorable[pos]",
        "    ok = cell_id[pos] == spec_cell",
        "specimens on cells with no map value no longer dropped",
    ),
]


def run(cmd, cwd, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


def main(repo: Path, commit: str, scratch_root: Path, out: Path) -> None:
    py = repo / ".venv/bin/python"
    lines = [f"revert checks at {commit}, test file {TEST}", ""]
    for rid, rel, forward, reverted, what in REVERTS:
        branch = f"revert-refit-{rid}"
        tree = scratch_root / branch
        r = run(["git", "worktree", "add", "-q", "-b", branch, str(tree), commit], repo)
        if r.returncode:
            raise SystemExit(r.stderr)
        try:
            path = tree / rel
            saved = path.read_text(encoding="utf-8")
            assert saved.count(forward) == 1, f"{rid}: forward text found {saved.count(forward)}x"
            path.write_text(saved.replace(forward, reverted), encoding="utf-8")
            env = {"PYTHONPATH": str(tree / "src"), "PATH": "/usr/bin:/bin"}
            # compile and import log, read before any result
            comp = run([str(py), "-m", "py_compile", str(tree / rel)], tree, env)
            imp = run([str(py), "-c", "import forager_forecast.t7.model as m, "
                       "forager_forecast.t7.specimens, forager_forecast.t7.metrics; "
                       "print(m.__file__)"], tree, env)  # fmt: skip
            imported = imp.stdout.strip()
            ok = (comp.returncode == 0 and imp.returncode == 0
                  and imported.startswith(str(tree)))  # fmt: skip
            lines.append(f"[{rid}] {what} ({rel})")
            lines.append(f"  compile rc {comp.returncode} {comp.stderr.strip()[:300]}")
            lines.append(f"  import rc {imp.returncode}, model imported from {imported}")
            if not ok:
                lines.append("  REFUSED: the reverted build did not compile or import from the "
                             "scratch tree; no result is cited")  # fmt: skip
            else:
                xml = tree / "junit.xml"
                run([str(py), "-m", "pytest", "-q", "-p", "no:cacheprovider", TEST,
                     f"--junitxml={xml}", f"--basetemp={tree}/tmp"], tree, env)  # fmt: skip
                suite = ET.parse(xml).getroot()
                suite = suite if suite.tag == "testsuite" else suite[0]
                lines.append(f"  tests {suite.get('tests')}, failures {suite.get('failures')}, "
                             f"errors {suite.get('errors')}")  # fmt: skip
                for case in suite.iter("testcase"):
                    for bad in list(case.findall("failure")) + list(case.findall("error")):
                        msg = (bad.get("message") or "").replace("\n", " ")[:220]
                        lines.append(f"    FAILED {case.get('name')}: {msg}")
            # restore from the saved copy, never from git; confirm the forward change
            path.write_text(saved, encoding="utf-8")
            back = path.read_text(encoding="utf-8")
            lines.append(f"  restored from saved copy: equal {back == saved}, "
                         f"forward text present {back.count(forward) == 1}")  # fmt: skip
            lines.append("")
        finally:
            run(["git", "worktree", "remove", "--force", str(tree)], repo)
            run(["git", "branch", "-D", branch], repo)
            shutil.rmtree(tree, ignore_errors=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]))
