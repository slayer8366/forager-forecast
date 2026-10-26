"""Plan section 3: one more check of the 2024-25 jump, read by a rule fixed before counting.

The totals are iNaturalist's own, for Cantharellus and for all fungi in T1's box, by year. They
are counts of presences under a rule, so they sit under the counting word; this module only holds
the rule, and is tested on made-up totals. Nothing here queries iNaturalist or GBIF.

The rule (plan section 3, quoted): "if the share of chanterelle records surviving the 1,000 m
filter, or the share on GBIF-eligible licences, moved by more than a third between 2023 and 2024
*and* the same share for all fungi did not, the jump is labelled 'partly reporting'. Otherwise the
label stays 'undetermined'." Like T8's, it changes only the write-up's label.

Proposed readings (design.PENDING, step "count"): R-share-move (relative, |s1 / s0 - 1| > 1/3,
computed exactly on the counts), R-years (2023 to 2024 only), R-accuracy (at most 1,000 m, out of
all records), R-licence (CC0, CC BY, CC BY-NC), R-grade (research grade). A share with no records
behind it has nothing to read, and the label stays "undetermined".
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from forager_forecast.t8b import design
from forager_forecast.t8b.design import (
    JUMP_BASELINE_YEAR,
    JUMP_RISE_YEAR,
    JUMP_SHARE_MOVE,
    PARTLY_REPORTING,
    UNDETERMINED,
)

MOVE = JUMP_SHARE_MOVE


@dataclass(frozen=True)
class Totals:
    """One taxon's records in the box in one year."""

    records: int
    with_accuracy: int  # a stated location accuracy
    accuracy_ok: int  # a stated accuracy of at most 1,000 m (R-accuracy)
    eligible_licence: int  # CC0, CC BY or CC BY-NC (R-licence)

    def __post_init__(self) -> None:
        if min(self.records, self.with_accuracy, self.accuracy_ok, self.eligible_licence) < 0:
            raise ValueError("a total is negative")
        if not (self.accuracy_ok <= self.with_accuracy <= self.records):
            raise ValueError("accuracy totals do not nest inside the records")
        if self.eligible_licence > self.records:
            raise ValueError("licence total does not nest inside the records")

    def share(self, part: str) -> tuple[int, int]:
        return getattr(self, part), self.records


def share_moved(before: tuple[int, int], after: tuple[int, int]) -> bool:
    """(part, whole) twice: did the share move by more than a third of itself? Exact."""
    s0, s1 = Fraction(*before), Fraction(*after)
    if s0 == 0:
        return s1 != 0
    return abs(s1 / s0 - 1) > MOVE


def read_rule(chanterelle: dict[int, Totals], fungi: dict[int, Totals]) -> dict:
    """The label, with each share's movement and the reason."""
    design.require_ruled("count")
    y0, y1 = JUMP_BASELINE_YEAR, JUMP_RISE_YEAR
    for name, tallies in (("chanterelle", chanterelle), ("fungi", fungi)):
        for y in (y0, y1):
            if y not in tallies:
                raise ValueError(f"{name} totals for {y} are missing")
            if tallies[y].records == 0:
                return {
                    "label": UNDETERMINED,
                    "reason": f"no records for {name} in {y}, so no share to read",
                }
    out: dict = {"years": [y0, y1]}
    hits = []
    for key, part in (("accuracy", "accuracy_ok"), ("licence", "eligible_licence")):
        ch = share_moved(chanterelle[y0].share(part), chanterelle[y1].share(part))
        fu = share_moved(fungi[y0].share(part), fungi[y1].share(part))
        out[key] = {
            "chanterelle": [float(Fraction(*chanterelle[y].share(part))) for y in (y0, y1)],
            "fungi": [float(Fraction(*fungi[y].share(part))) for y in (y0, y1)],
            "chanterelle_moved": ch,
            "fungi_moved": fu,
        }
        if ch and not fu:
            hits.append(key)
    if hits:
        out["label"] = PARTLY_REPORTING
        out["reason"] = f"chanterelle {' and '.join(hits)} share moved by over a third; fungi's not"
    else:
        out["label"] = UNDETERMINED
        out["reason"] = "no chanterelle share moved by over a third without all fungi's moving"
    return out
