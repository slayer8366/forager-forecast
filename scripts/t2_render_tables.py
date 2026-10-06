"""Render the T2 count tables as Markdown for the run report, from scripts/t2_count_table.py output.

Usage: uv run python scripts/t2_render_tables.py <output directory>

For each group (cantharellus, laetiporus, all_fungi): a table of stage by region, summed over
years; and a table of year by region at the source stage and after the last step. Then the
license table by group, license and publisher at the source stage and after the last step, and
the summary's step counts, eventDate shapes and withheld texts.
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from forager_forecast.records.counts import ALL_FUNGI, OUTSIDE_T1_BOXES, T1_BOXES
from forager_forecast.records.filters import r6_audit_steps

GROUPS = ("cantharellus", "laetiporus", ALL_FUNGI)
REGIONS = (*[box.name for box in T1_BOXES], OUTSIDE_T1_BOXES)
STAGES = ("source", *r6_audit_steps().names())
FINAL = STAGES[-1]


def main(out_dir: Path) -> None:
    counts: dict[tuple[str, str, str, str], int] = defaultdict(int)
    years: set[str] = set()
    with (out_dir / "counts_by_stage_group_region_year.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row["stage"], row["group"], row["region"], row["year"])
            counts[key] += int(row["records"])
            years.add(row["year"])
    unknown = sorted({key[2] for key in counts} - set(REGIONS))
    if unknown:
        # The year tables below loop over REGIONS only, so an unknown label (for example
        # rest_of_north_america, written before the D26 rename) would print as 0 there, silently
        # (D26 review, finding 4). Refused before anything is printed.
        raise SystemExit(f"regions not known to this renderer: {unknown}; known: {list(REGIONS)}")
    unknown_stages = sorted({key[0] for key in counts} - set(STAGES))
    if unknown_stages:
        # D97 and D98 renamed R6's date step; the stage tables loop over STAGES only, so a CSV
        # written under the old name would print 0 for the renamed stage, silently.
        raise SystemExit(
            f"stages not known to this renderer: {unknown_stages}; known: {list(STAGES)}"
        )
    year_list = sorted(years)
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))

    print(
        f"Rows read: {summary['rows_read']:,}; could not be loaded: "
        f"{sum(summary['unloadable_rows'].values()):,}; loaded: {summary['source_count']:,}; "
        f"survivors: {summary['survivors']:,}.\n"
    )
    for reason, n in summary["unloadable_rows"].items():
        print(f"- could not be loaded, {reason}: {n:,}")
    print()
    print("| Step | Before | Dropped | After |\n|---|---|---|---|")
    for step in summary["steps"]:
        print(f"| {step['step']} | {step['before']:,} | {step['dropped']:,} | {step['after']:,} |")
    print()

    region_columns = REGIONS

    for group in GROUPS:
        print(f"### {group}: stage by region, all years\n")
        print("| Stage | " + " | ".join(region_columns) + " | Total |")
        print("|---|" + "---|" * (len(region_columns) + 1))
        for stage in STAGES:
            cells = [
                sum(counts[(stage, group, region, y)] for y in year_list)
                for region in region_columns
            ]
            print(f"| {stage} | " + " | ".join(f"{c:,}" for c in cells) + f" | {sum(cells):,} |")
        print()
        print(f"### {group}: year by region, at the source stage and after the last step\n")
        header = [f"{region} {label}" for region in REGIONS for label in ("source", "final")]
        print("| Year | " + " | ".join(header) + " |")
        print("|---|" + "---|" * len(header))
        for year in year_list:
            cells = []
            for region in REGIONS:
                cells.append(counts[("source", group, region, year)])
                cells.append(counts[(FINAL, group, region, year)])
            print(f"| {year} | " + " | ".join(f"{c:,}" for c in cells) + " |")
        print()

    licenses: dict[tuple[str, str], dict[tuple[str, str], int]] = defaultdict(dict)
    with (out_dir / "counts_by_license.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            licenses[(row["stage"], row["group"])][(row["license"], row["datasetKey"])] = int(
                row["records"]
            )
    print("### By license and publisher, at the source stage and after the last step\n")
    print("| Group | Stage | License | Publisher (datasetKey) | Records |\n|---|---|---|---|---|")
    for group in GROUPS:
        for stage in ("source", FINAL):
            table = licenses.get((stage, group), {})
            for (license_text, dataset_key), n in sorted(table.items(), key=lambda item: -item[1]):
                print(f"| {group} | {stage} | {license_text} | {dataset_key} | {n:,} |")
    print()

    print("### eventDate shapes at the source stage\n")
    print("| Shape | Rows |\n|---|---|")
    for shape, n in summary["event_date_shapes_of_rows_read"].items():
        print(f"| {shape} | {n:,} |")
    print()
    print("### informationWithheld texts at the source stage (first 40 characters)\n")
    print(f"Distinct prefixes: {summary['information_withheld_distinct_prefixes']}\n")
    print("| Prefix | Rows |\n|---|---|")
    for prefix, n in summary["information_withheld_prefixes_of_rows_read"].items():
        print(f"| {prefix} | {n:,} |")
    print()
    print("### dataGeneralizations texts at the source stage (first 40 characters)\n")
    print(f"Distinct prefixes: {summary['data_generalizations_distinct_prefixes']}\n")
    print("| Prefix | Rows |\n|---|---|")
    for prefix, n in summary["data_generalizations_prefixes_of_rows_read"].items():
        print(f"| {prefix} | {n:,} |")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
