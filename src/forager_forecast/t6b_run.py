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

import functools
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


def _latest_unit_lines(manifest: Path) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for entry in read_lines(manifest):
        if entry.get("kind") == "unit":
            latest[entry["unit"]] = entry
    return latest


def done_units(manifest: Path, out_dir: Path) -> set[str]:
    """Units whose latest line is ok (not deferred) and whose files still hash to that line's."""
    done = set()
    for unit, entry in _latest_unit_lines(manifest).items():
        if entry.get("status", "ok") != "ok":
            continue
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


# Planner's call after night section 2 (Forager RECORD -641): a network failure in a fetch is
# retried after these waits (s), never past the stop time; a tile that still fails is deferred.
RETRY_DELAYS = (30, 120, 300, 900)
_NETWORK_WORDS = ("curl", "http", "timed out", "timeout", "resolve", "name resolution",
                  "connection", "network", "temporary failure")  # fmt: skip


def is_network_error(exc: BaseException) -> bool:
    """True for a failure of the network, not of the code: a URL error, a timeout, a dropped
    connection, an HTTP 5xx, or a GDAL /vsicurl read error. An HTTP 4xx is not one."""
    import http.client
    import socket
    import urllib.error

    if isinstance(exc, urllib.error.HTTPError):
        return exc.code >= 500
    if isinstance(exc, (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError,
                        http.client.IncompleteRead, http.client.RemoteDisconnected)):  # fmt: skip
        return True
    try:
        from rasterio.errors import RasterioError
    except ImportError:  # pragma: no cover
        RasterioError = ()  # noqa: N806
    if RasterioError and isinstance(exc, RasterioError):
        text = str(exc).lower()
        return "/vsicurl/" in text or any(w in text for w in _NETWORK_WORDS)
    cause = exc.__cause__ or exc.__context__
    return cause is not None and cause is not exc and is_network_error(cause)


def attempt(work, unit: str, retry_delays=RETRY_DELAYS, deadline: float | None = None,
            sleep=time.sleep, now=time.time) -> dict:  # fmt: skip
    """Run ``work(unit)``, retrying network errors; deferred if it still fails. Others raise."""
    errors: list[str] = []
    for k in range(len(retry_delays) + 1):
        try:
            result = work(unit)
            return {"status": "ok", "attempts": k + 1, "network_errors": errors, **result}
        except Exception as exc:
            if not is_network_error(exc):
                raise
            errors.append(f"{type(exc).__name__}: {exc}")
            if k == len(retry_delays):
                break
            delay = retry_delays[k]
            if deadline is not None and now() + delay >= deadline:
                break
            sleep(delay)
    return {"status": "deferred", "attempts": len(errors), "network_errors": errors,
            "error": errors[-1], "files": {}}  # fmt: skip


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
    retry_delays=RETRY_DELAYS,
    sleep=time.sleep,
) -> dict:
    """Run pending units in order until done, the stop time, or the pause file. Returns a summary.

    ``work(unit)`` returns a dict with ``files`` ({name: sha256}, relative to out_dir); it runs
    in a worker process when workers > 1, so it must be picklable.
    """
    started = time.time()
    done = done_units(manifest, out_dir)
    previously = {e["unit"] for e in read_lines(manifest) if e.get("kind") == "unit"}
    latest = _latest_unit_lines(manifest)
    was_deferred = {u for u, e in latest.items() if e.get("status") == "deferred"}
    pending = [u for u in units if u not in done and u in was_deferred] + [
        u for u in units if u not in done and u not in was_deferred
    ]
    deadline = until.timestamp() if until is not None else None
    if workers <= 1:
        guarded = functools.partial(attempt, work, retry_delays=retry_delays, deadline=deadline,
                                    sleep=sleep, now=lambda: clock().timestamp())  # fmt: skip
    else:
        guarded = functools.partial(attempt, work, retry_delays=retry_delays, deadline=deadline)
    groups: dict[str | None, list[str]] = {}
    for u in units:
        groups.setdefault(group_of(u), []).append(u)
    prepared: set[str | None] = set()
    finished: list[str] = []
    deferred: list[str] = []
    reason = None

    def record(unit: str, result: dict, seconds: float) -> None:
        append_line(manifest, {
            "kind": "unit", "layer": layer, "unit": unit, "seconds": round(seconds, 1),
            "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "redone": unit in previously, **result,
        })  # fmt: skip
        if result.get("status") == "deferred":
            deferred.append(unit)
            return
        finished.append(unit)
        group = group_of(unit)
        if cleanup and group is not None and all(u in done or u in finished for u in groups[group]):
            t0 = time.time()
            info = cleanup(group) or {}
            append_line(manifest, {"kind": "cleanup", "layer": layer, "group": group,
                                   "seconds": round(time.time() - t0, 1), **info})  # fmt: skip

    def ensure_prepared(unit: str) -> str | None:
        """Prepare the unit's group once. A prepare may answer {"stop_section": reason}."""
        group = group_of(unit)
        if prepare and group is not None and group not in prepared:
            t0 = time.time()
            info = prepare(group) or {}
            append_line(manifest, {"kind": "prepare", "layer": layer, "group": group,
                                   "seconds": round(time.time() - t0, 1), **info})  # fmt: skip
            if info.get("stop_section"):
                return str(info["stop_section"])
            prepared.add(group)
        return None

    if workers <= 1:
        for unit in pending:
            reason = stop_reason(until, pause_file, clock)
            if reason:
                break
            reason = ensure_prepared(unit)
            if reason:
                break
            t0 = time.time()
            result = guarded(unit)
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
                    reason = ensure_prepared(queue[0])
                    if reason:
                        break
                    unit = queue.pop(0)
                    running[pool.submit(guarded, unit)] = (unit, time.time())
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
        reason = f"every tile tried; {len(deferred)} deferred after network errors"
    summary = {
        "kind": "section", "layer": layer,
        "started_at": datetime.fromtimestamp(started).astimezone().isoformat(timespec="seconds"),
        "ended_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "seconds": round(time.time() - started, 1), "units_total": len(units),
        "units_done_before": len(done), "units_done_now": len(finished),
        "units_ok": len(finished), "units_deferred": len(deferred),
        "units_remaining": len(remaining), "stopped": reason or "all units done",
    }  # fmt: skip
    append_line(manifest, summary)
    return summary
