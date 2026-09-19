"""The count table: records by pipeline stage, forager group, region and year.

Regions are the two T1 boxes plus "rest of North America"
(docs/dispatch/2026-09-18-t2-record-audit.md, "Then build"; box limits from
docs/dispatch/2026-09-18-t1-calendar-smoke-test.md, "Boxes, for T1 only"). Groups are the two
phase 1 forager groups at genus level (D9, D12; SPEC.md Scope), told apart by GBIF genusKey, with
every record also counted under "all_fungi" so the table shows the denominator the observation
layer (T6) will need.
"""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from forager_forecast.records.filters import Record


@dataclass(frozen=True)
class Box:
    """A latitude and longitude box. Limits are inclusive at both ends."""

    name: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float

    def contains(self, latitude: float, longitude: float) -> bool:
        return (
            self.lat_min <= latitude <= self.lat_max and self.lon_min <= longitude <= self.lon_max
        )


# T1 dispatch: "Pacific Northwest: 42.0 to 49.5 N, 125.0 to 121.0 W" and
# "East: 38.0 to 46.0 N, 84.0 to 70.0 W". West longitudes are negative here.
T1_BOXES = (
    Box("pnw", 42.0, 49.5, -125.0, -121.0),
    Box("east", 38.0, 46.0, -84.0, -70.0),
)
REST_OF_NORTH_AMERICA = "rest_of_north_america"
NO_COORDINATES = "no_coordinates"

# GBIF Backbone genus keys, resolved with /v1/species/match on 2026-09-18:
# Cantharellus Adans. ex Fr., 1821 -> 9623860 (EXACT, ACCEPTED);
# Laetiporus Murrill, 1904 -> 2542160 (EXACT, ACCEPTED).
GROUP_BY_GENUS_KEY = {
    "9623860": "cantharellus",
    "2542160": "laetiporus",
}
ALL_FUNGI = "all_fungi"
STAGE_SOURCE = "source"


def region_of(record: Record, boxes: Iterable[Box] = T1_BOXES) -> str:
    try:
        latitude = float(record["decimalLatitude"])
        longitude = float(record["decimalLongitude"])
    except KeyError, ValueError:
        return NO_COORDINATES
    for box in boxes:
        if box.contains(latitude, longitude):
            return box.name
    return REST_OF_NORTH_AMERICA


def group_of(record: Record) -> str | None:
    """The forager group a record belongs to, or None for any other fungus."""
    return GROUP_BY_GENUS_KEY.get(record.get("genusKey", "").strip())


def year_of(record: Record) -> str:
    return record.get("year", "").strip() or "no_year"


@dataclass(frozen=True)
class CountKey:
    stage: str
    group: str
    region: str
    year: str


class CountTable:
    """Tallies (stage, group, region, year). Plug add() into Pipeline.on_pass."""

    def __init__(self) -> None:
        self._counts: Counter[CountKey] = Counter()

    def add(self, stage: str, record: Record) -> None:
        region = region_of(record)
        year = year_of(record)
        self._counts[CountKey(stage, ALL_FUNGI, region, year)] += 1
        group = group_of(record)
        if group is not None:
            self._counts[CountKey(stage, group, region, year)] += 1

    def count(self, stage: str, group: str, region: str, year: str) -> int:
        return self._counts[CountKey(stage, group, region, year)]

    def rows(self) -> list[tuple[str, str, str, str, int]]:
        return sorted(
            (key.stage, key.group, key.region, key.year, n) for key, n in self._counts.items()
        )

    def write_csv(self, path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(("stage", "group", "region", "year", "records"))
            writer.writerows(self.rows())
