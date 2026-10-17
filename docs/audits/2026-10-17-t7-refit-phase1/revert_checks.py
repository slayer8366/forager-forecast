"""Revert checks for the T7 re-fit's Phase 1 tests (dispatch 2026-10-17-T7R).

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

TEST = "tests/test_t7_refit.py"
MODEL = "src/forager_forecast/t7/model.py"
METRICS = "src/forager_forecast/t7/metrics.py"
SPEC = "src/forager_forecast/t7/specimens.py"
FIT = "scripts/t7_fit.py"

# (id, file, forward text, reverted text, what the revert undoes)
REVERTS = [
    (
        "r1",
        MODEL,
        "    held = [i for i, f in enumerate(features) if f in HELD]",
        "    held = [i for i, f in enumerate(features) if f == EFFORT]",
        "access back among the habitat inputs' interaction group",
    ),
    (
        "r2",
        MODEL,
        "        out[name] = [*features[: k + 1], ACCESS, *features[k + 1 :]]",
        '        out[name] = list(features) if name.startswith("A") else '
        "[*features[: k + 1], ACCESS, *features[k + 1 :]]",
        "model A without the access band",
    ),
    (
        "r3",
        MODEL,
        "    return [f for f in features if f not in HELD]",
        "    return [f for f in features if f != EFFORT]",
        "access back among the area of applicability's predictors",
    ),
    (
        "r4",
        METRICS,
        "            wi = w if times is None else w * times[u]",
        "            wi = w if times is None else "
        "w * np.random.default_rng(len(gains)).permutation(times)[u]",
        "each group's resample its own draw (a permutation per group), not one for both",
    ),
    (
        "r5",
        SPEC,
        "    if licence_class(dataset_licence) is None:\n        return DATASET_LICENCE\n",
        "",
        "the dataset licence filter removed",
    ),
    (
        "r6",
        SPEC,
        "MAX_UNCERTAINTY_M = 1000.0",
        "MAX_UNCERTAINTY_M = 5000.0",
        "the uncertainty limit at 5 km",
    ),
    (
        "r7",
        FIT,
        '    if condition_4_status == CONDITION_4_PENDING and verdict == "pass":',
        "    if False:",
        'a pending condition 4 no longer keeps the verdict from "pass"',
    ),
    (
        "r8",
        FIT,
        "            raise SystemExit(f\"{path}: inside the judged run's folder {judged}; "
        'never written")',
        "            pass",
        "the judged folders no longer refused",
    ),
    (
        "r9",
        FIT,
        "            md.ACCESS: np.full(len(f), held_access), md.CONIFER_COVER: con,",
        "            md.ACCESS: np.full(len(f), held_access) + f[:, 0], md.CONIFER_COVER: con,",
        "access on the map no longer one held value",
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
