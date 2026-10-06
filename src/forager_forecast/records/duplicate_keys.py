"""Both of D27's duplicate keys, counted over the same records (D27: "Reports give both counts").

Each step list ends in one duplicate step: T1's in the event key, the R6 audit's in the
observer-duplicate key (records/filters.py). Neither run says what the other key would keep over the
same records. KeyTally is an on_pass sink that watches the records clearing a list's last filter,
which are exactly the records its duplicate step reads, and keeps for each named key the lowest
gbifID per key value and that record's region. Since the lowest gbifID survives a duplicate (D65),
its count and regions are what a Pipeline with that key as its duplicate step would keep. The step
lists themselves are unchanged.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Callable, Hashable, Mapping

from forager_forecast.records.counts import region_of
from forager_forecast.records.filters import Steps, event_key, observer_key
from forager_forecast.records.occurrence import Record

# D27's two named keys.
D27_KEYS: Mapping[str, Callable[[Record], Hashable]] = {
    "event": event_key,
    "observer": observer_key,
}


def _digest(key: Hashable) -> bytes:
    return hashlib.blake2b(repr(key).encode("utf-8"), digest_size=16).digest()


class KeyTally:
    """Counts, for each named key, what a duplicate step in that key would keep.

    Feed add() from Pipeline.on_pass. Only records passed with stage == at_stage are read.
    """

    def __init__(self, at_stage: str, keys: Mapping[str, Callable[[Record], Hashable]]) -> None:
        self.at_stage = at_stage
        self._keys = dict(keys)
        self._lowest: dict[str, dict[bytes, tuple[int, str]]] = {name: {} for name in self._keys}
        self.entered = 0
        self.entered_by_region: Counter[str] = Counter()
        # Records with no recordedBy share one observer in the observer key (D32 follow-up
        # report, "Not verified"); counted here, not changed.
        self.empty_observer_entered = 0

    @classmethod
    def for_steps(cls, steps: Steps) -> KeyTally:
        """A tally of D27's two keys at the stage a step list's duplicate step reads."""
        if not steps.filters:
            raise ValueError("a step list with no filters has no stage before its duplicate step")
        return cls(steps.filters[-1].name, D27_KEYS)

    def add(self, stage: str, record: Record) -> None:
        if stage != self.at_stage:
            return
        region = region_of(record)
        self.entered += 1
        self.entered_by_region[region] += 1
        if not record.recorded_by.strip():
            self.empty_observer_entered += 1
        for name, key in self._keys.items():
            table = self._lowest[name]
            digest = _digest(key(record))
            current = table.get(digest)
            if current is None or record.gbif_id < current[0]:
                table[digest] = (record.gbif_id, region)

    def survivors(self, name: str) -> int:
        return len(self._lowest[name])

    def survivors_by_region(self, name: str) -> Counter[str]:
        return Counter(region for _gbif_id, region in self._lowest[name].values())
