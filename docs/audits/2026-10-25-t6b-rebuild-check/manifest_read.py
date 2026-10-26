"""T6b rebuild check, items 3 to 5: read the surviving manifest copy and the run log, read-only.

Committed exactly as it ran. Usage (repository root, under the dispatch's cap):

    systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0 nice -n 10 \
        .venv/bin/python docs/audits/2026-10-25-t6b-rebuild-check/manifest_read.py

Reads /mnt/work/Zynergy/forecast-data/t6b/manifest.jsonl.gz (checked first against the committed
manifest_summary.json) and docs/audits/2026-10-07-t6b-run/{run.log.txt,tiles_trees.json}. Prints
JSON: the stage lines, every SCANFI prepare line, each section with its worker count, and the
store at the loss, per stage, on the latest line per unit (as done_units reads them).
"""

import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RUN = REPO / "docs" / "audits" / "2026-10-07-t6b-run"
COPY = Path("/mnt/work/Zynergy/forecast-data/t6b/manifest.jsonl.gz")
CURRENT_LAYOUT = "t6b-bands-f4e9b848ba51"  # forager_forecast.t6b_hosts.BAND_LAYOUT, checked below


def stage_of(layer: str) -> str:
    return layer if layer in ("soil", "trees", "trees-us-half", "check") else "scanfi-layers"


def main() -> None:
    from forager_forecast.t6b_hosts import BAND_LAYOUT

    data = gzip.decompress(COPY.read_bytes())
    summary = json.loads((RUN / "manifest_summary.json").read_text())
    out: dict = {
        "copy_sha256_of_gzip": hashlib.sha256(COPY.read_bytes()).hexdigest(),
        "decompressed_sha256": hashlib.sha256(data).hexdigest(),
        "matches_summary": hashlib.sha256(data).hexdigest() == summary["sha256"]
        and len(data) == summary["bytes"]
        and data.count(b"\n") == summary["lines"],
        "band_layout_in_code": BAND_LAYOUT,
        "band_layout_constant_matches": BAND_LAYOUT == CURRENT_LAYOUT,
    }
    lines = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    out["stages"] = [{k: v for k, v in e.items() if k != "counts"} for e in lines
                     if e.get("kind") == "stage"]  # fmt: skip
    out["scanfi_prepare"] = [e for e in lines if e.get("kind") == "prepare"
                             and e.get("scanfi_whole") != "already on the drive"]  # fmt: skip

    starts = []
    for line in (RUN / "run.log.txt").read_text().splitlines():
        m = re.match(r"(\S+) section start, until (\S+), stages (\S+), workers (\d+)", line)
        if m:
            starts.append((datetime.fromisoformat(m[1]), m[3], int(m[4]), m[2]))
    sections = []
    for e in lines:
        if e.get("kind") != "section":
            continue
        t = datetime.fromisoformat(e["started_at"])
        before = [s for s in starts if s[0] <= t]
        start = before[-1] if before else None
        sections.append({
            "layer": e["layer"], "started_at": e["started_at"], "seconds": e["seconds"],
            "units_done_now": e["units_done_now"], "stopped": e["stopped"],
            "workers": start[2] if start else None, "stages": start[1] if start else None,
            "units_per_hour": round(e["units_done_now"] / e["seconds"] * 3600, 1)
            if e["seconds"] else None,
        })  # fmt: skip
    out["sections"] = sections

    latest: dict[str, dict] = {}
    for e in lines:
        if e.get("kind") == "unit":
            latest[e["unit"]] = e
    by_stage: dict[str, Counter] = defaultdict(Counter)
    for e in latest.values():
        st = stage_of(str(e.get("layer")))
        layout = e.get("band_layout")
        tag = e.get("status", "ok") + (f" layout={layout}" if st.startswith("trees") else "")
        by_stage[st][tag] += 1
    out["store_at_loss_latest_line_per_unit"] = {k: dict(v) for k, v in sorted(by_stage.items())}

    tiles = json.loads((RUN / "tiles_trees.json").read_text())
    current = {u for u, e in latest.items() if e.get("layer") == "trees"
               and e.get("status", "ok") == "ok"
               and e.get("band_layout") == BAND_LAYOUT}  # fmt: skip
    out["tree_tiles"] = {
        "listed": len(tiles),
        "with_canadian_cells": sum(t["canada"] for t in tiles),
        "ok_current_layout": len(current),
        "not_ok_current_layout": len(tiles) - len({t["key"] for t in tiles} & current),
        "of_which_canadian": sum(t["canada"] for t in tiles if t["key"] not in current),
    }

    # Unit seconds under the current layout, for the rates (item 5).
    secs: dict[str, list[float]] = defaultdict(list)
    for e in lines:
        if e.get("kind") == "unit" and e.get("status", "ok") == "ok":
            st = stage_of(str(e.get("layer")))
            if st.startswith("trees") and e.get("band_layout") != BAND_LAYOUT:
                continue
            secs[st].append(float(e["seconds"]))
    out["unit_seconds"] = {
        k: {"lines": len(v), "mean": round(sum(v) / len(v), 1), "total_h": round(sum(v) / 3600, 1)}
        for k, v in sorted(secs.items())
    }
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
