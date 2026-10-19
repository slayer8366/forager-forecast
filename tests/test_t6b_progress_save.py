"""T6b's section save (dispatch 2026-10-19-t6b-progress-save), through the runner's real entry
points, ``commit_progress`` and ``main`` in scripts/t6b_run.py, against a throwaway git repository
that has this repository's large-file hook and a bare remote.

Git gets a small summary of the manifest (its sha256, size, line count and unit counts); the full
manifest is gzipped to a folder outside every repository. A failed commit or push is logged and the
section exits non-zero, after everything outside git is written.
"""

import gzip
import hashlib
import importlib.util
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "t6b_run.py"
ONE_MB = 1_048_576
EVIDENCE_REL = Path("docs") / "audits" / "t6b-run"


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


@pytest.fixture
def save(tmp_path, monkeypatch):
    """The runner module pointed at a scratch repository, drive folder and outside folder."""
    repo = tmp_path / "repo"
    repo.mkdir()
    assert git(repo, "init", "-q", "-b", "t6b-test").returncode == 0
    git(repo, "config", "user.name", "save-test")
    git(repo, "config", "user.email", "save-test@example.invalid")
    (repo / "scripts").mkdir()
    (repo / ".githooks").mkdir()
    shutil.copy(ROOT / "scripts" / "check-large-files.sh", repo / "scripts")
    shutil.copy(ROOT / ".githooks" / "pre-commit", repo / ".githooks")
    git(repo, "config", "core.hooksPath", ".githooks")
    evidence = repo / EVIDENCE_REL
    evidence.mkdir(parents=True)
    (evidence / "manifest.jsonl.gz").write_bytes(gzip.compress(b'{"kind": "old"}\n', mtime=0))
    (evidence / "sections.jsonl").write_text("")
    git(repo, "add", ".")
    assert git(repo, "commit", "-q", "-m", "base").returncode == 0
    remote = tmp_path / "remote.git"
    assert git(tmp_path, "init", "-q", "--bare", str(remote)).returncode == 0
    git(repo, "remote", "add", "origin", str(remote))
    assert git(repo, "push", "-q", "origin", "t6b-test").returncode == 0

    spec = importlib.util.spec_from_file_location("t6b_run_script", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    t6b = tmp_path / "drive" / "t6b"
    t6b.mkdir(parents=True)
    (t6b / "run.log").write_text("")
    outside = tmp_path / "outside" / "t6b"
    for name, value in {"REPO": repo, "DRIVE": t6b.parent, "T6B": t6b,
                        "MANIFEST": t6b / "manifest.jsonl", "PAUSE": t6b / "PAUSE",
                        "EVIDENCE": evidence}.items():  # fmt: skip
        monkeypatch.setattr(mod, name, value)
    # raising=False: before the change the runner has no such constant, and the tests must still
    # reach the behaviour they check rather than fail on the missing name.
    monkeypatch.setattr(mod, "MANIFEST_COPY_DIR", outside, raising=False)
    mod.test_paths = {"repo": repo, "evidence": evidence, "t6b": t6b, "outside": outside,
                      "remote": remote}  # fmt: skip
    return mod


def _big_manifest(path: Path) -> bytes:
    """Unit lines like the real run's, enough of them that the gzip is over 1 MB."""
    rng = random.Random(20261019)
    with open(path, "w") as f:
        for k in range(26000):
            line = {"kind": "unit", "layer": "balsamFir", "unit": f"balsamFir:256_{k}_{k % 40}",
                    "status": "ok", "files": {f"b_{k}.npz": f"{rng.getrandbits(256):064x}"}}  # fmt: skip
            f.write(json.dumps(line, sort_keys=True) + "\n")
    raw = path.read_bytes()
    assert len(gzip.compress(raw, compresslevel=9, mtime=0)) > ONE_MB  # the case that failed
    return raw


def _head_files(repo: Path) -> list[str]:
    return git(repo, "ls-tree", "-r", "--name-only", "HEAD").stdout.split()


def test_a_manifest_whose_gzip_is_over_the_limit_commits_a_summary_and_not_the_gzip(save):
    p = save.test_paths
    raw = _big_manifest(save.MANIFEST)
    head_gz = git(p["repo"], "rev-parse", f"HEAD:{EVIDENCE_REL}/manifest.jsonl.gz").stdout

    ok = save.commit_progress([], p["evidence"])

    assert ok is True
    tree = _head_files(p["repo"])
    assert f"{EVIDENCE_REL}/manifest_summary.json" in tree
    # The committed gzip is frozen: the same blob as before the section.
    assert git(p["repo"], "rev-parse", f"HEAD:{EVIDENCE_REL}/manifest.jsonl.gz").stdout == head_gz
    summary = json.loads(git(p["repo"], "show", f"HEAD:{EVIDENCE_REL}/manifest_summary.json").stdout)
    assert summary["sha256"] == hashlib.sha256(raw).hexdigest()
    copy = p["outside"] / "manifest.jsonl.gz"
    assert gzip.decompress(copy.read_bytes()) == raw
    # Pushed: the remote branch is the local commit.
    assert (git(p["remote"], "rev-parse", "t6b-test").stdout
            == git(p["repo"], "rev-parse", "HEAD").stdout)  # fmt: skip


def test_the_summary_matches_the_manifest_it_came_from(save):
    p = save.test_paths
    lines = [
        {"kind": "stage", "stage": "mask"},
        {"kind": "unit", "layer": "trees", "unit": "256_1_1", "status": "ok"},
        {"kind": "unit", "layer": "trees", "unit": "256_1_2", "status": "deferred"},
        {"kind": "before_unit", "unit": "256_1_2"},
        {"kind": "unit", "layer": "trees", "unit": "256_1_2", "status": "ok", "redone": True},
        {"kind": "unit", "layer": "trees", "unit": "256_1_3", "status": "failed"},
        {"kind": "unit", "layer": "soil", "unit": "2048_0_0"},  # no status: ok, as done_units
        {"kind": "unit", "layer": "balsamFir", "unit": "balsamFir:256_1_1", "status": "ok"},
        {"kind": "section", "units_done_now": 4},
    ]
    save.MANIFEST.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in lines))
    raw = save.MANIFEST.read_bytes()

    ok = save.commit_progress([], p["evidence"])

    shown = git(p["repo"], "show", f"HEAD:{EVIDENCE_REL}/manifest_summary.json")
    assert shown.returncode == 0, "no summary committed: " + shown.stderr
    assert ok is True
    summary = json.loads(shown.stdout)
    assert summary["sha256"] == hashlib.sha256(raw).hexdigest()
    assert summary["bytes"] == len(raw)
    assert summary["lines"] == 9
    assert summary["lines_by_kind"] == {"before_unit": 1, "section": 1, "stage": 1, "unit": 6}
    # Latest line per unit: 256_1_2 counts once, as ok, not as deferred.
    assert summary["units"] == 5
    assert summary["units_by_layer_and_status"] == {
        "balsamFir": {"ok": 1},
        "soil": {"ok": 1},
        "trees": {"failed": 1, "ok": 2},
    }
    # The copy outside git is of the very manifest the summary describes.
    copy = Path(summary["copy_outside_git"])
    assert copy == p["outside"] / "manifest.jsonl.gz"
    assert hashlib.sha256(gzip.decompress(copy.read_bytes())).hexdigest() == summary["sha256"]


def test_a_leftover_staged_oversize_gzip_does_not_block_the_next_section(save):
    p = save.test_paths
    head_gz = git(p["repo"], "rev-parse", f"HEAD:{EVIDENCE_REL}/manifest.jsonl.gz").stdout
    # What the 2026-10-18 section left behind: an over-size gzip, staged, never committed.
    (p["evidence"] / "manifest.jsonl.gz").write_bytes(random.Random(7).randbytes(ONE_MB + 56725))
    assert git(p["repo"], "add", str(p["evidence"] / "manifest.jsonl.gz")).returncode == 0
    save.MANIFEST.write_text(json.dumps({"kind": "unit", "layer": "soil", "unit": "a"}) + "\n")

    ok = save.commit_progress([], p["evidence"])

    assert ok is True
    assert git(p["repo"], "rev-parse", f"HEAD:{EVIDENCE_REL}/manifest.jsonl.gz").stdout == head_gz
    assert f"{EVIDENCE_REL}/manifest_summary.json" in _head_files(p["repo"])


def _run_paused_section(save, monkeypatch):
    """main() with the pause file present: no stage starts, and the section ends and saves."""
    save.PAUSE.touch()
    monkeypatch.setattr(sys, "argv", ["t6b_run.py", "--until", "23:59", "--stages",
                                      "scanfi-layers", "--workers", "1"])  # fmt: skip
    with pytest.raises(SystemExit) as exited:
        save.main()
    return exited.value.code


def test_a_refused_commit_is_logged_and_the_section_exits_non_zero_after_the_copy(save, monkeypatch):
    p = save.test_paths
    save.MANIFEST.write_text(json.dumps({"kind": "unit", "layer": "soil", "unit": "a"}) + "\n")
    raw = save.MANIFEST.read_bytes()
    hook = p["repo"] / ".githooks" / "pre-commit"
    hook.write_text("#!/usr/bin/env bash\necho 'REFUSED BY TEST HOOK'\nexit 1\n")
    head = git(p["repo"], "rev-parse", "HEAD").stdout

    code = _run_paused_section(save, monkeypatch)

    assert code not in (0, None)
    assert git(p["repo"], "rev-parse", "HEAD").stdout == head  # nothing committed
    log = (save.T6B / "run.log").read_text()
    assert "commit refused" in log and "REFUSED BY TEST HOOK" in log
    copy = p["outside"] / "manifest.jsonl.gz"
    assert gzip.decompress(copy.read_bytes()) == raw  # written before git was tried
    summary = json.loads((p["evidence"] / "manifest_summary.json").read_text())
    assert summary["sha256"] == hashlib.sha256(raw).hexdigest()


def test_a_failed_push_is_logged_and_the_section_exits_non_zero(save, monkeypatch):
    p = save.test_paths
    save.MANIFEST.write_text(json.dumps({"kind": "unit", "layer": "soil", "unit": "a"}) + "\n")
    git(p["repo"], "remote", "set-url", "origin", str(p["remote"].parent / "no-such-remote.git"))
    head = git(p["repo"], "rev-parse", "HEAD").stdout

    code = _run_paused_section(save, monkeypatch)

    assert code not in (0, None)
    assert git(p["repo"], "rev-parse", "HEAD").stdout != head  # the commit itself landed
    assert "push failed" in (save.T6B / "run.log").read_text()
