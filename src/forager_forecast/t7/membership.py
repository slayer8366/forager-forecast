"""T7 item 5: the membership list this project owns, and the join of records to it.

Domain code knows only this list's format, never any published table's columns (the planner's
design requirement of 2026-10-16, from the alternatives scoping in Forager
prompts/preserved/2026-10-15-11-membership-list-alternatives.md, and CLAUDE.md's "wrap external
integrations behind an interface this project owns"). A published table reaches it only through
an adapter (``t7/fungaltraits.py`` for the first one) that writes this format. Swapping the list
costs a decision row and a re-run, not code.

**The normalised format** (UTF-8, tab-separated, one header row, one row per genus):

| column | meaning |
|---|---|
| ``genus`` | genus name as GBIF's ``genus`` column spells it; unique in the file |
| ``genus_key`` | GBIF ``genusKey`` if known, else empty |
| ``family`` | family name, or empty; used only for records identified to family (M2) |
| ``lifestyle`` | ``ectomycorrhizal``, ``wood_rot`` or ``other`` |
| ``certainty`` | ``clear``, ``mixed`` or ``uncertain`` |
| ``source_id`` | which source and version the row came from |
| ``note`` | free text: why the row has its lifestyle and certainty |

``family`` is one column beyond the planner's list: M2 (RECORD -1030) handles records named only
to family, which a genus-only list cannot place.

The file's sha256 is checked before a row is read, against the value the caller records (the
manifest, a decision row); a list that differs refuses to load. Its fingerprint is that sha256, and
the join refuses a list whose fingerprint is not the one it was given.

Runs (M2 (a), RECORD -1030): the **main** run keeps genera of the group's lifestyle with certainty
``clear``; the **side** run, reported beside, adds ``mixed`` and ``uncertain`` genera of that
lifestyle and records named only to a family all of whose listed genera have that lifestyle.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forager_forecast.t7.names import TaxonNames

_STUB = "T7 build: not written yet (tests first)"

COLUMNS = ("genus", "genus_key", "family", "lifestyle", "certainty", "source_id", "note")
LIFESTYLES = ("ectomycorrhizal", "wood_rot", "other")
CERTAINTIES = ("clear", "mixed", "uncertain")
MAIN_RUN = "main"
SIDE_RUN = "side"

# Join outcomes, counted by reason.
IN_GROUP = "in group"
NOT_IN_GROUP = "genus listed, not in group"
SIDE_ONLY = "genus listed, mixed or uncertain (side run only)"
FAMILY_ONLY_SIDE = "family only, family wholly in group (side run only)"
FAMILY_ONLY_OUT = "family only, family not wholly in group"
NOT_LISTED = "genus not in the list"
NO_NAME = "no genus or family name"


class MembershipListError(ValueError):
    """The list file is malformed, or its sha256 or fingerprint is not the recorded one."""


@dataclass(frozen=True)
class ListRow:
    genus: str
    genus_key: int | None
    family: str
    lifestyle: str
    certainty: str
    source_id: str
    note: str


def file_sha256(path: Path) -> str:
    raise NotImplementedError(_STUB)


def write_list(path: Path, rows: list[ListRow]) -> str:
    """Write rows in the normalised format; returns the file's sha256."""
    raise NotImplementedError(_STUB)


@dataclass(frozen=True)
class MembershipList:
    rows: dict[str, ListRow]
    sha256: str

    @property
    def fingerprint(self) -> str:
        raise NotImplementedError(_STUB)


def load_list(path: Path, expected_sha256: str) -> MembershipList:
    raise NotImplementedError(_STUB)


@dataclass(frozen=True)
class GroupSpec:
    """A group by lifestyle from the list, or (the comparison, M4) by fixed genus names."""

    name: str
    lifestyle: str | None = None
    genera: tuple[str, ...] = ()


MYCORRHIZAL_GROUP = GroupSpec("mycorrhizal group", lifestyle="ectomycorrhizal")
# M4 (a), RECORD -1030: chicken of the woods as the comparison, read as genus Laetiporus (D109).
COMPARISON_GROUP = GroupSpec("comparison: chicken of the woods", genera=("Laetiporus",))


class Join:
    """Records' names to the group, for one run, on a list whose fingerprint was checked."""

    def __init__(self, members: MembershipList, expected_fingerprint: str, group: GroupSpec,
                 run: str) -> None:  # fmt: skip
        raise NotImplementedError(_STUB)

    def outcome(self, names: TaxonNames) -> str:
        raise NotImplementedError(_STUB)

    def joins(self, names: TaxonNames) -> bool:
        raise NotImplementedError(_STUB)
