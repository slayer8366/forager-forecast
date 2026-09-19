"""T1 count tables from a SIMPLE_CSV download zip: by box, year and filter step, and by license.

Usage: uv run python scripts/t1_count_table.py <download.zip> <output directory>

Reads the zip's one CSV member twice, once per T1 box, holding one box's records in memory at a
time (the East box is about 945,000 rows), and runs apply_t1_filters_observed once per box and
year. That is exact: every T1 filter is per record except the duplicate step, whose key holds
the event date, so no step joins records across years or boxes. Rows that cannot become a Record
are counted by reason and box, never dropped silently; rows outside both boxes are counted too.
The totals are checked against the row count of the file, which the report checks against the
download's totalRecords.

Outputs, all CSV or JSON under the output directory (gitignored under data/):
counts_by_box_year_step.csv, counts_by_license.csv, unloadable_rows.csv, summary.json.
"""

import csv
import io
import json
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from forager_forecast.records import (
    SOURCE_STAGE,
    T1_FILTER_STEPS,
    Record,
    apply_t1_filters_observed,
)
from forager_forecast.simple_csv import (
    UnloadableRow,
    is_cantharellus,
    missing_columns,
    read_rows,
    record_from_row,
)
from forager_forecast.t1_design import BOXES, box_of

ALL_FUNGI = "all_fungi"
CANTHARELLUS = "cantharellus"
STAGES = (SOURCE_STAGE, *[name for name, _ in T1_FILTER_STEPS])


def csv_member(archive: zipfile.ZipFile) -> str:
    members = [name for name in archive.namelist() if name.endswith(".csv")]
    if len(members) != 1:
        raise SystemExit(f"expected one .csv member, found {members}")
    return members[0]


def box_name_of_row(row: dict[str, str]) -> str:
    try:
        box = box_of(float(row["decimalLatitude"]), float(row["decimalLongitude"]))
    except (KeyError, ValueError):
        return "unknown"
    return box.name if box is not None else "outside"


def main(zip_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = zipfile.ZipFile(zip_path)
    member = csv_member(archive)

    step_counts: Counter[tuple[str, str, int, str]] = Counter()  # box, group, year, stage
    license_counts: Counter[tuple[str, str, str, str]] = Counter()  # box, group, stage, license
    unloadable: Counter[tuple[str, str]] = Counter()  # box or unknown, reason
    outside_boxes = 0
    total_rows = 0
    header: list[str] = []

    with archive.open(member) as raw:
        header = io.TextIOWrapper(raw, encoding="utf-8", newline="").readline()
        header = header.rstrip("\r\n").split("\t")
    lacking = missing_columns(header)
    if lacking:
        raise SystemExit(f"file lacks columns {lacking}; header is {header}")

    for pass_index, box in enumerate(BOXES):
        first_pass = pass_index == 0
        buckets: dict[int, list[Record]] = defaultdict(list)
        with archive.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            for row in read_rows(text):
                if first_pass:
                    total_rows += 1
                try:
                    record = record_from_row(row)
                except UnloadableRow as error:
                    if first_pass:
                        unloadable[(box_name_of_row(row), error.reason)] += 1
                    continue
                record_box = box_of(record.latitude, record.longitude)
                if record_box is None:
                    if first_pass:
                        outside_boxes += 1
                    continue
                if record_box is not box:
                    continue
                buckets[record.event_date.year].append(record)

        for year, records in sorted(buckets.items()):

            def observe(
                stage: str, survivors: list[Record], year: int = year, name: str = box.name
            ) -> None:
                step_counts[(name, ALL_FUNGI, year, stage)] += len(survivors)
                for record in survivors:
                    license_counts[(name, ALL_FUNGI, stage, record.license or "(empty)")] += 1
                    if is_cantharellus(record):
                        step_counts[(name, CANTHARELLUS, year, stage)] += 1
                        license_counts[
                            (name, CANTHARELLUS, stage, record.license or "(empty)")
                        ] += 1

            apply_t1_filters_observed(records, observe)
        buckets.clear()

    with (out_dir / "counts_by_box_year_step.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("box", "group", "year", "stage", "records"))
        writer.writerows(sorted((*k, n) for k, n in step_counts.items()))
    with (out_dir / "counts_by_license.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("box", "group", "stage", "license", "records"))
        writer.writerows(sorted((*k, n) for k, n in license_counts.items()))
    with (out_dir / "unloadable_rows.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("box", "reason", "rows"))
        writer.writerows(sorted((*k, n) for k, n in unloadable.items()))

    source_total = sum(
        n
        for (_, group, _, stage), n in step_counts.items()
        if group == ALL_FUNGI and stage == SOURCE_STAGE
    )
    summary = {
        "zip": str(zip_path),
        "member": member,
        "header": header,
        "total_rows": total_rows,
        "loadable_rows_inside_boxes": source_total,
        "rows_outside_boxes": outside_boxes,
        "unloadable_rows": sum(unloadable.values()),
        "accounted": source_total + outside_boxes + sum(unloadable.values()),
        "stages": list(STAGES),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if summary["accounted"] != total_rows:
        raise SystemExit("row accounting does not add up; see summary.json")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
