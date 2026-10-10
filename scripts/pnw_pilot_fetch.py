"""Fetch the live weather the PNW pilot's scoring needs, from Open-Meteo's archive (RECORD -814).

Run:  uv run python scripts/pnw_pilot_fetch.py --week 2026-W41 --records <t1_1000m.csv>
          --out <dir> [--batch 50] [--per-minute 400 --per-hour 4000 --per-day 8000]

Every 0.1 degree cell of T1's PNW box, the 90 days before the week's Monday, batched many cells
per request (live_weather.multi_archive_url, pinned per D19, D21, D25). Cells holding any record
of the list given come first (planner, 2026-10-10), most records first, then the rest by id.

Resumable: the batch plan is written once to <out>/plan.json and reused; a batch whose body is
already on disk is skipped. Every request is appended to <out>/ledger.jsonl with its time, cost
by the pricing page's rule, status and body hash, and the body is saved with its request beside
it in <out>/raw/. The budget is read back from the ledger, so a restart keeps the windows.

A rate-limit answer stops the run with exit 3 and is never retried (planner: "stop and tell me").
Other failures are retried three times, each attempt counted in the ledger, then exit 2.
"""

import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, date, datetime
from pathlib import Path

from forager_forecast import live_weather as lw
from forager_forecast.cells import Cell, IsoWeek, cell_for
from forager_forecast.t1_design import BOXES


def log(msg: str) -> None:
    print(f"{datetime.now(UTC).isoformat(timespec='seconds')} {msg}", flush=True)


def parse_week(text: str) -> IsoWeek:
    year, week = text.split("-W")
    return IsoWeek(int(year), int(week))


def plan(records: Path, batch: int) -> list[list[Cell]]:
    pnw = next(b for b in BOXES if b.name == "pnw")
    cells = lw.box_cells(pnw)
    inside = set(cells)
    counts: dict[Cell, int] = {}
    with records.open(newline="") as f:
        for row in csv.DictReader(f):
            c = cell_for(float(row["latitude"]), float(row["longitude"]))
            if c in inside:
                counts[c] = counts.get(c, 0) + 1
    ordered = sorted(cells, key=lambda c: (-counts.get(c, 0), c.id))
    log(f"{len(cells)} cells, {len(counts)} hold records")
    return [ordered[i : i + batch] for i in range(0, len(ordered), batch)]


def read_ledger(path: Path) -> list[tuple[datetime, float]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        e = json.loads(line)
        out.append((datetime.fromisoformat(e["utc"]), float(e["cost"])))
    return out


def append_ledger(path: Path, entry: dict) -> None:
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", required=True)
    ap.add_argument("--records", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--batch", type=int, default=50)
    ap.add_argument("--per-minute", type=float, default=400)
    ap.add_argument("--per-hour", type=float, default=4000)
    ap.add_argument("--per-day", type=float, default=8000)
    ap.add_argument("--max-batches", type=int, default=0, help="stop after this many new ones")
    a = ap.parse_args()
    week = parse_week(a.week)
    start, end = lw.window_span(week)
    budget = lw.Budget(a.per_minute, a.per_hour, a.per_day)
    raw = a.out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    ledger_path = a.out / "ledger.jsonl"
    plan_path = a.out / "plan.json"
    if plan_path.exists():
        p = json.loads(plan_path.read_text())
        if (p["week"], p["start"], p["end"]) != (week.id, start.isoformat(), end.isoformat()):
            raise SystemExit(f"{plan_path} is for another week or span")
        batches = [[Cell(*map(int, cid.split("_"))) for cid in b] for b in p["batches"]]
    else:
        batches = plan(a.records, a.batch)
        plan_path.write_text(
            json.dumps(
                {
                    "week": week.id,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "records": str(a.records),
                    "batches": [[c.id for c in b] for b in batches],
                },
                indent=1,
            )
            + "\n"
        )
    log(f"week {week.id}: days {start} to {end}, {len(batches)} batches")
    fetched = 0
    for i, cells in enumerate(batches):
        body_path = raw / f"batch_{i:03d}.json"
        if body_path.exists():
            continue
        if a.max_batches and fetched >= a.max_batches:
            log(f"stopping after {fetched} new batches (--max-batches)")
            return 0
        fetched += 1
        url = lw.multi_archive_url(cells, start, end)
        cost = lw.request_cost(len(cells), start, end)
        for attempt in range(1, 4):
            wait = budget.wait_seconds(read_ledger(ledger_path), datetime.now(UTC), cost)
            if wait > 0:
                log(f"batch {i}: waiting {wait:.0f} s for the budget")
                time.sleep(wait + 1)
            requested = datetime.now(UTC)
            status, body_bytes, error = 0, b"", None
            try:
                with urllib.request.urlopen(url, timeout=180) as resp:
                    status, body_bytes = resp.status, resp.read()
            except urllib.error.HTTPError as err:
                status, body_bytes, error = err.code, err.read(), repr(err)
            except Exception as err:  # noqa: BLE001  logged in the ledger, retried, then exit 2
                error = repr(err)
            digest = hashlib.sha256(body_bytes).hexdigest()
            append_ledger(
                ledger_path,
                {
                    "utc": requested.isoformat(),
                    "batch": i,
                    "attempt": attempt,
                    "locations": len(cells),
                    "cost": cost,
                    "status": status,
                    "sha256": digest,
                    "error": error,
                },
            )
            try:
                body = json.loads(body_bytes) if body_bytes else None
            except json.JSONDecodeError:
                body = None
            if lw.is_rate_limited(status, body):
                log(f"batch {i}: RATE LIMITED, status {status}, {body}; stopping")
                return 3
            if status == 200 and body is not None:
                lw.split_by_cell(cells, body)  # raises WrongCell before anything is saved
                (raw / f"batch_{i:03d}.request.json").write_text(
                    json.dumps(
                        {
                            "url": url,
                            "cells": [c.id for c in cells],
                            "start": start.isoformat(),
                            "end": end.isoformat(),
                            "cost": cost,
                            "requested_utc": requested.isoformat(),
                            "status": status,
                            "sha256": digest,
                        },
                        indent=1,
                    )
                    + "\n"
                )
                body_path.write_bytes(body_bytes)
                log(f"batch {i}: {len(cells)} cells, {cost:.1f} calls, sha256 {digest[:12]}")
                break
            log(
                f"batch {i} attempt {attempt}: status {status} error {error} body {body_bytes[:200]!r}"
            )
            time.sleep(30 * attempt)
        else:
            log(f"batch {i}: failed three times; stopping")
            return 2
    used = sum(c for _t, c in read_ledger(ledger_path))
    log(f"all {len(batches)} batches on disk; {used:.1f} calls in the ledger")
    return 0


if __name__ == "__main__":
    sys.exit(main())
