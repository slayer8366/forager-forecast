"""Revert checks on the review's own code, under CLAUDE.md's runner rules: the file is copied
before the edit and restored from that copy (never from git); the compile/collection log is read
before any result, and a run with a compile error is refused; each revert's failures must be the
test its own edit can break, with that test's message; after every revert the forward text is
confirmed present. Writes revert_check.txt beside it.

Two reverts:
  r1  within_cluster_difference: the block draw counts no longer multiply the row weights
      (``stat(w * t)`` -> ``stat(w)``), i.e. condition 2's interval would no longer be D145's.
  r2  Ranked.auc (every pooled AUC and difference): ties counted as concordant (``0.5 * wn`` ->
      ``wn``); the two tests that compare pooled AUCs with the pair count must both fail.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "review_common.py"
TEST = HERE / "test_review_common.py"
PY = sys.executable
REVERTS = {
    "r1": ("    diffs = np.array([stat(w * t) for t in _draws(resample_by, resamples, seed)])",
           "    diffs = np.array([stat(w) for t in _draws(resample_by, resamples, seed)])",
           ["test_within_cluster_block_resampled_interval_matches_brute_force"],
           "rows must be weighted by their block's draw count"),
    "r2": ("        return float((wp * (below + 0.5 * wn)).sum() / (wp.sum() * wn.sum()))",
           "        return float((wp * (below + wn)).sum() / (wp.sum() * wn.sum()))",
           ["test_weighted_auc_matches_brute_force_with_ties",
            "test_auc_difference_interval_matches_brute_force"],
           "ties must count half"),
}


def run_tests(xml: Path) -> tuple[int, str]:
    p = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(TEST),
                        f"--junitxml={xml}"], capture_output=True, text=True, cwd=HERE)
    return p.returncode, p.stdout + p.stderr


def read_xml(xml: Path) -> dict:
    root = ET.parse(xml).getroot()
    out = {}
    for case in root.iter("testcase"):
        f = case.find("failure")
        e = case.find("error")
        out[case.get("name")] = ("error: " + (e.get("message") or "")) if e is not None else (
            "fail: " + (f.get("message") or "")) if f is not None else "pass"
    return out


def main() -> None:
    lines = []
    log = lines.append
    saved = HERE / "review_common.py.saved-copy"
    shutil.copyfile(TARGET, saved)
    forward = TARGET.read_text()
    xml0 = HERE / ".forward.xml"
    rc0, out0 = run_tests(xml0)
    res0 = read_xml(xml0)
    log(f"forward run: exit {rc0}; {res0}")
    if any(v != "pass" for v in res0.values()):
        raise SystemExit("forward tests do not all pass; nothing to revert against")
    for name, (old, new, expect_test, expect_msg) in REVERTS.items():
        if old not in forward:
            raise SystemExit(f"{name}: the forward line is not in the file")
        TARGET.write_text(forward.replace(old, new, 1))
        try:
            c = subprocess.run([PY, "-c", f"import ast,sys; ast.parse(open({str(TARGET)!r}).read())"],
                               capture_output=True, text=True)
            if c.returncode != 0:
                log(f"{name}: COMPILE ERROR, results refused: {c.stderr.strip()}")
                continue
            xml = HERE / f".{name}.xml"
            if xml.exists():
                xml.unlink()
            rc_, out = run_tests(xml)
            if "error" in out.lower().split("passed")[0] and "collected 0" in out:
                log(f"{name}: collection error, results refused: {out[-500:]}")
                continue
            res = read_xml(xml)
            failed = {k: v for k, v in res.items() if v != "pass"}
            # every failure must be a test this edit can break (the listed ones), and the first
            # listed test must fail with the edit's own message
            specific = (sorted(failed) == sorted(expect_test)) and (expect_msg in failed.get(expect_test[0], ""))
            log(f"{name}: exit {rc_}; failed {sorted(failed)}; expected {sorted(expect_test)} with "
                f"'{expect_msg}': {'CONFIRMED' if specific else 'NOT CONFIRMED'}")
            for k, v in failed.items():
                log(f"    {k}: {v[:300]}")
            xml.unlink()
        finally:
            shutil.copyfile(saved, TARGET)
            assert TARGET.read_text() == forward and old in TARGET.read_text(), "forward text lost"
            log(f"{name}: restored from the saved copy; forward line present: True")
    xml0.unlink()
    saved.unlink()
    (HERE / "revert_check.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
