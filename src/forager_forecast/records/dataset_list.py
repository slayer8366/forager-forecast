"""D29: a download's constituent datasets, each with its licence and record count, and by licence.

D29 asks that, beside each DOI, the download's dataset list be filed with each dataset's licence and
record count, plus the by-licence counts table. D48 makes the licence that applies each record's
own licence field, so the by-licence table counts records by that field and the dataset list
carries the dataset × licence split too; the dataset's own licence is reported as GBIF states it.
D61 settles what ships; this is provenance and attribution.

Three sources, kept apart so they can be compared: the rows of the download (counted here), the
download's rights.txt (each dataset's rights as supplied, at download time), and GBIF's public API
now (no credentials): /occurrence/download/{key}/datasets for GBIF's own per-dataset record counts
and /dataset/{key} for each dataset's title and licence.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable, Mapping
from typing import Any
from urllib.request import Request, urlopen

DATASET_URL = "https://api.gbif.org/v1/dataset/{key}"
DOWNLOAD_DATASETS_URL = (
    "https://api.gbif.org/v1/occurrence/download/{key}/datasets?offset={offset}&limit={limit}"
)
USER_AGENT = "forager-forecast D29 dataset list (https://github.com/slayer8366/forager-forecast)"
EMPTY = "(empty)"


def get_json(url: str, opener: Callable = urlopen) -> Any:
    """One public GET, no credentials."""
    request = Request(
        url, method="GET", headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    with opener(request, timeout=60) as response:
        status = getattr(response, "status", None)
        body = response.read().decode("utf-8")
    if status != 200:
        raise RuntimeError(f"GET {url} answered HTTP {status}")
    return json.loads(body)


def dataset_metadata(key: str, opener: Callable = urlopen) -> dict[str, Any]:
    return get_json(DATASET_URL.format(key=key), opener=opener)


def download_datasets(key: str, opener: Callable = urlopen, limit: int = 100) -> list[dict]:
    """GBIF's per-dataset record counts for one download, every page."""
    results: list[dict] = []
    offset = 0
    while True:
        page = get_json(
            DOWNLOAD_DATASETS_URL.format(key=key, offset=offset, limit=limit), opener=opener
        )
        results.extend(page["results"])
        if page.get("endOfRecords", True) or not page["results"]:
            return results
        offset += len(page["results"])


class DatasetTally:
    """Every row of a download, by datasetKey, by its own licence field, and by both."""

    def __init__(self) -> None:
        self.rows = 0
        self._pairs: Counter[tuple[str, str]] = Counter()

    def add_row(self, row: Mapping[str, str]) -> None:
        self.rows += 1
        dataset = row.get("datasetKey", "").strip() or EMPTY
        license_text = row.get("license", "").strip() or EMPTY
        self._pairs[(dataset, license_text)] += 1

    def by_dataset(self) -> dict[str, int]:
        out: Counter[str] = Counter()
        for (dataset, _license), n in self._pairs.items():
            out[dataset] += n
        return dict(out)

    def by_license(self) -> dict[str, int]:
        out: Counter[str] = Counter()
        for (_dataset, license_text), n in self._pairs.items():
            out[license_text] += n
        return dict(out)

    def by_dataset_and_license(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for (dataset, license_text), n in self._pairs.items():
            out.setdefault(dataset, {})[license_text] = n
        return out


def parse_rights(text: str) -> list[tuple[str, str]]:
    """rights.txt from a GBIF DWCA download: (title, rights as supplied) pairs, in file order."""
    lines = [line for line in text.splitlines() if line.strip()]
    pairs: list[tuple[str, str]] = []
    for at in range(0, len(lines), 2):
        title_line = lines[at]
        rights_line = lines[at + 1] if at + 1 < len(lines) else ""
        if not title_line.startswith("Dataset:") or not rights_line.startswith(
            "Rights as supplied:"
        ):
            raise ValueError(f"rights.txt out of step at line {at + 2}: {rights_line!r}")
        pairs.append(
            (
                title_line.removeprefix("Dataset:").strip(),
                rights_line.removeprefix("Rights as supplied:").strip(),
            )
        )
    return pairs
