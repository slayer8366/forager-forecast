"""Plan section 3: the jump check's reading rule."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Totals:
    records: int
    with_accuracy: int
    accuracy_ok: int
    eligible_licence: int

def share_moved(before: tuple[int, int], after: tuple[int, int]) -> bool:
    raise NotImplementedError

def read_rule(chanterelle, fungi):
    raise NotImplementedError
