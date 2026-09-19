"""The R6 filter pipeline for GBIF occurrence records, every step counted.

A record is one row of a GBIF Darwin Core Archive occurrence.txt: a mapping from column name to
text, as csv.DictReader yields it. The pipeline reads records and never writes to them. Its input
is a stream, so a 2.5 million row table (the size of the shared pull on 2026-09-18, GBIF search
API count) passes through without being held in memory; only the duplicate step keeps state, a set
of 16-byte digests.

The four steps are the four the dispatch names, in the dispatch's order
(docs/dispatch/2026-09-18-t2-record-audit.md, "Then build"):

1. user_obscured
2. coordinate_uncertainty (above 250 m or missing; R6)
3. default_first_of_month_date
4. duplicate_observer_cell_day

Nothing is dropped from any source. A step returns True to say "this record does not flow on", and
the pipeline counts it under that step. The counts and the survivors are what T2 reports.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import math
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path

Record = Mapping[str, str]

# SPEC.md R6: "coordinate uncertainty above 250 m" never reaches habitat training. Fixed by the
# spec and the dispatch's do-not-touch list; not a parameter of any function here.
R6_MAX_COORDINATE_UNCERTAINTY_M = 250

# The weather cell that defines sighting chance is the 0.1 degree cell (D19, accepted in D21).
# The duplicate step's "cell" is this cell.
WEATHER_CELL_DEGREES = 0.1


def is_user_obscured(record: Record) -> bool:
    """True when the publisher says the coordinates were withheld or generalised.

    On GBIF an obscured iNaturalist record carries informationWithheld "Coordinate uncertainty
    increased to NNNNNm at the request of the observer" and a coordinateUncertaintyInMeters of
    about 26 to 29 km (T2 report, spot checks of 2026-09-18; 177 of a 900-record sample, all of
    that form). dataGeneralizations was empty on every sampled record; it is read anyway because
    Darwin Core defines it for exactly this purpose and other publishers in the pull may use it.
    Any non-empty text in either counts, so a taxon-geoprivacy obscuring, should one ever appear,
    lands here too rather than passing as open.
    """
    return bool(record.get("informationWithheld", "").strip()) or bool(
        record.get("dataGeneralizations", "").strip()
    )


def coordinate_uncertainty_m(record: Record) -> float | None:
    """The uncertainty radius in metres, or None when missing or not a number."""
    text = record.get("coordinateUncertaintyInMeters", "").strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


def exceeds_r6_uncertainty(record: Record) -> bool:
    """True when the uncertainty is above 250 m or missing. Exactly 250 m passes."""
    value = coordinate_uncertainty_m(record)
    return value is None or value > R6_MAX_COORDINATE_UNCERTAINTY_M


def is_default_first_of_month_date(record: Record) -> bool:
    """True for a date on the first of a month with no time or a time of 00:00:00.

    That is the shape a default date takes when a source knew only the month: the T1 dispatch
    words it "first of month at 00:00:00". A first-of-month date that carries a real clock time is
    a real observation and passes. Ranges ("2019-08-01/2019-08-31"), month-only dates ("2019-08")
    and empty dates are not this step's concern and pass; the dispatch names no step for them, and
    the report says how many there were.
    """
    text = record.get("eventDate", "").strip()
    if not text or "/" in text:
        return False
    day_part, _, time_part = text.partition("T")
    try:
        day = dt.date.fromisoformat(day_part)
    except ValueError:
        return False
    if day.day != 1:
        return False
    return time_part == "" or time_part.startswith("00:00:00")


def weather_cell(latitude: float, longitude: float) -> tuple[int, int]:
    """The 0.1 degree cell holding a point, as integer row and column indices (floor)."""
    scale = round(1 / WEATHER_CELL_DEGREES)
    # Round to a millionth of a degree first so a value read as 47.7999999999 from text that meant
    # 47.8 does not fall into the cell below.
    return math.floor(round(latitude * scale, 6)), math.floor(round(longitude * scale, 6))


def observation_day(record: Record) -> str:
    """The calendar day as text, "YYYY-MM-DD", or the raw eventDate when it is not that shape."""
    text = record.get("eventDate", "").strip()
    return text[:10] if len(text) >= 10 else text


def duplicate_key(record: Record) -> str:
    """Observer, 0.1 degree cell and day. Two records with the same key are duplicates."""
    observer = record.get("recordedBy", "").strip()
    try:
        cell = weather_cell(float(record["decimalLatitude"]), float(record["decimalLongitude"]))
        cell_text = f"{cell[0]},{cell[1]}"
    except KeyError, ValueError:
        cell_text = "no-cell"
    return f"{observer}|{cell_text}|{observation_day(record)}"


class DuplicateObserverCellDay:
    """Stateful: the first record with a key flows on, every later one with that key is dropped.

    Keeps a 16-byte BLAKE2b digest per distinct key rather than the key text, so 2.5 million keys
    cost tens of megabytes, not hundreds, on a machine sharing 11 GB with other sessions. A fresh
    instance per pipeline run; default_steps() makes one.
    """

    def __init__(self) -> None:
        self._seen: set[bytes] = set()

    def __call__(self, record: Record) -> bool:
        digest = hashlib.blake2b(duplicate_key(record).encode("utf-8"), digest_size=16).digest()
        if digest in self._seen:
            return True
        self._seen.add(digest)
        return False


@dataclass(frozen=True)
class FilterStep:
    name: str
    drops: Callable[[Record], bool]


def default_steps() -> list[FilterStep]:
    """The dispatch's four steps in the dispatch's order, with fresh state."""
    return [
        FilterStep("user_obscured", is_user_obscured),
        FilterStep("coordinate_uncertainty", exceeds_r6_uncertainty),
        FilterStep("default_first_of_month_date", is_default_first_of_month_date),
        FilterStep("duplicate_observer_cell_day", DuplicateObserverCellDay()),
    ]


@dataclass
class StepCount:
    step: str
    before: int = 0
    dropped: int = 0

    @property
    def after(self) -> int:
        return self.before - self.dropped


@dataclass
class Pipeline:
    """Runs the steps over a stream and counts what each one drops.

    run() is a generator: it yields the records that pass every step, in input order, and fills
    counts as it goes. Read counts only after the generator is exhausted. Pass on_pass to see each
    record as it clears each stage (the count table hooks in there); the stage name "source" is
    called for every record before any step.
    """

    steps: list[FilterStep] = field(default_factory=default_steps)
    on_pass: Callable[[str, Record], None] | None = None
    counts: list[StepCount] = field(init=False)
    source_count: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        names = [step.name for step in self.steps]
        if len(set(names)) != len(names):
            raise ValueError(f"step names repeat: {names}")
        self.counts = [StepCount(step.name) for step in self.steps]

    def run(self, source: Iterable[Record]) -> Iterator[Record]:
        for record in source:
            self.source_count += 1
            if self.on_pass is not None:
                self.on_pass("source", record)
            for step, count in zip(self.steps, self.counts, strict=True):
                count.before += 1
                if step.drops(record):
                    count.dropped += 1
                    break
                if self.on_pass is not None:
                    self.on_pass(step.name, record)
            else:
                yield record


def read_occurrence_table(path: Path) -> Iterator[Record]:
    """Stream the rows of a GBIF Darwin Core Archive occurrence.txt (or verbatim.txt).

    Tab separated, one header row, no quoting: GBIF writes these tables with QUOTE_NONE and
    escapes tabs and newlines inside values, so a reader that honoured quotes would mis-split on a
    stray double quote in a remark. Opened read-only and never written back.
    """
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            yield {key: (value if value is not None else "") for key, value in row.items()}
