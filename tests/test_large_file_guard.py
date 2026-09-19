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
