"""T7 part B: fetch the road and trail sources once each, one at a time, and check each.

Usage (repository root, low priority):
    nice -n 19 ionice -c 3 .venv/bin/python scripts/t7_access_fetch.py
Writes <RAW_DIR>/<name>.zip read-only, and <RAW_DIR>/<name>.request.json beside it (URL, UTC time,
HTTP headers, size, sha256, the check made and its result). A file already present with a passing
record is skipped, never fetched twice. A failed check stops the run and leaves the file as
<name>.zip.failed for inspection.
"""

import datetime as dt
import json
import subprocess
import sys
import time
import zipfile

from forager_forecast.t7.access_sources import (
    CHECK_ETAG,
    RAW_DIR,
    etag_matches,
    sha256,
    sources,
)


def head(url: str) -> dict:
    out = subprocess.run(["curl", "-sIL", "--max-time", "120", url], check=True,
                         capture_output=True, text=True).stdout  # fmt: skip
    return last_headers(out)


def last_headers(out: str) -> dict:
    """The final response's headers from curl's header dump (after any redirects)."""
    block = out.replace("\r", "").strip().split("\n\n")[-1]
    headers = {"status": block.splitlines()[0] if block else ""}
    for line in block.splitlines()[1:]:
        k, _, v = line.partition(":")
        headers[k.strip().lower()] = v.strip()
    return headers


def main(only: list[str]) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for src in sources():
        if only and src.name not in only:
            continue
        target = RAW_DIR / f"{src.name}.zip"
        record_path = RAW_DIR / f"{src.name}.request.json"
        if target.exists() and record_path.exists():
            if json.loads(record_path.read_text()).get("check_passed"):
                print(f"{src.name}: present, skipped", flush=True)
                continue
        headers = head(src.url)
        partial = target.with_suffix(".zip.partial")
        started = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
        t = time.perf_counter()
        dump = partial.with_suffix(".headers")
        subprocess.run(["curl", "-sfL", "--retry", "3", "--max-time", "7200", "-D", str(dump),
                        "-o", str(partial), src.url], check=True)  # fmt: skip
        got = last_headers(dump.read_text(errors="replace"))
        dump.unlink()
        size = partial.stat().st_size
        if src.check == CHECK_ETAG:
            etag = headers.get("etag", "")
            passed = bool(etag) and etag_matches(partial, etag)
            expected = etag
        else:
            # The length the file was actually served with (the GET's final response). A HEAD can
            # answer something else: the BLM hub answers HEAD with 202 and a 183-byte JSON status
            # while it prepares the export (first run, 2026-10-17, recorded as a failed check).
            length = got.get("content-length")
            passed = length is None or int(length) == size
        with zipfile.ZipFile(partial) as z:
            zip_ok = z.testzip() is None
            expected = length if length is not None else "no length served (chunked)"
        record = {
            "name": src.name,
            "url": src.url,
            "fetched_utc": started,
            "seconds": round(time.perf_counter() - t, 1),
            "http_head": headers,
            "http_get": got,
            "size_bytes": size,
            "sha256": sha256(partial),
            "check": src.check,
            "check_expected": expected,
            "zip_crc_ok": zip_ok,
            "check_passed": passed and zip_ok,
        }
        print(json.dumps(record), flush=True)
        passed = passed and zip_ok
        if not passed:
            partial.rename(target.with_suffix(".zip.failed"))
            record_path.write_text(json.dumps(record, indent=2) + "\n")
            raise SystemExit(f"{src.name}: check failed ({src.check})")
        partial.rename(target)
        target.chmod(0o444)
        record_path.write_text(json.dumps(record, indent=2) + "\n")
        record_path.chmod(0o444)


if __name__ == "__main__":
    main(sys.argv[1:])
