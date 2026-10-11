"""Decide whether the PNW pilot chain goes on past the equivalence gate, and record why.

Run:  uv run python scripts/pnw_gate_override.py <equivalence json> <failures json> <record out>
          --not-before <ISO UTC> [--override "Forager RECORD -854"]

The gate itself (pnw_equivalence.land_route_pass, HOURLY_TOL, EPS, its comparison, and the
"pass" it writes) is not changed by this file and still runs first. This is a separate path,
added for the owner's ruling Forager RECORD -854 (2026-10-11, "Option 1": fit anyway, failure on
the record), so that a fit can go on past a land-route fail only when it is told to by name, and
the fail travels with every output it produces.

Exit 0: go on. Exit 3: stop. Either way the record is written to <record out>, and the fit
script copies it into each fit summary and each model.json (pnw_t1_fit.py --gate-record).

- Gate passed: go on. An override given anyway is recorded as unused.
- Gate failed, no override: stop (exit 3), as before this file existed.
- Gate failed, override given: go on only when all of these hold, else stop:
  * the override is exactly OVERRIDE;
  * the fail is the land route alone (every required span compared);
  * the failing hours, named by pnw_land_route_failures.py from the same run's cached bodies,
    agree with the run's own offset-0 counts and are exactly the hours the ruling was given for
    (RULED_HOURS). The ruling covers one known hour; a different or a further failing hour is a
    new fact for the owner, not something this override was given for.
- An equivalence result older than --not-before (the run did not write one) is a stop.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

OVERRIDE = "Forager RECORD -854"
# The hour the owner ruled on (RECORD -854; step 0 of the gate-override dispatch, 903a170).
RULED_HOURS = [{"variable": "t2m", "land_point": [493, -1250], "hour_utc": "2025-12-12T11:00"}]


def _key(h: dict) -> tuple:
    return (h["variable"], tuple(h["land_point"]), h["hour_utc"])


def decide(equivalence: dict, failures: dict | None, override: str | None) -> tuple[int, dict]:
    """(exit code, record). The record holds the gate result as the gate wrote it."""
    gate = equivalence["gate"]
    land = equivalence["hourly_land_route"]
    record = {
        "gate_pass": bool(gate["pass"]),
        "land_route_pass": bool(land["pass"]),
        "spans_complete": gate["spans_complete"],
        "hourly_by_variable": land["by_variable"],
        "equivalence_written_utc": equivalence["written_utc"],
        "override_given": override,
        "failing_hours": [],
    }
    if gate["pass"]:
        record["override"] = "unused: the gate passed" if override else "none"
        return 0, record
    if failures is not None:
        record["failing_hours"] = failures["failing_hours"]
    if override is None:
        record["override"] = "none"
        record["stop"] = "gate failed and no override was given"
        return 3, record
    if override != OVERRIDE:
        record["override"] = "refused"
        record["stop"] = f"override {override!r} is not {OVERRIDE!r}"
        return 3, record
    if gate["spans_complete"] is False:
        record["override"] = "refused"
        record["stop"] = "required spans missing; the override covers the land route only"
        return 3, record
    if failures is None:
        record["override"] = "refused"
        record["stop"] = "no failing-hours list from this run"
        return 3, record
    offset0 = {
        v: r["matched_compared_by_offset_hours"]["0"] for v, r in land["by_variable"].items()
    }
    if {v: list(c) for v, c in failures["offset0_matched_compared"].items()} != offset0:
        record["override"] = "refused"
        record["stop"] = "failing-hours list does not match this run's offset-0 counts"
        return 3, record
    if sorted(map(_key, failures["failing_hours"])) != sorted(map(_key, RULED_HOURS)):
        record["override"] = "refused"
        record["stop"] = "failing hours differ from the hour RECORD -854 was given for"
        return 3, record
    record["override"] = (
        f"used: {OVERRIDE} (owner, 2026-10-11, 'fit anyway, failure on the record'); the gate "
        "failed and its result stands as written"
    )
    return 0, record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("equivalence", type=Path)
    ap.add_argument("failures", type=Path)
    ap.add_argument("record", type=Path)
    ap.add_argument("--not-before", required=True)
    ap.add_argument("--override")
    args = ap.parse_args()
    eq = json.loads(args.equivalence.read_text()) if args.equivalence.exists() else None
    if eq is None or datetime.fromisoformat(eq["written_utc"]) < datetime.fromisoformat(
        args.not_before
    ):
        print(f"GATE RECORD: no equivalence result from this run in {args.equivalence}; stop")
        return 3
    failures = json.loads(args.failures.read_text()) if args.failures.exists() else None
    code, record = decide(eq, failures, args.override)
    record["proceed"] = code == 0
    args.record.write_text(json.dumps(record, indent=2) + "\n")
    print(f"GATE RECORD: gate pass {record['gate_pass']}, override {record['override']}")
    if code:
        print(f"GATE RECORD: stop: {record['stop']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
