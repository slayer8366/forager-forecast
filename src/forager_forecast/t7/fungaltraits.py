"""The FungalTraits adapter: its genus table to this project's normalised membership list.

History. D142 (Forager RECORD -1071) built T7 on FungalTraits ahead of the authors' permission,
with the table kept outside every repository. Dr Sergei Põlme, the corresponding author, then
agreed to a dated copy in this public repository (RECORD -1080), and the owner ruled that the
whole table is committed (RECORD -1081, D143). So, since D143:

- The table is read from the committed export in ``reference/fungaltraits-2020/``
  (``EXPORT_DATA``, the ``data`` sheet as gzip CSV; ``t7/table_export.py``), refused unless its
  sha256 is the one recorded in ``EXPORT_DATA_SHA256`` and in that folder's ``provenance.json``.
  The export holds every sheet, row and column of the workbook's cell values; a test matches it
  cell by cell against the workbook wherever the workbook is present.
- The workbook itself stays outside the repository (1,243,643 bytes, over the 1 MiB guard), at a
  configured path (``FORAGER_FORECAST_FUNGALTRAITS``, default under
  ``/mnt/work/Zynergy/forecast-data/membership/``), refused unless its sha256 is the one recorded
  at the single fetch (``SOURCE`` below). ``read_traits`` still reads it, for that test and for
  the check that both routes give the same list.
- The adapter's output, the normalised list, is written outside the repository; it can be
  rewritten from the committed export at any time and its sha256 is recorded below.

Fetched once, 2026-10-16T02:03:46Z to 02:03:56Z (UTC), from the University of Pretoria repository
record http://hdl.handle.net/2263/80202 (item a8309ba3-aa1a-4324-8969-5c7980fa88b6), file
"Polme_FungalTraitsTabS1_2020.xlsx", described there as "Table S1. Traits of genera". The
repository states its size (1,243,643 bytes) and MD5 (73a66e29b7a786ba884c971b52b5b08f); both
matched. Rights as stated on the record: "© 2021, Mushroom Research Foundation. The original
publication is available at https://www.springer.com/journal/13225." No open licence is stated
(RECORD -1036 found the same).

**The conversion rule** was written as a proposal before any record was joined to it. The owner
accepted its fruitbody test as the first of the four counting rules ("mushroom-forming genera only
by FungalTraits' fruitbody type"; RECORD -1081, D144):

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
from forager_forecast.t7.table_export import read_csv_gz
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
    "https://doi.org/10.1007/s13225-020-00466-2. Table S1, committed as a lossless export with "
    "the corresponding author's consent (Forager RECORD -1080, -1081; D143)."
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
# puffball or truffle a person can find and photograph. Proposed for M1; accepted with the four
# counting rules (D144).
MUSHROOM_FRUITBODIES = frozenset({
    "agaricoid", "apothecium_(hymenium_on_surface)", "clathroid", "clavarioid", "corticioid",
    "gasteroid", "gasteroid-hypogeous", "phalloid", "polyporoid", "tremelloid",
})  # fmt: skip
RULE_VERSION = "fungaltraits-adapter-1 (ruled D144, 2026-10-16)"

# The committed export (D143). Its folder's provenance.json records the same values with the
# original's size, MD5 and sha256, the source, the rights field as seen and the consent.
EXPORT_DIR = Path(__file__).resolve().parents[3] / "reference" / "fungaltraits-2020"
EXPORT_DATA = EXPORT_DIR / "data.csv.gz"
EXPORT_DATA_SHA256 = "0826341f2c87445835aac9f4f8b579cb473a693124cc3465b09b4878724565de"
EXPORT_TRAIT_STATES = EXPORT_DIR / "trait_states.csv.gz"
EXPORT_TRAIT_STATES_SHA256 = "da6ef2e03d3276c1ddf4ea1e34564e996e9704f7db7ed09796bb9aea85126ac1"

# The normalised list ``convert_export`` writes from the committed export under RULE_VERSION
# (10,765 genera). Before D143 the list was written from the workbook by ``convert``, with sha256
# 972324a8a1e64c74408e1f6900d6661dd2fa71adb39f9f8ec24a177be40c42ed; the rows are the same, and
# only ``source_id`` differs (it names the export and the rule's ruled version). A changed rule
# writes a different list, and this value moves with a decision row.
NORMALISED_LIST_SHA256 = "436cac17b16590328e681977a40cf8ccebc9fe9aa0313eecef589dd149b309bf"


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


def _check_sha256(path: Path, expected_sha256: str) -> None:
    actual = file_sha256(path)
    if actual != expected_sha256:
        raise SourceMismatch(
            f"{Path(path).name}: sha256 {actual} is not the recorded {expected_sha256}"
        )


def read_traits(path: Path, expected_sha256: str = SOURCE.sha256) -> list[GenusTraits]:
    """From the workbook (outside the repository)."""
    _check_sha256(path, expected_sha256)
    header, rows = read_table(path, SOURCE.sheet)
    return _traits(path, header, rows)


def read_traits_export(
    path: Path = EXPORT_DATA, expected_sha256: str = EXPORT_DATA_SHA256
) -> list[GenusTraits]:
    """From the committed export of the workbook's ``data`` sheet (D143)."""
    _check_sha256(path, expected_sha256)
    grid = read_csv_gz(path)
    header = [h.strip() for h in grid[0]]

    def body():
        for row in grid[1:]:
            row = row + [""] * (len(header) - len(row))
            yield dict(zip(header, row[: len(header)], strict=True))

    return _traits(path, header, body())


def _traits(path: Path, header: list[str], rows) -> list[GenusTraits]:
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


def export_source_id(expected_sha256: str = EXPORT_DATA_SHA256) -> str:
    return (
        f"FungalTraits Table S1 data sheet, export sha256 {expected_sha256[:16]} of workbook "
        f"sha256 {SOURCE.sha256[:16]}, rule {RULE_VERSION}"
    )


def convert_export(
    out: Path, path: Path = EXPORT_DATA, expected_sha256: str = EXPORT_DATA_SHA256
) -> str:
    """Read the committed export, write the normalised list to ``out``; returns its sha256."""
    traits = read_traits_export(path, expected_sha256)
    rows = to_list_rows(traits, export_source_id(expected_sha256))
    return write_list(out, rows)


# --- T7 part C: the saprotroph comparison group (D146; Forager RECORD -1164, -1167) -------------

SAPROTROPH_LIFESTYLES = ("litter_saprotroph", "soil_saprotroph")


@dataclass(frozen=True)
class SaprotrophGenera:
    main: tuple[str, ...]
    side_only: tuple[str, ...]
    excluded_ectomycorrhizal: tuple[str, ...]


def _qualifies(t: GenusTraits) -> bool:
    return t.primary in SAPROTROPH_LIFESTYLES and t.fruitbody in MUSHROOM_FRUITBODIES


def saprotroph_genera(traits: list[GenusTraits]) -> SaprotrophGenera:
    """The saprotroph comparison group from the table's rows, sorted by genus.

    A genus qualifies when its primary lifestyle is litter or soil saprotroph (D146; not
    ``unspecified_saprotroph``, Forager RECORD -1164) and its fruitbody type is mushroom-forming
    (D144 rule 1, ``MUSHROOM_FRUITBODIES``). Of those (RECORD -1167): a genus with
    "ectomycorrhizal" in its secondary lifestyle or lifestyle comment is out (the adapter's
    ``classify`` puts these in the mycorrhizal group's side run); a genus with any other
    secondary lifestyle enters the side run only; the main run takes the rest, which have no
    secondary lifestyle. A qualifying genus on more than one row is refused: no ruling covers it."""
    rows: dict[str, list[GenusTraits]] = {}
    for t in traits:
        rows.setdefault(t.genus, []).append(t)
    main, side, out = [], [], []
    for genus, group in sorted(rows.items()):
        if not any(_qualifies(t) for t in group):
            continue
        if len(group) > 1:
            raise ValueError(f"{genus}: on {len(group)} rows, one of which meets D146; no ruling")
        t = group[0]
        if ECM in t.secondary.lower() or ECM in t.lifestyle_comment.lower():
            out.append(genus)
        elif t.secondary:
            side.append(genus)
        else:
            main.append(genus)
    return SaprotrophGenera(tuple(main), tuple(side), tuple(out))
