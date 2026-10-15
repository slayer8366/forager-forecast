"""T1's PNW records from D26's download: the survivors of T1's step list, written once for the fit.

Run:  uv run python scripts/pnw_t1_records.py <download.zip> <expected sha256> <out dir>

Checks the zip's sha256 first. Reads occurrence.txt out of the zip (never extracted). Keeps the
records whose coordinates fall in T1's PNW box (t1_design.box_of), since only the PNW is fitted
(D123). Then runs three step lists over those records, each in its own Pipeline:

- `t1_1000m`: t1_steps() as it is (the headline, D33).
- `t1_5000m`: t1_steps() with the uncertainty limit at 5,000 m (D33 (3) sensitivity).
- `t1_1000m_cc`: t1_steps() over CC0 and CC BY records only, by each record's own licence field
  (D29, D48, the commercial-safe track).

Each survivor list is written as CSV (gbif_id, taxon_key, genus_key, latitude, longitude,
event_date, license), with step counts and the Cantharellus count, to <out dir>.
"""

import csv
import dataclasses
import hashlib
import io
import json
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from forager_forecast.records.filters import (
    FilterStep,
    Pipeline,
    Steps,
    UncertaintyAbove,
    t1_steps,
)
from forager_forecast.records.occurrence import OccurrenceLoader, read_occurrence_rows
from forager_forecast.t1_design import CANTHARELLUS_GENUS_KEY, box_of

# D26's download (docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json); the zip's sha256 is checked.
GBIF_DOWNLOAD_KEY = "0012112-260928105237408"
GBIF_DOI = "10.15468/dl.8jxmeb"
CC_LICENSES = {"CC0_1_0", "CC_BY_4_0"}
UNCERTAINTY_STEP = "coordinate uncertainty present and at most 1,000 m"


def with_uncertainty_limit(steps: Steps, limit_m: float) -> Steps:
    filters = tuple(
        FilterStep(
            f"coordinate uncertainty present and at most {limit_m:,.0f} m",
            UncertaintyAbove(limit_m),
        )
        if s.name == UNCERTAINTY_STEP
        else s
        for s in steps.filters
    )
    if filters == steps.filters:
        raise SystemExit("the uncertainty step was not found in t1_steps()")
    return dataclasses.replace(steps, filters=filters)


def run(steps: Steps, records) -> dict:
    pipeline = Pipeline(steps)
    kept = pipeline.run(records)
    return {
        "kept": kept,
        "source": pipeline.source_count,
        "steps": [
            {"step": c.step, "before": c.before, "dropped": c.dropped, "after": c.after}
            for c in pipeline.counts
        ],
    }


def main(zip_path: Path, expected_sha: str, out_dir: Path) -> None:
    started = time.monotonic()
    h = hashlib.sha256()
    with zip_path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    if h.hexdigest() != expected_sha:
        raise SystemExit(f"zip sha256 {h.hexdigest()} differs from {expected_sha}")
    loader = OccurrenceLoader()
    box_records = []
    with zipfile.ZipFile(zip_path).open("occurrence.txt") as raw:
        handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        for record in loader.load(read_occurrence_rows(handle)):
            box = box_of(record.latitude, record.longitude)
            if box is not None and box.name == "pnw":
                box_records.append(record)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "gbif_download_key": GBIF_DOWNLOAD_KEY,
        "gbif_doi": GBIF_DOI,
        "zip": str(zip_path),
        "zip_sha256": h.hexdigest(),
        "rows_read": loader.rows_read,
        "unloadable": dict(loader.unloadable.most_common()),
        "records_in_pnw_box": len(box_records),
        "written_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "lists": {},
    }
    lists = {
        "t1_1000m": (t1_steps(), box_records),
        "t1_5000m": (with_uncertainty_limit(t1_steps(), 5000.0), box_records),
        "t1_1000m_cc": (t1_steps(), [r for r in box_records if r.license in CC_LICENSES]),
    }
    for name, (steps, records) in lists.items():
        result = run(steps, records)
        kept = result.pop("kept")
        path = out_dir / f"{name}.csv"
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "gbif_id",
                    "taxon_key",
                    "genus_key",
                    "latitude",
                    "longitude",
                    "event_date",
                    "license",
                ]
            )
            for r in kept:
                w.writerow(
                    [
                        r.gbif_id,
                        r.taxon_key,
                        r.genus_key or "",
                        repr(r.latitude),
                        repr(r.longitude),
                        r.event_date.isoformat(),
                        r.license,
                    ]
                )
        result["survivors"] = len(kept)
        result["cantharellus_survivors"] = sum(r.genus_key == CANTHARELLUS_GENUS_KEY for r in kept)
        result["cantharellus_by_year"] = {}
        for r in kept:
            if r.genus_key == CANTHARELLUS_GENUS_KEY:
                y = str(r.event_date.year)
                result["cantharellus_by_year"][y] = result["cantharellus_by_year"].get(y, 0) + 1
        result["cantharellus_by_year"] = dict(sorted(result["cantharellus_by_year"].items()))
        result["csv_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        summary["lists"][name] = result
    summary["seconds"] = round(time.monotonic() - started, 1)
    (out_dir / "records_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "lists"}, indent=1))
    for name, r in summary["lists"].items():
        print(
            name,
            r["survivors"],
            "cantharellus",
            r["cantharellus_survivors"],
            r["cantharellus_by_year"],
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
