"""T7 item 6: the presence list, thinned and weighted (P2, M2, M3).

From typed, named records to presences of one group, one run:

1. R6's step list (``records/filters.r6_audit_steps``: not user-obscured, uncertainty present and
   at most 250 m, the date kept as given, D27's observer duplicate key), run through the shared
   ``Pipeline`` so every step is counted.
2. The box test by the 250 m cell's centre (the PNW box, plan "The box"), the record placed in its
   master-grid cell first.
3. The membership join (``t7/membership.Join``), each outcome counted.
4. SPEC R6's own check on what remains: no record above 250 m reaches the table; one that does
   stops the run (plan, abort conditions).

Then thinning and weighting. **Both are proposals (P2 and V9 (e) are not ruled)**, and the values
below are the coder's, to be fixed by the owner before any presence is counted:

- Thinning: one presence per genus and 250 m cell, the lowest gbifID kept, so one person's many
  photos of one patch count once, and two genera in one cell count as two.
- Weighting, M3 (b) (RECORD -1030, provisional): every genus at or above
  ``PROPOSED_MIN_PRESENCES_PER_GENUS`` thinned presences carries the same total weight, 1; the
  genera below it are pooled and carry 1 together ("reported but not weighted on their own").
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

from forager_forecast.records.filters import r6_audit_steps  # noqa: F401
from forager_forecast.records.occurrence import Record
from forager_forecast.t4_layer import LonLatBox
from forager_forecast.t7.membership import Join
from forager_forecast.t7.names import TaxonNames

_STUB = "T7 build: not written yet (tests first)"

PROPOSED_MIN_PRESENCES_PER_GENUS = 30
POOLED = "(genera under the minimum, pooled)"
OUTSIDE_BOX = "outside the box (250 m cell centre)"


class R6Violation(RuntimeError):
    """A record above 250 m reached the presence table (SPEC R6)."""


@dataclass(frozen=True)
class Presence:
    gbif_id: int
    genus: str
    cell_id: int
    lat_tenths: int
    lon_tenths: int
    year: int
    uncertainty_m: float
    license: str


@dataclass
class PresenceCounts:
    r6_steps: list
    outcomes: Counter

    def as_dict(self) -> dict:
        raise NotImplementedError(_STUB)


def select_presences(
    named: Iterable[tuple[Record, TaxonNames]], join: Join, box: LonLatBox
) -> tuple[list[Presence], PresenceCounts]:
    raise NotImplementedError(_STUB)


def thin(presences: Iterable[Presence]) -> list[Presence]:
    raise NotImplementedError(_STUB)


@dataclass(frozen=True)
class GenusWeights:
    weights: np.ndarray
    unit_of: dict[str, str]
    presences_per_unit: dict[str, int]


def genus_weights(presences: list[Presence], min_presences: int) -> GenusWeights:
    raise NotImplementedError(_STUB)
