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

import csv
import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

from forager_forecast.t7.names import TaxonNames

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
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def _clean(text: str) -> str:
    return " ".join(str(text).replace("\t", " ").split())


def write_list(path: Path, rows: list[ListRow]) -> str:
    """Write rows in the normalised format; returns the file's sha256."""
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE,
                   escapechar=None)  # fmt: skip
    w.writerow(COLUMNS)
    for r in sorted(rows, key=lambda r: r.genus):
        key = "" if r.genus_key is None else str(r.genus_key)
        w.writerow([_clean(v) for v in (r.genus, key, r.family, r.lifestyle, r.certainty,
                                        r.source_id, r.note)])  # fmt: skip
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(buf.getvalue(), encoding="utf-8")
    partial.rename(path)
    return file_sha256(path)


@dataclass(frozen=True)
class MembershipList:
    rows: dict[str, ListRow]
    sha256: str

    @property
    def fingerprint(self) -> str:
        return self.sha256


def load_list(path: Path, expected_sha256: str) -> MembershipList:
    actual = file_sha256(path)
    if actual != expected_sha256:
        raise MembershipListError(
            f"{Path(path).name}: sha256 {actual} is not the recorded {expected_sha256}"
        )
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines or lines[0].split("\t") != list(COLUMNS):
        raise MembershipListError(f"{Path(path).name}: header is not {COLUMNS}")
    rows: dict[str, ListRow] = {}
    for n, line in enumerate(lines[1:], start=2):
        parts = line.split("\t")
        if len(parts) != len(COLUMNS):
            raise MembershipListError(f"line {n}: {len(parts)} columns, not {len(COLUMNS)}")
        genus, key, family, lifestyle, certainty, source_id, note = (p.strip() for p in parts)
        if not genus:
            raise MembershipListError(f"line {n}: no genus")
        if genus in rows:
            raise MembershipListError(f"line {n}: genus {genus!r} listed twice")
        if lifestyle not in LIFESTYLES:
            raise MembershipListError(f"line {n}: lifestyle {lifestyle!r} not in {LIFESTYLES}")
        if certainty not in CERTAINTIES:
            raise MembershipListError(f"line {n}: certainty {certainty!r} not in {CERTAINTIES}")
        try:
            genus_key = int(key) if key else None
        except ValueError as error:
            raise MembershipListError(f"line {n}: genus_key {key!r} not an integer") from error
        rows[genus] = ListRow(genus, genus_key, family, lifestyle, certainty, source_id, note)
    return MembershipList(rows, actual)


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
        if members.fingerprint != expected_fingerprint:
            raise MembershipListError(
                f"list fingerprint {members.fingerprint} is not the expected {expected_fingerprint}"
            )
        if run not in (MAIN_RUN, SIDE_RUN):
            raise ValueError(f"run {run!r} is neither {MAIN_RUN!r} nor {SIDE_RUN!r}")
        if (group.lifestyle is None) == (not group.genera):
            raise ValueError("a group is defined by a lifestyle or by genera, not both or neither")
        self.members, self.group, self.run = members, group, run
        families: dict[str, list[ListRow]] = {}
        for row in members.rows.values():
            if row.family:
                families.setdefault(row.family, []).append(row)
        self._family_wholly_in = {
            f: group.lifestyle is not None and all(r.lifestyle == group.lifestyle for r in rows)
            for f, rows in families.items()
        }

    def outcome(self, names: TaxonNames) -> str:
        if self.group.genera:
            if names.genus in self.group.genera:
                return IN_GROUP
            if not names.genus:
                return NO_NAME if not names.family else FAMILY_ONLY_OUT
            return NOT_IN_GROUP if names.genus in self.members.rows else NOT_LISTED
        if names.genus:
            row = self.members.rows.get(names.genus)
            if row is None:
                return NOT_LISTED
            if row.lifestyle != self.group.lifestyle:
                return NOT_IN_GROUP
            if row.certainty == "clear" or self.run == SIDE_RUN:
                return IN_GROUP
            return SIDE_ONLY
        if not names.family:
            return NO_NAME
        if self._family_wholly_in.get(names.family, False):
            return IN_GROUP if self.run == SIDE_RUN else FAMILY_ONLY_SIDE
        return FAMILY_ONLY_OUT

    def joins(self, names: TaxonNames) -> bool:
        return self.outcome(names) == IN_GROUP


def ectomycorrhizal_overlap(genera, members: MembershipList) -> dict[str, str]:
    """The given genera that the list classes ectomycorrhizal, each with its certainty ("clear"
    is the mycorrhizal group's main run; "mixed" and "uncertain" its side run). A comparison group
    must return none (T7 part C)."""
    return {
        g: members.rows[g].certainty
        for g in genera
        if g in members.rows and members.rows[g].lifestyle == "ectomycorrhizal"
    }
