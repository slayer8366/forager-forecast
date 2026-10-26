"""The pulls queue's guards and its one whole-file fetch (dispatch 2026-10-26-pulls).

The queue runs one download at a time as a detached user unit, and stops itself, logging why, on:
- a checksum mismatch (the file is renamed ``<name>.mismatch`` and never used);
- a login wall (a 401 or 403, a redirect to a sign-in page, or an HTML page where data was due);
- less than ``MIN_FREE`` bytes free on the drive, counting the file about to arrive;
- a ``PAUSE`` file at the forecast-data folder's root.

It resumes: a file whose checksum already matches is skipped, and a partial file is deleted and
fetched again, never trusted.
"""

import hashlib
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

# "less than 20 GB free on the drive" (dispatch, How to run it), taken as 20 GiB, the stricter of
# the two readings, since the dispatch's own "194 GB free" is the drive's free space in GiB.
MIN_FREE = 20 * 1024**3
_CHUNK = 8 << 20
LOGIN_WORDS = ("login", "signin", "sign-in", "sign_in", "oauth", "authorize", "/urs", "account")


class QueueStop(RuntimeError):
    """The queue must stop here; the message is the reason it logs."""


class ChecksumMismatch(QueueStop):
    pass


class LoginWall(QueueStop):
    pass


def stop_reason(root: Path, need_bytes: int = 0, free_bytes: Callable[[Path], int] | None = None,
                min_free: int = MIN_FREE) -> str | None:  # fmt: skip
    """Why the queue must stop before (or while) fetching ``need_bytes`` more, or None."""
    root = Path(root)
    if (root / "PAUSE").exists():
        return f"PAUSE file at {root / 'PAUSE'}"
    free = (free_bytes or (lambda r: shutil.disk_usage(r).free))(root)
    if free - need_bytes < min_free:
        return (f"{free} bytes free with {need_bytes} still to arrive would leave less than "
                f"{min_free} bytes free")  # fmt: skip
    return None


def is_login_wall(status: int, final_url: str, content_type: str | None) -> bool:
    if status in (401, 403):
        return True
    parts = urlsplit(final_url)
    where = (parts.netloc + parts.path).lower()
    if any(w in where for w in LOGIN_WORDS):
        return True
    return (content_type or "").lower().startswith("text/html")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(_CHUNK):
            h.update(block)
    return h.hexdigest()


def already_verified(path: Path, sha256: str) -> bool:
    """True if ``path`` exists and hashes to ``sha256``; a ``.partial`` beside it is deleted."""
    path = Path(path)
    path.with_name(path.name + ".partial").unlink(missing_ok=True)
    return path.is_file() and sha256_file(path) == sha256


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def fetch_verified(url: str, dest: Path, sha256: str, opener, should_stop=lambda _n: None,
                   expected_size: int | None = None, clock=None) -> dict:  # fmt: skip
    """GET ``url`` whole to ``dest`` through ``dest.partial``, refusing anything but ``sha256``.

    ``opener(url)`` gives a response with ``status``, ``url`` (after redirects), ``headers`` and
    ``read``. ``should_stop(bytes_still_to_come)`` is asked before the first byte and after every
    chunk; a reason it returns stops the queue and deletes the partial file.
    """
    import time

    clock = clock or time.monotonic
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".partial")
    partial.unlink(missing_ok=True)
    requested_at = _now()
    t0 = clock()
    response = opener(url)
    status = getattr(response, "status", 200)
    final_url = getattr(response, "url", url)
    ctype = response.headers.get("Content-Type")
    if is_login_wall(status, final_url, ctype):
        response.close()
        raise LoginWall(f"{url}: login wall (HTTP {status}, {ctype}, ended at "
                        f"{urlsplit(final_url).netloc}{urlsplit(final_url).path})")  # fmt: skip
    length = response.headers.get("Content-Length")
    length = int(length) if length is not None else None
    if expected_size is not None and length is not None and length != expected_size:
        response.close()
        raise ChecksumMismatch(f"{url}: {length} bytes offered, expected {expected_size}")
    todo = length if length is not None else (expected_size or 0)
    h = hashlib.sha256()
    written = 0
    try:
        with partial.open("wb") as out:
            reason = should_stop(todo)
            while reason is None and (chunk := response.read(_CHUNK)):
                h.update(chunk)
                out.write(chunk)
                written += len(chunk)
                reason = should_stop(max(todo - written, 0))
        if reason is not None:
            raise QueueStop(f"{dest.name}: stopped at {written} bytes: {reason}")
        if length is not None and written != length:
            raise OSError(f"{url}: {written} of {length} bytes arrived")
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    finally:
        response.close()
    got = h.hexdigest()
    if got != sha256:
        partial.rename(dest.with_name(dest.name + ".mismatch"))
        raise ChecksumMismatch(f"{dest.name}: sha256 {got}, expected {sha256}")
    partial.rename(dest)
    fu = urlsplit(final_url)
    return {
        "source": url,
        "final_url_without_query": f"{fu.scheme}://{fu.netloc}{fu.path}",
        "requested_at": requested_at,
        "finished_at": _now(),
        "seconds": round(clock() - t0, 1),
        "account": "anonymous",
        "http": {
            "status": status,
            "content_type": ctype,
            "content_length": length,
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
        },
        "file": dest.name,
        "bytes": written,
        "sha256": got,
        "expected_sha256": sha256,
        "sha256_ok": True,
    }
