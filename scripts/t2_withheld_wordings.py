"""Tally the distinct informationWithheld wordings in a DWCA download, digits normalised.

Usage: uv run python scripts/t2_withheld_wordings.py <download.zip>

This is the second pass behind the "withheld texts" table of the T2 credentialed run report
(data/t2/counts/withheld_wordings.txt): the run script's 40-character prefix tally cut the number
inside "increased to 27840m" and so counted one wording many times. Here every digit run is
replaced by N before counting, and the tally is also given by publisher and for Cantharellus
(genusKey 9623860). Reads occurrence.txt straight out of the zip and writes nothing. Filed after
the report because the T2 credentialed run review found the table not reproducible from the repo.
"""

import io
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

CANTHARELLUS_GENUS_KEY = "9623860"


def main(zip_path: Path) -> None:
    archive = zipfile.ZipFile(zip_path)
    with archive.open("occurrence.txt") as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        header = text.readline().rstrip("\r\n").split("\t")
        withheld_at = header.index("informationWithheld")
        generalized_at = header.index("dataGeneralizations")
        dataset_at = header.index("datasetKey")
        genus_at = header.index("genusKey")
        wording: Counter[str] = Counter()
        by_dataset: Counter[str] = Counter()
        rows = generalized = cantharellus = 0
        for line in text:
            rows += 1
            columns = line.rstrip("\n").split("\t")
            if columns[generalized_at].strip():
                generalized += 1
            withheld = columns[withheld_at].strip()
            if withheld:
                wording[re.sub(r"\d+", "N", withheld)[:90]] += 1
                by_dataset[columns[dataset_at]] += 1
                if columns[genus_at] == CANTHARELLUS_GENUS_KEY:
                    cantharellus += 1
    print("rows read:", rows)
    print("rows with non-empty dataGeneralizations:", generalized)
    print(
        "rows with non-empty informationWithheld:",
        sum(wording.values()),
        "; of which Cantharellus:",
        cantharellus,
    )
    print("distinct wordings (digits normalised to N):", len(wording))
    for text_, n in wording.most_common(20):
        print(f"  {n:>8}  {text_}")
    print("withheld rows by datasetKey:")
    for dataset, n in by_dataset.most_common(10):
        print(f"  {n:>8}  {dataset}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
