"""Write the committed FungalTraits export and its provenance file (D143, Forager RECORD -1081).

Usage: python scripts/t7_fungaltraits_export.py [workbook] [out_dir]

Reads the workbook outside the repository (refused unless its size, MD5 and sha256 are the ones
recorded at the single fetch), writes one deterministic gzip CSV per sheet to
``reference/fungaltraits-2020/``, compares every cell back against the workbook (refused on any
mismatch), and writes ``provenance.json`` beside them. Running it twice gives the same bytes.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

from forager_forecast.t7 import fungaltraits as ft
from forager_forecast.t7.membership import file_sha256
from forager_forecast.t7.table_export import compare_export, export_workbook

CONSENT = {
    "from": "Dr Sergei Põlme, corresponding author of Põlme et al. 2020",
    "to": "the owner (Brandon), with Dr Leho Tedersoo copied",
    "received": "2026-10-16 00:22, the owner's time (Pacific); Forager RECORD 2026-09-28-1080",
    "answering": (
        "the owner's request of 2026-10-15 23:09 to keep a dated, unmodified copy of the "
        "FungalTraits table in the public repository, cited and credited, for non-commercial use"
    ),
    "words_verbatim": (
        "Hi Brandon! I support such initiatives where science can contribute to public "
        "knowledge, so it is fine by me. Best Sergei"
    ),
    "caveat": (
        "The repository record marks the item '© 2021, Mushroom Research Foundation' (the "
        "journal's publisher). The corresponding author's consent is recorded as consent for this "
        "use, not as a licence from that publisher (Forager RECORD 2026-09-28-1080)."
    ),
    "owner_ruling": (
        'Forager RECORD 2026-09-28-1081; the owner, verbatim: "1 we asked for the table, why not '
        'use it? My concern is leaving behind details we may decide to use later on." and '
        '"2 yes". Decision row D143.'
    ),
}


def main(argv: list[str]) -> int:
    workbook = Path(argv[1]) if len(argv) > 1 else ft.table_path()
    out_dir = Path(argv[2]) if len(argv) > 2 else ft.EXPORT_DIR
    data = workbook.read_bytes()
    checks = {
        "size": (len(data), ft.SOURCE.size),
        "md5": (hashlib.md5(data).hexdigest(), ft.SOURCE.md5),
        "sha256": (file_sha256(workbook), ft.SOURCE.sha256),
    }
    for name, (got, want) in checks.items():
        if got != want:
            print(f"refused: workbook {name} {got} is not the recorded {want}", file=sys.stderr)
            return 1
    exports = export_workbook(workbook, out_dir)
    comparisons = []
    for e in exports:
        c = compare_export(workbook, e.sheet, out_dir / e.file_name)
        if c.mismatches:
            print(f"refused: {e.sheet}: {c.mismatches}", file=sys.stderr)
            return 1
        comparisons.append(c)
    provenance = {
        "what": (
            "FungalTraits, Table S1 'Traits of genera', every sheet, row and column of the "
            "workbook's cell values, one gzip-compressed UTF-8 CSV per sheet. Line r of a CSV is "
            "the sheet's row r; field c is its column c. Unmodified: no cell is edited, added or "
            "dropped. Not carried: cell styles, column widths, row heights, rich-text formatting "
            "inside 3 strings (their text is kept), saved filter views, the thumbnail and document "
            "properties. The workbook has no formulas and no numeric cells; every non-empty cell "
            "is a shared string."
        ),
        "citation": (
            "Põlme, S., Abarenkov, K., Henrik Nilsson, R. et al. FungalTraits: a user-friendly "
            "traits database of fungi and fungus-like stramenopiles. Fungal Diversity 105, 1-16 "
            "(2020). https://doi.org/10.1007/s13225-020-00466-2"
        ),
        "source": {
            "url": ft.SOURCE.url,
            "record": ft.SOURCE.landing,
            "record_handle": "2263/80202",
            "repository": "University of Pretoria institutional repository (UPSpace)",
            "item": "a8309ba3-aa1a-4324-8969-5c7980fa88b6",
            "file_name": ft.SOURCE.file_name,
            "fetched_utc": ft.SOURCE.fetched_utc,
            "size_bytes": ft.SOURCE.size,
            "md5": ft.SOURCE.md5,
            "sha256": ft.SOURCE.sha256,
            "size_and_md5_checked_against": "the repository's own stated values, at the fetch",
            "rights_field_as_seen": ft.SOURCE.rights_as_stated,
            "licence": "none stated at source (Forager RECORD 2026-09-28-1036)",
        },
        "consent": CONSENT,
        "exports": [asdict(e) for e in exports],
        "check": [
            {
                "sheet": c.sheet,
                "stored_rows": c.stored_rows,
                "cells_compared": c.cells_compared,
                "non_empty_cells": c.non_empty_cells,
                "formulas": c.formulas,
                "mismatches": len(c.mismatches),
            }
            for c in comparisons
        ],
        "written_by": "scripts/t7_fungaltraits_export.py",
        "decision": "D143",
    }
    text = json.dumps(provenance, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "provenance.json").write_text(text, encoding="utf-8")
    for e in exports:
        print(f"{e.file_name}: {e.rows} rows x {e.columns} columns, {e.gz_size} bytes, "
              f"sha256 {e.gz_sha256}")  # fmt: skip
    for c in comparisons:
        print(f"{c.sheet}: {c.cells_compared} cells compared, {c.non_empty_cells} non-empty, "
              f"{c.formulas} formulas, 0 mismatches")  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
