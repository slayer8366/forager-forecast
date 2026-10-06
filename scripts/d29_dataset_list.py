"""D29: write a download's dataset list, with licences and record counts, beside its DOI record.

Usage:
  uv run python scripts/d29_dataset_list.py <download.zip> <doi record .json> <output .json>
      [<metadata cache .json>]

Reads the zip in place (never extracted): every row of occurrence.txt (a DWCA) or of the single
table (a SIMPLE_CSV), counted by datasetKey and by each record's own licence field (D48); the
DWCA's dataset/<key>.xml (title and licence as supplied at download time) and rights.txt. Then
GBIF's public API, no credentials, one request at a time with a pause between:
/occurrence/download/<key>/datasets (GBIF's per-dataset counts for this download) and
/dataset/<key> for each dataset (title and licence now). The optional cache file keeps the
/dataset/<key> fields already read, so a second DOI does not ask again for the same dataset; each
entry carries its own read time.

Only these fields of a dataset record are kept: key, title, license, doi, publishingOrganizationKey,
modified. Contact details in GBIF's dataset records are not copied (D36).
"""

import io
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from forager_forecast.records.dataset_list import (
    DatasetTally,
    dataset_metadata,
    download_datasets,
    parse_rights,
)
from forager_forecast.records.occurrence import read_occurrence_rows

PAUSE_S = 1.0
KEPT_FIELDS = ("key", "title", "license", "doi", "publishingOrganizationKey", "modified")


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def eml_fields(text: bytes) -> dict[str, str]:
    root = ET.fromstring(text)
    dataset = next(el for el in root.iter() if el.tag.split("}")[-1] == "dataset")
    title = next((el for el in dataset if el.tag.split("}")[-1] == "title"), None)
    rights = next(
        (el for el in dataset.iter() if el.tag.split("}")[-1] == "intellectualRights"), None
    )
    url = ""
    if rights is not None:
        link = next((el for el in rights.iter() if el.tag.split("}")[-1] == "ulink"), None)
        url = link.get("url", "") if link is not None else ""
    return {
        "title_in_zip": (title.text or "").strip() if title is not None else "",
        "license_in_zip": url,
        "rights_text_in_zip": re.sub(r"\s+", " ", "".join(rights.itertext())).strip()
        if rights is not None
        else "",
    }


def main(zip_path: Path, doi_record: Path, out_path: Path, cache_path: Path | None) -> None:
    record = json.loads(doi_record.read_text(encoding="utf-8"))
    key, doi = record["download_key"], record["doi"]
    archive = zipfile.ZipFile(zip_path)
    members = archive.namelist()
    table = "occurrence.txt" if "occurrence.txt" in members else members[0]
    started = now_utc()

    tally = DatasetTally()
    with archive.open(table) as raw:
        for row in read_occurrence_rows(io.TextIOWrapper(raw, encoding="utf-8", newline="")):
            tally.add_row(row)
    print(f"{table}: {tally.rows:,} rows, {len(tally.by_dataset())} datasets", flush=True)

    in_zip = {}
    for name in members:
        if name.startswith("dataset/") and name.endswith(".xml"):
            in_zip[name.removeprefix("dataset/").removesuffix(".xml")] = eml_fields(
                archive.read(name)
            )
    rights = (
        parse_rights(archive.read("rights.txt").decode("utf-8"))
        if "rights.txt" in members
        else None
    )

    gbif_list_read = now_utc()
    gbif_list = download_datasets(key)
    requests = 1 + (len(gbif_list) - 1) // 100
    gbif_counts = {r["datasetKey"]: r for r in gbif_list}

    cache = (
        json.loads(cache_path.read_text(encoding="utf-8"))
        if cache_path and cache_path.exists()
        else {}
    )
    keys = sorted(set(tally.by_dataset()) | set(gbif_counts) | set(in_zip))
    for dataset_key in keys:
        if dataset_key in cache or dataset_key == "(empty)":
            continue
        time.sleep(PAUSE_S)
        read_at = now_utc()
        fields = dataset_metadata(dataset_key)
        requests += 1
        cache[dataset_key] = {**{f: fields.get(f) for f in KEPT_FIELDS}, "read_utc": read_at}
        if cache_path:
            cache_path.write_text(
                json.dumps(cache, indent=1, sort_keys=True) + "\n", encoding="utf-8"
            )

    by_dataset = tally.by_dataset()
    split = tally.by_dataset_and_license()
    datasets = []
    for dataset_key in sorted(keys, key=lambda k: -by_dataset.get(k, 0)):
        api = cache.get(dataset_key, {})
        gbif = gbif_counts.get(dataset_key, {})
        datasets.append(
            {
                "datasetKey": dataset_key,
                "title": api.get("title"),
                "license_per_gbif_api": api.get("license"),
                "api_read_utc": api.get("read_utc"),
                "dataset_doi": api.get("doi"),
                **in_zip.get(dataset_key, {"title_in_zip": None, "license_in_zip": None}),
                "records_counted_in_download": by_dataset.get(dataset_key, 0),
                "records_per_gbif_download_list": gbif.get("numberRecords"),
                "records_by_own_license_field": dict(
                    sorted(split.get(dataset_key, {}).items(), key=lambda kv: -kv[1])
                ),
            }
        )
    out = {
        "what": (
            "D29 dataset list for this download: each constituent dataset with its licence and "
            "record count, and records by their own licence field (D48). Licences are quoted as "
            "GBIF reports them; read times are UTC."
        ),
        "download_key": key,
        "doi": doi,
        "doi_record": str(doi_record),
        "zip_sha256_from_doi_record": record.get("sha256_of_zip"),
        "table_read": table,
        "rows_counted": tally.rows,
        "total_records_in_doi_record": record.get("total_records"),
        "number_of_datasets_in_doi_record": record.get("number_of_datasets"),
        "datasets_counted": len(by_dataset),
        "gbif_download_datasets_list_read_utc": gbif_list_read,
        "gbif_download_datasets_listed": len(gbif_list),
        "run_started_utc": started,
        "api_requests_this_run": requests,
        "rights_txt_in_zip": [{"title": t, "rights_as_supplied": r} for t, r in rights]
        if rights is not None
        else None,
        "records_by_own_license_field": dict(
            sorted(tally.by_license().items(), key=lambda kv: -kv[1])
        ),
        "datasets": datasets,
    }
    out_path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}; {requests} API requests", flush=True)


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        raise SystemExit(__doc__)
    main(
        Path(sys.argv[1]),
        Path(sys.argv[2]),
        Path(sys.argv[3]),
        Path(sys.argv[4]) if len(sys.argv) == 5 else None,
    )
