"""T6 verify-first: step counts and frame size for the proposed effort step list.

Run after the proposal was committed (docs/audits/2026-10-06-t6-proposal.md, 9cd95df). Reads
D26's zip in place, streamed, never extracted. Counts only what the size and memory estimate
needs: records at each step of the proposed list, survivors under both D27 keys, distinct cells,
distinct (cell, ISO week) pairs, distinct observer-days, and the benchmark class's records and
the class names its key carries in this download. It does not split anything by weekday, season,
year or region, and fits nothing.

Usage: uv run python scripts/t6_frame_size.py ZIP OUT.json
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import threading
import time
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path

from forager_forecast.cells import cell_for, iso_week_of
from forager_forecast.records.filters import (
    UncertaintyAbove,
    drops_no_dated_record,
    event_key,
    is_user_obscured,
    observer_key,
)
from forager_forecast.records.occurrence import (
    OccurrenceLoader,
    missing_columns,
    read_occurrence_rows,
)

# Lecanoromycetes, GBIF backbone match of 2026-10-06 (proposal, choice 3).
BENCHMARK_CLASS_KEY = "180"
FIRST_DAY = date(2015, 1, 1)
LAST_DAY = date(2025, 12, 31)
RSS_LIMIT_KB = 5 * 1024 * 1024


def rss_kb() -> int:
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    raise RuntimeError("VmRSS not found in /proc/self/status")


def watchdog(peak: list[int]) -> None:
    while True:
        current = rss_kb()
        peak[0] = max(peak[0], current)
        if current > RSS_LIMIT_KB:
            print(f"STOP: resident memory {current} kB is over the 5 GB limit", file=sys.stderr)
            import os

            os._exit(3)
        time.sleep(2)


def digest(value: object) -> bytes:
    return hashlib.blake2b(repr(value).encode("utf-8"), digest_size=16).digest()


def main(zip_path: Path, out_path: Path) -> None:
    peak = [0]
    threading.Thread(target=watchdog, args=(peak,), daemon=True).start()
    started = time.time()
    benchmark_ids: set[int] = set()
    benchmark_class_names: Counter[str] = Counter()

    def rows():
        with zipfile.ZipFile(zip_path) as archive, archive.open("occurrence.txt") as raw:
            handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = read_occurrence_rows(handle)
            first = True
            for row in reader:
                if first:
                    missing = missing_columns(row.keys())
                    if missing or "classKey" not in row:
                        raise SystemExit(f"columns missing: {missing + ['classKey']}")
                    first = False
                if row.get("classKey", "").strip() == BENCHMARK_CLASS_KEY:
                    benchmark_class_names[row.get("class", "").strip()] += 1
                    try:
                        benchmark_ids.add(int(row.get("gbifID", "").strip()))
                    except ValueError:
                        pass
                yield row

    loader = OccurrenceLoader()
    uncertainty = UncertaintyAbove(1000.0)
    steps = [
        ("not user-obscured", is_user_obscured),
        ("coordinate uncertainty present and at most 1,000 m", uncertainty),
        ("date kept as given (D97, D98)", drops_no_dated_record),
    ]
    step_counts = {name: {"before": 0, "dropped": 0} for name, _ in steps}
    observer_kept: dict[bytes, int] = {}
    event_kept: dict[bytes, int] = {}
    # Per observer-key survivor: gbifID, cell, cell-week, whole week, benchmark, observer-day.
    observer_survivor_info: dict[bytes, tuple[int, bytes, bytes, bool, bool, bytes]] = {}
    outside_whole_weeks = 0

    for record in loader.load(rows()):
        dropped = False
        for name, drops in steps:
            step_counts[name]["before"] += 1
            if drops(record):
                step_counts[name]["dropped"] += 1
                dropped = True
                break
        if dropped:
            continue
        okey = digest(observer_key(record))
        ekey = digest(event_key(record))
        if ekey not in event_kept or record.gbif_id < event_kept[ekey]:
            event_kept[ekey] = record.gbif_id
        current = observer_kept.get(okey)
        if current is None or record.gbif_id < current:
            observer_kept[okey] = record.gbif_id
            cell = cell_for(record.latitude, record.longitude)
            week = iso_week_of(record.event_date)
            monday = week.monday()
            whole = monday >= FIRST_DAY and date.fromordinal(monday.toordinal() + 6) <= LAST_DAY
            observer = record.recorded_by or f"anonymous:{record.dataset_key}"
            observer_survivor_info[okey] = (
                record.gbif_id,
                digest((cell.lat_tenths, cell.lon_tenths)),
                digest((cell.lat_tenths, cell.lon_tenths, week.year, week.week)),
                whole,
                record.gbif_id in benchmark_ids,
                digest((observer, cell.lat_tenths, cell.lon_tenths, record.event_date)),
            )

    cells: set[bytes] = set()
    cell_weeks: set[bytes] = set()
    observer_days: set[bytes] = set()
    benchmark_observer_days: set[bytes] = set()
    survivors_in_whole_weeks = 0
    benchmark_survivors = 0
    for _gid, cell_d, cw_d, whole, bench, od in observer_survivor_info.values():
        if bench:
            benchmark_survivors += 1
        if not whole:
            outside_whole_weeks += 1
            continue
        survivors_in_whole_weeks += 1
        cells.add(cell_d)
        cell_weeks.add(cw_d)
        observer_days.add(od)
        if bench:
            benchmark_observer_days.add(od)

    result = {
        "zip": str(zip_path),
        "rows_read": loader.rows_read,
        "unloadable": dict(loader.unloadable),
        "loaded": loader.rows_read - sum(loader.unloadable.values()),
        "steps": step_counts,
        "survivors_observer_key": len(observer_kept),
        "survivors_event_key": len(event_kept),
        "observer_key_survivors_outside_whole_weeks": outside_whole_weeks,
        "observer_key_survivors_in_whole_weeks": survivors_in_whole_weeks,
        "distinct_cells_with_any_observer_day": len(cells),
        "distinct_cell_weeks_with_any_observer_day": len(cell_weeks),
        "distinct_observer_days": len(observer_days),
        "benchmark_class_key": BENCHMARK_CLASS_KEY,
        "benchmark_rows_in_download": sum(benchmark_class_names.values()),
        "benchmark_class_names": dict(benchmark_class_names),
        "benchmark_observer_key_survivors": benchmark_survivors,
        "benchmark_distinct_observer_days_in_whole_weeks": len(benchmark_observer_days),
        "frame_rows_if_built_in_full": len(cells) * 573 * 2,
        "seconds": round(time.time() - started, 1),
        "peak_rss_kb_watchdog": peak[0],
    }
    last = list(step_counts.values())[-1]
    result["after_filters"] = last["before"] - last["dropped"]
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
