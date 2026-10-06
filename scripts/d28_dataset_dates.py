"""D28 supplement: one dataset's date-only records by calendar date, to show how they cluster.

Usage: uv run python scripts/d28_dataset_dates.py <download.zip> <datasetKey> <output .json>

Reads occurrence.txt in place through the loader. Counts that dataset's date-only records (no clock
time) by date, and says how many distinct dates carry them and which fall on the 1st. Written after
the day-of-month table, as an observation for the owner; it changes no verdict and no rule.
"""

import io
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

from forager_forecast.records.date_quality import is_date_only
from forager_forecast.records.occurrence import OccurrenceLoader, read_occurrence_rows


def main(zip_path: Path, dataset_key: str, out_path: Path) -> None:
    loader = OccurrenceLoader()
    by_date: Counter[str] = Counter()
    with zipfile.ZipFile(zip_path).open("occurrence.txt") as raw:
        rows = read_occurrence_rows(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
        for record in loader.load(r for r in rows if r.get("datasetKey") == dataset_key):
            if is_date_only(record):
                by_date[record.event_date.isoformat()] += 1
    on_first = {d: n for d, n in sorted(by_date.items()) if d.endswith("-01")}
    out = {
        "datasetKey": dataset_key,
        "date_only_records": sum(by_date.values()),
        "distinct_dates": len(by_date),
        "largest_dates": by_date.most_common(10),
        "dates_on_the_1st": on_first,
        "unloadable_in_this_dataset": dict(loader.unloadable),
    }
    out_path.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
