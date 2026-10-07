"""T6b: a run in sections (D114), resumable by unit, with a tile manifest.

- A section works through units (tiles) in a fixed order and stops **before starting** a new unit
  once the local stop time has passed or the pause file exists. Units already running finish, so
  the section ends on whole tiles. Nothing restarts on its own.
- Every finished unit appends one JSON line to the manifest (flushed and fsynced), with its output
  files' sha256. A unit counts as done only if its line is there and every file it names still
  hashes to the recorded value; otherwise it is run again and the line says ``"redone": true``.
  Outputs are written as ``.partial`` and renamed (t6b_layers), so an interrupted unit leaves no
  file that looks whole.
- Units can share a group (a SCANFI super-window, D115 item 2): ``prepare(group)`` runs once before
  the group's first pending unit, and ``cleanup(group)`` once all its units are done.
- Up to ``workers`` units run at once in worker processes (D115 item 2: two, inside the one cap).
"""

import hashlib
import json
import os
import time
from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from datetime import datetime
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def append_line(manifest: Path, entry: dict) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest, "a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_lines(manifest: Path) -> list[dict]:
    if not Path(manifest).exists():
        return []
    out = []
    for line in Path(manifest).read_text().splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def done_units(manifest: Path, out_dir: Path) -> set[str]:
    """Units whose latest line is done and whose files still hash to what that line records."""
    latest: dict[str, dict] = {}
    for entry in read_lines(manifest):
        if entry.get("kind") == "unit":
            latest[entry["unit"]] = entry
    done = set()
    for unit, entry in latest.items():
        files = entry.get("files", {})
        if all((Path(out_dir) / name).exists() for name in files) and all(
            sha256_file(Path(out_dir) / name) == sha for name, sha in files.items()
        ):
            done.add(unit)
    return done


def next_stop(until_hhmm: str, now: datetime) -> datetime:
    """The next local time at HH:MM: today if still ahead, else tomorrow."""
    hh, mm = (int(x) for x in until_hhmm.split(":"))
    stop = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if stop <= now:
        stop = stop.fromtimestamp(stop.timestamp() + 86400)
    return stop


def stop_reason(until: datetime | None, pause_file: Path, clock=datetime.now) -> str | None:
    if Path(pause_file).exists():
        return f"pause file {pause_file}"
    if until is not None and clock() >= until:
        return f"stop time {until.isoformat(timespec='minutes')} reached"
    return None


def run_section(
    units: list[str],
    work: Callable[[str], dict],
    manifest: Path,
    out_dir: Path,
    *,
    until: datetime | None,
    pause_file: Path,
    workers: int = 1,
    group_of: Callable[[str], str | None] = lambda unit: None,
    prepare: Callable[[str], dict] | None = None,
    cleanup: Callable[[str], dict] | None = None,
    layer: str = "",
    clock=datetime.now,
) -> dict:
    """Run pending units in order until done, the stop time, or the pause file. Returns a summary.

    ``work(unit)`` returns a dict with ``files`` ({name: sha256}, relative to out_dir); it runs
    in a worker process when workers > 1, so it must be picklable.
    """
    started = time.time()
    done = done_units(manifest, out_dir)
    previously = {e["unit"] for e in read_lines(manifest) if e.get("kind") == "unit"}
    pending = [u for u in units if u not in done]
    groups: dict[str | None, list[str]] = {}
    for u in units:
        groups.setdefault(group_of(u), []).append(u)
    prepared: set[str | None] = set()
    finished: list[str] = []
    reason = None

    def record(unit: str, result: dict, seconds: float) -> None:
        append_line(manifest, {
            "kind": "unit", "layer": layer, "unit": unit, "seconds": round(seconds, 1),
            "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "redone": unit in previously, **result,
        })  # fmt: skip
        finished.append(unit)
        group = group_of(unit)
        if cleanup and group is not None and all(u in done or u in finished for u in groups[group]):
            t0 = time.time()
            info = cleanup(group) or {}
            append_line(manifest, {"kind": "cleanup", "layer": layer, "group": group,
                                   "seconds": round(time.time() - t0, 1), **info})  # fmt: skip

    def ensure_prepared(unit: str) -> None:
        group = group_of(unit)
        if prepare and group is not None and group not in prepared:
            t0 = time.time()
            info = prepare(group) or {}
            append_line(manifest, {"kind": "prepare", "layer": layer, "group": group,
                                   "seconds": round(time.time() - t0, 1), **info})  # fmt: skip
            prepared.add(group)

    if workers <= 1:
        for unit in pending:
            reason = stop_reason(until, pause_file, clock)
            if reason:
                break
            ensure_prepared(unit)
            t0 = time.time()
            result = work(unit)
            record(unit, result, time.time() - t0)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            running = {}
            queue = list(pending)
            while queue or running:
                while queue and len(running) < workers and reason is None:
                    reason = stop_reason(until, pause_file, clock)
                    if reason:
                        break
                    unit = queue.pop(0)
                    ensure_prepared(unit)
                    running[pool.submit(work, unit)] = (unit, time.time())
                if reason:
                    queue = []
                if not running:
                    break
                finished_now, _ = wait(running, return_when=FIRST_COMPLETED)
                for fut in finished_now:
                    unit, t0 = running.pop(fut)
                    record(unit, fut.result(), time.time() - t0)
    remaining = [u for u in units if u not in done and u not in finished]
    if reason is None and remaining:
        reason = "unknown"
    summary = {
        "kind": "section", "layer": layer,
        "started_at": datetime.fromtimestamp(started).astimezone().isoformat(timespec="seconds"),
        "ended_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "seconds": round(time.time() - started, 1), "units_total": len(units),
        "units_done_before": len(done), "units_done_now": len(finished),
        "units_remaining": len(remaining), "stopped": reason or "all units done",
    }  # fmt: skip
    append_line(manifest, summary)
    return summary
