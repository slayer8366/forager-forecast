"""The 1 MB guard, exercised end to end in a throwaway git repository.

Two callers share scripts/check-large-files.sh: the pre-commit hook (--staged) and CI (--all).
These tests drive both through real git commands rather than calling the script's internals,
so a change that breaks the hook wiring, the size source, or the exit code fails here.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "check-large-files.sh"
HOOK = REPO / ".githooks" / "pre-commit"
ONE_MB = 1_048_576


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    assert git(tmp_path, "init", "-q", "-b", "main").returncode == 0
    git(tmp_path, "config", "user.name", "guard-test")
    git(tmp_path, "config", "user.email", "guard-test@example.invalid")
    (tmp_path / "scripts").mkdir()
    (tmp_path / ".githooks").mkdir()
    shutil.copy(SCRIPT, tmp_path / "scripts" / "check-large-files.sh")
    shutil.copy(HOOK, tmp_path / ".githooks" / "pre-commit")
    git(tmp_path, "config", "core.hooksPath", ".githooks")
    return tmp_path


def stage(repo: Path, name: str, size: int) -> None:
    (repo / name).write_bytes(b"\0" * size)
    assert git(repo, "add", name).returncode == 0


def test_commit_with_a_file_over_1mb_is_refused_and_nothing_is_committed(repo: Path):
    stage(repo, "big.bin", ONE_MB + 1)
    result = git(repo, "commit", "-q", "-m", "too big")
    assert result.returncode != 0
    assert "LARGE FILE: big.bin is 1048577 bytes" in result.stdout + result.stderr
    assert git(repo, "rev-parse", "--verify", "HEAD").returncode != 0


def test_commit_passes_once_the_large_file_is_removed(repo: Path):
    stage(repo, "big.bin", ONE_MB + 1)
    assert git(repo, "commit", "-q", "-m", "too big").returncode != 0
    git(repo, "rm", "-q", "--cached", "big.bin")
    (repo / "big.bin").unlink()
    stage(repo, "small.txt", 3)
    result = git(repo, "commit", "-q", "-m", "small")
    assert result.returncode == 0, result.stderr
    assert git(repo, "rev-parse", "--verify", "HEAD").returncode == 0


def test_exactly_1mb_passes(repo: Path):
    stage(repo, "edge.bin", ONE_MB)
    result = git(repo, "commit", "-q", "-m", "edge")
    assert result.returncode == 0, result.stderr


def test_all_mode_catches_a_file_that_bypassed_the_hook(repo: Path):
    stage(repo, "big.bin", ONE_MB + 1)
    assert git(repo, "commit", "-q", "--no-verify", "-m", "bypassed").returncode == 0
    result = subprocess.run(
        ["scripts/check-large-files.sh", "--all"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "LARGE FILE: big.bin is 1048577 bytes" in result.stdout


def test_all_mode_passes_on_a_clean_tree(repo: Path):
    stage(repo, "small.txt", 3)
    assert git(repo, "commit", "-q", "-m", "small").returncode == 0
    result = subprocess.run(
        ["scripts/check-large-files.sh", "--all"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "1 file(s) checked" in result.stdout


# Forager RECORD -803, the owner: "Store it compressed (Recommended)". T6b's evidence copy of its
# run manifest is committed gzipped; the 1 MB limit is unchanged.


def test_the_t6b_evidence_manifest_is_committed_compressed_under_the_unchanged_limit(repo: Path):
    import gzip
    import json
    import random

    from forager_forecast.t6b_run import copy_manifest_evidence

    rng = random.Random(20261010)
    manifest = repo / "manifest.jsonl"
    with open(manifest, "w") as f:  # unit lines like the real run's, over 1 MB uncompressed
        for k in range(7000):
            sha = f"{rng.getrandbits(256):064x}"
            line = {"kind": "unit", "unit": f"balsamFir:256_{k}_{k % 40}", "status": "ok",
                    "seconds": round(rng.uniform(20, 60), 1),
                    "files": {f"scanfi_balsamFir_256_{k}.npz": sha}}  # fmt: skip
            f.write(json.dumps(line, sort_keys=True) + "\n")
    raw = manifest.read_bytes()
    assert len(raw) > ONE_MB
    evidence = repo / "evidence"
    evidence.mkdir()
    (evidence / "manifest.jsonl").write_bytes(raw[: ONE_MB // 2])  # an older uncompressed copy
    git(repo, "add", "evidence")
    assert git(repo, "commit", "-q", "-m", "older evidence").returncode == 0
    (evidence / "manifest.jsonl").write_bytes(raw)
    git(repo, "add", "evidence")
    # Positive control: the uncompressed copy is refused by the hook as it stands.
    refused = git(repo, "commit", "-q", "-m", "uncompressed")
    assert (
        refused.returncode != 0
        and "LARGE FILE: evidence/manifest.jsonl" in refused.stdout + refused.stderr
    )

    written = copy_manifest_evidence(manifest, evidence)
    assert written == evidence / "manifest.jsonl.gz"
    assert not (evidence / "manifest.jsonl").exists()
    git(repo, "add", "evidence")
    result = git(repo, "commit", "-q", "-m", "compressed")
    assert result.returncode == 0, result.stdout + result.stderr
    tree = git(repo, "ls-tree", "-r", "--name-only", "HEAD").stdout.split()
    assert "evidence/manifest.jsonl.gz" in tree and "evidence/manifest.jsonl" not in tree
    blob = subprocess.run(["git", "show", "HEAD:evidence/manifest.jsonl.gz"], cwd=repo,
                          capture_output=True, check=True).stdout  # fmt: skip
    assert len(blob) <= ONE_MB and gzip.decompress(blob) == raw
    # The same manifest compresses to the same bytes, so an unchanged manifest stages nothing.
    copy_manifest_evidence(manifest, evidence)
    assert (evidence / "manifest.jsonl.gz").read_bytes() == blob
