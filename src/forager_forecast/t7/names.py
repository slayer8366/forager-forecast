"""T7 item 4: genus and family names from the D26 download, beside each typed Record.

``records/occurrence.py`` reads ``acceptedTaxonKey`` and ``genusKey`` only (T7 verify report V16).
A membership list of genus names joins to records on the names the download itself carries
(``genus``, ``family``, ``order``, ``taxonRank``; header columns 166, 162, 160 and 173 of D26's
``occurrence.txt``, V16), offline, never through GBIF's matching API (plan, "Do not touch").

This is a new path beside the loader, not a change to it: ``load_named`` feeds each row to the
existing ``OccurrenceLoader`` one at a time, so a row that cannot become a Record is counted by
the loader's own reasons (D66) and gets no names.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass

from forager_forecast.records.occurrence import OccurrenceLoader, Record

_STUB = "T7 build: not written yet (tests first)"

NAME_COLUMNS = ("genus", "family", "order", "taxonRank")


@dataclass(frozen=True, slots=True)
class TaxonNames:
    genus: str
    family: str
    order: str
    rank: str


def missing_name_columns(fieldnames: Iterable[str] | None) -> list[str]:
    raise NotImplementedError(_STUB)


def names_from_row(row: Mapping[str, str]) -> TaxonNames:
    raise NotImplementedError(_STUB)


def load_named(
    rows: Iterable[Mapping[str, str]], loader: OccurrenceLoader
) -> Iterator[tuple[Record, TaxonNames]]:
    raise NotImplementedError(_STUB)
