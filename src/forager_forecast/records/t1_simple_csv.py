# Not part of the pipeline. Kept unchanged as the evidence of T1's provisional run over SIMPLE_CSV
# download 0005709 (D67), as D30 kept the T0b verify script; the code below this header is as it
# stood at main 1d5bd80. The one Record type and filter pipeline are records/occurrence.py and
# records/filters.py.
"""Rows of a GBIF SIMPLE_CSV download, read into T1 Records.

Written for the T1 run (T1 run report, 2026-09-19) against download 0005709-260916113435855.
The format is tab separated with no quoting and one header row
(https://techdocs.gbif.org/en/data-use/download-formats, saved copy
data/t1/gbif_download_formats.txt): the reader here uses QUOTE_NONE so a stray double quote in a
locality cannot swallow a tab. Nothing here opens a file; the caller streams the zip member in.

What a SIMPLE_CSV row does not carry, and how that is handled:

- No genusKey. Record.genus_key is filled with the Cantharellus genus key when the row's kingdom
  is Fungi and its genus is Cantharellus, else None (the name is a homonym: a coral genus shares
  it, T1 completion report, "GBIF backbone keys").
- eventDate is text that may be a day, a day with a clock time, or a range. A Record needs one
  calendar day, so a row whose eventDate does not name exactly one day raises UnloadableRow with
  a reason, and the caller counts it. Nothing is guessed: a range across days is not a day, and a
  month-only date is not a day.
"""

import csv
import math
from collections.abc import Iterator, Mapping
from datetime import date, time
from typing import TextIO

from forager_forecast.records.t1_record import Record
from forager_forecast.t1_design import CANTHARELLUS_GENUS_KEY

FUNGI_KINGDOM_NAME = "Fungi"
CANTHARELLUS_GENUS_NAME = "Cantharellus"

# The columns a Record is built from. A file missing any of them cannot be loaded.
COLUMNS_READ = (
    "gbifID",
    "kingdom",
    "genus",
    "taxonKey",
    "decimalLatitude",
    "decimalLongitude",
    "coordinateUncertaintyInMeters",
    "eventDate",
    "license",
)


class UnloadableRow(ValueError):
    """A row that cannot become a Record, with the reason the caller should count it under."""

    def __init__(self, reason: str, gbif_id: str = ""):
        self.reason = reason
        self.gbif_id = gbif_id
        super().__init__(f"{reason} (gbifID {gbif_id or 'unknown'})")


def read_rows(handle: TextIO) -> Iterator[dict[str, str]]:
    """Stream the rows of a SIMPLE_CSV file as dicts of column name to text."""
    reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
    for row in reader:
        yield {key: (value if value is not None else "") for key, value in row.items()}


def missing_columns(fieldnames: Iterator[str] | list[str] | None) -> list[str]:
    present = set(fieldnames or ())
    return [column for column in COLUMNS_READ if column not in present]


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

    Accepts "2020-09-15", "2020-09-15T10:30:00", "2020-09-15T10:30:00Z", an offset suffix, and a
    range whose two ends fall on the same day (the start's clock time is kept). Raises
    UnloadableRow for an empty value, a month-only or year-only value, and a range that spans
    more than one day.
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


def record_from_row(row: Mapping[str, str]) -> Record:
    """A Record from one SIMPLE_CSV row, or UnloadableRow naming what the row lacks."""
    gbif_id_text = row.get("gbifID", "").strip()
    try:
        gbif_id = int(gbif_id_text)
    except ValueError as error:
        raise UnloadableRow("gbifID not an integer", gbif_id_text) from error
    try:
        taxon_key = int(row.get("taxonKey", "").strip())
    except ValueError as error:
        raise UnloadableRow("taxonKey empty or not an integer", gbif_id_text) from error
    latitude = _optional_float(row.get("decimalLatitude", ""))
    longitude = _optional_float(row.get("decimalLongitude", ""))
    if latitude is None or longitude is None:
        raise UnloadableRow("coordinates missing or not numbers", gbif_id_text)
    try:
        event_date, event_time = parse_event(row.get("eventDate", ""))
    except UnloadableRow as error:
        raise UnloadableRow(error.reason, gbif_id_text) from error
    is_cantharellus = (
        row.get("kingdom", "").strip() == FUNGI_KINGDOM_NAME
        and row.get("genus", "").strip() == CANTHARELLUS_GENUS_NAME
    )
    return Record(
        gbif_id=gbif_id,
        taxon_key=taxon_key,
        genus_key=CANTHARELLUS_GENUS_KEY if is_cantharellus else None,
        latitude=latitude,
        longitude=longitude,
        event_date=event_date,
        event_time=event_time,
        coordinate_uncertainty_m=_optional_float(row.get("coordinateUncertaintyInMeters", "")),
        license=row.get("license", "").strip(),
    )


def is_cantharellus(record: Record) -> bool:
    return record.genus_key == CANTHARELLUS_GENUS_KEY
