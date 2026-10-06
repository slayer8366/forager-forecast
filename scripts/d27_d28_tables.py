"""D27 and D28 over one DWCA download: both duplicate keys, the day-of-month table, the rules.

Usage:
  uv run python scripts/d27_d28_tables.py <download.zip> <datasets .json from d29_dataset_list.py>
      <output directory>

Reads occurrence.txt straight out of the zip (never extracted), once per pass, in one process.

Pass 1 runs T1's step list as it stands (the provisional date rule) with three sinks on on_pass:
the day-of-month table at the source stage (records/date_quality.py), and the two-key tally at the
stage the duplicate step reads (records/duplicate_keys.py). The table is assessed with the test
fixed before any count was read (verify report section 3, commit ea579c2), and the assessment is
written before any other pass runs. Then each candidate rule runs over both step lists, each pass
with the two-key tally:

- drop_all: the provisional rule (D28, D65), the step lists unchanged;
- keep_all: only midnight on the 1st written as a clock time is dropped (the T1 dispatch's words);
- per_dataset: date-only on the 1st dropped only in "clear excess" datasets;
- per_dataset_plus_small and per_dataset_plus_too_few: the same, also dropping them in the "small
  excess" or the "too few to test" datasets, the two choices left to the owner. A variant whose
  dataset set equals per_dataset's is not run again; the output says so.

Every pass checks that the tally's count in the list's own key equals the pipeline's survivors,
overall and by region, and that every row read is accounted for. Outputs, written as each pass
ends: day_of_month_by_dataset.csv, assessment.json, pass_<list>_<rule>.json, runs.json.
"""

import csv
import io
import json
import resource
import sys
import time
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from forager_forecast.records import date_quality as dq
from forager_forecast.records.counts import region_of
from forager_forecast.records.duplicate_keys import KeyTally
from forager_forecast.records.filters import Pipeline, r6_audit_steps, t1_steps
from forager_forecast.records.occurrence import (
    OccurrenceLoader,
    missing_columns,
    read_occurrence_rows,
)

LISTS = {"t1": (t1_steps, "event"), "r6": (r6_audit_steps, "observer")}


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def run_pass(zip_path: Path, steps, own_key: str, extra_sinks=()) -> dict:
    started = time.monotonic()
    loader = OccurrenceLoader()
    tally = KeyTally.for_steps(steps)
    sinks = (tally.add, *extra_sinks)

    def on_pass(stage, record):
        for sink in sinks:
            sink(stage, record)

    pipeline = Pipeline(steps, on_pass=on_pass)
    with zipfile.ZipFile(zip_path).open("occurrence.txt") as raw:
        handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        kept = pipeline.run(loader.load(read_occurrence_rows(handle)))
    if loader.rows_read != pipeline.source_count + sum(loader.unloadable.values()):
        raise SystemExit("rows read are not all accounted for")
    kept_regions = Counter(region_of(r) for r in kept)
    if tally.survivors(own_key) != len(kept) or tally.survivors_by_region(own_key) != kept_regions:
        raise SystemExit(f"the {own_key} tally disagrees with the pipeline's survivors")
    return {
        "rows_read": loader.rows_read,
        "unloadable": dict(loader.unloadable.most_common()),
        "source": pipeline.source_count,
        "steps": [
            {"step": c.step, "before": c.before, "dropped": c.dropped, "after": c.after}
            for c in pipeline.counts
        ],
        "duplicate_step_reads": {
            "stage": tally.at_stage,
            "records": tally.entered,
            "by_region": dict(sorted(tally.entered_by_region.items())),
            "records_with_empty_recordedBy": tally.empty_observer_entered,
        },
        "survivors": {
            name: {
                "total": tally.survivors(name),
                "by_region": dict(sorted(tally.survivors_by_region(name).items())),
            }
            for name in ("event", "observer")
        },
        "list_own_key": own_key,
        "seconds": round(time.monotonic() - started, 1),
        "peak_rss_mb_so_far": round(peak_rss_mb(), 1),
    }


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main(zip_path: Path, datasets_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path).open("occurrence.txt") as raw:
        header = io.TextIOWrapper(raw, encoding="utf-8", newline="").readline()
    lacking = missing_columns(header.rstrip("\r\n").split("\t"))
    if lacking:
        raise SystemExit(f"occurrence.txt lacks columns {lacking}")
    titles = {
        d["datasetKey"]: d["title"]
        for d in json.loads(datasets_path.read_text(encoding="utf-8"))["datasets"]
    }
    runs = {"zip": str(zip_path), "started_utc": datetime.now(UTC).isoformat(timespec="seconds")}

    # Pass 1: T1 as it stands, with the day-of-month table at the source stage.
    table = dq.DayOfMonthTable()
    first = run_pass(zip_path, t1_steps(), "event", extra_sinks=(table.add,))
    write_json(out_dir / "pass_t1_drop_all.json", {"rule": "drop_all", **first})

    rows = sorted(table.datasets().values(), key=lambda r: -r.loaded)
    with (out_dir / "day_of_month_by_dataset.csv").open("w", encoding="utf-8", newline="") as h:
        writer = csv.writer(h)
        writer.writerow(
            ("datasetKey", "title", "loaded", "date_only", "midnight_first_with_clock")
            + tuple(f"day_{d}" for d in range(1, 32))
        )
        for row in rows:
            writer.writerow(
                (
                    row.dataset_key,
                    titles.get(row.dataset_key, ""),
                    row.loaded,
                    row.n,
                    row.midnight_first_with_clock,
                )
                + tuple(row.date_only_by_day[d] for d in range(1, 32))
            )
    assessed = dq.assess(rows)
    by_verdict = {
        v: sorted(a.dataset_key for a in assessed if a.verdict == v)
        for v in (dq.CLEAR, dq.SMALL, dq.TOO_FEW, dq.CLOSE)
    }
    write_json(
        out_dir / "assessment.json",
        {
            "fixed_in": "docs/audits/2026-10-06-d27-d29-verify-report.md section 3, commit ea579c2",
            "reference_share": dq.REFERENCE_SHARE,
            "calendar_share_shown_not_used": dq.CALENDAR_SHARE,
            "min_date_only": dq.MIN_DATE_ONLY,
            "family_level": dq.FAMILY_LEVEL,
            "clear_excess_lower_end": dq.CLEAR_EXCESS_SHARE,
            "interval_level": dq.INTERVAL_LEVEL,
            "datasets": [
                {
                    "datasetKey": a.dataset_key,
                    "title": titles.get(a.dataset_key, ""),
                    "loaded": next(r.loaded for r in rows if r.dataset_key == a.dataset_key),
                    "date_only": a.n,
                    "date_only_on_the_1st": a.k,
                    "share": a.share,
                    "ratio_to_1_in_30": a.ratio_to_reference,
                    "ratio_to_calendar_share": a.ratio_to_calendar,
                    "interval_95": a.interval,
                    "p_value_one_sided": a.p_value,
                    "level_each": a.level_each,
                    "excess_on_the_1st": a.excess_on_first,
                    "verdict": a.verdict,
                }
                for a in assessed
            ],
            "by_verdict": by_verdict,
        },
    )
    print(f"assessment written: { {v: len(k) for v, k in by_verdict.items()} }", flush=True)

    clear = frozenset(by_verdict[dq.CLEAR])
    rules = {
        "drop_all": (dq.DROP_ALL, None),
        "keep_all": (dq.KEEP_ALL, None),
        "per_dataset": (dq.DefaultDateInDatasets(clear), clear),
        "per_dataset_plus_small": (
            dq.DefaultDateInDatasets(clear | set(by_verdict[dq.SMALL])),
            clear | set(by_verdict[dq.SMALL]),
        ),
        "per_dataset_plus_too_few": (
            dq.DefaultDateInDatasets(clear | set(by_verdict[dq.TOO_FEW])),
            clear | set(by_verdict[dq.TOO_FEW]),
        ),
    }
    runs["rules"] = {name: sorted(s) if s is not None else None for name, (_, s) in rules.items()}
    runs["passes"] = {"t1_drop_all": "pass_t1_drop_all.json"}
    for list_name, (make_steps, own_key) in LISTS.items():
        for rule_name, (drops, datasets) in rules.items():
            label = f"{list_name}_{rule_name}"
            if label == "t1_drop_all":
                continue
            if rule_name.startswith("per_dataset_plus") and datasets == clear:
                runs["passes"][label] = f"not run: same datasets as {list_name}_per_dataset"
                continue
            steps = dq.with_date_rule(make_steps(), drops)
            result = run_pass(zip_path, steps, own_key)
            write_json(out_dir / f"pass_{label}.json", {"rule": rule_name, **result})
            runs["passes"][label] = f"pass_{label}.json"
            print(
                f"{label}: {result['seconds']} s, peak {result['peak_rss_mb_so_far']} MB",
                flush=True,
            )
            write_json(out_dir / "runs.json", runs)
    runs["finished_utc"] = datetime.now(UTC).isoformat(timespec="seconds")
    runs["peak_rss_mb"] = round(peak_rss_mb(), 1)
    write_json(out_dir / "runs.json", runs)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
