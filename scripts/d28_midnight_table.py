"""D28's midnight count over one DWCA download, by dataset (D28 dispatch, Part 1).

Usage:
  uv run python scripts/d28_midnight_table.py <download.zip> <expected zip sha256>
      <datasets .json from d29_dataset_list.py> <output directory>

Checks the zip's sha256 first and stops if it differs. Reads occurrence.txt straight out of the zip
(never extracted), once, in one process, and hands every record the loader types to
records/midnight.py's MidnightTable at the source stage, before any filter (the same population as
D95). No Pipeline is run, so no survivor set is held in memory; the date-step reach is counted by
the table from the two step lists' own filters. Assessed under the measure fixed before any count
(docs/audits/2026-10-06-d28-midnight-measure.md, commit 00d23f6).

Outputs: midnight_by_dataset.json (counts, every day's midnight count, the assessment, the pooled
row), midnight_table.md, run.json.
"""

import hashlib
import io
import json
import resource
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from forager_forecast.records import midnight as mn
from forager_forecast.records.filters import SOURCE_STAGE, r6_audit_steps, t1_steps
from forager_forecast.records.occurrence import OccurrenceLoader, read_occurrence_rows


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def fmt(x, places=4):
    return "" if x is None else f"{x:.{places}f}"


def fmt_p(p):
    if p is None:
        return ""
    return f"{p:.3g}" if p < 0.001 else f"{p:.3f}"


def main(zip_path: Path, expected_sha: str, datasets_path: Path, out_dir: Path) -> None:
    started_utc = datetime.now(UTC).isoformat(timespec="seconds")
    started = time.monotonic()
    digest = sha256_of(zip_path)
    if digest != expected_sha:
        raise SystemExit(f"zip sha256 {digest} differs from the DOI record's {expected_sha}")
    out_dir.mkdir(parents=True, exist_ok=True)
    titles = {
        d["datasetKey"]: d["title"]
        for d in json.loads(datasets_path.read_text(encoding="utf-8"))["datasets"]
    }
    loader = OccurrenceLoader()
    table = mn.MidnightTable({"t1": t1_steps(), "r6": r6_audit_steps()})
    loaded = 0
    with zipfile.ZipFile(zip_path).open("occurrence.txt") as raw:
        handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        for record in loader.load(read_occurrence_rows(handle)):
            loaded += 1
            table.add(SOURCE_STAGE, record)
    if loader.rows_read != loaded + sum(loader.unloadable.values()):
        raise SystemExit("rows read are not all accounted for")

    rows = sorted(table.datasets().values(), key=lambda r: (-r.m, -r.timed, r.dataset_key))
    assessed = {a.dataset_key: a for a in mn.assess_midnight(rows)}
    all_rows = mn.pooled(rows)
    pooled_a = mn.assess_midnight([all_rows])[0]

    def entry(row, a):
        return {
            "datasetKey": row.dataset_key,
            "title": titles.get(row.dataset_key, "(not in the dataset list)"),
            "timed_records": row.timed,
            "midnight_any_day": row.m,
            "midnight_on_1st": row.k,
            "midnight_days_2_to_31": row.m - row.k,
            "midnight_by_day": {str(d): row.midnight_by_day[d] for d in range(1, 32)},
            "timed_not_midnight": row.timed_not_midnight,
            "timed_not_midnight_on_1st": row.timed_not_midnight_on_first,
            "midnight_on_1st_reaching_date_step": dict(row.first_midnight_reaching_date_step),
            "any_day_midnight_share": a.any_day_share,
            "share_of_midnight_on_1st": a.share_on_first,
            "ratio_to_expected": a.ratio_to_expected,
            "ratio_to_one_in_thirty": a.ratio_to_one_in_thirty,
            "own_calendar_share_on_1st": a.own_calendar_share,
            "interval_95": a.interval,
            "p_value": a.p_value,
            "level_each": a.level_each,
            "verdict": a.verdict,
        }

    result = {
        "measure": "docs/audits/2026-10-06-d28-midnight-measure.md (commit 00d23f6)",
        "zip": str(zip_path),
        "zip_sha256": digest,
        "rows_read": loader.rows_read,
        "unloadable": dict(loader.unloadable.most_common()),
        "records_loaded": loaded,
        "expected_share": mn.EXPECTED_SHARE,
        "min_midnight": mn.MIN_MIDNIGHT,
        "datasets_tested": sum(1 for a in assessed.values() if a.level_each is not None),
        "datasets": [entry(r, assessed[r.dataset_key]) for r in rows],
        "pooled_not_a_verdict": entry(all_rows, pooled_a),
    }
    (out_dir / "midnight_by_dataset.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "| Dataset | Timed records | Midnight, any day | Midnight share | Midnight on the 1st "
        "| Midnight, days 2-31 | Share on the 1st | x expected | Own calendar share | 95% range "
        "| p-value | Verdict | Reach date step (T1 / R6) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in [*result["datasets"], result["pooled_not_a_verdict"]]:
        rng = item["interval_95"]
        reach = item["midnight_on_1st_reaching_date_step"]
        verdict = (
            item["verdict"] if item is not result["pooled_not_a_verdict"] else "(not a verdict)"
        )
        lines.append(
            f"| {item['title'] if item['datasetKey'] != '(all datasets)' else 'All datasets'} "
            f"| {item['timed_records']:,} | {item['midnight_any_day']:,} "
            f"| {fmt(item['any_day_midnight_share'])} | {item['midnight_on_1st']:,} "
            f"| {item['midnight_days_2_to_31']:,} | {fmt(item['share_of_midnight_on_1st'])} "
            f"| {fmt(item['ratio_to_expected'], 2)} | {fmt(item['own_calendar_share_on_1st'])} "
            f"| {'' if rng is None else fmt(rng[0]) + ' to ' + fmt(rng[1])} "
            f"| {fmt_p(item['p_value'])} | {verdict} "
            f"| {reach.get('t1', 0)} / {reach.get('r6', 0)} |"
        )
    (out_dir / "midnight_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    run = {
        "started_utc": started_utc,
        "ended_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "seconds": round(time.monotonic() - started, 1),
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
    }
    (out_dir / "run.json").write_text(json.dumps(run, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(run))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]))
