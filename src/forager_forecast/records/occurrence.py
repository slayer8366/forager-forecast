"""The one Record type and the loader that builds it from a GBIF Darwin Core Archive row.

D42 left two Record representations side by side until D32's follow-up task chose one. D66 chose
T1's frozen dataclass, extended with the DWCA fields the filter steps and count tables read, built
by one loader. Every field is parsed once, here. A row that cannot be typed raises UnloadableRow
with a reason, and OccurrenceLoader counts it by that reason rather than letting it flow on: a row
whose eventDate names no single day, or whose coordinates are missing, has no cell-week and cannot
be filtered or keyed honestly (D66, measured at 9,627 of 2,549,508 rows of download 0005714 in
docs/audits/2026-10-06-d32-followup-verify-report.md).

Rows come from occurrence.txt in a DWCA zip (D26, D45, D67). T1's SIMPLE_CSV download is not read
here; records/t1_simple_csv.py is kept unchanged as the evidence of T1's provisional run (D67).
"""

from __future__ import annotations

import csv
import math
import sys
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import date, time
from pathlib import Path
from typing import TextIO


@dataclass(frozen=True, slots=True)
class Record:
    """One occurrence, as the fields the pipeline and count tables need from a DWCA row."""

    gbif_id: int
    # The accepted GBIF taxon key at whatever rank the record was identified (D27).
    taxon_key: int
    genus_key: int | None
    latitude: float
    longitude: float
    event_date: date
    event_time: time | None
    coordinate_uncertainty_m: float | None
    license: str = ""
    dataset_key: str = ""
    recorded_by: str = ""
    information_withheld: str = ""
    data_generalizations: str = ""
    # GBIF classKey, read for T6's benchmark (D103). Not in COLUMNS_READ: a table without the
    # column loads with None here, and T6's script refuses such a table itself.
    class_key: int | None = None


# The DWCA columns a Record is built from. A file missing any of them cannot be loaded.
COLUMNS_READ = (
    "gbifID",
    "acceptedTaxonKey",
    "genusKey",
    "decimalLatitude",
    "decimalLongitude",
    "coordinateUncertaintyInMeters",
    "eventDate",
    "license",
    "datasetKey",
    "recordedBy",
    "informationWithheld",
    "dataGeneralizations",
)


class UnloadableRow(ValueError):
    """A row that cannot become a Record, with the reason the caller counts it under."""

    def __init__(self, reason: str, gbif_id: str = ""):
        self.reason = reason
        self.gbif_id = gbif_id
        super().__init__(f"{reason} (gbifID {gbif_id or 'unknown'})")


def missing_columns(fieldnames: Iterable[str] | None) -> list[str]:
    present = set(fieldnames or ())
    return [column for column in COLUMNS_READ if column not in present]


def read_occurrence_rows(handle: TextIO) -> Iterator[dict[str, str]]:
    """Stream the rows of an open occurrence.txt (or verbatim.txt) as column name to text.

    Tab separated, one header row, no quoting: GBIF writes these tables with QUOTE_NONE and
    escapes tabs and newlines inside values, so a reader that honoured quotes would mis-split on a
    stray double quote in a remark. Takes an open text handle so the table can be streamed
    straight out of the download zip without extracting it (T2 run report, 2026-09-19).
    """
    reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
    for row in reader:
        yield {key: (value if value is not None else "") for key, value in row.items()}


def read_occurrence_table(path: Path) -> Iterator[dict[str, str]]:
    """Stream the rows of an occurrence.txt on disk. Opened read-only and never written back."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        yield from read_occurrence_rows(handle)


def _parse_instant(text: str) -> tuple[date, time | None]:
    day_part, separator, clock_part = text.partition("T")
    if len(day_part) != 10:
        raise UnloadableRow("eventDate does not name a calendar day")
    try:
        day = date.fromisoformat(day_part)
    except ValueError as error:
        raise UnloadableRow("eventDate does not name a calendar day") from error
    if not separator:
        return day, None
    clock_text = clock_part.removesuffix("Z")
    for sign in "+-":
        offset_at = clock_text.find(sign)
        if offset_at > 0:
            clock_text = clock_text[:offset_at]
    try:
        clock = time.fromisoformat(clock_text)
    except ValueError as error:
        raise UnloadableRow("eventDate clock time is not readable") from error
    return day, clock.replace(tzinfo=None)


def parse_event(text: str) -> tuple[date, time | None]:
    """One calendar day and, when the value carries one, a clock time.

    T1's parser (records/t1_simple_csv.py, kept there unchanged under D67), the one D65 chose for
    both step lists. Accepts "2020-09-15", "2020-09-15T10:30:00", "2020-09-15T10:30", a "Z" or
    offset suffix, and a range whose two ends fall on the same day (the start's clock time is
    kept). Raises UnloadableRow for an empty value, a month-only or year-only value, and a range
    that spans more than one day.
    """
    text = text.strip()
    if not text:
        raise UnloadableRow("eventDate empty")
    ends = text.split("/")
    if len(ends) > 2:
        raise UnloadableRow("eventDate is not a day or a range")
    instants = [_parse_instant(end) for end in ends]
    if len(instants) == 2 and instants[0][0] != instants[1][0]:
        raise UnloadableRow("eventDate spans more than one day")
    return instants[0]


def _optional_float(text: str) -> float | None:
    text = text.strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


def _optional_int(text: str) -> int | None:
    text = text.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def record_from_row(row: Mapping[str, str]) -> Record:
    """A Record from one DWCA occurrence row, or UnloadableRow naming what the row lacks."""
    gbif_id_text = row.get("gbifID", "").strip()
    try:
        gbif_id = int(gbif_id_text)
    except ValueError as error:
        raise UnloadableRow("gbifID not an integer", gbif_id_text) from error
    taxon_key = _optional_int(row.get("acceptedTaxonKey", ""))
    if taxon_key is None:
        raise UnloadableRow("acceptedTaxonKey empty or not an integer", gbif_id_text)
    latitude = _optional_float(row.get("decimalLatitude", ""))
    longitude = _optional_float(row.get("decimalLongitude", ""))
    if latitude is None or longitude is None:
        raise UnloadableRow("coordinates missing or not numbers", gbif_id_text)
    if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
        raise UnloadableRow("coordinates out of range", gbif_id_text)
    try:
        event_date, event_time = parse_event(row.get("eventDate", ""))
    except UnloadableRow as error:
        raise UnloadableRow(error.reason, gbif_id_text) from error
    return Record(
        gbif_id=gbif_id,
        taxon_key=taxon_key,
        genus_key=_optional_int(row.get("genusKey", "")),
        latitude=latitude,
        longitude=longitude,
        event_date=event_date,
        event_time=event_time,
        coordinate_uncertainty_m=_optional_float(row.get("coordinateUncertaintyInMeters", "")),
        # Licence and publisher repeat across millions of rows; interning keeps one copy each.
        license=sys.intern(row.get("license", "").strip()),
        dataset_key=sys.intern(row.get("datasetKey", "").strip()),
        recorded_by=row.get("recordedBy", "").strip(),
        information_withheld=row.get("informationWithheld", "").strip(),
        data_generalizations=row.get("dataGeneralizations", "").strip(),
        class_key=_optional_int(row.get("classKey", "")),
    )


class OccurrenceLoader:
    """Turns rows into Records and counts, by reason, every row it cannot type (D66).

    rows_read equals the Records yielded plus the sum of unloadable, so no row goes uncounted.
    """

    def __init__(self) -> None:
        self.rows_read = 0
        self.unloadable: Counter[str] = Counter()

    def load(self, rows: Iterable[Mapping[str, str]]) -> Iterator[Record]:
        for row in rows:
            self.rows_read += 1
            try:
                record = record_from_row(row)
            except UnloadableRow as error:
                self.unloadable[error.reason] += 1
                continue
            yield record
