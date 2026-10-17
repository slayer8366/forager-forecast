"""T7 re-fit, P10b condition 4 (D145; Forager RECORD -1160): herbarium specimen records."""

from __future__ import annotations

from forager_forecast.pnw import PNW_BOX
from forager_forecast.t4_layer import LonLatBox

MAX_UNCERTAINTY_M = 1000.0
INTERIOR = LonLatBox(south=42.0, north=49.0, west=-120.0, east=-111.0)
KEPT = "kept"


def specimen_predicate(box: LonLatBox = PNW_BOX) -> dict:
    raise NotImplementedError


def licence_class(text: str) -> str | None:
    raise NotImplementedError


def classify(row, dataset_licence: str, join) -> str:
    raise NotImplementedError


def assert_open_licences(kept_rows, dataset_licences: dict) -> None:
    raise NotImplementedError
