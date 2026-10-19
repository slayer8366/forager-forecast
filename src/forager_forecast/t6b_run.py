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
import subprocess
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


def done_units(manifest: Path, out_dir: Path, band_layout: str | None = None) -> set[str]:
    """Units whose latest line is ok (not deferred) and whose files still hash to that line's.

    With ``band_layout`` (tree units), the line must also name that layout: a tile built with
    another genus list is not done, so it is rebuilt rather than skipped (verify report F1)."""
    done = set()
    for unit, entry in _latest_unit_lines(manifest).items():
        if entry.get("status", "ok") != "ok":
            continue
        if band_layout is not None and entry.get("band_layout") != band_layout:
            continue
        files = entry.get("files", {})
        if all((Path(out_dir) / name).exists() for name in files) and all(
            sha256_file(Path(out_dir) / name) == sha for name, sha in files.items()
        ):
            done.add(unit)
    return done


# Forager RECORD -803, the owner: "Store it compressed (Recommended)". The repository's evidence
# copy of the run manifest is gzipped; the repository's 1 MB per-file limit is unchanged. The
# manifest on the drive stays plain JSON lines. The gzip header carries no name and no time, so
# the same manifest always gives the same bytes and an unchanged manifest stages no change.
EVIDENCE_MANIFEST = "manifest.jsonl.gz"


def copy_manifest_evidence(manifest: Path, evidence_dir: Path) -> Path:
    """Write ``manifest`` gzipped into ``evidence_dir`` and drop any uncompressed copy there."""
    import gzip

    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    out = evidence_dir / EVIDENCE_MANIFEST
    partial = out.with_name(out.name + ".partial")
    with open(partial, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                                                   compresslevel=9, mtime=0) as gz:  # fmt: skip
        gz.write(Path(manifest).read_bytes())
    partial.rename(out)
    plain = evidence_dir / "manifest.jsonl"
    if plain.exists():
        plain.unlink()
    return out


# Dispatch 2026-10-19-t6b-progress-save (forecast RECORD 2026-09-28-2012), the owner: "I'll take
# your recommendations". The gzipped manifest crossed the 1 MB limit at 1,105,301 bytes on
# 2026-10-18, so the repository now gets a summary of the manifest in place of it, and the gzipped
# copy is written outside every repository. The committed manifest.jsonl.gz stays frozen at bf9c315.
EVIDENCE_SUMMARY = "manifest_summary.json"


def manifest_summary(data: bytes) -> dict:
    """What git keeps of the manifest: its sha256, size and line count, and its units.

    Units are counted on the latest line per unit, as ``done_units`` reads them, by layer and
    status (a line with no status is ok). The planner's ruling: label them units, not tiles."""
    lines_by_kind: dict[str, int] = {}
    latest: dict[str, dict] = {}
    for line in data.decode().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        kind = str(entry.get("kind"))
        lines_by_kind[kind] = lines_by_kind.get(kind, 0) + 1
        if kind == "unit":
            latest[entry["unit"]] = entry
    units: dict[str, dict[str, int]] = {}
    for entry in latest.values():
        by_status = units.setdefault(str(entry.get("layer")), {})
        status = entry.get("status", "ok")
        by_status[status] = by_status.get(status, 0) + 1
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "lines": data.count(b"\n"),
        "lines_by_kind": dict(sorted(lines_by_kind.items())),
        "units": len(latest),
        "units_by_layer_and_status": {
            layer: dict(sorted(s.items())) for layer, s in sorted(units.items())
        },
    }


def save_manifest_outside(manifest: Path, copy_dir: Path) -> dict:
    """Gzip ``manifest`` into ``copy_dir`` (replacing the last copy) and return its summary.

    The bytes are read once, so the summary's sha256 is of exactly the bytes the copy holds."""
    import gzip

    data = Path(manifest).read_bytes()
    copy_dir = Path(copy_dir)
    copy_dir.mkdir(parents=True, exist_ok=True)
    out = copy_dir / EVIDENCE_MANIFEST
    partial = out.with_name(out.name + ".partial")
    with open(partial, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                                                   compresslevel=9, mtime=0) as gz:  # fmt: skip
        gz.write(data)
    partial.rename(out)
    summary = manifest_summary(data)
    summary["manifest"] = str(manifest)
    summary["copy_outside_git"] = str(out)
    return summary


def commit_paths(repo: Path, paths: list[Path], message: str, log: Callable[[str], None]) -> bool:
    """Commit and push only ``paths``; log any failure and return False, never raise.

    ``git commit -- <paths>`` commits those paths alone, so a file left staged by an earlier
    failure can neither enter this commit nor block it; the large-file hook still checks every
    path committed (seen in a scratch repository, step-0 report)."""

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)

    def said(r: subprocess.CompletedProcess[str]) -> str:
        return " ".join((r.stdout + r.stderr).split())

    names = [str(p) for p in paths]
    added = git("add", "--", *names)
    if added.returncode != 0:
        log(f"progress save: git add failed (exit {added.returncode}): {said(added)}")
        return False
    if git("diff", "--cached", "--quiet", "--", *names).returncode == 0:
        log("progress save: nothing changed to commit")
        return True
    committed = git("commit", "-q", "-m", message, "--", *names)
    if committed.returncode != 0:
        log(f"progress save: commit refused (exit {committed.returncode}): {said(committed)}")
        return False
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    pushed = git("push", "-q", "origin", branch.stdout.strip())
    if branch.returncode != 0 or pushed.returncode != 0:
        log(f"progress save: push failed (exit {pushed.returncode}): {said(pushed)}")
        return False
    log(f"progress save: committed and pushed {git('rev-parse', '--short', 'HEAD').stdout.strip()}")
    return True


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


# D122 (Forager RECORD -805): the -642 call "non-network errors still stop it" is replaced. A unit
# that raises anything else is recorded as failed, with its message, and the section carries on;
# it is not done, so the next section tries it again. A worker killed outright (out of memory)
# still breaks the process pool and ends the section: that is not an error inside the unit.
TRACEBACK_CHARS = 2000


def _failed(exc: BaseException, attempts: int, network_errors: list[str]) -> dict:
    import traceback

    text = "".join(traceback.format_exception(exc))
    return {"status": "failed", "attempts": attempts, "network_errors": network_errors,
            "error": f"{type(exc).__name__}: {exc}", "traceback": text[-TRACEBACK_CHARS:],
            "files": {}}  # fmt: skip


def attempt(work, unit: str, retry_delays=RETRY_DELAYS, deadline: float | None = None,
            sleep=time.sleep, now=time.time) -> dict:  # fmt: skip
    """Run ``work(unit)``, retrying network errors; deferred if it still fails. Any other error
    fails this unit only (D122): its line carries the message and the traceback's end."""
    errors: list[str] = []
    for k in range(len(retry_delays) + 1):
        try:
            result = work(unit)
            return {"status": "ok", "attempts": k + 1, "network_errors": errors, **result}
        except Exception as exc:
            if not is_network_error(exc):
                return _failed(exc, k + 1, errors)
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
    band_layout: str | None = None,
    before_unit: Callable[[str], dict | None] | None = None,
) -> dict:
    """Run pending units in order until done, the stop time, or the pause file. Returns a summary.

    ``work(unit)`` returns a dict with ``files`` ({name: sha256}, relative to out_dir); it runs
    in a worker process when workers > 1, so it must be picklable.

    ``band_layout``: see ``done_units``. ``before_unit(unit)`` runs in this process just before a
    unit starts; a non-empty answer is written to the manifest, and ``{"stop_section": reason}``
    ends the section before that unit (the tree stages' free-space check and supersede).
    """
    started = time.time()
    done = done_units(manifest, out_dir, band_layout)
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
    failed: list[str] = []
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
        if result.get("status") == "failed":
            failed.append(unit)
            return
        finished.append(unit)
        group = group_of(unit)
        if cleanup and group is not None and all(u in done or u in finished for u in groups[group]):
            t0 = time.time()
            info = cleanup(group) or {}
            append_line(manifest, {"kind": "cleanup", "layer": layer, "group": group,
                                   "seconds": round(time.time() - t0, 1), **info})  # fmt: skip

    def check_before(unit: str) -> str | None:
        if before_unit is None:
            return None
        info = before_unit(unit) or {}
        if info:
            append_line(manifest, {"kind": "before_unit", "layer": layer, "unit": unit, **info})
        return str(info["stop_section"]) if info.get("stop_section") else None

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
            reason = ensure_prepared(unit) or check_before(unit)
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
                    reason = ensure_prepared(queue[0]) or check_before(queue[0])
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
        reason = (f"every tile tried; {len(deferred)} deferred after network errors, "
                  f"{len(failed)} failed")  # fmt: skip
    summary = {
        "kind": "section", "layer": layer,
        "started_at": datetime.fromtimestamp(started).astimezone().isoformat(timespec="seconds"),
        "ended_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "seconds": round(time.time() - started, 1), "units_total": len(units),
        "units_done_before": len(done), "units_done_now": len(finished),
        "units_ok": len(finished), "units_deferred": len(deferred), "units_failed": len(failed),
        "units_remaining": len(remaining), "stopped": reason or "all units done",
    }  # fmt: skip
    append_line(manifest, summary)
    return summary
