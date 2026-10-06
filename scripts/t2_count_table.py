"""T2 count tables from a DWCA download zip: by stage, group, region and year, and by license.

Usage: uv run python scripts/t2_count_table.py <download.zip> <output directory>

Streams occurrence.txt straight out of the zip (no extraction: the table is several gigabytes
uncompressed) through the loader (records/occurrence.py) and the R6 audit step list
(records/filters.py, r6_audit_steps) with both tables hooked on on_pass. Records are read and
never written. Rows the loader cannot type are counted by reason (D66), and every row read is
accounted for: loaded plus unloadable equals rows read. Beside the two tables the script tallies,
over every row read, the shape of every eventDate and the first 40 characters of every non-empty
informationWithheld and dataGeneralizations text. The header is checked for every column the
loader reads before any row is counted, so a column name mismatch fails at once rather than as a
silent empty count.

Outputs under the output directory (gitignored under data/): counts_by_stage_group_region_year.csv,
counts_by_license.csv, summary.json.
"""

import io
import json
import sys
import zipfile
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

from forager_forecast.records.counts import CountTable
from forager_forecast.records.filters import Pipeline, r6_audit_steps
from forager_forecast.records.licenses import LicenseTable, fan_out
from forager_forecast.records.occurrence import (
    OccurrenceLoader,
    missing_columns,
    read_occurrence_rows,
)

OCCURRENCE_MEMBER = "occurrence.txt"


def event_date_shape(text: str) -> str:
    text = text.strip()
    if not text:
        return "empty"
    if "/" in text:
        return "range"
    day_part, separator, _ = text.partition("T")
    if len(day_part) == 10:
        return "day with time" if separator else "day only"
    if len(day_part) == 7:
        return "month only"
    if len(day_part) == 4:
        return "year only"
    return "other"


def main(zip_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = zipfile.ZipFile(zip_path)
    members = archive.namelist()
    if OCCURRENCE_MEMBER not in members:
        raise SystemExit(f"{OCCURRENCE_MEMBER} not in the zip; members are {members}")

    with archive.open(OCCURRENCE_MEMBER) as raw:
        header = io.TextIOWrapper(raw, encoding="utf-8", newline="").readline()
    header_columns = header.rstrip("\r\n").split("\t")
    lacking = missing_columns(header_columns)
    if lacking:
        raise SystemExit(f"occurrence.txt lacks columns {lacking}")

    table = CountTable()
    licenses = LicenseTable()
    date_shapes: Counter[str] = Counter()
    withheld_prefixes: Counter[str] = Counter()
    generalization_prefixes: Counter[str] = Counter()

    def shapes(rows: Iterator[dict[str, str]]) -> Iterator[dict[str, str]]:
        for row in rows:
            date_shapes[event_date_shape(row.get("eventDate", ""))] += 1
            withheld = row.get("informationWithheld", "").strip()
            if withheld:
                withheld_prefixes[withheld[:40]] += 1
            generalized = row.get("dataGeneralizations", "").strip()
            if generalized:
                generalization_prefixes[generalized[:40]] += 1
            yield row

    loader = OccurrenceLoader()
    pipeline = Pipeline(r6_audit_steps(), on_pass=fan_out(table.add, licenses.add))
    with archive.open(OCCURRENCE_MEMBER) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        survivors = len(pipeline.run(loader.load(shapes(read_occurrence_rows(text)))))

    table.write_csv(out_dir / "counts_by_stage_group_region_year.csv")
    licenses.write_csv(out_dir / "counts_by_license.csv")
    summary = {
        "zip": str(zip_path),
        "members": members,
        "header_column_count": len(header_columns),
        "rows_read": loader.rows_read,
        "unloadable_rows": dict(loader.unloadable.most_common()),
        "source_count": pipeline.source_count,
        "steps": [
            {"step": c.step, "before": c.before, "dropped": c.dropped, "after": c.after}
            for c in pipeline.counts
        ],
        "survivors": survivors,
        "event_date_shapes_of_rows_read": dict(date_shapes.most_common()),
        "information_withheld_prefixes_of_rows_read": dict(withheld_prefixes.most_common(30)),
        "information_withheld_distinct_prefixes": len(withheld_prefixes),
        "data_generalizations_prefixes_of_rows_read": dict(generalization_prefixes.most_common(30)),
        "data_generalizations_distinct_prefixes": len(generalization_prefixes),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if pipeline.counts[-1].after != survivors:
        raise SystemExit("survivor count disagrees with the last step's after count")
    if loader.rows_read != pipeline.source_count + sum(loader.unloadable.values()):
        raise SystemExit("rows read do not equal loaded plus unloadable rows")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
