"""T7 re-fit, P10b condition 4 (D145; Forager RECORD -1160): herbarium specimen records.

One occurrence download from the aggregator (dispatch 2026-10-17-T7R, Phase 1 item 4): basis of
record ``PRESERVED_SPECIMEN``, with coordinates, no geospatial issue, inside the PNW box. The taxon
filter is the coder's choice: the kingdom Fungi (backbone key 5), so no genus on the membership
list can be lost to a class or phylum filter; the genus filter is applied locally, through the
same ``Join`` the presence count used (the mycorrhizal group's main run, the list V9 used).

Kept locally, and only (``classify``):

- the record's dataset licence, and the record's own licence, are both CC0 or CC BY (BY-NC is out:
  the searches report names two herbaria, Washington State's and Michigan's, under BY-NC);
- a stated coordinate uncertainty of 1,000 m or less (none stated is out);
- a genus in the mycorrhizal main run (``Join.joins``: lifestyle ectomycorrhizal, certainty
  clear; a record named only to family is out of the main run).

How a 1 km record is scored against a 250 m map, against which background, and over which
records, is not built here: those are owner-level choices (the dispatch's stop).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from forager_forecast.pnw import PNW_BOX
from forager_forecast.t4_layer import LonLatBox
from forager_forecast.t7.names import names_from_row

MAX_UNCERTAINTY_M = 1000.0
# The searches report's interior sub-box (docs/audits/2026-10-17-t7-searches.md, branch
# t7-searches, section 3.1): 42 to 49 N, 120 to 111 W.
INTERIOR = LonLatBox(south=42.0, north=49.0, west=-120.0, east=-111.0)
FUNGI_KINGDOM_KEY = 5

KEPT = "kept"
DATASET_LICENCE = "dataset licence not CC0 or CC BY"
RECORD_LICENCE = "record licence not CC0 or CC BY"
NO_UNCERTAINTY = "no stated coordinate uncertainty"
UNCERTAINTY_OVER = "coordinate uncertainty over 1,000 m"
NOT_IN_MAIN_RUN = "not in the mycorrhizal main run"
UNCERTAINTY_BANDS = ((0.0, 100.0), (100.0, 250.0), (250.0, 500.0), (500.0, 1000.0))

# The aggregator writes licences as URLs (dataset records) or as codes (occurrence records).
_LICENCES = {
    "CC0": ("creativecommons.org/publicdomain/zero/1.0", "CC0_1_0"),
    "CC BY": ("creativecommons.org/licenses/by/4.0", "CC_BY_4_0"),
}


def specimen_predicate(box: LonLatBox = PNW_BOX) -> dict:
    """The download's predicate. The box as a counter-clockwise WKT polygon, the winding the
    aggregator requires (``t1_design.Box.wkt_polygon``)."""
    polygon = (
        f"POLYGON(({box.west} {box.south},{box.east} {box.south},{box.east} {box.north},"
        f"{box.west} {box.north},{box.west} {box.south}))"
    )
    return {
        "type": "and",
        "predicates": [
            {"type": "equals", "key": "TAXON_KEY", "value": str(FUNGI_KINGDOM_KEY)},
            {"type": "equals", "key": "BASIS_OF_RECORD", "value": "PRESERVED_SPECIMEN"},
            {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
            {"type": "equals", "key": "HAS_GEOSPATIAL_ISSUE", "value": "false"},
            {"type": "within", "geometry": polygon},
        ],
    }


def licence_class(text: str) -> str | None:
    """ "CC0" or "CC BY" for those licences, in either of the aggregator's spellings; None for
    anything else, BY-NC and BY-SA included."""
    t = (text or "").strip()
    for name, (url_part, code) in _LICENCES.items():
        if t == code:
            return name
        if url_part in t and t.rstrip("/").split(url_part, 1)[1] in ("", "/legalcode"):
            return name
    return None


def uncertainty_m(row: Mapping[str, str]) -> float | None:
    text = (row.get("coordinateUncertaintyInMeters") or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def classify(row: Mapping[str, str], dataset_licence: str, join) -> str:
    """``KEPT``, or the first reason the record is out, in this order: dataset licence, record
    licence, uncertainty, genus."""
    if licence_class(dataset_licence) is None:
        return DATASET_LICENCE
    if licence_class(row.get("license", "")) is None:
        return RECORD_LICENCE
    u = uncertainty_m(row)
    if u is None:
        return NO_UNCERTAINTY
    if u > MAX_UNCERTAINTY_M:
        return UNCERTAINTY_OVER
    if not join.joins(names_from_row(row)):
        return NOT_IN_MAIN_RUN
    return KEPT


def assert_open_licences(kept_rows: Iterable[Mapping[str, str]],
                         dataset_licences: Mapping[str, str]) -> None:  # fmt: skip
    """The dispatch's stop: a licence other than CC0 or CC BY entering the specimen set."""
    for row in kept_rows:
        key = row.get("datasetKey", "")
        if licence_class(dataset_licences.get(key, "")) is None:
            raise RuntimeError(f"dataset {key}: licence {dataset_licences.get(key)!r} in the set")
        if licence_class(row.get("license", "")) is None:
            raise RuntimeError(f"record licence {row.get('license')!r} in the set ({key})")


def uncertainty_band(u: float) -> str:
    """The report's uncertainty bands over the kept range (0 to 1,000 m), upper edges inclusive."""
    for low, high in UNCERTAINTY_BANDS:
        if (low == 0.0 and u <= high) or low < u <= high:
            return f"{low:g} to {high:g} m" if low else f"up to {high:g} m"
    raise ValueError(f"uncertainty {u} is outside the kept range")
