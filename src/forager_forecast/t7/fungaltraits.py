"""The FungalTraits adapter: its genus table to this project's normalised membership list.

Owner's ruling (Forager RECORD -1071, D142): build T7 on FungalTraits ahead of the authors'
permission, the table kept as a local copy only, outside every repository; nothing from it is
committed or published until permission (RECORD -1036, -1070). So:

- The table is read from a configured path (``FORAGER_FORECAST_FUNGALTRAITS``, default under
  ``/mnt/work/Zynergy/forecast-data/membership/``) and refused unless its sha256 is the one
  recorded at the single fetch (``SOURCE`` below).
- The adapter's output, the normalised list, is written beside it on /mnt/work, never into a
  repository. This module holds the conversion rule only; no genus name of the table is written
  here or in any test.

Fetched once, 2026-10-16T02:03:46Z to 02:03:56Z (UTC), from the University of Pretoria repository
record http://hdl.handle.net/2263/80202 (item a8309ba3-aa1a-4324-8969-5c7980fa88b6), file
"Polme_FungalTraitsTabS1_2020.xlsx", described there as "Table S1. Traits of genera". The
repository states its size (1,243,643 bytes) and MD5 (73a66e29b7a786ba884c971b52b5b08f); both
matched. Rights as stated on the record: "© 2021, Mushroom Research Foundation. The original
publication is available at https://www.springer.com/journal/13225." No open licence is stated
(RECORD -1036 found the same).

**The conversion rule is a proposal**, written before any record is joined to it, and needs the
owner's word before V9 (M1, M2; RECORD -1030):

- ``primary_lifestyle`` "ectomycorrhizal", no secondary lifestyle, no lifestyle comment, and a
  mushroom-forming fruitbody type (``MUSHROOM_FRUITBODIES``): ectomycorrhizal, clear.
- ``primary_lifestyle`` "ectomycorrhizal" with a secondary lifestyle or a lifestyle comment:
  ectomycorrhizal, mixed.
- ``primary_lifestyle`` "ectomycorrhizal" whose fruitbody type is not mushroom-forming or not
  given: ectomycorrhizal, uncertain (M1 keeps "the mushroom-forming genera").
- Another primary lifestyle with "ectomycorrhizal" in the secondary lifestyle or the lifestyle
  comment: ectomycorrhizal, mixed.
- ``primary_lifestyle`` "wood_saprotroph": wood_rot, clear (mixed with a secondary lifestyle).
- No primary lifestyle: other, uncertain. Any other: other, clear.
- A genus on two or more rows whose classes disagree: ectomycorrhizal if any row is, else the
  first row's lifestyle, and uncertain.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from forager_forecast.t7.membership import ListRow, file_sha256, write_list
from forager_forecast.t7.xlsx import read_table


@dataclass(frozen=True)
class SourceRecord:
    url: str
    landing: str
    file_name: str
    fetched_utc: str
    size: int
    md5: str
    sha256: str
    sheet: str
    rights_as_stated: str


SOURCE = SourceRecord(
    url="https://repository.up.ac.za/bitstreams/03249ba0-734b-4e0c-be8b-60c7accaa480/download",
    landing="http://hdl.handle.net/2263/80202",
    file_name="Polme_FungalTraitsTabS1_2020.xlsx",
    fetched_utc="2026-10-16T02:03:46Z",
    size=1_243_643,
    md5="73a66e29b7a786ba884c971b52b5b08f",
    sha256="0092d7fb8bd315b7801cc71e91c7eb889fa07f1e77dade5827b44f093b46bf2a",
    sheet="data",
    rights_as_stated=(
        "© 2021, Mushroom Research Foundation. The original publication is available at "
        "https://www.springer.com/journal/13225."
    ),
)
CITATION = (
    "Põlme, S., Abarenkov, K., Henrik Nilsson, R. et al. FungalTraits: a user-friendly traits "
    "database of fungi and fungus-like stramenopiles. Fungal Diversity 105, 1-16 (2020). "
    "https://doi.org/10.1007/s13225-020-00466-2. Table S1, local copy only (Forager RECORD -1071)."
)
PATH_ENV = "FORAGER_FORECAST_FUNGALTRAITS"
DEFAULT_PATH = Path("/mnt/work/Zynergy/forecast-data/membership") / SOURCE.file_name

COLUMNS_READ = (
    "Family",
    "GENUS",
    "primary_lifestyle",
    "Secondary_lifestyle",
    "Comment_on_lifestyle_template",
    "Fruitbody_type_template",
)
ECM = "ectomycorrhizal"
WOOD = "wood_saprotroph"
# Fruitbody types from the table's "trait states" sheet that form a mushroom, crust, coral, cup,
# puffball or truffle a person can find and photograph. Proposal, for the owner (M1).
MUSHROOM_FRUITBODIES = frozenset({
    "agaricoid", "apothecium_(hymenium_on_surface)", "clathroid", "clavarioid", "corticioid",
    "gasteroid", "gasteroid-hypogeous", "phalloid", "polyporoid", "tremelloid",
})  # fmt: skip
RULE_VERSION = "fungaltraits-adapter-1 (proposal, 2026-10-16)"
# The normalised list ``convert`` wrote from the recorded table under RULE_VERSION, on
# 2026-10-16 to /mnt/work/Zynergy/forecast-data/membership/membership_list_fungaltraits.tsv
# (10,765 genera). A hash, not an extract. A changed rule writes a different list, and this value
# moves with a decision row.
NORMALISED_LIST_SHA256 = "972324a8a1e64c74408e1f6900d6661dd2fa71adb39f9f8ec24a177be40c42ed"


class SourceMismatch(ValueError):
    """The table on disk is not the one fetched and recorded."""


def table_path(env=os.environ) -> Path:
    value = env.get(PATH_ENV)
    return Path(value) if value else DEFAULT_PATH


@dataclass(frozen=True)
class GenusTraits:
    family: str
    genus: str
    primary: str
    secondary: str
    lifestyle_comment: str
    fruitbody: str


def read_traits(path: Path, expected_sha256: str = SOURCE.sha256) -> list[GenusTraits]:
    actual = file_sha256(path)
    if actual != expected_sha256:
        raise SourceMismatch(
            f"{Path(path).name}: sha256 {actual} is not the recorded {expected_sha256}"
        )
    header, rows = read_table(path, SOURCE.sheet)
    missing = [c for c in COLUMNS_READ if c not in header]
    if missing:
        raise SourceMismatch(f"{Path(path).name}: no column {missing}")
    out = []
    for row in rows:
        genus = row["GENUS"].strip()
        if not genus:
            continue
        out.append(GenusTraits(
            row["Family"].strip(), genus, row["primary_lifestyle"].strip(),
            row["Secondary_lifestyle"].strip(), row["Comment_on_lifestyle_template"].strip(),
            row["Fruitbody_type_template"].strip(),
        ))  # fmt: skip
    return out


def classify(traits: GenusTraits) -> tuple[str, str, str]:
    """(lifestyle, certainty, note) under the proposed rule."""
    p, sec, com, fb = traits.primary, traits.secondary, traits.lifestyle_comment, traits.fruitbody
    if p == ECM:
        if sec or com:
            return "ectomycorrhizal", "mixed", f"primary {ECM}; secondary {sec!r}; comment given"
        if fb not in MUSHROOM_FRUITBODIES:
            return "ectomycorrhizal", "uncertain", f"primary {ECM}; fruitbody {fb!r} not counted"
        return "ectomycorrhizal", "clear", f"primary {ECM}; fruitbody {fb}"
    if ECM in sec.lower() or ECM in com.lower():
        return "ectomycorrhizal", "mixed", f"primary {p!r}; {ECM} in secondary or comment"
    if p == WOOD:
        certainty = "mixed" if sec else "clear"
        return "wood_rot", certainty, f"primary {WOOD}; secondary {sec!r}"
    if not p:
        return "other", "uncertain", "no primary lifestyle given"
    return "other", "clear", f"primary {p!r}"


def to_list_rows(traits: list[GenusTraits], source_id: str) -> list[ListRow]:
    by_genus: dict[str, list[GenusTraits]] = {}
    for t in traits:
        by_genus.setdefault(t.genus, []).append(t)
    rows = []
    for genus, group in by_genus.items():
        classes = [classify(t) for t in group]
        lifestyle, certainty, note = classes[0]
        if len({(c[0], c[1]) for c in classes}) > 1:
            lifestyle = ECM if any(c[0] == ECM for c in classes) else classes[0][0]
            certainty, note = (
                "uncertain",
                f"{len(group)} rows disagree: " + "; ".join(c[2] for c in classes),
            )
        rows.append(ListRow(genus, None, group[0].family, lifestyle, certainty, source_id, note))
    return rows


def convert(path: Path, out: Path, expected_sha256: str = SOURCE.sha256) -> str:
    """Read the table, write the normalised list to ``out``; returns its sha256."""
    source_id = f"FungalTraits Table S1, sha256 {expected_sha256[:16]}, rule {RULE_VERSION}"
    return write_list(out, to_list_rows(read_traits(path, expected_sha256), source_id))
