"""Survivors of both step lists as they now stand (D97, D98) over one DWCA download.

Usage:
  uv run python scripts/d28_survivors.py <download.zip> <expected zip sha256> <output directory>

Checks the zip's sha256 first. Then runs t1_steps() and r6_audit_steps() as they are in
records/filters.py, one pass each, reading occurrence.txt out of the zip (never extracted), with
the two-key tally, through run_pass from scripts/d27_d28_tables.py (the pass the D27 to D29 review
re-derived): it checks every row read is accounted for and that the tally in the list's own key
equals the pipeline's survivors, overall and by region. Writes pass_t1.json, pass_r6.json, run.json.
"""

import hashlib
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from d27_d28_tables import peak_rss_mb, run_pass, write_json  # noqa: E402

from forager_forecast.records.filters import r6_audit_steps, t1_steps  # noqa: E402

LISTS = {"t1": (t1_steps, "event"), "r6": (r6_audit_steps, "observer")}


def main(zip_path: Path, expected_sha: str, out_dir: Path) -> None:
    started_utc = datetime.now(UTC).isoformat(timespec="seconds")
    started = time.monotonic()
    h = hashlib.sha256()
    with zip_path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            h.update(chunk)
    if h.hexdigest() != expected_sha:
        raise SystemExit(f"zip sha256 {h.hexdigest()} differs from the DOI record's {expected_sha}")
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, (make_steps, own_key) in LISTS.items():
        steps = make_steps()
        result = run_pass(zip_path, steps, own_key)
        write_json(
            out_dir / f"pass_{name}.json", {"list": name, "step_names": steps.names(), **result}
        )
        print(name, result["survivors"][own_key]["total"], flush=True)
    write_json(
        out_dir / "run.json",
        {
            "zip": str(zip_path),
            "zip_sha256": h.hexdigest(),
            "started_utc": started_utc,
            "ended_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "seconds": round(time.monotonic() - started, 1),
            "peak_rss_mb": round(peak_rss_mb(), 1),
        },
    )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
