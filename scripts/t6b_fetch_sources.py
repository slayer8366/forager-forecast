"""T6b: fetch the whole-file sources onto the flash drive (CEC boundaries, CEC ecoregions, NALCMS).

Usage (repository root, under the dispatch's memory cap):
    .venv/bin/python scripts/t6b_fetch_sources.py [vectors] [nalcms]
Writes forecast-data/t6b/sources/<name>.request.json beside each file; copy them to docs/pulls/.
"""

import json
import sys
import time
from pathlib import Path

from forager_forecast.t6b_sources import (
    CEC_ECOREGIONS_URL,
    CEC_POLITICAL_URL,
    NALCMS_SMALL_MEMBERS,
    NALCMS_TIF_MEMBER,
    NALCMS_URL,
    download,
    extract_zip_member,
    http_headers,
    http_range_reader,
)

DRIVE = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data")
OUT = DRIVE / "t6b" / "sources"


def main(steps):
    if not DRIVE.is_dir():
        raise SystemExit("flash drive not mounted")
    OUT.mkdir(parents=True, exist_ok=True)
    if "vectors" in steps:
        for name, url in (
            ("cec_political", CEC_POLITICAL_URL),
            ("cec_ecoregions_l3", CEC_ECOREGIONS_URL),
        ):
            t = time.perf_counter()
            record = download(url, OUT / f"{name}.zip")
            record["seconds"] = round(time.perf_counter() - t, 1)
            (OUT / f"{name}.request.json").write_text(json.dumps(record, indent=2) + "\n")
            print(json.dumps(record), flush=True)
    if "nalcms" in steps:
        headers = http_headers(NALCMS_URL)
        reader = http_range_reader(NALCMS_URL)
        records = []
        for member in (*NALCMS_SMALL_MEMBERS, NALCMS_TIF_MEMBER):
            t = time.perf_counter()
            rec = extract_zip_member(
                reader, headers["content_length"], member, OUT / "nalcms" / Path(member).name
            )
            rec["seconds"] = round(time.perf_counter() - t, 1)
            records.append(rec)
            print(json.dumps(rec), flush=True)
        body = {
            "source": NALCMS_URL,
            "dataset": "CEC NA Environmental Atlas, Land Cover 2020 30m (NALCMS), Ed. 2.0",
            "licence": "CC BY 4.0 (metadata, Use limitations)",
            "account": "anonymous",
            "http": headers,
            "members": records,
            "rulings": ["D112"],
        }
        (OUT / "nalcms.request.json").write_text(json.dumps(body, indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
