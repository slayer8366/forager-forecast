# Not part of the pipeline. Kept unchanged as the evidence of T1's provisional run over SIMPLE_CSV
# download 0005709 (D67), as D30 kept the T0b verify script; the code below this header is as it
# stood at main 1d5bd80. The one Record type and filter pipeline are records/occurrence.py and
# records/filters.py.
"""Render the T1 count tables as Markdown for the run report, from scripts/t1_count_table.py output.

Usage: uv run python scripts/t1_render_tables.py <output directory>

Prints, for each box and group, a table of stage by year with a total column; the license table
by box, group and stage at the source and final stages; the unloadable rows; and the premise check
"each box has at least 1,000 usable Cantharellus records across at least 8 years", read as: the
final stage total is at least 1,000 and the number of years with at least one final-stage record
is at least 8. Both readings of "across at least 8 years" that the dispatch could mean are shown
(years with any record, years with at least 100) so the owner can apply either.
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from forager_forecast.records.t1_record import SOURCE_STAGE, T1_FILTER_STEPS
from forager_forecast.t1_design import BOXES, FIRST_YEAR, LAST_YEAR

STAGES = (SOURCE_STAGE, *[name for name, _ in T1_FILTER_STEPS])
FINAL = STAGES[-1]
YEARS = list(range(FIRST_YEAR, LAST_YEAR + 1))


def main(out_dir: Path) -> None:
    counts: dict[tuple[str, str, str], dict[int, int]] = defaultdict(dict)
    with (out_dir / "counts_by_box_year_step.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            counts[(row["box"], row["group"], row["stage"])][int(row["year"])] = int(row["records"])
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    print(
        f"Rows in file: {summary['total_rows']:,}; loadable inside a box: "
        f"{summary['loadable_rows_inside_boxes']:,}; outside both boxes: "
        f"{summary['rows_outside_boxes']:,}; unloadable: {summary['unloadable_rows']:,}; "
        f"accounted: {summary['accounted']:,}.\n"
    )

    for box in BOXES:
        for group in ("cantharellus", "all_fungi"):
            print(f"### {box.name}, {group}\n")
            print("| Stage | " + " | ".join(str(y) for y in YEARS) + " | Total |")
            print("|---|" + "---|" * (len(YEARS) + 1))
            for stage in STAGES:
                by_year = counts.get((box.name, group, stage), {})
                cells = [f"{by_year.get(y, 0):,}" for y in YEARS]
                print(f"| {stage} | " + " | ".join(cells) + f" | {sum(by_year.values()):,} |")
            print()

    print("### Premise: at least 1,000 usable Cantharellus records across at least 8 years\n")
    print(
        "| Box | Final Cantharellus total | Years with any | Years with at least 100 "
        "| Smallest year | Verdict (total >= 1,000 and years with any >= 8) |"
    )
    print("|---|---|---|---|---|---|")
    for box in BOXES:
        final = counts.get((box.name, "cantharellus", FINAL), {})
        total = sum(final.values())
        years_any = sum(1 for y in YEARS if final.get(y, 0) > 0)
        years_100 = sum(1 for y in YEARS if final.get(y, 0) >= 100)
        smallest = min(((final.get(y, 0), y) for y in YEARS), default=(0, None))
        verdict = "holds" if total >= 1000 and years_any >= 8 else "fails"
        print(
            f"| {box.name} | {total:,} | {years_any} | {years_100} "
            f"| {smallest[0]:,} ({smallest[1]}) | {verdict} |"
        )
    print()

    licenses: dict[tuple[str, str, str], dict[str, int]] = defaultdict(dict)
    with (out_dir / "counts_by_license.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            licenses[(row["box"], row["group"], row["stage"])][row["license"]] = int(row["records"])
    names = sorted({name for table in licenses.values() for name in table})
    print("### By license, at the source stage and after the last filter\n")
    print("| Box | Group | Stage | " + " | ".join(names) + " | Total |")
    print("|---|---|---|" + "---|" * (len(names) + 1))
    for box in BOXES:
        for group in ("cantharellus", "all_fungi"):
            for stage in (SOURCE_STAGE, FINAL):
                table = licenses.get((box.name, group, stage), {})
                print(
                    f"| {box.name} | {group} | {stage} | "
                    + " | ".join(f"{table.get(n, 0):,}" for n in names)
                    + f" | {sum(table.values()):,} |"
                )
    print()

    print("### Rows that could not become a Record\n")
    print("| Box | Reason | Rows |\n|---|---|---|")
    with (out_dir / "unloadable_rows.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        print(f"| {row['box']} | {row['reason']} | {int(row['rows']):,} |")
    if not rows:
        print("| (none) | | 0 |")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
