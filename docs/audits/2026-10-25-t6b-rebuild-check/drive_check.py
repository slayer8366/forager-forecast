"""T6b rebuild check, item 2 (dispatch 2026-10-25-t6b-rebuild-check): what the run relies on,
tried on the new flash drive with small scratch files, through the runner's own functions.

Committed exactly as it ran. Usage (repository root, under the dispatch's cap):

    systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0 nice -n 10 \
        .venv/bin/python docs/audits/2026-10-25-t6b-rebuild-check/drive_check.py \
        --scratch /mnt/work/scratch/t6b-rebuild/check

Writes only under ``DRIVE/t6b-check`` and ``--scratch``; deletes neither (the caller does, and
lists what it deleted). Prints one JSON object per check and a final tally. Exits 1 on any FAIL.
"""

import argparse
import functools
import gzip
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import rasterio

from forager_forecast.drive import DRIVE
from forager_forecast.grid import GridWindow
from forager_forecast.t6b_layers import _write_tif, require_free_space
from forager_forecast.t6b_run import (
    append_line,
    done_units,
    manifest_summary,
    read_lines,
    run_section,
    sha256_file,
)

REPO = Path(__file__).resolve().parents[3]
ROOT = DRIVE / "t6b-check"
RESULTS: list[dict] = []


def check(name: str, ok: bool, **detail) -> None:
    row = {"check": name, "result": "PASS" if ok else "FAIL", **detail}
    RESULTS.append(row)
    print(json.dumps(row, default=str), flush=True)


def toy_unit(out_dir: str, unit: str, pause_after: str | None = None) -> dict:
    """A unit that writes one small GeoTIFF the way every T6b tile is written (``_write_tif``:
    ``.partial`` first, then renamed). With ``pause_after``, it creates that pause file once it
    has written its tile, as an operator's ``touch`` would mid-section."""
    window = GridWindow(0, 0, 4 * 250, 4 * 250)
    name = f"toy_{unit}.tif"
    data = np.full((4, 4), sum(map(ord, unit)) % 250, dtype="uint8")
    sha = _write_tif(Path(out_dir) / name, window, {"v": data}, "uint8", {"band_layout": "check"})
    if pause_after:
        Path(pause_after).touch()
    return {"files": {name: sha}}


def mount_facts() -> None:
    mounts = [line.split() for line in Path("/proc/self/mounts").read_text().splitlines()]
    here = [m for m in mounts if m[1] == str(DRIVE)]
    st = DRIVE.stat()
    check("mount: DRIVE is a mount point", os.path.ismount(DRIVE), drive=str(DRIVE))
    check("mount: the runner's own test, DRIVE.is_dir()", DRIVE.is_dir())
    check("mount: ext4, read-write", bool(here) and here[0][2] == "ext4"
          and "rw" in here[0][3].split(","), mount=here[0] if here else None)  # fmt: skip
    check("mount: owned by this user", st.st_uid == os.getuid(), uid=st.st_uid,
          mode=oct(stat.S_IMODE(st.st_mode)))  # fmt: skip
    free = require_free_space(DRIVE, 1)
    try:
        require_free_space(DRIVE, free * 2)
        refused = False
    except OSError:
        refused = True
    check("free space: require_free_space reads the drive and refuses more than is free",
          refused and free > 50e9, free_bytes=free)  # fmt: skip


def section_checks() -> None:
    tiles, manifest, pause = ROOT / "tiles", ROOT / "manifest.jsonl", ROOT / "PAUSE"
    until = datetime.now() + timedelta(hours=1)
    work = functools.partial(toy_unit, str(tiles))
    s1 = run_section(["a", "b", "c"], work, manifest, tiles, until=until, pause_file=pause,
                     workers=2, layer="check")  # fmt: skip
    lines = read_lines(manifest)
    units = [e for e in lines if e.get("kind") == "unit"]
    hashed = all(sha256_file(tiles / n) == s for e in units for n, s in e["files"].items())
    check("section, two workers: three tiles written, renamed, one fsynced manifest line each",
          s1["units_ok"] == 3 and len(units) == 3 and hashed
          and not list(tiles.glob("*.partial")), summary=s1)  # fmt: skip
    with rasterio.open(tiles / "toy_a.tif") as ds:
        tag = ds.tags().get("band_layout")
    check("tile: reads back from the drive with its band_layout tag", tag == "check", tag=tag)

    s2 = run_section(["a", "b", "c"], work, manifest, tiles, until=until, pause_file=pause,
                     workers=2, layer="check")  # fmt: skip
    check("resume: a second section finds all three done by their hashes, runs none",
          s2["units_done_before"] == 3 and s2["units_done_now"] == 0, summary=s2)  # fmt: skip

    with open(tiles / "toy_c.tif", "r+b") as f:  # a tile that no longer hashes
        f.seek(-1, 2)
        last = f.read(1)
        f.seek(-1, 2)
        f.write(bytes([last[0] ^ 0xFF]))
    (tiles / "toy_z.tif.partial").write_bytes(b"half a tile")  # an interrupted write
    done = done_units(manifest, tiles)
    s3 = run_section(["a", "b", "c", "d"], work, manifest, tiles, until=until, pause_file=pause,
                     workers=1, layer="check")  # fmt: skip
    last = {e["unit"]: e for e in read_lines(manifest) if e.get("kind") == "unit"}
    check("rehash: a changed tile is not done and is redone; an interrupted .partial is not a tile",
          done == {"a", "b"} and s3["units_done_now"] == 2 and last["c"]["redone"] is True
          and last["d"]["redone"] is False and "z" not in done
          and not (tiles / "toy_z.tif").exists(), done_before=sorted(done), summary=s3)  # fmt: skip
    (tiles / "toy_z.tif.partial").unlink()

    pause.touch()
    s4 = run_section(["e"], work, manifest, tiles, until=until, pause_file=pause, workers=1,
                     layer="check")  # fmt: skip
    check("PAUSE present at the start: no tile starts",
          s4["units_done_now"] == 0 and s4["stopped"] == f"pause file {pause}"
          and not (tiles / "toy_e.tif").exists(), summary=s4)  # fmt: skip
    pause.unlink()

    paused = functools.partial(toy_unit, str(tiles), pause_after=str(pause))
    s5 = run_section(["f", "g", "h"], paused, manifest, tiles, until=until, pause_file=pause,
                     workers=1, layer="check")  # fmt: skip
    check("PAUSE touched mid-section: the tile in hand finishes, no new one starts",
          s5["units_done_now"] == 1 and s5["stopped"] == f"pause file {pause}"
          and (tiles / "toy_f.tif").exists() and not (tiles / "toy_g.tif").exists(),
          summary=s5)  # fmt: skip
    pause.unlink()

    n = len(read_lines(manifest))
    append_line(manifest, {"kind": "check", "note": "plain append"})
    check("manifest: append_line adds exactly one line", len(read_lines(manifest)) == n + 1,
          lines=n + 1, bytes=manifest.stat().st_size)  # fmt: skip


def runner_module():
    spec = importlib.util.spec_from_file_location("t6b_run_script", REPO / "scripts" / "t6b_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def supersede_check(mod) -> None:
    mod.T6B = ROOT
    stale = ROOT / "tiles" / "trees" / "trees_256_0_0.tif"
    window = GridWindow(0, 0, 1000, 1000)
    sha = _write_tif(stale, window, {"v": np.zeros((4, 4), "uint8")}, "uint8",
                     {"band_layout": "an older layout"})  # fmt: skip
    dest = ROOT / "superseded" / "check-trees"
    info = mod.move_aside_stale([stale], dest)
    moved = dest / "tiles" / "trees" / stale.name
    check("supersede: a tile of an older layout is moved aside on the drive, kept, same bytes",
          not stale.exists() and moved.exists() and sha256_file(moved) == sha
          and info.get("superseded", {}).get(stale.name) == sha, info=info)  # fmt: skip


def symlink_check(scratch: Path) -> None:
    target = ROOT / "t5" / "treemap2023"
    target.mkdir(parents=True)
    (target / "probe.txt").write_text("t5 probe\n")
    inside = ROOT / "t5-link"
    inside.symlink_to(target)
    outside = scratch / "data_t5"  # as T5's gitignored data/t5 pointed at the old drive
    outside.symlink_to(ROOT / "t5")
    check("symlinks: on the drive, and from /mnt/work into the drive, both read through",
          (inside / "probe.txt").read_text() == "t5 probe\n"
          and (outside / "treemap2023" / "probe.txt").read_text() == "t5 probe\n"
          and inside.is_symlink() and outside.is_symlink(),
          inside=f"{inside} -> {os.readlink(inside)}",
          outside=f"{outside} -> {os.readlink(outside)}")  # fmt: skip


def read_only_check() -> None:
    tiles, manifest = ROOT / "tiles", ROOT / "manifest.jsonl"
    paths = [*sorted(tiles.rglob("*")), tiles, manifest]
    for p in paths:
        p.chmod(stat.S_IMODE(p.stat().st_mode) & ~0o222)
    errors = {}
    for label, action in (
        ("new file", lambda: (tiles / "new.tif").write_bytes(b"x")),
        ("overwrite tile", lambda: (tiles / "toy_a.tif").write_bytes(b"x")),
        ("append manifest", lambda: append_line(manifest, {"kind": "check"})),
        ("delete tile", lambda: (tiles / "toy_b.tif").unlink()),
    ):
        try:
            action()
            errors[label] = None
        except PermissionError as exc:
            errors[label] = f"PermissionError: {exc.strerror}"
    readable = done_units(manifest, tiles) >= {"a", "b", "c", "d", "f"}
    with rasterio.open(tiles / "toy_a.tif") as ds:
        opened = ds.read(1).shape == (4, 4)
    check("read-only: chmod a-w refuses new, overwrite, append and delete; reads and rehash work",
          all(errors.values()) and readable and opened, refused=errors)  # fmt: skip
    for p in paths:
        p.chmod(stat.S_IMODE(p.stat().st_mode) | 0o200)


def progress_save_check(mod, scratch: Path) -> None:
    """``commit_progress`` from the runner, against a scratch repository with this repository's
    large-file hook and a bare remote, reading the manifest and run.log from the drive. The
    committed run.log is copied before the save logs its own commit, so the drive's log is that
    copy plus the lines written after it (run 2 of this script failed on asking for equality)."""
    repo, remote, outside = scratch / "repo", scratch / "remote.git", scratch / "outside" / "t6b"

    def git(cwd, *args):
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)

    repo.mkdir()
    git(repo, "init", "-q", "-b", "t6b-check")
    git(repo, "config", "user.name", "drive-check")
    git(repo, "config", "user.email", "drive-check@example.invalid")
    for rel in ("scripts/check-large-files.sh", ".githooks/pre-commit"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, repo / rel)
    git(repo, "config", "core.hooksPath", ".githooks")
    (repo / "README").write_text("scratch\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "base")
    git(scratch, "init", "-q", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "origin", "t6b-check")
    mod.REPO, mod.T6B, mod.DRIVE = repo, ROOT, DRIVE
    mod.MANIFEST, mod.PAUSE = ROOT / "manifest.jsonl", ROOT / "PAUSE"
    mod.MANIFEST_COPY_DIR = outside
    mod.log("drive check: run.log on the drive")
    evidence = repo / "docs" / "audits" / "t6b-run"
    saved = mod.commit_progress([{"layer": "check", "units_done_now": 0}], evidence)
    data = (ROOT / "manifest.jsonl").read_bytes()
    copy = gzip.decompress((outside / "manifest.jsonl.gz").read_bytes())
    summary = json.loads((evidence / "manifest_summary.json").read_text())
    pushed = git(remote, "log", "--oneline", "-1", "t6b-check").stdout.strip()
    check("progress save: manifest read from the drive, gzipped outside, summary committed, pushed",
          saved and copy == data and summary["sha256"] == hashlib.sha256(data).hexdigest()
          == manifest_summary(data)["sha256"] and "T6b run section" in pushed
          and (ROOT / "run.log").read_text().startswith((evidence / "run.log.txt").read_text()),
          committed=pushed, sha256=summary["sha256"], lines=summary["lines"])  # fmt: skip


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--scratch", required=True, type=Path)
    args = p.parse_args()
    if ROOT.exists() or args.scratch.exists():
        sys.exit(f"{ROOT} or {args.scratch} already exists: start from nothing")
    if not DRIVE.is_dir():
        sys.exit("flash drive not mounted")
    ROOT.mkdir()
    args.scratch.mkdir(parents=True)
    mount_facts()
    section_checks()
    mod = runner_module()
    supersede_check(mod)
    symlink_check(args.scratch)
    read_only_check()
    progress_save_check(mod, args.scratch)
    fails = [r["check"] for r in RESULTS if r["result"] != "PASS"]
    print(json.dumps({"checks": len(RESULTS), "pass": len(RESULTS) - len(fails), "fail": fails}))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
