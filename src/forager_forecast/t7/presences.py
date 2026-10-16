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
from pyproj import Transformer

from forager_forecast.grid import GEOGRAPHIC_CRS, GRID_CRS, cell_for_lonlat
from forager_forecast.records.filters import (
    R6_MAX_COORDINATE_UNCERTAINTY_M,
    Pipeline,
    r6_audit_steps,
)
from forager_forecast.records.occurrence import Record
from forager_forecast.t4_layer import LonLatBox
from forager_forecast.t7.keying import weather_cells
from forager_forecast.t7.membership import Join
from forager_forecast.t7.names import TaxonNames

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
        return {
            "r6_steps": [
                {"step": c.step, "before": c.before, "dropped": c.dropped, "after": c.after}
                for c in self.r6_steps
            ],
            "outcomes": dict(sorted(self.outcomes.items())),
        }


_TO_LONLAT = Transformer.from_crs(GRID_CRS, GEOGRAPHIC_CRS, always_xy=True)


def _centre_lonlat(cell) -> tuple[float, float]:
    lon, lat = _TO_LONLAT.transform(*cell.center)
    return float(lon), float(lat)


def select_presences(
    named: Iterable[tuple[Record, TaxonNames]], join: Join, box: LonLatBox
) -> tuple[list[Presence], PresenceCounts]:
    names_of: dict[int, TaxonNames] = {}

    def records():
        for record, names in named:
            names_of[record.gbif_id] = names
            yield record

    pipeline = Pipeline(r6_audit_steps())
    survivors = pipeline.run(records())
    outcomes: Counter = Counter()
    presences: list[Presence] = []
    for record in survivors:
        cell = cell_for_lonlat(record.longitude, record.latitude)
        lon, lat = _centre_lonlat(cell)
        if not bool(box.contains(lon, lat)):
            outcomes[OUTSIDE_BOX] += 1
            continue
        names = names_of[record.gbif_id]
        outcome = join.outcome(names)
        outcomes[outcome] += 1
        if not join.joins(names):
            continue
        u = record.coordinate_uncertainty_m
        if u is None or u > R6_MAX_COORDINATE_UNCERTAINTY_M:
            raise R6Violation(f"gbifID {record.gbif_id}: uncertainty {u} m reached the table")
        lat_t, lon_t = weather_cells(np.array([record.longitude]), np.array([record.latitude]))
        presences.append(Presence(
            record.gbif_id, names.genus or f"(family {names.family})", cell.id, int(lat_t[0]),
            int(lon_t[0]), record.event_date.year, float(u), record.license,
        ))  # fmt: skip
    return presences, PresenceCounts(pipeline.counts, outcomes)


def thin(presences: Iterable[Presence]) -> list[Presence]:
    kept: dict[tuple[str, int], Presence] = {}
    for p in presences:
        key = (p.genus, p.cell_id)
        if key not in kept or p.gbif_id < kept[key].gbif_id:
            kept[key] = p
    return sorted(kept.values(), key=lambda p: p.gbif_id)


@dataclass(frozen=True)
class GenusWeights:
    weights: np.ndarray
    unit_of: dict[str, str]
    presences_per_unit: dict[str, int]


def genus_weights(presences: list[Presence], min_presences: int) -> GenusWeights:
    per_genus = Counter(p.genus for p in presences)
    unit_of = {g: (g if n >= min_presences else POOLED) for g, n in per_genus.items()}
    per_unit = Counter()
    for g, n in per_genus.items():
        per_unit[unit_of[g]] += n
    weights = np.array([1.0 / per_unit[unit_of[p.genus]] for p in presences])
    return GenusWeights(weights, unit_of, dict(per_unit))
