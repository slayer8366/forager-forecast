"""The count table by license: records by pipeline stage, forager group, license and publisher.

The T1 and T2 follow-up dispatch of 2026-09-18 asks for a second count table by license beside
the one by region and year. The publisher (GBIF datasetKey) sits in the same key because the
licence gate the T2 review names (check 6) is per publisher: DATA_REGISTER.md must carry each
publisher's licence before its records are used, and a table keyed by licence alone cannot say
which publisher a licence belongs to. Plug add() into Pipeline.on_pass beside CountTable.add().
"""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from forager_forecast.records.counts import ALL_FUNGI, group_of
from forager_forecast.records.occurrence import Record

EMPTY = "(empty)"


@dataclass(frozen=True)
class LicenseKey:
    stage: str
    group: str
    license: str
    dataset_key: str


class LicenseTable:
    """Tallies (stage, group, license, datasetKey); every record also under all_fungi."""

    def __init__(self) -> None:
        self._counts: Counter[LicenseKey] = Counter()

    def add(self, stage: str, record: Record) -> None:
        license_text = record.license or EMPTY
        dataset_key = record.dataset_key or EMPTY
        self._counts[LicenseKey(stage, ALL_FUNGI, license_text, dataset_key)] += 1
        group = group_of(record)
        if group is not None:
            self._counts[LicenseKey(stage, group, license_text, dataset_key)] += 1

    def count(self, stage: str, group: str, license_text: str, dataset_key: str) -> int:
        return self._counts[LicenseKey(stage, group, license_text, dataset_key)]

    def rows(self) -> list[tuple[str, str, str, str, int]]:
        return sorted(
            (key.stage, key.group, key.license, key.dataset_key, n)
            for key, n in self._counts.items()
        )

    def write_csv(self, path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(("stage", "group", "license", "datasetKey", "records"))
            writer.writerows(self.rows())


def fan_out(*sinks: Callable[[str, Record], None]) -> Callable[[str, Record], None]:
    """One on_pass callable that feeds every table, in the order given."""

    def on_pass(stage: str, record: Record) -> None:
        for sink in sinks:
            sink(stage, record)

    return on_pass
