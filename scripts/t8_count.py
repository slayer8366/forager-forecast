"""T8's count: the jump check (J1 to J6) and the lichen attach, under the owner's first word
(plan section 9, item 2; D133 (8)). The work is forager_forecast.t8.count.run_count.

Run, only once the owner's word to count is relayed and every count reading is ruled
(design.require_ruled refuses otherwise):

    systemd-run --user --unit=t8-count -p MemoryMax=3G -p MemorySwapMax=0 -p Nice=10 \\
        --working-directory=$PWD .venv/bin/python scripts/t8_count.py \\
        --out ~/Zynergy/forecast-data/t8/count

Reads D26's zip in place (sha256 from its pull record, checked first) and T1's unit files; reads no
weather. Refuses with uncommitted tracked files, and refuses an output folder that already holds
anything.
"""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from forager_forecast.t8 import count as tc

REPO = Path(__file__).resolve().parents[1]
DOI_RECORD = REPO / "docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json"
D26_ZIP = (
    Path.home() / "Zynergy/forager-forecast-d26/data/d26/downloads/0012112-260928105237408.zip"
)
FITS = Path.home() / "Zynergy/forecast-data-pnw-pilot/fits"


def log(msg: str) -> None:
    print(f"{datetime.now(UTC).isoformat(timespec='seconds')} {msg}", flush=True)


def code_state() -> tuple[str, str]:
    def git(*a: str) -> str:
        return subprocess.run(
            ["git", *a], capture_output=True, text=True, check=True, cwd=REPO
        ).stdout.strip()

    return git("rev-parse", "HEAD"), git("status", "--porcelain", "--untracked-files=no")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path, default=D26_ZIP)
    ap.add_argument("--fits", type=Path, default=FITS)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--species-rule", choices=["speciesKey", "taxonRank"], default="speciesKey")
    args = ap.parse_args()
    commit, dirty = code_state()
    if dirty:
        raise SystemExit(f"tracked files are uncommitted; commit before counting:\n{dirty}")
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"{args.out} already holds files; a count never writes over another")
    expected = json.loads(DOI_RECORD.read_text())["sha256_of_zip"]
    summary = tc.run_count(args.zip, expected, args.fits, args.out, args.species_rule, log)
    summary_path = args.out / "count_summary.json"
    data = json.loads(summary_path.read_text())
    data["commit"] = commit
    summary_path.write_text(json.dumps(data, indent=2) + "\n")
    log(f"jump check: {summary['jump']['label']}; {summary['seconds']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
